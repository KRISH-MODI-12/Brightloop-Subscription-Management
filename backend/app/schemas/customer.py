from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from app.schemas.auth import UserResponse


class CustomerBase(BaseModel):
    company_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "India"
    postal_code: Optional[str] = None
    gst_number: Optional[str] = None
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    user_id: Optional[int] = None
    # Can also create customer + user inline
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None


class CustomerUpdate(CustomerBase):
    is_active: Optional[bool] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True
