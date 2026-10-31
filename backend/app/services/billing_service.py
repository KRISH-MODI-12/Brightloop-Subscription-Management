from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.plan import BillingFrequency
from app.services.audit_service import log_action
from app.services.notification_service import create_notification
from app.models.notification import NotificationType
from app.services.tax_discount_service import round_curr
from app.services.sequence_service import get_next_document_number


def generate_invoice_number(db: Session) -> str:
    return get_next_document_number(db, "invoice", "INV")


def get_billing_period(start_date: date, frequency: BillingFrequency) -> tuple[date, date]:
    if frequency == BillingFrequency.DAILY:
        return start_date, start_date + timedelta(days=1)
    elif frequency == BillingFrequency.WEEKLY:
        return start_date, start_date + timedelta(days=7)
    elif frequency == BillingFrequency.MONTHLY:
        month = start_date.month + 1
        year = start_date.year
        if month > 12:
            month = 1
            year += 1
        day = min(start_date.day, 28)
        end_date = date(year, month, day)
        return start_date, end_date
    elif frequency == BillingFrequency.YEARLY:
        end_date = date(start_date.year + 1, start_date.month, min(start_date.day, 28))
        return start_date, end_date
    return start_date, start_date + timedelta(days=30)


def create_invoice_from_subscription(
    db: Session,
    subscription: Subscription,
    created_by: Optional[int] = None,
    custom_period_start: Optional[date] = None,
    custom_period_end: Optional[date] = None
) -> Invoice:
    if subscription.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.CONFIRMED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot generate invoice for subscription in '{subscription.status.value}' status."
        )

    # Check if subscription was already billed for the current cycle
    if not custom_period_start and subscription.last_invoice_date and subscription.next_invoice_date and subscription.next_invoice_date > date.today():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Subscription {subscription.subscription_number} is already billed up to {subscription.next_invoice_date}. Next billing is not due yet."
        )

    frequency = subscription.plan.billing_frequency if subscription.plan else BillingFrequency.MONTHLY
    period_start = custom_period_start or subscription.next_invoice_date or subscription.start_date
    period_end = custom_period_end or get_billing_period(period_start, frequency)[1]

    # Duplicate invoice prevention check
    existing = db.query(Invoice).filter(
        Invoice.subscription_id == subscription.id,
        Invoice.billing_period_start == period_start,
        Invoice.billing_period_end == period_end,
        Invoice.status != InvoiceStatus.CANCELLED
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An invoice ({existing.invoice_number}) already exists for this subscription billing period ({period_start} to {period_end})."
        )

    # Calculate due date based on payment terms
    term_days = 30
    term_val = subscription.payment_terms.value if hasattr(subscription.payment_terms, "value") else str(subscription.payment_terms).lower()
    if term_val == "immediate":
        term_days = 0
    elif term_val == "net_15":
        term_days = 15
    elif term_val == "net_30":
        term_days = 30
    elif term_val == "net_45":
        term_days = 45
    elif term_val == "net_60":
        term_days = 60

    invoice_date = date.today()
    due_date = invoice_date + timedelta(days=term_days)

    invoice = Invoice(
        invoice_number=generate_invoice_number(db),
        customer_id=subscription.customer_id,
        subscription_id=subscription.id,
        invoice_date=invoice_date,
        due_date=due_date,
        billing_period_start=period_start,
        billing_period_end=period_end,
        subtotal=subscription.subtotal,
        tax_amount=subscription.tax_amount,
        discount_amount=subscription.discount_amount,
        total=subscription.total_amount,
        amount_paid=Decimal("0.00"),
        amount_due=subscription.total_amount,
        status=InvoiceStatus.CONFIRMED,
        notes=f"Auto-generated invoice for {subscription.subscription_number} ({period_start} to {period_end})",
        created_by=created_by
    )
    db.add(invoice)
    db.flush()  # assign invoice.id

    # Copy line items
    for s_line in subscription.lines:
        inv_line = InvoiceLine(
            invoice_id=invoice.id,
            product_id=s_line.product_id,
            variant_id=s_line.variant_id,
            description=s_line.description,
            quantity=s_line.quantity,
            unit_price=s_line.unit_price,
            tax_id=s_line.tax_id,
            tax_amount=s_line.tax_amount,
            discount_amount=s_line.discount_amount,
            line_total=s_line.line_total
        )
        db.add(inv_line)

    # Update subscription invoice dates
    subscription.last_invoice_date = invoice_date
    subscription.next_invoice_date = period_end

    db.commit()
    db.refresh(invoice)

    log_action(
        db=db,
        action="INVOICE_GENERATED",
        entity_type="invoice",
        entity_id=invoice.id,
        user_id=created_by,
        details=f"Invoice {invoice.invoice_number} created for subscription {subscription.subscription_number}. Total: ₹{invoice.total}"
    )

    customer = subscription.customer
    if customer and customer.user_id:
        create_notification(
            db=db,
            user_id=customer.user_id,
            title="New Invoice Generated",
            message=f"Invoice {invoice.invoice_number} for ₹{invoice.total} is ready for payment. Due date: {due_date}.",
            notification_type=NotificationType.INVOICE_GENERATED,
            link=f"/invoices/{invoice.id}"
        )

    return invoice


def run_recurring_billing_job(db: Session) -> dict:
    today = date.today()
    # Find all active subscriptions where next_invoice_date is today or earlier
    active_subs = db.query(Subscription).filter(
        Subscription.status == SubscriptionStatus.ACTIVE,
        Subscription.is_deleted == False
    ).all()

    generated_count = 0
    errors = []

    for sub in active_subs:
        # Check if due for billing
        due = False
        if not sub.last_invoice_date:
            due = True
        elif sub.next_invoice_date and sub.next_invoice_date <= today:
            due = True

        if due:
            try:
                create_invoice_from_subscription(db, sub)
                generated_count += 1
            except Exception as e:
                errors.append(f"Subscription {sub.subscription_number}: {str(e)}")

    # Check for overdue invoices and update their status
    overdue_invoices = db.query(Invoice).filter(
        Invoice.due_date < today,
        Invoice.amount_due > Decimal("0.00"),
        Invoice.status.in_([InvoiceStatus.CONFIRMED, InvoiceStatus.PARTIALLY_PAID])
    ).all()

    overdue_count = 0
    for inv in overdue_invoices:
        inv.status = InvoiceStatus.OVERDUE
        overdue_count += 1
        if inv.customer and inv.customer.user_id:
            create_notification(
                db=db,
                user_id=inv.customer.user_id,
                title="Invoice Overdue Notice",
                message=f"Invoice {inv.invoice_number} for ₹{inv.amount_due} was due on {inv.due_date} and is now overdue.",
                notification_type=NotificationType.INVOICE_OVERDUE,
                link=f"/invoices/{inv.id}"
            )
    db.commit()

    return {
        "generated_invoices": generated_count,
        "overdue_marked": overdue_count,
        "errors": errors
    }
