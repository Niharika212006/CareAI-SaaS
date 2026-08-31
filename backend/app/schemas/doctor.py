"""Doctor profile schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.doctor import DoctorApprovalStatus
from app.schemas.user import UserRead


class DoctorProfileBase(BaseModel):
    """Base fields for doctor profile."""
    specialization: str
    license_number: str
    experience_years: int = 0
    bio: Optional[str] = None
    hospital_affiliation: Optional[str] = None
    consultation_fee: Decimal = Decimal("0.00")


class DoctorProfileCreate(DoctorProfileBase):
    """Schema for creating a doctor profile during application."""
    pass


class DoctorProfileUpdate(BaseModel):
    """Schema for updating a doctor profile."""
    specialization: Optional[str] = None
    experience_years: Optional[int] = None
    bio: Optional[str] = None
    hospital_affiliation: Optional[str] = None
    consultation_fee: Optional[Decimal] = None


class DoctorApprovalUpdate(BaseModel):
    """Schema for admin approval or rejection of a doctor profile."""
    approval_status: DoctorApprovalStatus
    rejection_reason: Optional[str] = None


class DoctorProfileRead(DoctorProfileBase):
    """Schema for reading doctor profile."""
    id: int
    user_id: int
    approval_status: DoctorApprovalStatus
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    user: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)
