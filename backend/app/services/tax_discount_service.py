from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.tax import Tax, TaxType
from app.models.discount import Discount, DiscountType, DiscountUsage


def round_curr(val: Decimal) -> Decimal:
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_tax(tax: Optional[Tax], taxable_amount: Decimal) -> Decimal:
    if not tax or not tax.is_active or tax.is_deleted:
        return Decimal("0.00")
    if tax.tax_type == TaxType.PERCENTAGE:
        return round_curr(taxable_amount * (tax.rate / Decimal("100.00")))
    elif tax.tax_type == TaxType.FIXED:
        return round_curr(tax.rate)
    return Decimal("0.00")


def evaluate_discount(
    db: Session,
    discount_id: Optional[int],
    subtotal: Decimal,
    quantity: int = 1
) -> Tuple[Decimal, Optional[str]]:
    if not discount_id:
        return Decimal("0.00"), None

    discount = db.query(Discount).filter(
        Discount.id == discount_id,
        Discount.is_active == True,
        Discount.is_deleted == False
    ).first()

    if not discount:
        return Decimal("0.00"), "Discount not found or inactive"

    today = date.today()
    if discount.start_date and today < discount.start_date:
        return Decimal("0.00"), f"Discount starts on {discount.start_date}"
    if discount.end_date and today > discount.end_date:
        return Decimal("0.00"), f"Discount expired on {discount.end_date}"

    if discount.max_usage_limit and discount.usage_count >= discount.max_usage_limit:
        return Decimal("0.00"), "Discount maximum usage limit reached"

    if discount.min_purchase_amount and subtotal < discount.min_purchase_amount:
        return Decimal("0.00"), f"Minimum purchase amount of ₹{discount.min_purchase_amount} required"

    if discount.min_quantity and quantity < discount.min_quantity:
        return Decimal("0.00"), f"Minimum quantity of {discount.min_quantity} required"

    if discount.discount_type == DiscountType.PERCENTAGE:
        # Cap percentage at 100%
        pct = min(discount.value, Decimal("100.00"))
        discount_amount = round_curr(subtotal * (pct / Decimal("100.00")))
    else:  # FIXED
        discount_amount = min(round_curr(discount.value), subtotal)

    return discount_amount, None


def record_discount_usage(
    db: Session,
    discount_id: int,
    customer_id: int,
    amount: Decimal,
    subscription_id: Optional[int] = None,
    invoice_id: Optional[int] = None
) -> Optional[DiscountUsage]:
    discount = db.query(Discount).filter(Discount.id == discount_id).first()
    if not discount:
        return None

    usage = DiscountUsage(
        discount_id=discount_id,
        customer_id=customer_id,
        subscription_id=subscription_id,
        invoice_id=invoice_id,
        amount=amount
    )
    db.add(usage)
    discount.usage_count += 1
    db.commit()
    return usage
