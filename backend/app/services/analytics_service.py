from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, distinct
from app.models.customer import Customer
from app.models.product import Product
from app.models.plan import SubscriptionPlan, BillingFrequency
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment
from app.schemas.dashboard import (
    DashboardStats, MonthlyRevenuePoint, SubscriptionGrowthPoint,
    StatusDistribution, ProductRevenue, DashboardAnalyticsResponse
)
from app.services.tax_discount_service import round_curr


def calculate_mrr(active_subscriptions: List[Subscription]) -> Decimal:
    total_mrr = Decimal("0.00")
    for sub in active_subscriptions:
        sub_total = sub.total_amount
        freq = sub.plan.billing_frequency if sub.plan else BillingFrequency.MONTHLY
        if freq == BillingFrequency.DAILY:
            monthly_equiv = sub_total * Decimal("30.00")
        elif freq == BillingFrequency.WEEKLY:
            monthly_equiv = sub_total * Decimal("4.33")
        elif freq == BillingFrequency.MONTHLY:
            monthly_equiv = sub_total * Decimal("1.00")
        elif freq == BillingFrequency.YEARLY:
            monthly_equiv = sub_total / Decimal("12.00")
        else:
            monthly_equiv = sub_total
        total_mrr += monthly_equiv
    return round_curr(total_mrr)


def get_dashboard_analytics(db: Session, customer_id: int = None) -> DashboardAnalyticsResponse:
    today = date.today()

    # Base queries
    customer_filter = [Customer.is_deleted == False]
    sub_filter = [Subscription.is_deleted == False]
    inv_filter = [Invoice.is_deleted == False]
    pay_filter = [Payment.is_reversed == False]

    if customer_id:
        sub_filter.append(Subscription.customer_id == customer_id)
        inv_filter.append(Invoice.customer_id == customer_id)
        pay_filter.append(Payment.customer_id == customer_id)

    # 1. Total Customers
    if customer_id:
        total_customers = 1
    else:
        total_customers = db.query(Customer).filter(*customer_filter).count()

    # 2. Active Subscriptions
    active_subs = db.query(Subscription).filter(
        Subscription.status == SubscriptionStatus.ACTIVE,
        *sub_filter
    ).all()
    active_subscriptions_count = len(active_subs)

    # 3. Total Products
    total_products = db.query(Product).filter(Product.is_deleted == False).count()

    # 4. Total Revenue Collected (from actual settled payments)
    total_rev_res = db.query(func.coalesce(func.sum(Payment.amount), Decimal("0.00"))).filter(*pay_filter).scalar()
    total_revenue_collected = round_curr(Decimal(str(total_rev_res or "0.00")))

    # 5. MRR & ARR
    mrr = calculate_mrr(active_subs)
    arr = round_curr(mrr * Decimal("12.00"))

    # 6. Outstanding Payments / Receivables
    pending_res = db.query(func.coalesce(func.sum(Invoice.amount_due), Decimal("0.00"))).filter(
        Invoice.status.in_([InvoiceStatus.CONFIRMED, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE]),
        *inv_filter
    ).scalar()
    pending_payments = round_curr(Decimal(str(pending_res or "0.00")))

    # 7. Overdue Invoices
    overdue_query = db.query(Invoice).filter(
        or_(
            Invoice.status == InvoiceStatus.OVERDUE,
            and_(
                Invoice.due_date < today,
                Invoice.amount_due > Decimal("0.00"),
                Invoice.status.in_([InvoiceStatus.CONFIRMED, InvoiceStatus.PARTIALLY_PAID])
            )
        ),
        *inv_filter
    )
    overdue_invoices_count = overdue_query.count()
    overdue_amount_res = db.query(func.coalesce(func.sum(Invoice.amount_due), Decimal("0.00"))).filter(
        or_(
            Invoice.status == InvoiceStatus.OVERDUE,
            and_(
                Invoice.due_date < today,
                Invoice.amount_due > Decimal("0.00"),
                Invoice.status.in_([InvoiceStatus.CONFIRMED, InvoiceStatus.PARTIALLY_PAID])
            )
        ),
        *inv_filter
    ).scalar()
    overdue_invoices_amount = round_curr(Decimal(str(overdue_amount_res or "0.00")))

    # 8. Upcoming Renewals (next 30 days)
    thirty_days = today + timedelta(days=30)
    upcoming_renewals_count = db.query(Subscription).filter(
        Subscription.status == SubscriptionStatus.ACTIVE,
        Subscription.expiry_date >= today,
        Subscription.expiry_date <= thirty_days,
        *sub_filter
    ).count()

    stats = DashboardStats(
        total_customers=total_customers,
        active_subscriptions=active_subscriptions_count,
        total_products=total_products,
        total_revenue_collected=total_revenue_collected,
        mrr=mrr,
        arr=arr,
        pending_payments=pending_payments,
        overdue_invoices_count=overdue_invoices_count,
        overdue_invoices_amount=overdue_invoices_amount,
        upcoming_renewals_count=upcoming_renewals_count
    )

    # 9. Monthly Revenue points (last 6 months)
    monthly_revenue: List[MonthlyRevenuePoint] = []
    for i in range(5, -1, -1):
        target_month_date = today - timedelta(days=i * 30)
        m_start = date(target_month_date.year, target_month_date.month, 1)
        if target_month_date.month == 12:
            m_end = date(target_month_date.year + 1, 1, 1)
        else:
            m_end = date(target_month_date.year, target_month_date.month + 1, 1)

        m_name = m_start.strftime("%b %Y")

        # Collected
        m_rev = db.query(func.coalesce(func.sum(Payment.amount), Decimal("0.00"))).filter(
            Payment.payment_date >= m_start,
            Payment.payment_date < m_end,
            *pay_filter
        ).scalar()

        # Invoiced
        m_inv = db.query(func.coalesce(func.sum(Invoice.total), Decimal("0.00"))).filter(
            Invoice.invoice_date >= m_start,
            Invoice.invoice_date < m_end,
            *inv_filter
        ).scalar()

        monthly_revenue.append(MonthlyRevenuePoint(
            month=m_name,
            revenue=round_curr(Decimal(str(m_rev or "0.00"))),
            invoiced=round_curr(Decimal(str(m_inv or "0.00")))
        ))

    # 10. Subscription Growth points
    subscription_growth: List[SubscriptionGrowthPoint] = []
    for i in range(5, -1, -1):
        target_month_date = today - timedelta(days=i * 30)
        m_start = date(target_month_date.year, target_month_date.month, 1)
        if target_month_date.month == 12:
            m_end = date(target_month_date.year + 1, 1, 1)
        else:
            m_end = date(target_month_date.year, target_month_date.month + 1, 1)

        m_name = m_start.strftime("%b %Y")
        new_count = db.query(Subscription).filter(
            Subscription.created_at >= datetime(m_start.year, m_start.month, m_start.day),
            Subscription.created_at < datetime(m_end.year, m_end.month, m_end.day),
            *sub_filter
        ).count()
        cancelled_count = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.CANCELLED,
            Subscription.updated_at >= datetime(m_start.year, m_start.month, m_start.day),
            Subscription.updated_at < datetime(m_end.year, m_end.month, m_end.day),
            *sub_filter
        ).count()

        subscription_growth.append(SubscriptionGrowthPoint(
            month=m_name,
            active=active_subscriptions_count,
            new_subs=new_count,
            cancelled=cancelled_count
        ))

    # 11. Subscription Status Distribution
    all_sub_statuses = [
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.DRAFT,
        SubscriptionStatus.QUOTATION,
        SubscriptionStatus.CONFIRMED,
        SubscriptionStatus.PAUSED,
        SubscriptionStatus.CLOSED,
        SubscriptionStatus.CANCELLED
    ]
    subscription_status_distribution = []
    for st in all_sub_statuses:
        c = db.query(Subscription).filter(Subscription.status == st, *sub_filter).count()
        if c > 0:
            subscription_status_distribution.append(StatusDistribution(name=st.value.title(), value=c))

    # 12. Payment Status Distribution
    payment_status_distribution = []
    for pst in [InvoiceStatus.PAID, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE, InvoiceStatus.CONFIRMED, InvoiceStatus.DRAFT]:
        c = db.query(Invoice).filter(Invoice.status == pst, *inv_filter).count()
        if c > 0:
            payment_status_distribution.append(StatusDistribution(name=pst.value.replace('_', ' ').title(), value=c))

    # 13. Revenue by Product
    products = db.query(Product).filter(Product.is_deleted == False).all()
    revenue_by_product = []
    for p in products:
        p_sub_count = db.query(distinct(Subscription.id)).join(Subscription.lines).filter(
            Subscription.lines.property.mapper.class_.product_id == p.id,
            *sub_filter
        ).count()

        p_rev_res = db.query(func.coalesce(func.sum(Invoice.lines.property.mapper.class_.line_total), Decimal("0.00"))).join(Invoice).filter(
            Invoice.lines.property.mapper.class_.product_id == p.id,
            Invoice.status == InvoiceStatus.PAID,
            *inv_filter
        ).scalar()

        revenue_by_product.append(ProductRevenue(
            product_name=p.name,
            revenue=round_curr(Decimal(str(p_rev_res or "0.00"))),
            subscription_count=p_sub_count
        ))

    return DashboardAnalyticsResponse(
        stats=stats,
        monthly_revenue=monthly_revenue,
        subscription_growth=subscription_growth,
        subscription_status_distribution=subscription_status_distribution,
        payment_status_distribution=payment_status_distribution,
        revenue_by_product=revenue_by_product
    )
