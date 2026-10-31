from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
from app.models.payment import PaymentMethod
from app.schemas.customer import CustomerResponse


class PaymentBase(BaseModel):
    invoice_id: int
    customer_id: Optional[int] = None
    amount: Decimal
    payment_method: PaymentMethod = PaymentMethod.BANK_TRANSFER
    payment_date: date = date.today()
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentReversalRequest(BaseModel):
    reason: str


class PaymentResponse(PaymentBase):
    id: int
    payment_number: str
    is_reversed: bool
    reversed_reason: Optional[str] = None
    recorded_by: int
    created_at: datetime
    updated_at: datetime
    customer: Optional[CustomerResponse] = None

    class Config:
        from_attributes = True
