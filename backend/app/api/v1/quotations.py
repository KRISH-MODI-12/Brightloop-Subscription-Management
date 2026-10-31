from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.quotation import Quotation, QuotationLine, QuotationStatus
from app.models.customer import Customer
from app.models.plan import SubscriptionPlan
from app.models.product import Product, ProductVariant
from app.models.tax import Tax
from app.models.subscription import Subscription, SubscriptionLine, SubscriptionStatus, PaymentTerms
from app.models.user import User, UserRole
from app.core.deps import get_current_user, get_staff_or_admin
from app.schemas.quotation import QuotationCreate, QuotationUpdate, QuotationResponse
from app.schemas.subscription import SubscriptionResponse
from app.services.audit_service import log_action
from app.services.subscription_service import generate_subscription_number, calculate_expiry_date
from app.services.tax_discount_service import round_curr

router = APIRouter(prefix="/quotations", tags=["Quotations"])


def generate_quotation_number(db: Session) -> str:
    count = db.query(Quotation).count() + 1
    year = date.today().year
    return f"QUO-{year}-{count:04d}"


@router.get("", response_model=List[QuotationResponse])
def list_quotations(
    customer_id: Optional[int] = None,
    status: Optional[QuotationStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Quotation)
    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust:
            return []
        query = query.filter(Quotation.customer_id == cust.id)
    else:
        if customer_id:
            query = query.filter(Quotation.customer_id == customer_id)

    if status:
        query = query.filter(Quotation.status == status)

    return query.order_by(Quotation.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=QuotationResponse, status_code=status.HTTP_201_CREATED)
def create_quotation(
    q_in: QuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin)
):
    customer = db.query(Customer).filter(Customer.id == q_in.customer_id, Customer.is_deleted == False).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    if q_in.valid_until < date.today():
        raise HTTPException(status_code=400, detail="Validity date cannot be in the past.")

    quotation = Quotation(
        quotation_number=generate_quotation_number(db),
        customer_id=q_in.customer_id,
        plan_id=q_in.plan_id,
        valid_until=q_in.valid_until,
        notes=q_in.notes,
        status=QuotationStatus.DRAFT,
        created_by=current_user.id
    )
    db.add(quotation)
    db.flush()

    subtotal = Decimal("0.00")
    total_tax = Decimal("0.00")
    total_disc = Decimal("0.00")

    for line_in in q_in.lines:
        line_sub = round_curr(line_in.unit_price * line_in.quantity)
        line_tax = round_curr(line_in.tax_amount)
        line_disc = round_curr(line_in.discount_amount)
        line_tot = round_curr(line_sub + line_tax - line_disc)

        q_line = QuotationLine(
            quotation_id=quotation.id,
            product_id=line_in.product_id,
            variant_id=line_in.variant_id,
            description=line_in.description,
            quantity=line_in.quantity,
            unit_price=line_in.unit_price,
            tax_id=line_in.tax_id,
            tax_amount=line_tax,
            discount_amount=line_disc,
            line_total=line_tot
        )
        db.add(q_line)

        subtotal += line_sub
        total_tax += line_tax
        total_disc += line_disc

    quotation.subtotal = subtotal
    quotation.tax_amount = total_tax
    quotation.discount_amount = total_disc
    quotation.total = round_curr(subtotal + total_tax - total_disc)

    db.commit()
    db.refresh(quotation)

    log_action(
        db=db,
        action="QUOTATION_CREATED",
        entity_type="quotation",
        entity_id=quotation.id,
        user_id=current_user.id,
        details=f"Quotation {quotation.quotation_number} created. Total: ₹{quotation.total}"
    )

    return quotation


@router.get("/{quotation_id}", response_model=QuotationResponse)
def get_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found.")

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust or quotation.customer_id != cust.id:
            raise HTTPException(status_code=403, detail="Access denied to this quotation.")

    return quotation


@router.post("/{quotation_id}/confirm", response_model=SubscriptionResponse)
def confirm_quotation_to_subscription(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin)
):
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found.")

    if quotation.status == QuotationStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail="Quotation is already confirmed into a subscription.")

    if quotation.valid_until < date.today():
        quotation.status = QuotationStatus.EXPIRED
        db.commit()
        raise HTTPException(
            status_code=400,
            detail=f"Quotation expired on {quotation.valid_until}. Please renew validity before confirming."
        )

    # Ensure plan
    plan = quotation.plan
    if not plan and quotation.plan_id:
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == quotation.plan_id).first()

    if not plan:
        raise HTTPException(status_code=400, detail="Quotation must be linked to a subscription plan to confirm.")

    start_date = date.today()
    expiry_date = calculate_expiry_date(start_date, plan.billing_frequency)

    subscription = Subscription(
        subscription_number=generate_subscription_number(db),
        customer_id=quotation.customer_id,
        plan_id=plan.id,
        quotation_id=quotation.id,
        start_date=start_date,
        expiry_date=expiry_date,
        payment_terms=PaymentTerms.NET_30,
        subtotal=quotation.subtotal,
        tax_amount=quotation.tax_amount,
        discount_amount=quotation.discount_amount,
        total_amount=quotation.total,
        status=SubscriptionStatus.ACTIVE,
        created_by=current_user.id,
        notes=f"Created from Quotation {quotation.quotation_number}"
    )
    db.add(subscription)
    db.flush()

    for q_line in quotation.lines:
        s_line = SubscriptionLine(
            subscription_id=subscription.id,
            product_id=q_line.product_id,
            variant_id=q_line.variant_id,
            description=q_line.description,
            quantity=q_line.quantity,
            unit_price=q_line.unit_price,
            tax_id=q_line.tax_id,
            tax_amount=q_line.tax_amount,
            discount_amount=q_line.discount_amount,
            line_total=q_line.line_total
        )
        db.add(s_line)

    quotation.status = QuotationStatus.CONFIRMED
    db.commit()
    db.refresh(subscription)

    log_action(
        db=db,
        action="QUOTATION_CONFIRMED_TO_SUBSCRIPTION",
        entity_type="subscription",
        entity_id=subscription.id,
        user_id=current_user.id,
        details=f"Quotation {quotation.quotation_number} converted to Subscription {subscription.subscription_number}"
    )

    return subscription
