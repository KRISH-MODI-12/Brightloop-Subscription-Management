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


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    UPI = "upi"
    CARD = "card"
    OTHER = "other"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_number = Column(String(50), unique=True, nullable=False, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(SAEnum(PaymentMethod), nullable=False, default=PaymentMethod.BANK_TRANSFER)
    payment_date = Column(Date, nullable=False, default=date.today)
    transaction_reference = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    is_reversed = Column(Boolean, default=False, nullable=False)
    reversed_reason = Column(Text, nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    invoice = relationship("Invoice", back_populates="payments")
    customer = relationship("Customer", backref="payments", lazy="joined")
    recorder = relationship("User", backref="recorded_payments", lazy="joined")
