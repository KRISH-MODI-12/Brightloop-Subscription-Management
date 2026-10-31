from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.plan import SubscriptionPlan, PlanStatus, BillingFrequency
from app.models.product import Product
from app.models.user import User
from app.core.deps import get_admin_user, get_current_user
from app.schemas.plan import PlanCreate, PlanUpdate, PlanResponse
from app.services.audit_service import log_action

router = APIRouter(prefix="/plans", tags=["Subscription Plans"])


@router.get("", response_model=List[PlanResponse])
def list_plans(
    product_id: Optional[int] = None,
    billing_frequency: Optional[BillingFrequency] = None,
    status: Optional[PlanStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_deleted == False)
    if product_id:
        query = query.filter(SubscriptionPlan.product_id == product_id)
    if billing_frequency:
        query = query.filter(SubscriptionPlan.billing_frequency == billing_frequency)
    if status:
        query = query.filter(SubscriptionPlan.status == status)

    return query.offset(skip).limit(limit).all()


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    plan_in: PlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    if plan_in.price < Decimal("0.00"):
        raise HTTPException(status_code=400, detail="Plan price cannot be negative.")
    if plan_in.min_quantity < 1:
        raise HTTPException(status_code=400, detail="Minimum quantity must be at least 1.")
    if plan_in.start_date and plan_in.end_date and plan_in.start_date > plan_in.end_date:
        raise HTTPException(status_code=400, detail="Start date cannot be after end date.")

    product = db.query(Product).filter(Product.id == plan_in.product_id, Product.is_deleted == False).first()
    if not product:
        raise HTTPException(status_code=404, detail="Related product not found.")

    plan = SubscriptionPlan(
        name=plan_in.name,
        product_id=plan_in.product_id,
        price=plan_in.price,
        billing_frequency=plan_in.billing_frequency,
        min_quantity=plan_in.min_quantity,
        start_date=plan_in.start_date,
        end_date=plan_in.end_date,
        auto_close=plan_in.auto_close,
        allow_early_closure=plan_in.allow_early_closure,
        allow_pause=plan_in.allow_pause,
        allow_renewal=plan_in.allow_renewal,
        description=plan_in.description,
        status=plan_in.status
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    log_action(
        db=db,
        action="PLAN_CREATED",
        entity_type="subscription_plan",
        entity_id=plan.id,
        user_id=current_user.id,
        details=f"Plan '{plan.name}' created with frequency {plan.billing_frequency.value} at ₹{plan.price}"
    )

    return plan


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id, SubscriptionPlan.is_deleted == False).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found.")
    return plan


@router.put("/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: int,
    plan_in: PlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id, SubscriptionPlan.is_deleted == False).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found.")

    for field, val in plan_in.model_dump(exclude_unset=True).items():
        if field == "price" and val is not None and val < Decimal("0.00"):
            raise HTTPException(status_code=400, detail="Plan price cannot be negative.")
        setattr(plan, field, val)

    db.commit()
    db.refresh(plan)

    log_action(
        db=db,
        action="PLAN_UPDATED",
        entity_type="subscription_plan",
        entity_id=plan.id,
        user_id=current_user.id,
        details=f"Plan '{plan.name}' updated"
    )

    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id, SubscriptionPlan.is_deleted == False).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found.")

    plan.is_deleted = True
    plan.status = PlanStatus.ARCHIVED
    db.commit()

    log_action(
        db=db,
        action="PLAN_DELETED",
        entity_type="subscription_plan",
        entity_id=plan.id,
        user_id=current_user.id,
        details=f"Plan '{plan.name}' archived"
    )
    return None
