from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.customer import Customer
from app.models.user import User, UserRole
from app.core.deps import get_current_user, get_staff_or_admin
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.core.security import get_password_hash, validate_password_strength
from app.services.audit_service import log_action

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=List[CustomerResponse])
def list_customers(
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Customer).filter(Customer.is_deleted == False)

    # Customer isolation
    if current_user.role == UserRole.CUSTOMER:
        query = query.filter(Customer.user_id == current_user.id)
    else:
        if search:
            query = query.join(Customer.user).filter(
                or_(
                    Customer.company_name.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    Customer.city.ilike(f"%{search}%")
                )
            )

    return query.offset(skip).limit(limit).all()


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    cust_in: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin)
):
    if cust_in.user_id:
        user = db.query(User).filter(User.id == cust_in.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
    else:
        if not cust_in.email or not cust_in.full_name or not cust_in.password:
            raise HTTPException(status_code=400, detail="Email, full name and password required to create new user.")
        
        existing = db.query(User).filter(User.email == cust_in.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered.")

        is_valid, msg = validate_password_strength(cust_in.password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=msg)

        user = User(
            email=cust_in.email,
            full_name=cust_in.full_name,
            phone=cust_in.phone,
            hashed_password=get_password_hash(cust_in.password),
            role=UserRole.CUSTOMER,
            is_active=True
        )
        db.add(user)
        db.flush()

    customer = Customer(
        user_id=user.id,
        company_name=cust_in.company_name,
        address=cust_in.address,
        city=cust_in.city,
        state=cust_in.state,
        country=cust_in.country or "India",
        postal_code=cust_in.postal_code,
        gst_number=cust_in.gst_number,
        notes=cust_in.notes
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    log_action(
        db=db,
        action="CUSTOMER_CREATED",
        entity_type="customer",
        entity_id=customer.id,
        user_id=current_user.id,
        details=f"Customer created for user {user.email}"
    )

    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.is_deleted == False).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    if current_user.role == UserRole.CUSTOMER and customer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this customer record.")

    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    cust_in: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin)
):
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.is_deleted == False).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    for field, val in cust_in.model_dump(exclude_unset=True).items():
        if field in ["full_name", "phone"]:
            if customer.user:
                setattr(customer.user, field, val)
        elif hasattr(customer, field):
            setattr(customer, field, val)

    db.commit()
    db.refresh(customer)

    log_action(
        db=db,
        action="CUSTOMER_UPDATED",
        entity_type="customer",
        entity_id=customer.id,
        user_id=current_user.id,
        details="Customer details updated"
    )

    return customer
