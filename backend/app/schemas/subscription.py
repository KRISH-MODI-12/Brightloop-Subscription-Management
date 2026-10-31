from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
from app.models.subscription import SubscriptionStatus, PaymentTerms
from app.schemas.customer import CustomerResponse
from app.schemas.plan import PlanResponse
from app.schemas.product import ProductResponse, ProductVariantResponse
from app.schemas.tax import TaxResponse
from app.schemas.discount import DiscountResponse


class SubscriptionLineBase(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    description: Optional[str] = None
    quantity: int = 1
    unit_price: Decimal
    tax_id: Optional[int] = None
    tax_amount: Decimal = Decimal("0.00")
    discount_id: Optional[int] = None
    discount_amount: Decimal = Decimal("0.00")
    line_total: Decimal = Decimal("0.00")


class SubscriptionLineCreate(SubscriptionLineBase):
    pass


class SubscriptionLineResponse(SubscriptionLineBase):
    id: int
    subscription_id: int
    product: Optional[ProductResponse] = None
    variant: Optional[ProductVariantResponse] = None
    tax: Optional[TaxResponse] = None
    discount: Optional[DiscountResponse] = None

    class Config:
        from_attributes = True


class SubscriptionStatusHistoryResponse(BaseModel):
    id: int
    from_status: Optional[SubscriptionStatus] = None
    to_status: SubscriptionStatus
    changed_by: int
    reason: Optional[str] = None
    changed_at: datetime

    class Config:
        from_attributes = True


class SubscriptionBase(BaseModel):
    customer_id: int
    plan_id: int
    quotation_id: Optional[int] = None
    start_date: date
    payment_terms: PaymentTerms = PaymentTerms.NET_30
    notes: Optional[str] = None


class SubscriptionCreate(SubscriptionBase):
    expiry_date: Optional[date] = None  # Auto calculated from plan frequency if not provided
    lines: List[SubscriptionLineCreate] = []


class SubscriptionUpdate(BaseModel):
    plan_id: Optional[int] = None
    expiry_date: Optional[date] = None
    payment_terms: Optional[PaymentTerms] = None
    notes: Optional[str] = None
    status: Optional[SubscriptionStatus] = None


class SubscriptionActionRequest(BaseModel):
    reason: Optional[str] = None


class SubscriptionResponse(SubscriptionBase):
    id: int
    subscription_number: str
    expiry_date: date
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    status: SubscriptionStatus
    last_invoice_date: Optional[date] = None
    next_invoice_date: Optional[date] = None
    renewal_count: int
    created_by: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    customer: Optional[CustomerResponse] = None
    plan: Optional[PlanResponse] = None
    lines: List[SubscriptionLineResponse] = []
    status_history: List[SubscriptionStatusHistoryResponse] = []

    class Config:
        from_attributes = True
