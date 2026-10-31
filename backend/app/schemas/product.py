from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from app.models.product import ProductType, ProductStatus


class ProductVariantBase(BaseModel):
    variant_name: str
    additional_price: Decimal = Decimal("0.00")
    description: Optional[str] = None
    is_active: bool = True


class ProductVariantCreate(ProductVariantBase):
    pass


class ProductVariantResponse(ProductVariantBase):
    id: int
    product_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str
    product_type: ProductType = ProductType.SOFTWARE
    sales_price: Decimal = Decimal("0.00")
    cost_price: Decimal = Decimal("0.00")
    description: Optional[str] = None
    status: ProductStatus = ProductStatus.ACTIVE


class ProductCreate(ProductBase):
    variants: Optional[List[ProductVariantCreate]] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    product_type: Optional[ProductType] = None
    sales_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    description: Optional[str] = None
    status: Optional[ProductStatus] = None


class ProductResponse(ProductBase):
    id: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    variants: List[ProductVariantResponse] = []

    class Config:
        from_attributes = True
