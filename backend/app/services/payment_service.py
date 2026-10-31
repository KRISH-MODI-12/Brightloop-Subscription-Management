from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.payment import Payment, PaymentMethod
from app.models.invoice import Invoice, InvoiceStatus
from app.services.audit_service import log_action
from app.services.notification_service import create_notification
from app.models.notification import NotificationType
from app.services.tax_discount_service import round_curr
from app.services.sequence_service import get_next_document_number


def generate_payment_number(db: Session) -> str:
    return get_next_document_number(db, "payment", "PAY")


def record_payment(
    db: Session,
    invoice_id: int,
    amount: Decimal,
    payment_method: PaymentMethod,
    recorded_by: int,
    payment_date: Optional[date] = None,
    transaction_reference: Optional[str] = None,
    notes: Optional[str] = None
) -> Payment:
    amount = round_curr(amount)
    if amount <= Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be greater than zero."
        )

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found."
        )

    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice is already fully paid."
        )

    if invoice.status == InvoiceStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot record payment on a cancelled invoice."
        )

    # Prevent overpayment
    if amount > invoice.amount_due:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment amount (₹{amount}) exceeds remaining balance (₹{invoice.amount_due})."
        )

    payment = Payment(
        payment_number=generate_payment_number(db),
        invoice_id=invoice.id,
        customer_id=invoice.customer_id,
        amount=amount,
        payment_method=payment_method,
        payment_date=payment_date or date.today(),
        transaction_reference=transaction_reference,
        notes=notes,
        is_reversed=False,
        recorded_by=recorded_by
    )
    db.add(payment)

    # Update invoice balances
    invoice.amount_paid = round_curr(invoice.amount_paid + amount)
    invoice.amount_due = round_curr(invoice.total - invoice.amount_paid)

    if invoice.amount_due <= Decimal("0.00"):
        invoice.status = InvoiceStatus.PAID
    else:
        invoice.status = InvoiceStatus.PARTIALLY_PAID

    db.commit()
    db.refresh(payment)
    db.refresh(invoice)

    log_action(
        db=db,
        action="PAYMENT_RECORDED",
        entity_type="payment",
        entity_id=payment.id,
        user_id=recorded_by,
        details=f"Payment {payment.payment_number} for ₹{amount} applied to Invoice {invoice.invoice_number}. New due: ₹{invoice.amount_due}"
    )

    if invoice.customer and invoice.customer.user_id:
        create_notification(
            db=db,
            user_id=invoice.customer.user_id,
            title="Payment Received",
            message=f"We received your payment of ₹{amount} for invoice {invoice.invoice_number}. Status: {invoice.status.value.replace('_', ' ').title()}.",
            notification_type=NotificationType.PAYMENT_RECEIVED,
            link=f"/invoices/{invoice.id}"
        )

    return payment


def reverse_payment(
    db: Session,
    payment_id: int,
    user_id: int,
    reason: str
) -> Payment:
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found."
        )

    if payment.is_reversed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment has already been reversed."
        )

    invoice = payment.invoice
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Associated invoice not found."
        )

    payment.is_reversed = True
    payment.reversed_reason = reason

    # Adjust invoice amounts back
    invoice.amount_paid = max(Decimal("0.00"), round_curr(invoice.amount_paid - payment.amount))
    invoice.amount_due = round_curr(invoice.total - invoice.amount_paid)

    if invoice.amount_paid == Decimal("0.00"):
        invoice.status = InvoiceStatus.CONFIRMED if date.today() <= invoice.due_date else InvoiceStatus.OVERDUE
    else:
        invoice.status = InvoiceStatus.PARTIALLY_PAID

    db.commit()
    db.refresh(payment)
    db.refresh(invoice)

    log_action(
        db=db,
        action="PAYMENT_REVERSED",
        entity_type="payment",
        entity_id=payment.id,
        user_id=user_id,
        details=f"Payment {payment.payment_number} for ₹{payment.amount} reversed. Reason: {reason}"
    )

    return payment
