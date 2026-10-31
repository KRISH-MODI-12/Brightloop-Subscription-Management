from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.tax import Tax
from app.models.user import User
from app.core.deps import get_admin_user, get_current_user
from app.schemas.tax import TaxCreate, TaxUpdate, TaxResponse
from app.services.audit_service import log_action

router = APIRouter(prefix="/taxes", tags=["Taxes"])


@router.get("", response_model=List[TaxResponse])
def list_taxes(db: Session = Depends(get_db)):
    return db.query(Tax).filter(Tax.is_deleted == False).all()


@router.post("", response_model=TaxResponse, status_code=status.HTTP_201_CREATED)
def create_tax(
    tax_in: TaxCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    if tax_in.rate < Decimal("0.00"):
        raise HTTPException(status_code=400, detail="Tax rate cannot be negative.")

    tax = Tax(
        name=tax_in.name,
        rate=tax_in.rate,
        tax_type=tax_in.tax_type,
        description=tax_in.description,
        is_active=tax_in.is_active
    )
    db.add(tax)
    db.commit()
    db.refresh(tax)

    log_action(
        db=db,
        action="TAX_CREATED",
        entity_type="tax",
        entity_id=tax.id,
        user_id=current_user.id,
        details=f"Tax '{tax.name}' ({tax.rate}%) created"
    )

    return tax


@router.put("/{tax_id}", response_model=TaxResponse)
def update_tax(
    tax_id: int,
    tax_in: TaxUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    tax = db.query(Tax).filter(Tax.id == tax_id, Tax.is_deleted == False).first()
    if not tax:
        raise HTTPException(status_code=404, detail="Tax rule not found.")

    for field, val in tax_in.model_dump(exclude_unset=True).items():
        if field == "rate" and val is not None and val < Decimal("0.00"):
            raise HTTPException(status_code=400, detail="Tax rate cannot be negative.")
        setattr(tax, field, val)

    db.commit()
    db.refresh(tax)

    log_action(
        db=db,
        action="TAX_UPDATED",
        entity_type="tax",
        entity_id=tax.id,
        user_id=current_user.id,
        details=f"Tax '{tax.name}' updated"
    )

    return tax


@router.delete("/{tax_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tax(
    tax_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    tax = db.query(Tax).filter(Tax.id == tax_id, Tax.is_deleted == False).first()
    if not tax:
        raise HTTPException(status_code=404, detail="Tax rule not found.")

    tax.is_deleted = True
    tax.is_active = False
    db.commit()

    log_action(
        db=db,
        action="TAX_DELETED",
        entity_type="tax",
        entity_id=tax.id,
        user_id=current_user.id,
        details=f"Tax '{tax.name}' deleted"
    )
    return None
