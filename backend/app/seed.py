import sys
import os
from datetime import date, datetime, timedelta
from decimal import Decimal

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, Base
from app.core.datetime_utils import utc_now
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.product import Product, ProductVariant, ProductType, ProductStatus
from app.models.plan import SubscriptionPlan, BillingFrequency, PlanStatus
from app.models.tax import Tax, TaxType
from app.models.discount import Discount, DiscountType
from app.models.subscription import Subscription, SubscriptionLine, SubscriptionStatus, PaymentTerms, SubscriptionStatusHistory
from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from app.models.payment import Payment, PaymentMethod
from app.models.notification import Notification, NotificationType
from app.core.security import get_password_hash


def seed_database():
    print("Creating tables if not exists...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if admin already exists
    if db.query(User).filter(User.email == "admin@brightloop.com").first():
        print("Database already seeded. Skipping.")
        db.close()
        return

    print("Seeding initial users (1 Admin, 2 Staff, 10 Customers)...")
    # 1. Admin
    admin = User(
        email="admin@brightloop.com",
        full_name="Rajesh Sharma (Admin)",
        phone="+91 98765 43210",
        hashed_password=get_password_hash("Admin@123!"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(admin)

    # 2. Staff
    staff1 = User(
        email="staff1@brightloop.com",
        full_name="Pooja Patel (Staff)",
        phone="+91 98765 43211",
        hashed_password=get_password_hash("Staff@123!"),
        role=UserRole.STAFF,
        is_active=True
    )
    staff2 = User(
        email="staff2@brightloop.com",
        full_name="Arjun Mehta (Staff)",
        phone="+91 98765 43212",
        hashed_password=get_password_hash("Staff@123!"),
        role=UserRole.STAFF,
        is_active=True
    )
    db.add_all([staff1, staff2])
    db.flush()

    # 3. 10 Customers
    customer_data = [
        ("Acme Technologies", "customer1@brightloop.com", "Ananya Verma", "+91 91234 56781", "Bangalore", "Karnataka", "29ABCDE1234F1Z5"),
        ("Zenith Logistics", "customer2@brightloop.com", "Vikram Singh", "+91 91234 56782", "Mumbai", "Maharashtra", "27ABCDE1234F1Z6"),
        ("CloudScale Retail", "customer3@brightloop.com", "Kiran Rao", "+91 91234 56783", "Hyderabad", "Telangana", "36ABCDE1234F1Z7"),
        ("Pulse Healthcare", "customer4@brightloop.com", "Dr. Sameer Joshi", "+91 91234 56784", "Pune", "Maharashtra", "27ABCDE1234F1Z8"),
        ("Nexus FinTech", "customer5@brightloop.com", "Sneha Roy", "+91 91234 56785", "Gurgaon", "Haryana", "06ABCDE1234F1Z9"),
        ("Delta Manufacturing", "customer6@brightloop.com", "Rohan Gupta", "+91 91234 56786", "Ahmedabad", "Gujarat", "24ABCDE1234F1Z0"),
        ("BrightWave Media", "customer7@brightloop.com", "Tara Sen", "+91 91234 56787", "Kolkata", "West Bengal", "19ABCDE1234F1Z1"),
        ("Starlight Hotels", "customer8@brightloop.com", "Deepak Nair", "+91 91234 56788", "Kochi", "Kerala", "32ABCDE1234F1Z2"),
        ("Vanguard Security", "customer9@brightloop.com", "Manoj Tiwari", "+91 91234 56789", "Noida", "Uttar Pradesh", "09ABCDE1234F1Z3"),
        ("Aura Cosmetics", "customer10@brightloop.com", "Isha Kapoor", "+91 91234 56780", "Delhi", "Delhi", "07ABCDE1234F1Z4")
    ]

    customers = []
    for comp, email, name, phone, city, state, gst in customer_data:
        u = User(
            email=email,
            full_name=name,
            phone=phone,
            hashed_password=get_password_hash("Customer@123!"),
            role=UserRole.CUSTOMER,
            is_active=True
        )
        db.add(u)
        db.flush()

        cust = Customer(
            user_id=u.id,
            company_name=comp,
            address=f"Suite 400, Tech Park, {city}",
            city=city,
            state=state,
            postal_code="560001",
            gst_number=gst
        )
        db.add(cust)
        customers.append(cust)

    db.flush()

    # 4. Taxes
    print("Seeding Tax rules...")
    tax_gst18 = Tax(name="GST 18%", rate=Decimal("18.00"), tax_type=TaxType.PERCENTAGE, description="Standard Integrated GST")
    tax_cgst9 = Tax(name="CGST 9%", rate=Decimal("9.00"), tax_type=TaxType.PERCENTAGE, description="Central GST")
    tax_sgst9 = Tax(name="SGST 9%", rate=Decimal("9.00"), tax_type=TaxType.PERCENTAGE, description="State GST")
    tax_zero = Tax(name="Exempt / Zero Tax", rate=Decimal("0.00"), tax_type=TaxType.PERCENTAGE, description="0% tax")
    db.add_all([tax_gst18, tax_cgst9, tax_sgst9, tax_zero])
    db.flush()

    # 5. Discounts
    print("Seeding Discounts...")
    disc_startup = Discount(name="Startup Booster", discount_type=DiscountType.PERCENTAGE, value=Decimal("15.00"), description="15% discount for startups")
    disc_annual = Discount(name="Annual Saver", discount_type=DiscountType.PERCENTAGE, value=Decimal("20.00"), min_purchase_amount=Decimal("10000.00"), description="20% off on yearly commitments")
    disc_flat = Discount(name="Welcome Flat ₹1000", discount_type=DiscountType.FIXED, value=Decimal("1000.00"), min_purchase_amount=Decimal("5000.00"), description="₹1000 instant credit")
    disc_festive = Discount(name="Festival Promo", discount_type=DiscountType.PERCENTAGE, value=Decimal("10.00"), max_usage_limit=100, description="10% festival special")
    disc_vip = Discount(name="Enterprise VIP", discount_type=DiscountType.PERCENTAGE, value=Decimal("25.00"), min_purchase_amount=Decimal("50000.00"), description="25% volume discount")
    db.add_all([disc_startup, disc_annual, disc_flat, disc_festive, disc_vip])
    db.flush()

    # 6. Products & Variants (8 products)
    print("Seeding Products and Variants...")
    p1 = Product(name="Brightloop Cloud ERP", product_type=ProductType.SOFTWARE, sales_price=Decimal("5000.00"), cost_price=Decimal("1200.00"), description="Enterprise resource planning with finance, inventory & supply chain.")
    p2 = Product(name="Brightloop CRM Pro", product_type=ProductType.SOFTWARE, sales_price=Decimal("2500.00"), cost_price=Decimal("500.00"), description="Lead scoring, automated pipelines, and multi-channel customer tracking.")
    p3 = Product(name="AI Analytics Engine", product_type=ProductType.SOFTWARE, sales_price=Decimal("3500.00"), cost_price=Decimal("900.00"), description="Predictive business intelligence and forecasting reports.")
    p4 = Product(name="Omni Helpdesk Suite", product_type=ProductType.SOFTWARE, sales_price=Decimal("1800.00"), cost_price=Decimal("350.00"), description="Ticketing system with live chat and SLA automation.")
    p5 = Product(name="PeopleHRMS", product_type=ProductType.SOFTWARE, sales_price=Decimal("2200.00"), cost_price=Decimal("400.00"), description="Payroll, attendance, and leave management system.")
    p6 = Product(name="Cloud Shield Security", product_type=ProductType.SOFTWARE, sales_price=Decimal("1500.00"), cost_price=Decimal("300.00"), description="WAF, DDoS mitigation, and vulnerability scanning.")
    p7 = Product(name="Payment Gateway Connector", product_type=ProductType.ADDON, sales_price=Decimal("800.00"), cost_price=Decimal("150.00"), description="Direct integration with Razorpay, Stripe, and UPI.")
    p8 = Product(name="24x7 Priority Support", product_type=ProductType.SUPPORT, sales_price=Decimal("1200.00"), cost_price=Decimal("600.00"), description="Dedicated SLA support with 15-minute response time.")
    db.add_all([p1, p2, p3, p4, p5, p6, p7, p8])
    db.flush()

    # Variants (Odoo Brand Additional Price = ₹560 as specified in prompt!)
    v1_odoo = ProductVariant(product_id=p1.id, variant_name="Odoo Enterprise Edition", additional_price=Decimal("560.00"), description="Custom Odoo branding and connector")
    v1_std = ProductVariant(product_id=p1.id, variant_name="Standard Edition", additional_price=Decimal("0.00"), description="Default cloud deployment")
    v2_pro = ProductVariant(product_id=p2.id, variant_name="Unlimited Contacts Pack", additional_price=Decimal("750.00"), description="Unlimited contacts & leads")
    db.add_all([v1_odoo, v1_std, v2_pro])
    db.flush()

    # 7. Subscription Plans (12 plans)
    print("Seeding Subscription Plans...")
    plans = [
        SubscriptionPlan(name="Cloud ERP Monthly", product_id=p1.id, price=Decimal("5000.00"), billing_frequency=BillingFrequency.MONTHLY, min_quantity=1),
        SubscriptionPlan(name="Cloud ERP Annual (Save 15%)", product_id=p1.id, price=Decimal("51000.00"), billing_frequency=BillingFrequency.YEARLY, min_quantity=1),
        SubscriptionPlan(name="CRM Pro Monthly", product_id=p2.id, price=Decimal("2500.00"), billing_frequency=BillingFrequency.MONTHLY, min_quantity=1),
        SubscriptionPlan(name="CRM Pro Annual", product_id=p2.id, price=Decimal("26000.00"), billing_frequency=BillingFrequency.YEARLY, min_quantity=1),
        SubscriptionPlan(name="AI Analytics Weekly Sprint", product_id=p3.id, price=Decimal("950.00"), billing_frequency=BillingFrequency.WEEKLY, min_quantity=1),
        SubscriptionPlan(name="AI Analytics Monthly", product_id=p3.id, price=Decimal("3500.00"), billing_frequency=BillingFrequency.MONTHLY, min_quantity=1),
        SubscriptionPlan(name="Helpdesk Daily Flex", product_id=p4.id, price=Decimal("75.00"), billing_frequency=BillingFrequency.DAILY, min_quantity=1),
        SubscriptionPlan(name="Helpdesk Suite Monthly", product_id=p4.id, price=Decimal("1800.00"), billing_frequency=BillingFrequency.MONTHLY, min_quantity=1),
        SubscriptionPlan(name="HRMS Monthly Basic", product_id=p5.id, price=Decimal("2200.00"), billing_frequency=BillingFrequency.MONTHLY, min_quantity=1),
        SubscriptionPlan(name="HRMS Annual Enterprise", product_id=p5.id, price=Decimal("22000.00"), billing_frequency=BillingFrequency.YEARLY, min_quantity=1),
        SubscriptionPlan(name="Cloud Shield Security Monthly", product_id=p6.id, price=Decimal("1500.00"), billing_frequency=BillingFrequency.MONTHLY, min_quantity=1),
        SubscriptionPlan(name="24x7 Priority Support Annual", product_id=p8.id, price=Decimal("12000.00"), billing_frequency=BillingFrequency.YEARLY, min_quantity=1),
    ]
    db.add_all(plans)
    db.flush()

    # 8. Subscriptions (15 with diverse statuses)
    print("Seeding 15 Subscriptions...")
    today = date.today()
    subs = []

    statuses = [
        SubscriptionStatus.ACTIVE, SubscriptionStatus.ACTIVE, SubscriptionStatus.ACTIVE,
        SubscriptionStatus.ACTIVE, SubscriptionStatus.ACTIVE, SubscriptionStatus.ACTIVE,
        SubscriptionStatus.CONFIRMED, SubscriptionStatus.CONFIRMED, SubscriptionStatus.QUOTATION,
        SubscriptionStatus.DRAFT, SubscriptionStatus.PAUSED, SubscriptionStatus.PAUSED,
        SubscriptionStatus.CLOSED, SubscriptionStatus.CLOSED, SubscriptionStatus.CANCELLED
    ]

    for i in range(15):
        cust = customers[i % len(customers)]
        plan = plans[i % len(plans)]
        st = statuses[i]
        start_d = today - timedelta(days=(i * 15) + 10)
        exp_d = start_d + timedelta(days=30 if plan.billing_frequency == BillingFrequency.MONTHLY else 365)
        if st == SubscriptionStatus.CLOSED:
            exp_d = today - timedelta(days=5) # Expired in past

        sub = Subscription(
            subscription_number=f"SUB-2026-{i+1:04d}",
            customer_id=cust.id,
            plan_id=plan.id,
            start_date=start_d,
            expiry_date=exp_d,
            payment_terms=PaymentTerms.NET_30,
            subtotal=plan.price,
            tax_amount=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            total_amount=plan.price,
            status=st,
            last_invoice_date=start_d if st in [SubscriptionStatus.ACTIVE, SubscriptionStatus.CLOSED] else None,
            next_invoice_date=exp_d if st == SubscriptionStatus.ACTIVE else None,
            created_by=admin.id
        )
        db.add(sub)
        db.flush()

        # Add line
        s_line = SubscriptionLine(
            subscription_id=sub.id,
            product_id=plan.product_id,
            quantity=1,
            unit_price=plan.price,
            line_total=plan.price
        )
        db.add(s_line)

        # Status History
        hist = SubscriptionStatusHistory(
            subscription_id=sub.id,
            from_status=None,
            to_status=st,
            changed_by=admin.id,
            reason="Seed creation",
            changed_at=utc_now() - timedelta(days=i*10)
        )
        db.add(hist)
        subs.append(sub)

    db.flush()

    # 9. Invoices (15 invoices with paid, partial, confirmed, overdue statuses)
    print("Seeding 15 Invoices...")
    invoices = []
    inv_statuses = [
        InvoiceStatus.PAID, InvoiceStatus.PAID, InvoiceStatus.PAID,
        InvoiceStatus.PAID, InvoiceStatus.PAID, InvoiceStatus.PARTIALLY_PAID,
        InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.CONFIRMED, InvoiceStatus.CONFIRMED,
        InvoiceStatus.OVERDUE, InvoiceStatus.OVERDUE, InvoiceStatus.OVERDUE,
        InvoiceStatus.DRAFT, InvoiceStatus.CONFIRMED, InvoiceStatus.PAID
    ]

    for i in range(15):
        sub = subs[i]
        st = inv_statuses[i]
        inv_date = today - timedelta(days=45 - (i * 2))
        due_date = inv_date + timedelta(days=15)
        if st == InvoiceStatus.OVERDUE:
            due_date = today - timedelta(days=10) # overdue in past

        tot = sub.total_amount
        if st == InvoiceStatus.PAID:
            paid = tot
            due = Decimal("0.00")
        elif st == InvoiceStatus.PARTIALLY_PAID:
            paid = Decimal(str(round(float(tot) * 0.4, 2)))
            due = tot - paid
        else:
            paid = Decimal("0.00")
            due = tot

        inv = Invoice(
            invoice_number=f"INV-2026-{i+1:04d}",
            customer_id=sub.customer_id,
            subscription_id=sub.id,
            invoice_date=inv_date,
            due_date=due_date,
            billing_period_start=inv_date,
            billing_period_end=inv_date + timedelta(days=30),
            subtotal=tot,
            tax_amount=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            total=tot,
            amount_paid=paid,
            amount_due=due,
            status=st,
            notes=f"Billing cycle invoice for {sub.subscription_number}",
            created_by=admin.id
        )
        db.add(inv)
        db.flush()

        inv_line = InvoiceLine(
            invoice_id=inv.id,
            product_id=sub.plan.product_id,
            quantity=1,
            unit_price=tot,
            line_total=tot
        )
        db.add(inv_line)
        invoices.append(inv)

    db.flush()

    # 10. Payments (10 payments)
    print("Seeding 10 Payments...")
    methods = [
        PaymentMethod.UPI, PaymentMethod.BANK_TRANSFER, PaymentMethod.CARD,
        PaymentMethod.UPI, PaymentMethod.BANK_TRANSFER, PaymentMethod.CARD,
        PaymentMethod.UPI, PaymentMethod.BANK_TRANSFER, PaymentMethod.CARD, PaymentMethod.CASH
    ]
    paid_invoices = [inv for inv in invoices if inv.amount_paid > Decimal("0.00")]

    for i in range(min(10, len(paid_invoices))):
        target_inv = paid_invoices[i]
        pay = Payment(
            payment_number=f"PAY-2026-{i+1:04d}",
            invoice_id=target_inv.id,
            customer_id=target_inv.customer_id,
            amount=target_inv.amount_paid,
            payment_method=methods[i],
            payment_date=target_inv.invoice_date + timedelta(days=3),
            transaction_reference=f"TXN-BL-{20260000 + i}",
            notes="Settled via payment gateway",
            recorded_by=staff1.id
        )
        db.add(pay)

    # 11. Initial Notifications
    print("Seeding Notifications...")
    for u in [admin, staff1]:
        db.add(Notification(
            user_id=u.id,
            title="System Ready",
            message="Brightloop Subscription Management System initialized with demonstration data.",
            notification_type=NotificationType.GENERAL,
            is_read=False
        ))

    db.commit()
    print("Database seeding completed successfully!")
    db.close()


if __name__ == "__main__":
    seed_database()
