from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
from app.models.discount import DiscountType


class DiscountBase(BaseModel):
    name: str
    discount_type: DiscountType = DiscountType.PERCENTAGE
    value: Decimal
    min_purchase_amount: Optional[Decimal] = None
    min_quantity: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_usage_limit: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True


class DiscountCreate(DiscountBase):
    pass


class DiscountUpdate(BaseModel):
    name: Optional[str] = None
    discount_type: Optional[DiscountType] = None
    value: Optional[Decimal] = None
    min_purchase_amount: Optional[Decimal] = None
    min_quantity: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_usage_limit: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DiscountResponse(DiscountBase):
    id: int
    usage_count: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
