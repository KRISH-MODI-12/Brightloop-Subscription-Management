import threading
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.sequence import DocumentSequence
from app.models.invoice import Invoice
from app.models.subscription import Subscription
from app.models.payment import Payment

_seq_lock = threading.Lock()
_table_ensured = False


def _ensure_table(db: Session) -> None:
    """Create the document_sequences table if it doesn't exist (idempotent)."""
    global _table_ensured
    if _table_ensured:
        return
    DocumentSequence.__table__.create(bind=db.get_bind(), checkfirst=True)
    _table_ensured = True


def _find_max_existing_number(db: Session, doc_type: str, prefix: str, year: int) -> int:
    """Find the maximum integer suffix in existing document numbers for the given prefix and year."""
    pattern = f"{prefix}-{year}-%"

    if doc_type == "invoice":
        rows = db.query(Invoice.invoice_number).filter(Invoice.invoice_number.like(pattern)).all()
    elif doc_type == "subscription":
        rows = db.query(Subscription.subscription_number).filter(Subscription.subscription_number.like(pattern)).all()
    elif doc_type == "payment":
        rows = db.query(Payment.payment_number).filter(Payment.payment_number.like(pattern)).all()
    else:
        return 0

    max_val = 0
    prefix_str = f"{prefix}-{year}-"
    for (num_str,) in rows:
        if num_str and num_str.startswith(prefix_str):
            try:
                val = int(num_str[len(prefix_str):])
                if val > max_val:
                    max_val = val
            except ValueError:
                continue
    return max_val


def get_next_document_number(db: Session, doc_type: str, prefix: str, year: int | None = None) -> str:
    """
    Atomically generate the next sequential document number.

    Uses a database-backed sequence table protected by a threading lock.
    On first call for a given (doc_type, year), seeds the counter from
    the maximum existing document number so that all historical numbers
    are preserved.
    """
    if year is None:
        year = date.today().year

    seq_name = f"{doc_type}_{year}"

    with _seq_lock:
        _ensure_table(db)

        seq = db.query(DocumentSequence).filter(DocumentSequence.name == seq_name).first()
        if seq is None:
            max_existing = _find_max_existing_number(db, doc_type, prefix, year)
            seq = DocumentSequence(
                name=seq_name,
                prefix=prefix,
                year=year,
                last_value=max_existing,
            )
            db.add(seq)
            db.flush()

        # Increment atomically
        seq.last_value += 1
        new_val = seq.last_value
        db.flush()

    return f"{prefix}-{year}-{new_val:04d}"
