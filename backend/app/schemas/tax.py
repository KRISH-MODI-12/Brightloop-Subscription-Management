from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from app.models.tax import TaxType


class TaxBase(BaseModel):
    name: str
    rate: Decimal
    tax_type: TaxType = TaxType.PERCENTAGE
    description: Optional[str] = None
    is_active: bool = True


class TaxCreate(TaxBase):
    pass


class TaxUpdate(BaseModel):
    name: Optional[str] = None
    rate: Optional[Decimal] = None
    tax_type: Optional[TaxType] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TaxResponse(TaxBase):
    id: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
