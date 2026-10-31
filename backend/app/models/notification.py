import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Enum as SAEnum,
    Text, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.core.datetime_utils import utc_now


class NotificationType(str, enum.Enum):
    REGISTRATION = "registration"
    PASSWORD_RESET = "password_reset"
    SUBSCRIPTION_CONFIRMED = "subscription_confirmed"
    SUBSCRIPTION_RENEWAL = "subscription_renewal"
    SUBSCRIPTION_EXPIRY = "subscription_expiry"
    INVOICE_GENERATED = "invoice_generated"
    INVOICE_OVERDUE = "invoice_overdue"
    PAYMENT_RECEIVED = "payment_received"
    GENERAL = "general"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(SAEnum(NotificationType), nullable=False, default=NotificationType.GENERAL)
    is_read = Column(Boolean, default=False, nullable=False)
    link = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", backref="notifications", lazy="joined")
