import enum
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Enum as SAEnum,
    Text, Numeric, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.core.datetime_utils import utc_now


class QuotationStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True)
    quotation_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=True)
    valid_until = Column(Date, nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    tax_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    discount_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    total = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    notes = Column(Text, nullable=True)
    status = Column(SAEnum(QuotationStatus), nullable=False, default=QuotationStatus.DRAFT)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    customer = relationship("Customer", backref="quotations", lazy="joined")
    plan = relationship("SubscriptionPlan", backref="quotations", lazy="joined")
    creator = relationship("User", backref="created_quotations", lazy="joined")
    lines = relationship("QuotationLine", back_populates="quotation", lazy="selectin", cascade="all, delete-orphan")


class QuotationLine(Base):
    __tablename__ = "quotation_lines"

    id = Column(Integer, primary_key=True, index=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True)
    description = Column(String(500), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)
    tax_id = Column(Integer, ForeignKey("taxes.id"), nullable=True)
    tax_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    discount_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    line_total = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    quotation = relationship("Quotation", back_populates="lines")
    product = relationship("Product", lazy="joined")
    variant = relationship("ProductVariant", lazy="joined")
    tax = relationship("Tax", lazy="joined")
