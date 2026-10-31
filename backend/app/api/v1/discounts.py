from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.discount import Discount, DiscountType
from app.models.user import User
from app.core.deps import get_admin_user, get_current_user
from app.schemas.discount import DiscountCreate, DiscountUpdate, DiscountResponse
from app.services.tax_discount_service import evaluate_discount
from app.services.audit_service import log_action

router = APIRouter(prefix="/discounts", tags=["Discounts"])


@router.get("", response_model=List[DiscountResponse])
def list_discounts(db: Session = Depends(get_db)):
    return db.query(Discount).filter(Discount.is_deleted == False).all()


@router.post("", response_model=DiscountResponse, status_code=status.HTTP_201_CREATED)
def create_discount(
    disc_in: DiscountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    if disc_in.value < Decimal("0.00"):
        raise HTTPException(status_code=400, detail="Discount value cannot be negative.")

    if disc_in.discount_type == DiscountType.PERCENTAGE and disc_in.value > Decimal("100.00"):
        raise HTTPException(status_code=400, detail="Percentage discount cannot exceed 100%.")

    if disc_in.start_date and disc_in.end_date and disc_in.start_date > disc_in.end_date:
        raise HTTPException(status_code=400, detail="Start date cannot be after end date.")

    discount = Discount(
        name=disc_in.name,
        discount_type=disc_in.discount_type,
        value=disc_in.value,
        min_purchase_amount=disc_in.min_purchase_amount,
        min_quantity=disc_in.min_quantity,
        start_date=disc_in.start_date,
        end_date=disc_in.end_date,
        max_usage_limit=disc_in.max_usage_limit,
        description=disc_in.description,
        is_active=disc_in.is_active
    )
    db.add(discount)
    db.commit()
    db.refresh(discount)

    log_action(
        db=db,
        action="DISCOUNT_CREATED",
        entity_type="discount",
        entity_id=discount.id,
        user_id=current_user.id,
        details=f"Discount '{discount.name}' created with value {discount.value}"
    )

    return discount


@router.get("/evaluate/{discount_id}")
def check_discount_eligibility(
    discount_id: int,
    subtotal: Decimal,
    quantity: int = 1,
    db: Session = Depends(get_db)
):
    amount, err = evaluate_discount(db, discount_id, subtotal, quantity)
    return {
        "eligible": err is None,
        "discount_amount": amount,
        "reason": err
    }


@router.put("/{discount_id}", response_model=DiscountResponse)
def update_discount(
    discount_id: int,
    disc_in: DiscountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    discount = db.query(Discount).filter(Discount.id == discount_id, Discount.is_deleted == False).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found.")

    for field, val in disc_in.model_dump(exclude_unset=True).items():
        if field == "value" and val is not None:
            if val < Decimal("0.00"):
                raise HTTPException(status_code=400, detail="Discount value cannot be negative.")
            if discount.discount_type == DiscountType.PERCENTAGE and val > Decimal("100.00"):
                raise HTTPException(status_code=400, detail="Percentage discount cannot exceed 100%.")
        setattr(discount, field, val)

    db.commit()
    db.refresh(discount)

    log_action(
        db=db,
        action="DISCOUNT_UPDATED",
        entity_type="discount",
        entity_id=discount.id,
        user_id=current_user.id,
        details=f"Discount '{discount.name}' updated"
    )

    return discount


@router.delete("/{discount_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_discount(
    discount_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    discount = db.query(Discount).filter(Discount.id == discount_id, Discount.is_deleted == False).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found.")

    discount.is_deleted = True
    discount.is_active = False
    db.commit()

    log_action(
        db=db,
        action="DISCOUNT_DELETED",
        entity_type="discount",
        entity_id=discount.id,
        user_id=current_user.id,
        details=f"Discount '{discount.name}' deleted"
    )
    return None
