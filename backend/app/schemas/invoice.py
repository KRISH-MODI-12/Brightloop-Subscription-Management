from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
from app.models.invoice import InvoiceStatus
from app.schemas.customer import CustomerResponse
from app.schemas.product import ProductResponse, ProductVariantResponse
from app.schemas.tax import TaxResponse


class InvoiceLineBase(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    description: Optional[str] = None
    quantity: int = 1
    unit_price: Decimal
    tax_id: Optional[int] = None
    tax_amount: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    line_total: Decimal = Decimal("0.00")


class InvoiceLineCreate(InvoiceLineBase):
    pass


class InvoiceLineResponse(InvoiceLineBase):
    id: int
    invoice_id: int
    product: Optional[ProductResponse] = None
    variant: Optional[ProductVariantResponse] = None
    tax: Optional[TaxResponse] = None

    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    customer_id: int
    subscription_id: Optional[int] = None
    invoice_date: date
    due_date: date
    billing_period_start: Optional[date] = None
    billing_period_end: Optional[date] = None
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    lines: List[InvoiceLineCreate] = []


class InvoiceUpdate(BaseModel):
    due_date: Optional[date] = None
    status: Optional[InvoiceStatus] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    id: int
    invoice_number: str
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    status: InvoiceStatus
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    customer: Optional[CustomerResponse] = None
    lines: List[InvoiceLineResponse] = []

    class Config:
        from_attributes = True
