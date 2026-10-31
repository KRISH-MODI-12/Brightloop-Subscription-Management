from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.subscription import (
    Subscription, SubscriptionLine, SubscriptionStatus,
    SubscriptionStatusHistory, PaymentTerms
)
from app.models.plan import SubscriptionPlan, BillingFrequency
from app.models.product import Product, ProductVariant
from app.models.customer import Customer
from app.services.audit_service import log_action
from app.services.notification_service import create_notification
from app.models.notification import NotificationType
from app.services.tax_discount_service import calculate_tax, evaluate_discount, record_discount_usage, round_curr
from app.services.sequence_service import get_next_document_number
from app.core.datetime_utils import utc_now


def generate_subscription_number(db: Session) -> str:
    return get_next_document_number(db, "subscription", "SUB")


def calculate_expiry_date(start_date: date, frequency: BillingFrequency) -> date:
    if frequency == BillingFrequency.DAILY:
        return start_date + timedelta(days=1)
    elif frequency == BillingFrequency.WEEKLY:
        return start_date + timedelta(days=7)
    elif frequency == BillingFrequency.MONTHLY:
        # Approximate 30 days or calendar month
        month = start_date.month + 1
        year = start_date.year
        if month > 12:
            month = 1
            year += 1
        day = min(start_date.day, 28)
        return date(year, month, day)
    elif frequency == BillingFrequency.YEARLY:
        return date(start_date.year + 1, start_date.month, min(start_date.day, 28))
    return start_date + timedelta(days=30)


VALID_TRANSITIONS = {
    SubscriptionStatus.DRAFT: [SubscriptionStatus.QUOTATION, SubscriptionStatus.CONFIRMED, SubscriptionStatus.CANCELLED],
    SubscriptionStatus.QUOTATION: [SubscriptionStatus.CONFIRMED, SubscriptionStatus.CANCELLED],
    SubscriptionStatus.CONFIRMED: [SubscriptionStatus.ACTIVE, SubscriptionStatus.CANCELLED],
    SubscriptionStatus.ACTIVE: [SubscriptionStatus.PAUSED, SubscriptionStatus.CLOSED, SubscriptionStatus.CANCELLED],
    SubscriptionStatus.PAUSED: [SubscriptionStatus.ACTIVE, SubscriptionStatus.CLOSED, SubscriptionStatus.CANCELLED],
    SubscriptionStatus.CLOSED: [SubscriptionStatus.CONFIRMED, SubscriptionStatus.ACTIVE], # Renew
    SubscriptionStatus.CANCELLED: []
}


def transition_subscription_status(
    db: Session,
    subscription: Subscription,
    target_status: SubscriptionStatus,
    user_id: int,
    reason: Optional[str] = None
) -> Subscription:
    current_status = subscription.status
    if target_status == current_status:
        return subscription

    allowed = VALID_TRANSITIONS.get(current_status, [])
    if target_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition subscription from '{current_status.value}' to '{target_status.value}'."
        )

    # Business rule checks
    plan = subscription.plan
    if target_status == SubscriptionStatus.PAUSED and not plan.allow_pause:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The subscription plan does not allow pausing."
        )

    if target_status == SubscriptionStatus.CLOSED and current_status == SubscriptionStatus.ACTIVE:
        if date.today() < subscription.expiry_date and not plan.allow_early_closure:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Early closure is not permitted for this subscription plan."
            )

    history = SubscriptionStatusHistory(
        subscription_id=subscription.id,
        from_status=current_status,
        to_status=target_status,
        changed_by=user_id,
        reason=reason,
        changed_at=utc_now()
    )
    db.add(history)

    subscription.status = target_status
    db.commit()
    db.refresh(subscription)

    log_action(
        db=db,
        action=f"SUBSCRIPTION_STATUS_{target_status.value.upper()}",
        entity_type="subscription",
        entity_id=subscription.id,
        user_id=user_id,
        details=f"Status changed from {current_status.value} to {target_status.value}. Reason: {reason or 'N/A'}"
    )

    # Notify customer
    customer = subscription.customer
    if customer and customer.user_id:
        create_notification(
            db=db,
            user_id=customer.user_id,
            title=f"Subscription Status Update: {target_status.value.title()}",
            message=f"Your subscription {subscription.subscription_number} is now {target_status.value}.",
            notification_type=NotificationType.SUBSCRIPTION_CONFIRMED if target_status == SubscriptionStatus.ACTIVE else NotificationType.GENERAL,
            link=f"/subscriptions/{subscription.id}"
        )

    return subscription


def renew_subscription(
    db: Session,
    subscription: Subscription,
    user_id: int,
    reason: Optional[str] = None
) -> Subscription:
    plan = subscription.plan
    if not plan.allow_renewal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan does not permit renewals."
        )

    new_start = max(date.today(), subscription.expiry_date)
    new_expiry = calculate_expiry_date(new_start, plan.billing_frequency)

    subscription.start_date = new_start
    subscription.expiry_date = new_expiry
    subscription.renewal_count += 1
    subscription.status = SubscriptionStatus.ACTIVE

    history = SubscriptionStatusHistory(
        subscription_id=subscription.id,
        from_status=subscription.status,
        to_status=SubscriptionStatus.ACTIVE,
        changed_by=user_id,
        reason=reason or f"Renewed (Cycle #{subscription.renewal_count})",
        changed_at=utc_now()
    )
    db.add(history)
    db.commit()
    db.refresh(subscription)

    log_action(
        db=db,
        action="SUBSCRIPTION_RENEWED",
        entity_type="subscription",
        entity_id=subscription.id,
        user_id=user_id,
        details=f"Renewed to expiry {new_expiry}. Renewal count: {subscription.renewal_count}"
    )

    customer = subscription.customer
    if customer and customer.user_id:
        create_notification(
            db=db,
            user_id=customer.user_id,
            title="Subscription Renewed",
            message=f"Your subscription {subscription.subscription_number} has been renewed until {new_expiry}.",
            notification_type=NotificationType.SUBSCRIPTION_RENEWAL,
            link=f"/subscriptions/{subscription.id}"
        )

    return subscription
