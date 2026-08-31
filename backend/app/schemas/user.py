"""User schemas for serialization and validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base fields for User."""
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    role: UserRole = UserRole.PATIENT


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str


class StaffCreate(BaseModel):
    """Schema for administrative staff provisioning (LAB_TECHNICIAN, PHARMACY_STAFF, ADMIN)."""
    email: EmailStr
    full_name: str
    password: str
    phone_number: Optional[str] = None
    role: UserRole = UserRole.LAB_TECHNICIAN


class UserLogin(BaseModel):
    """Schema for user login credentials."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user details."""
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None


class UserRead(UserBase):
    """Schema for reading user details."""
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
