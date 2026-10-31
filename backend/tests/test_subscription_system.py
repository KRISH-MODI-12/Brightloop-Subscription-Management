import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.product import Product, ProductVariant, ProductType, ProductStatus
from app.models.plan import SubscriptionPlan, BillingFrequency, PlanStatus
from app.models.tax import Tax, TaxType
from app.models.discount import Discount, DiscountType
from app.models.quotation import Quotation, QuotationLine, QuotationStatus
from app.models.subscription import (
    Subscription, SubscriptionLine, SubscriptionStatus, PaymentTerms
)
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import PaymentMethod
from app.core.security import (
    get_password_hash, verify_password, validate_password_strength, create_access_token, decode_token
)
from app.services.tax_discount_service import calculate_tax, evaluate_discount, round_curr
from app.services.subscription_service import (
    calculate_expiry_date, transition_subscription_status, renew_subscription
)
from app.services.billing_service import create_invoice_from_subscription, get_billing_period
from app.services.payment_service import record_payment, reverse_payment
from app.services.analytics_service import calculate_mrr, get_dashboard_analytics


@pytest.fixture(scope="function")
def db_session():
    # In-memory SQLite for blazing fast isolated testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# 1. Password validation tests
def test_password_policy():
    valid, _ = validate_password_strength("Short1!")
    assert not valid  # Too short

    valid, _ = validate_password_strength("nocaps123!@#")
    assert not valid  # Missing uppercase

    valid, _ = validate_password_strength("NOLOWERCAS123!")
    assert not valid  # Missing lowercase

    valid, _ = validate_password_strength("NoSpecial123")
    assert not valid  # Missing special character

    valid, _ = validate_password_strength("ValidPass@123")
    assert valid  # Passes all criteria


# 2. Hash and JWT test
def test_hash_and_jwt():
    raw = "SecureSecret!99"
    hashed = get_password_hash(raw)
    assert verify_password(raw, hashed)
    assert not verify_password("WrongPassword!", hashed)

    token = create_access_token(42)
    payload = decode_token(token)
    assert payload is not None
    assert payload.get("sub") == "42"


# 3. Tax calculation tests
def test_tax_calculations():
    tax18 = Tax(name="GST 18%", rate=Decimal("18.00"), tax_type=TaxType.PERCENTAGE, is_active=True)
    assert calculate_tax(tax18, Decimal("1000.00")) == Decimal("180.00")
    assert calculate_tax(tax18, Decimal("1560.00")) == Decimal("280.80")

    fixed_tax = Tax(name="Eco Fee", rate=Decimal("50.00"), tax_type=TaxType.FIXED, is_active=True)
    assert calculate_tax(fixed_tax, Decimal("1000.00")) == Decimal("50.00")


# 4. Discount rules and eligibility tests
def test_discount_eligibility(db_session):
    disc = Discount(
        name="10% Off",
        discount_type=DiscountType.PERCENTAGE,
        value=Decimal("10.00"),
        min_purchase_amount=Decimal("1000.00"),
        is_active=True
    )
    db_session.add(disc)
    db_session.commit()

    # Subtotal under threshold -> not eligible
    amt, err = evaluate_discount(db_session, disc.id, Decimal("500.00"), 1)
    assert amt == Decimal("0.00")
    assert err is not None

    # Subtotal >= 1000 -> eligible
    amt, err = evaluate_discount(db_session, disc.id, Decimal("2000.00"), 1)
    assert amt == Decimal("200.00")
    assert err is None


# 5. Subscription lifecycle and state transitions
def test_subscription_lifecycle(db_session):
    admin = User(email="admin@test.com", hashed_password="x", full_name="Admin", role=UserRole.ADMIN)
    db_session.add(admin)
    db_session.flush()

    cust = Customer(user_id=admin.id, company_name="Test Corp")
    prod = Product(name="Cloud ERP", sales_price=Decimal("1000.00"))
    db_session.add_all([cust, prod])
    db_session.flush()

    plan = SubscriptionPlan(
        name="Monthly ERP",
        product_id=prod.id,
        price=Decimal("1000.00"),
        billing_frequency=BillingFrequency.MONTHLY,
        allow_pause=True,
        allow_early_closure=True,
        allow_renewal=True
    )
    db_session.add(plan)
    db_session.flush()

    sub = Subscription(
        subscription_number="SUB-TEST-001",
        customer_id=cust.id,
        plan_id=plan.id,
        start_date=date.today(),
        expiry_date=calculate_expiry_date(date.today(), BillingFrequency.MONTHLY),
        subtotal=Decimal("1000.00"),
        total_amount=Decimal("1000.00"),
        status=SubscriptionStatus.DRAFT,
        created_by=admin.id
    )
    db_session.add(sub)
    db_session.commit()

    # Transition: DRAFT -> CONFIRMED -> ACTIVE -> PAUSED -> ACTIVE -> CLOSED
    transition_subscription_status(db_session, sub, SubscriptionStatus.CONFIRMED, admin.id)
    assert sub.status == SubscriptionStatus.CONFIRMED

    transition_subscription_status(db_session, sub, SubscriptionStatus.ACTIVE, admin.id)
    assert sub.status == SubscriptionStatus.ACTIVE

    transition_subscription_status(db_session, sub, SubscriptionStatus.PAUSED, admin.id)
    assert sub.status == SubscriptionStatus.PAUSED

    transition_subscription_status(db_session, sub, SubscriptionStatus.ACTIVE, admin.id)
    assert sub.status == SubscriptionStatus.ACTIVE

    transition_subscription_status(db_session, sub, SubscriptionStatus.CLOSED, admin.id)
    assert sub.status == SubscriptionStatus.CLOSED


# 6. Invoice generation and duplicate prevention
def test_invoice_generation_and_duplicate_prevention(db_session):
    admin = User(email="admin2@test.com", hashed_password="x", full_name="Admin", role=UserRole.ADMIN)
    db_session.add(admin)
    db_session.flush()

    cust = Customer(user_id=admin.id, company_name="Test Corp")
    prod = Product(name="Cloud ERP", sales_price=Decimal("1000.00"))
    db_session.add_all([cust, prod])
    db_session.flush()

    plan = SubscriptionPlan(
        name="Monthly ERP",
        product_id=prod.id,
        price=Decimal("1000.00"),
        billing_frequency=BillingFrequency.MONTHLY
    )
    db_session.add(plan)
    db_session.flush()

    sub = Subscription(
        subscription_number="SUB-TEST-002",
        customer_id=cust.id,
        plan_id=plan.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=30),
        subtotal=Decimal("1000.00"),
        total_amount=Decimal("1000.00"),
        status=SubscriptionStatus.ACTIVE,
        created_by=admin.id
    )
    db_session.add(sub)
    db_session.flush()

    # Generate first invoice
    inv1 = create_invoice_from_subscription(db_session, sub, admin.id)
    assert inv1 is not None
    assert inv1.total == Decimal("1000.00")
    assert inv1.amount_due == Decimal("1000.00")

    # Attempting to generate duplicate invoice for the same billing period must fail with 409
    with pytest.raises(Exception):
        create_invoice_from_subscription(
            db_session, sub, admin.id,
            custom_period_start=inv1.billing_period_start,
            custom_period_end=inv1.billing_period_end
        )


# 7. Partial Payment, Full Payment, and Reversal
def test_payments_and_reversals(db_session):
    admin = User(email="admin3@test.com", hashed_password="x", full_name="Admin", role=UserRole.ADMIN)
    db_session.add(admin)
    db_session.flush()

    cust = Customer(user_id=admin.id, company_name="FinTech Corp")
    db_session.add(cust)
    db_session.flush()

    inv = Invoice(
        invoice_number="INV-PAY-001",
        customer_id=cust.id,
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=15),
        total=Decimal("1000.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("1000.00"),
        status=InvoiceStatus.CONFIRMED,
        created_by=admin.id
    )
    db_session.add(inv)
    db_session.commit()

    # 1. Partial payment of ₹400
    pay1 = record_payment(
        db_session,
        invoice_id=inv.id,
        amount=Decimal("400.00"),
        payment_method=PaymentMethod.UPI,
        recorded_by=admin.id
    )
    assert inv.amount_paid == Decimal("400.00")
    assert inv.amount_due == Decimal("600.00")
    assert inv.status == InvoiceStatus.PARTIALLY_PAID

    # 2. Overpayment prevention (trying to pay ₹700 when only ₹600 is due)
    with pytest.raises(Exception):
        record_payment(
            db_session,
            invoice_id=inv.id,
            amount=Decimal("700.00"),
            payment_method=PaymentMethod.CARD,
            recorded_by=admin.id
        )

    # 3. Final settlement payment of remaining ₹600
    pay2 = record_payment(
        db_session,
        invoice_id=inv.id,
        amount=Decimal("600.00"),
        payment_method=PaymentMethod.BANK_TRANSFER,
        recorded_by=admin.id
    )
    assert inv.amount_paid == Decimal("1000.00")
    assert inv.amount_due == Decimal("0.00")
    assert inv.status == InvoiceStatus.PAID

    # 4. Payment Reversal of pay2 (₹600)
    rev = reverse_payment(db_session, pay2.id, admin.id, reason="Bank dishonour")
    assert rev.is_reversed is True
    assert inv.amount_paid == Decimal("400.00")
    assert inv.amount_due == Decimal("600.00")
    assert inv.status == InvoiceStatus.PARTIALLY_PAID


# 8. MRR Calculation Accuracy
def test_mrr_calculation(db_session):
    admin = User(email="admin4@test.com", hashed_password="x", full_name="Admin", role=UserRole.ADMIN)
    db_session.add(admin)
    db_session.flush()

    cust = Customer(user_id=admin.id)
    prod = Product(name="SaaS", sales_price=Decimal("12000.00"))
    db_session.add_all([cust, prod])
    db_session.flush()

    p_monthly = SubscriptionPlan(name="Monthly", product_id=prod.id, price=Decimal("1000.00"), billing_frequency=BillingFrequency.MONTHLY)
    p_yearly = SubscriptionPlan(name="Yearly", product_id=prod.id, price=Decimal("12000.00"), billing_frequency=BillingFrequency.YEARLY)
    db_session.add_all([p_monthly, p_yearly])
    db_session.flush()

    sub1 = Subscription(
        subscription_number="S1", customer_id=cust.id, plan_id=p_monthly.id, plan=p_monthly,
        start_date=date.today(), expiry_date=date.today()+timedelta(days=30),
        total_amount=Decimal("1000.00"), status=SubscriptionStatus.ACTIVE, created_by=admin.id
    )
    sub2 = Subscription(
        subscription_number="S2", customer_id=cust.id, plan_id=p_yearly.id, plan=p_yearly,
        start_date=date.today(), expiry_date=date.today()+timedelta(days=365),
        total_amount=Decimal("12000.00"), status=SubscriptionStatus.ACTIVE, created_by=admin.id
    )
    db_session.add_all([sub1, sub2])
    db_session.commit()
    # sub1 MRR = 1000, sub2 MRR = 12000 / 12 = 1000. Total MRR should be 2000.00
    mrr = calculate_mrr([sub1, sub2])
    assert mrr == Decimal("2000.00")
