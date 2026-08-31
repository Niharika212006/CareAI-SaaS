"""Appointment schemas for request validation and response serialization."""
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, ConfigDict, model_validator

from app.models.appointment import AppointmentStatus
from app.schemas.patient import PatientProfileRead
from app.schemas.doctor import DoctorProfileRead


class AppointmentBase(BaseModel):
    """Base fields for appointment."""
    doctor_id: int
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    appointment_datetime: Optional[datetime] = None
    reason: Optional[str] = None
    reason_for_visit: Optional[str] = None
    patient_notes: Optional[str] = None


class AppointmentCreate(BaseModel):
    """Schema for requesting a new consultation appointment."""
    doctor_id: int
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    appointment_datetime: Optional[datetime] = None
    reason: Optional[str] = None
    reason_for_visit: Optional[str] = None
    patient_notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_and_normalize_datetimes(self):
        # Resolve start time from appointment_datetime or scheduled_start
        start = self.scheduled_start or self.appointment_datetime
        if not start:
            raise ValueError("Either 'scheduled_start' or 'appointment_datetime' must be provided.")
        
        self.scheduled_start = start
        if not self.scheduled_end:
            self.scheduled_end = start + timedelta(minutes=30)
        elif self.scheduled_end <= self.scheduled_start:
            raise ValueError("scheduled_end must be after scheduled_start.")

        # Normalize reason
        if not self.reason_for_visit and self.reason:
            self.reason_for_visit = self.reason
        elif not self.reason and self.reason_for_visit:
            self.reason = self.reason_for_visit
            
        return self


class AppointmentUpdate(BaseModel):
    """Schema for modifying an appointment."""
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    reason: Optional[str] = None
    reason_for_visit: Optional[str] = None
    patient_notes: Optional[str] = None
    doctor_notes: Optional[str] = None
    meeting_link: Optional[str] = None


class AppointmentCancelRequest(BaseModel):
    """Schema for patient appointment cancellation request."""
    cancellation_reason: Optional[str] = None


class AppointmentRejectRequest(BaseModel):
    """Schema for doctor appointment rejection request."""
    rejection_reason: Optional[str] = None


class AppointmentCompleteRequest(BaseModel):
    """Schema for marking consultation complete with clinical notes."""
    doctor_notes: Optional[str] = None


class AppointmentRead(BaseModel):
    """Schema for reading an appointment record."""
    id: int
    patient_id: int
    doctor_id: int
    scheduled_start: datetime
    scheduled_end: datetime
    status: AppointmentStatus
    reason_for_visit: Optional[str] = None
    reason: Optional[str] = None
    patient_notes: Optional[str] = None
    doctor_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    rejection_reason: Optional[str] = None
    meeting_link: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    patient: Optional[PatientProfileRead] = None
    doctor: Optional[DoctorProfileRead] = None

    @model_validator(mode="after")
    def populate_aliases(self):
        if not self.reason and self.reason_for_visit:
            self.reason = self.reason_for_visit
        elif not self.reason_for_visit and self.reason:
            self.reason_for_visit = self.reason
        return self

    model_config = ConfigDict(from_attributes=True)

