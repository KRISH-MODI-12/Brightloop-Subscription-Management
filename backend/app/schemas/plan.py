from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
from app.models.plan import BillingFrequency, PlanStatus
from app.schemas.product import ProductResponse


class PlanBase(BaseModel):
    name: str
    product_id: int
    price: Decimal
    billing_frequency: BillingFrequency = BillingFrequency.MONTHLY
    min_quantity: int = 1
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    auto_close: bool = False
    allow_early_closure: bool = True
    allow_pause: bool = True
    allow_renewal: bool = True
    description: Optional[str] = None
    status: PlanStatus = PlanStatus.ACTIVE


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    product_id: Optional[int] = None
    price: Optional[Decimal] = None
    billing_frequency: Optional[BillingFrequency] = None
    min_quantity: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    auto_close: bool = None
    allow_early_closure: bool = None
    allow_pause: bool = None
    allow_renewal: bool = None
    description: Optional[str] = None
    status: Optional[PlanStatus] = None


class PlanResponse(PlanBase):
    id: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True
