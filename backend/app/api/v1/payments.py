from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.payment import Payment, PaymentMethod
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.user import User, UserRole
from app.core.deps import get_current_user, get_staff_or_admin
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentReversalRequest
from app.services.payment_service import record_payment, reverse_payment

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("", response_model=List[PaymentResponse])
def list_payments(
    invoice_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Payment)

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust:
            return []
        query = query.filter(Payment.customer_id == cust.id)
    else:
        if customer_id:
            query = query.filter(Payment.customer_id == customer_id)

    if invoice_id:
        query = query.filter(Payment.invoice_id == invoice_id)

    return query.order_by(Payment.payment_date.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def make_payment(
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin)
):
    return record_payment(
        db=db,
        invoice_id=payment_in.invoice_id,
        amount=payment_in.amount,
        payment_method=payment_in.payment_method,
        recorded_by=current_user.id,
        payment_date=payment_in.payment_date,
        transaction_reference=payment_in.transaction_reference,
        notes=payment_in.notes
    )


@router.post("/{payment_id}/reverse", response_model=PaymentResponse)
def reverse_payment_endpoint(
    payment_id: int,
    req: PaymentReversalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin)
):
    return reverse_payment(
        db=db,
        payment_id=payment_id,
        user_id=current_user.id,
        reason=req.reason
    )
