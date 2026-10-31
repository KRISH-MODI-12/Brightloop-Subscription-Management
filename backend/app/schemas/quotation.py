from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
from app.models.quotation import QuotationStatus
from app.schemas.customer import CustomerResponse
from app.schemas.product import ProductResponse, ProductVariantResponse
from app.schemas.tax import TaxResponse


class QuotationLineBase(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    description: Optional[str] = None
    quantity: int = 1
    unit_price: Decimal
    tax_id: Optional[int] = None
    tax_amount: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    line_total: Decimal = Decimal("0.00")


class QuotationLineCreate(QuotationLineBase):
    pass


class QuotationLineResponse(QuotationLineBase):
    id: int
    quotation_id: int
    product: Optional[ProductResponse] = None
    variant: Optional[ProductVariantResponse] = None
    tax: Optional[TaxResponse] = None

    class Config:
        from_attributes = True


class QuotationBase(BaseModel):
    customer_id: int
    plan_id: Optional[int] = None
    valid_until: date
    notes: Optional[str] = None


class QuotationCreate(QuotationBase):
    lines: List[QuotationLineCreate] = []


class QuotationUpdate(BaseModel):
    customer_id: Optional[int] = None
    plan_id: Optional[int] = None
    valid_until: Optional[date] = None
    notes: Optional[str] = None
    status: Optional[QuotationStatus] = None
    lines: Optional[List[QuotationLineCreate]] = None


class QuotationResponse(QuotationBase):
    id: int
    quotation_number: str
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total: Decimal
    status: QuotationStatus
    created_by: int
    created_at: datetime
    updated_at: datetime
    customer: Optional[CustomerResponse] = None
    lines: List[QuotationLineResponse] = []

    class Config:
        from_attributes = True
