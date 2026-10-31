import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Enum as SAEnum,
    Numeric
)
from app.database import Base
from app.core.datetime_utils import utc_now


class TaxType(str, enum.Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class Tax(Base):
    __tablename__ = "taxes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    rate = Column(Numeric(6, 2), nullable=False)
    tax_type = Column(SAEnum(TaxType), nullable=False, default=TaxType.PERCENTAGE)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
