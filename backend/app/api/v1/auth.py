from datetime import datetime, timedelta
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.datetime_utils import utc_now
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.core.security import (
    verify_password, get_password_hash, validate_password_strength,
    create_access_token
)
from app.core.deps import get_current_user
from app.schemas.auth import (
    UserCreate, UserResponse, LoginRequest, TokenResponse,
    PasswordResetRequest, PasswordResetConfirm, ChangePasswordRequest
)
from app.services.audit_service import log_action
from app.services.notification_service import create_notification
from app.models.notification import NotificationType

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if email exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Validate password policy
    is_valid, msg = validate_password_strength(user_in.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    # Create user - explicitly enforce CUSTOMER role for public registration
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        phone=user_in.phone,
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db.add(user)
    db.flush()

    customer_id = None
    # Always create customer profile for public registration
    customer = Customer(
        user_id=user.id,
        company_name=user_in.company_name,
        address=user_in.address,
        city=user_in.city,
        state=user_in.state,
        country=user_in.country or "India",
        postal_code=user_in.postal_code,
        gst_number=user_in.gst_number
    )
    db.add(customer)
    db.flush()
    customer_id = customer.id

    db.commit()
    db.refresh(user)

    log_action(
        db=db,
        action="USER_REGISTERED",
        entity_type="user",
        entity_id=user.id,
        user_id=user.id,
        details=f"New user registered with role {user.role.value}"
    )

    create_notification(
        db=db,
        user_id=user.id,
        title="Welcome to Brightloop!",
        message="Your account has been registered successfully. Explore our subscription plans.",
        notification_type=NotificationType.REGISTRATION
    )

    token = create_access_token(user.id)
    user_resp = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
        customer_id=customer_id
    )
    return TokenResponse(access_token=token, token_type="bearer", user=user_resp)


@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email, User.is_deleted == False).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your account is deactivated. Please contact support."
        )

    user.last_login = utc_now()
    db.commit()

    customer_id = None
    if user.customer_profile:
        customer_id = user.customer_profile[0].id if isinstance(user.customer_profile, list) and user.customer_profile else (user.customer_profile.id if hasattr(user.customer_profile, 'id') else None)

    token = create_access_token(user.id)
    user_resp = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
        customer_id=customer_id
    )
    return TokenResponse(access_token=token, token_type="bearer", user=user_resp)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        role=current_user.role,
        is_active=current_user.is_active,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        customer_id=cust.id if cust else None
    )


@router.post("/forgot-password")
def forgot_password(req: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email, User.is_deleted == False).first()
    if user:
        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        user.password_reset_expires = utc_now() + timedelta(hours=2)
        db.commit()

        create_notification(
            db=db,
            user_id=user.id,
            title="Password Reset Requested",
            message=f"Use reset token: {token} or follow the reset link to choose a new password.",
            notification_type=NotificationType.PASSWORD_RESET
        )
    return {"message": "If this email is registered, password reset instructions have been dispatched."}


@router.post("/reset-password")
def reset_password(req: PasswordResetConfirm, db: Session = Depends(get_db)):
    now_ts = utc_now()
    user = db.query(User).filter(
        User.password_reset_token == req.token,
        User.password_reset_expires > now_ts
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token."
        )

    is_valid, msg = validate_password_strength(req.new_password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    user.hashed_password = get_password_hash(req.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()

    return {"message": "Password has been successfully updated. You may now login."}
