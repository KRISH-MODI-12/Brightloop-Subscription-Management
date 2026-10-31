import pytest
import os
import tempfile
from datetime import date
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import all models so Base.metadata contains all tables
import app.models
from app.database import Base
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.subscription import Subscription
from app.models.payment import Payment
from app.models.sequence import DocumentSequence
from app.core.security import get_password_hash
from app.core.deps import require_roles
from app.schemas.auth import UserCreate, AdminUserCreate
from app.api.v1.auth import register
from app.api.v1.users import create_staff_or_admin
from app.services.billing_service import generate_invoice_number
from app.services.subscription_service import generate_subscription_number
from app.services.payment_service import generate_payment_number
import app.services.sequence_service as seq_svc


@pytest.fixture(scope="function")
def test_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_url = f"sqlite:///{path}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

    seq_svc._table_ensured = False

    yield {"session": session, "factory": Session, "engine": engine}

    session.close()
    engine.dispose()
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


# ==============================================================================
# P0.1: Public Registration Privilege Escalation Tests
# ==============================================================================

def test_register_forces_customer_when_admin_requested(test_db):
    db = test_db["session"]
    user_in = UserCreate(
        email="attacker_admin@example.com",
        password="ValidPassword@123",
        full_name="Attacker Admin",
        role=UserRole.ADMIN,
        company_name="Evil Corp"
    )
    token_resp = register(user_in=user_in, db=db)
    assert token_resp.user.role == UserRole.CUSTOMER

    user = db.query(User).filter(User.email == user_in.email).first()
    assert user is not None
    assert user.role == UserRole.CUSTOMER

    cust = db.query(Customer).filter(Customer.user_id == user.id).first()
    assert cust is not None
    assert cust.company_name == "Evil Corp"


def test_register_forces_customer_when_staff_requested(test_db):
    db = test_db["session"]
    user_in = UserCreate(
        email="attacker_staff@example.com",
        password="ValidPassword@123",
        full_name="Attacker Staff",
        role=UserRole.STAFF
    )
    token_resp = register(user_in=user_in, db=db)
    assert token_resp.user.role == UserRole.CUSTOMER

    user = db.query(User).filter(User.email == user_in.email).first()
    assert user.role == UserRole.CUSTOMER


def test_register_default_role_is_customer(test_db):
    db = test_db["session"]
    user_in = UserCreate(
        email="normal_cust@example.com",
        password="ValidPassword@123",
        full_name="Normal Customer"
    )
    token_resp = register(user_in=user_in, db=db)
    assert token_resp.user.role == UserRole.CUSTOMER


# ==============================================================================
# P0.2: Admin-Only Staff Creation & Authorization Tests
# ==============================================================================

def test_role_checker_enforcement():
    admin_checker = require_roles([UserRole.ADMIN])

    admin_user = User(id=1, email="admin@test.com", role=UserRole.ADMIN, is_active=True)
    staff_user = User(id=2, email="staff@test.com", role=UserRole.STAFF, is_active=True)
    cust_user = User(id=3, email="cust@test.com", role=UserRole.CUSTOMER, is_active=True)

    # Admin passes
    assert admin_checker(admin_user) == admin_user

    # Staff gets 403
    with pytest.raises(HTTPException) as exc_staff:
        admin_checker(staff_user)
    assert exc_staff.value.status_code == 403

    # Customer gets 403
    with pytest.raises(HTTPException) as exc_cust:
        admin_checker(cust_user)
    assert exc_cust.value.status_code == 403


def test_admin_can_create_staff(test_db):
    db = test_db["session"]
    admin = User(
        email="admin_creator@test.com",
        hashed_password=get_password_hash("AdminPass@123"),
        full_name="Admin Creator",
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(admin)
    db.commit()

    user_in = AdminUserCreate(
        email="staff_created@test.com",
        password="StaffPass@123",
        full_name="Staff Created",
        role=UserRole.STAFF
    )
    created = create_staff_or_admin(user_in=user_in, db=db, admin_user=admin)
    assert created.role == UserRole.STAFF
    assert created.email == "staff_created@test.com"

    db_user = db.query(User).filter(User.email == "staff_created@test.com").first()
    assert db_user is not None
    assert db_user.role == UserRole.STAFF


def test_admin_create_user_validation(test_db):
    db = test_db["session"]
    admin = User(
        email="admin_val@test.com",
        hashed_password=get_password_hash("AdminPass@123"),
        full_name="Admin Val",
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(admin)
    db.commit()

    # Weak password
    with pytest.raises(HTTPException) as exc_weak:
        create_staff_or_admin(
            user_in=AdminUserCreate(
                email="weak@test.com",
                password="weak",
                full_name="Weak Pass",
                role=UserRole.STAFF
            ),
            db=db,
            admin_user=admin
        )
    assert exc_weak.value.status_code == 400

    # Duplicate email
    with pytest.raises(HTTPException) as exc_dup:
        create_staff_or_admin(
            user_in=AdminUserCreate(
                email="admin_val@test.com",
                password="ValidPassword@123",
                full_name="Duplicate",
                role=UserRole.STAFF
            ),
            db=db,
            admin_user=admin
        )
    assert exc_dup.value.status_code == 400


# ==============================================================================
# P0.3: Document Number Generation Concurrency & Race Conditions
# ==============================================================================

def test_sequential_document_numbers(test_db):
    db = test_db["session"]
    nums = [generate_invoice_number(db) for _ in range(5)]
    db.commit()
    assert len(set(nums)) == 5
    for n in nums:
        assert n.startswith("INV-")


def test_preserves_existing_document_numbers(test_db):
    db = test_db["session"]
    # Seed existing records in database: INV-2026-0024
    admin = User(email="test_seq@test.com", hashed_password="x", full_name="T", role=UserRole.ADMIN)
    db.add(admin)
    db.flush()

    cust = Customer(user_id=admin.id, company_name="C")
    db.add(cust)
    db.flush()

    inv24 = Invoice(
        invoice_number="INV-2026-0024",
        customer_id=cust.id,
        invoice_date=date.today(),
        due_date=date.today(),
        subtotal=Decimal("100"),
        total=Decimal("100"),
        amount_paid=Decimal("0"),
        amount_due=Decimal("100")
    )
    db.add(inv24)
    db.commit()

    # Next invoice MUST be INV-2026-0025
    next_num = generate_invoice_number(db)
    assert next_num == "INV-2026-0025"


def test_concurrent_document_number_generation(test_db):
    factory = test_db["factory"]

    def gen(_):
        s = factory()
        try:
            num = generate_invoice_number(s)
            s.commit()
            return num
        finally:
            s.close()

    iterations = 25
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(gen, range(iterations)))

    assert len(results) == iterations
    assert len(set(results)) == iterations, f"Duplicates detected: {results}"


def test_concurrent_subscription_and_payment_generation(test_db):
    factory = test_db["factory"]

    def gen_sub(_):
        s = factory()
        try:
            num = generate_subscription_number(s)
            s.commit()
            return num
        finally:
            s.close()

    def gen_pay(_):
        s = factory()
        try:
            num = generate_payment_number(s)
            s.commit()
            return num
        finally:
            s.close()

    iterations = 20
    with ThreadPoolExecutor(max_workers=4) as executor:
        sub_results = list(executor.map(gen_sub, range(iterations)))
        pay_results = list(executor.map(gen_pay, range(iterations)))

    assert len(set(sub_results)) == iterations
    assert len(set(pay_results)) == iterations
    for s in sub_results:
        assert s.startswith("SUB-")
    for p in pay_results:
        assert p.startswith("PAY-")
