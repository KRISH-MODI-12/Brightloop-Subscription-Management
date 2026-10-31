from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from app.models.subscription import Subscription
from app.models.customer import Customer
from app.models.user import User, UserRole
from app.core.deps import get_current_user, get_staff_or_admin
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceResponse
from app.services.billing_service import (
    create_invoice_from_subscription, generate_invoice_number, run_recurring_billing_job
)
from app.services.pdf_service import generate_invoice_pdf
from app.services.audit_service import log_action
from app.services.tax_discount_service import round_curr

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get("", response_model=List[InvoiceResponse])
def list_invoices(
    customer_id: Optional[int] = None,
    subscription_id: Optional[int] = None,
    status: Optional[InvoiceStatus] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Invoice).filter(Invoice.is_deleted == False)

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust:
            return []
        query = query.filter(Invoice.customer_id == cust.id)
    else:
        if customer_id:
            query = query.filter(Invoice.customer_id == customer_id)

    if subscription_id:
        query = query.filter(Invoice.subscription_id == subscription_id)
    if status:
        query = query.filter(Invoice.status == status)
    if search:
        query = query.filter(
            or_(
                Invoice.invoice_number.ilike(f"%{search}%"),
                Invoice.notes.ilike(f"%{search}%")
            )
        )

    return query.order_by(Invoice.invoice_date.desc()).offset(skip).limit(limit).all()


@router.post("/from-subscription/{subscription_id}", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def generate_from_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin)
):
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found.")

    return create_invoice_from_subscription(db=db, subscription=sub, created_by=current_user.id)


@router.post("/run-billing-job")
def trigger_billing_job(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin)
):
    results = run_recurring_billing_job(db)
    log_action(
        db=db,
        action="MANUAL_BILLING_JOB_RUN",
        entity_type="system",
        user_id=current_user.id,
        details=f"Invoices generated: {results['generated_invoices']}, Overdue marked: {results['overdue_marked']}"
    )
    return results


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.is_deleted == False).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust or inv.customer_id != cust.id:
            raise HTTPException(status_code=403, detail="Access denied to this invoice.")

    return inv


@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.is_deleted == False).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust or inv.customer_id != cust.id:
            raise HTTPException(status_code=403, detail="Access denied to this invoice.")

    pdf_bytes = generate_invoice_pdf(inv)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Invoice-{inv.invoice_number}.pdf"}
    )


@router.put("/{invoice_id}/cancel", response_model=InvoiceResponse)
def cancel_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin)
):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    if inv.amount_paid > Decimal("0.00"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel an invoice with payments (₹{inv.amount_paid} recorded). Reverse payments first."
        )

    inv.status = InvoiceStatus.CANCELLED
    db.commit()
    db.refresh(inv)

    log_action(
        db=db,
        action="INVOICE_CANCELLED",
        entity_type="invoice",
        entity_id=inv.id,
        user_id=current_user.id,
        details=f"Invoice {inv.invoice_number} cancelled"
    )

    return inv
