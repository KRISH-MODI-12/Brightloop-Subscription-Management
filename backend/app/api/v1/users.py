from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.core.deps import get_admin_user
from app.core.security import get_password_hash, validate_password_strength
from app.schemas.auth import AdminUserCreate, UserResponse
from app.services.audit_service import log_action

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("", response_model=List[UserResponse])
def list_users(
    role: Optional[UserRole] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    List system users. Restricted to Admin only.
    """
    query = db.query(User).filter(User.is_deleted == False)
    if role:
        query = query.filter(User.role == role)
    users = query.offset(skip).limit(limit).all()

    # Populate customer_id for responses
    response_users = []
    for u in users:
        cust = db.query(Customer).filter(Customer.user_id == u.id).first()
        u_dict = {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "phone": u.phone,
            "role": u.role,
            "is_active": u.is_active,
            "last_login": u.last_login,
            "created_at": u.created_at,
            "customer_id": cust.id if cust else None
        }
        response_users.append(UserResponse(**u_dict))
    return response_users


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_staff_or_admin(
    user_in: AdminUserCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Create a new Staff or Admin user account.
    Restricted to Admin only. Prevents unauthorized role escalation.
    """
    # Check if email exists
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Validate password strength
    is_valid, msg = validate_password_strength(user_in.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    # Allowed roles for admin creation
    target_role = user_in.role or UserRole.STAFF

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        phone=user_in.phone,
        role=target_role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_action(
        db=db,
        action="USER_CREATED_BY_ADMIN",
        entity_type="user",
        entity_id=user.id,
        user_id=admin_user.id,
        details=f"Admin {admin_user.email} created user {user.email} with role {user.role.value}"
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
        customer_id=None
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Get user details by ID. Restricted to Admin only.
    """
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    cust = db.query(Customer).filter(Customer.user_id == user.id).first()
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
        customer_id=cust.id if cust else None
    )

