import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Enum as SAEnum,
    Text, Numeric, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.core.datetime_utils import utc_now


class ProductType(str, enum.Enum):
    SOFTWARE = "software"
    SERVICE = "service"
    ADDON = "addon"
    SUPPORT = "support"


class ProductStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    product_type = Column(SAEnum(ProductType), nullable=False, default=ProductType.SOFTWARE)
    sales_price = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    cost_price = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    description = Column(Text, nullable=True)
    status = Column(SAEnum(ProductStatus), nullable=False, default=ProductStatus.ACTIVE)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    variants = relationship("ProductVariant", back_populates="product", lazy="selectin")


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    variant_name = Column(String(255), nullable=False)
    additional_price = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    product = relationship("Product", back_populates="variants")
