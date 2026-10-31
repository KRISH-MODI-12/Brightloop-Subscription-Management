from sqlalchemy import Column, Integer, String
from app.database import Base


class DocumentSequence(Base):
    __tablename__ = "document_sequences"

    name = Column(String(64), primary_key=True)  # e.g., "invoice_2026", "subscription_2026", "payment_2026"
    prefix = Column(String(16), nullable=False)   # "INV", "SUB", "PAY"
    year = Column(Integer, nullable=False)        # 2026
    last_value = Column(Integer, nullable=False, default=0)

