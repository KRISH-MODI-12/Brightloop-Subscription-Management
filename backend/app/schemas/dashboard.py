from typing import List, Dict, Any, Optional
from decimal import Decimal
from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_customers: int
    active_subscriptions: int
    total_products: int
    total_revenue_collected: Decimal
    mrr: Decimal
    arr: Decimal
    pending_payments: Decimal
    overdue_invoices_count: int
    overdue_invoices_amount: Decimal
    upcoming_renewals_count: int


class MonthlyRevenuePoint(BaseModel):
    month: str
    revenue: Decimal
    invoiced: Decimal


class SubscriptionGrowthPoint(BaseModel):
    month: str
    active: int
    new_subs: int
    cancelled: int


class StatusDistribution(BaseModel):
    name: str
    value: int


class ProductRevenue(BaseModel):
    product_name: str
    revenue: Decimal
    subscription_count: int


class DashboardAnalyticsResponse(BaseModel):
    stats: DashboardStats
    monthly_revenue: List[MonthlyRevenuePoint]
    subscription_growth: List[SubscriptionGrowthPoint]
    subscription_status_distribution: List[StatusDistribution]
    payment_status_distribution: List[StatusDistribution]
    revenue_by_product: List[ProductRevenue]
