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


class SubscriptionStatus(str, enum.Enum):
    DRAFT = "draft"
    QUOTATION = "quotation"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class PaymentTerms(str, enum.Enum):
    IMMEDIATE = "immediate"
    NET_15 = "net_15"
    NET_30 = "net_30"
    NET_45 = "net_45"
    NET_60 = "net_60"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    subscription_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False, index=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id"), nullable=True)
    start_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    payment_terms = Column(SAEnum(PaymentTerms), nullable=False, default=PaymentTerms.NET_30)
    subtotal = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    tax_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    discount_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    total_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    status = Column(SAEnum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.DRAFT)
    last_invoice_date = Column(Date, nullable=True)
    next_invoice_date = Column(Date, nullable=True)
    renewal_count = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    customer = relationship("Customer", backref="subscriptions", lazy="joined")
    plan = relationship("SubscriptionPlan", backref="subscriptions", lazy="joined")
    quotation = relationship("Quotation", backref="subscription", lazy="joined")
    creator = relationship("User", backref="created_subscriptions", lazy="joined")
    lines = relationship("SubscriptionLine", back_populates="subscription", lazy="selectin", cascade="all, delete-orphan")
    status_history = relationship("SubscriptionStatusHistory", back_populates="subscription", lazy="selectin", order_by="SubscriptionStatusHistory.changed_at.desc()")


class SubscriptionLine(Base):
    __tablename__ = "subscription_lines"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True)
    description = Column(String(500), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)
    tax_id = Column(Integer, ForeignKey("taxes.id"), nullable=True)
    tax_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    discount_id = Column(Integer, ForeignKey("discounts.id"), nullable=True)
    discount_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    line_total = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    subscription = relationship("Subscription", back_populates="lines")
    product = relationship("Product", lazy="joined")
    variant = relationship("ProductVariant", lazy="joined")
    tax = relationship("Tax", lazy="joined")
    discount = relationship("Discount", lazy="joined")


class SubscriptionStatusHistory(Base):
    __tablename__ = "subscription_status_history"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(SAEnum(SubscriptionStatus), nullable=True)
    to_status = Column(SAEnum(SubscriptionStatus), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=utc_now, nullable=False)

    subscription = relationship("Subscription", back_populates="status_history")
    user = relationship("User", lazy="joined")
