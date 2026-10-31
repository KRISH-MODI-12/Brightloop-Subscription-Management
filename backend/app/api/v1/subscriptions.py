from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.subscription import (
    Subscription, SubscriptionLine, SubscriptionStatus,
    SubscriptionStatusHistory, PaymentTerms
)
from app.models.customer import Customer
from app.models.plan import SubscriptionPlan
from app.models.product import Product, ProductVariant
from app.models.tax import Tax
from app.models.discount import Discount
from app.models.user import User, UserRole
from app.core.deps import get_current_user, get_staff_or_admin
from app.schemas.subscription import (
    SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse,
    SubscriptionActionRequest
)
from app.services.subscription_service import (
    generate_subscription_number, calculate_expiry_date,
    transition_subscription_status, renew_subscription
)
from app.services.tax_discount_service import (
    calculate_tax, evaluate_discount, record_discount_usage, round_curr
)
from app.services.audit_service import log_action

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("", response_model=List[SubscriptionResponse])
def list_subscriptions(
    customer_id: Optional[int] = None,
    plan_id: Optional[int] = None,
    status: Optional[SubscriptionStatus] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Subscription).filter(Subscription.is_deleted == False)

    # Customer isolation
    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust:
            return []
        query = query.filter(Subscription.customer_id == cust.id)
    else:
        if customer_id:
            query = query.filter(Subscription.customer_id == customer_id)

    if plan_id:
        query = query.filter(Subscription.plan_id == plan_id)
    if status:
        query = query.filter(Subscription.status == status)
    if search:
        query = query.filter(
            or_(
                Subscription.subscription_number.ilike(f"%{search}%"),
                Subscription.notes.ilike(f"%{search}%")
            )
        )

    return query.order_by(Subscription.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    sub_in: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Customer can create their own subscription, staff/admin can create for anyone
    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust or cust.id != sub_in.customer_id:
            raise HTTPException(status_code=403, detail="You can only create subscriptions for your own account.")
    else:
        cust = db.query(Customer).filter(Customer.id == sub_in.customer_id).first()

    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found.")

    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub_in.plan_id, SubscriptionPlan.is_deleted == False).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found.")

    expiry_date = sub_in.expiry_date or calculate_expiry_date(sub_in.start_date, plan.billing_frequency)

    subscription = Subscription(
        subscription_number=generate_subscription_number(db),
        customer_id=sub_in.customer_id,
        plan_id=sub_in.plan_id,
        quotation_id=sub_in.quotation_id,
        start_date=sub_in.start_date,
        expiry_date=expiry_date,
        payment_terms=sub_in.payment_terms,
        notes=sub_in.notes,
        status=SubscriptionStatus.ACTIVE if current_user.role != UserRole.CUSTOMER else SubscriptionStatus.DRAFT,
        created_by=current_user.id
    )
    db.add(subscription)
    db.flush()

    subtotal = Decimal("0.00")
    total_tax = Decimal("0.00")
    total_disc = Decimal("0.00")

    # If no lines provided, auto-create one line from the plan and its product
    lines_to_add = sub_in.lines
    if not lines_to_add:
        line_sub = plan.price * plan.min_quantity
        sub_line = SubscriptionLine(
            subscription_id=subscription.id,
            product_id=plan.product_id,
            quantity=plan.min_quantity,
            unit_price=plan.price,
            tax_amount=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            line_total=line_sub
        )
        db.add(sub_line)
        subtotal += line_sub
    else:
        for line_in in lines_to_add:
            line_sub = round_curr(line_in.unit_price * line_in.quantity)
            line_tax = round_curr(line_in.tax_amount)
            line_disc = round_curr(line_in.discount_amount)
            line_tot = round_curr(line_sub + line_tax - line_disc)

            sub_line = SubscriptionLine(
                subscription_id=subscription.id,
                product_id=line_in.product_id,
                variant_id=line_in.variant_id,
                description=line_in.description,
                quantity=line_in.quantity,
                unit_price=line_in.unit_price,
                tax_id=line_in.tax_id,
                tax_amount=line_tax,
                discount_id=line_in.discount_id,
                discount_amount=line_disc,
                line_total=line_tot
            )
            db.add(sub_line)
            subtotal += line_sub
            total_tax += line_tax
            total_disc += line_disc

            if line_in.discount_id and line_disc > Decimal("0.00"):
                record_discount_usage(
                    db=db,
                    discount_id=line_in.discount_id,
                    customer_id=cust.id,
                    amount=line_disc,
                    subscription_id=subscription.id
                )

    subscription.subtotal = subtotal
    subscription.tax_amount = total_tax
    subscription.discount_amount = total_disc
    subscription.total_amount = round_curr(subtotal + total_tax - total_disc)

    # Initial history
    hist = SubscriptionStatusHistory(
        subscription_id=subscription.id,
        from_status=None,
        to_status=subscription.status,
        changed_by=current_user.id,
        reason="Initial subscription creation"
    )
    db.add(hist)

    db.commit()
    db.refresh(subscription)

    log_action(
        db=db,
        action="SUBSCRIPTION_CREATED",
        entity_type="subscription",
        entity_id=subscription.id,
        user_id=current_user.id,
        details=f"Subscription {subscription.subscription_number} created with total ₹{subscription.total_amount}"
    )

    return subscription


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = db.query(Subscription).filter(Subscription.id == subscription_id, Subscription.is_deleted == False).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found.")

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust or sub.customer_id != cust.id:
            raise HTTPException(status_code=403, detail="Access denied to this subscription.")

    return sub


@router.post("/{subscription_id}/confirm", response_model=SubscriptionResponse)
def confirm_subscription(
    subscription_id: int,
    req: SubscriptionActionRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin)
):
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found.")
    return transition_subscription_status(db, sub, SubscriptionStatus.CONFIRMED, current_user.id, req.reason if req else None)


@router.post("/{subscription_id}/activate", response_model=SubscriptionResponse)
def activate_subscription(
    subscription_id: int,
    req: SubscriptionActionRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin)
):
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found.")
    return transition_subscription_status(db, sub, SubscriptionStatus.ACTIVE, current_user.id, req.reason if req else None)


@router.post("/{subscription_id}/pause", response_model=SubscriptionResponse)
def pause_subscription(
    subscription_id: int,
    req: SubscriptionActionRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found.")

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust or sub.customer_id != cust.id:
            raise HTTPException(status_code=403, detail="Access denied.")

    return transition_subscription_status(db, sub, SubscriptionStatus.PAUSED, current_user.id, req.reason if req else "Paused by user")


@router.post("/{subscription_id}/resume", response_model=SubscriptionResponse)
def resume_subscription(
    subscription_id: int,
    req: SubscriptionActionRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found.")

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust or sub.customer_id != cust.id:
            raise HTTPException(status_code=403, detail="Access denied.")

    return transition_subscription_status(db, sub, SubscriptionStatus.ACTIVE, current_user.id, req.reason if req else "Resumed by user")


@router.post("/{subscription_id}/close", response_model=SubscriptionResponse)
def close_subscription(
    subscription_id: int,
    req: SubscriptionActionRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found.")

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust or sub.customer_id != cust.id:
            raise HTTPException(status_code=403, detail="Access denied.")

    return transition_subscription_status(db, sub, SubscriptionStatus.CLOSED, current_user.id, req.reason if req else "Closed early")


@router.post("/{subscription_id}/renew", response_model=SubscriptionResponse)
def renew_sub(
    subscription_id: int,
    req: SubscriptionActionRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found.")

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust or sub.customer_id != cust.id:
            raise HTTPException(status_code=403, detail="Access denied.")

    return renew_subscription(db, sub, current_user.id, req.reason if req else None)
