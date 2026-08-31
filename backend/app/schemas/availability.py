"""Schemas for doctor availability, unavailable dates, and time slot discovery."""
from datetime import time, date, datetime
from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator


DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class DoctorAvailabilityBase(BaseModel):
    """Base fields for weekly availability schedule."""
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 1=Tuesday, ..., 6=Sunday")
    start_time: time = Field(..., description="Start time (e.g. 09:00:00)")
    end_time: time = Field(..., description="End time (e.g. 17:00:00)")
    slot_duration_minutes: int = Field(30, ge=10, le=180, description="Duration in minutes per consultation slot")
    is_active: bool = Field(True, description="Whether this day schedule is currently active")

    @model_validator(mode="after")
    def validate_time_window(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be earlier than end_time.")
        return self


class DoctorAvailabilityCreate(DoctorAvailabilityBase):
    """Schema for adding new day availability."""
    pass


class DoctorAvailabilityUpdate(BaseModel):
    """Schema for editing existing day availability."""
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    slot_duration_minutes: Optional[int] = Field(None, ge=10, le=180)
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def validate_time_window_if_present(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValueError("start_time must be earlier than end_time.")
        return self


class DoctorAvailabilityRead(BaseModel):
    """Schema for reading doctor availability."""
    id: int
    doctor_id: int
    day_of_week: int
    day_name: Optional[str] = None
    start_time: time
    end_time: time
    slot_duration_minutes: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def populate_day_name(self):
        if 0 <= self.day_of_week < len(DAYS_OF_WEEK):
            self.day_name = DAYS_OF_WEEK[self.day_of_week]
        return self

    model_config = ConfigDict(from_attributes=True)


class DoctorUnavailableDateCreate(BaseModel):
    """Schema for marking a calendar day as unavailable."""
    unavailable_date: date = Field(..., description="Date doctor is absent/on leave (YYYY-MM-DD)")
    reason: Optional[str] = Field(None, max_length=255, description="e.g. Annual Leave, Medical Conference")


class DoctorUnavailableDateRead(BaseModel):
    """Schema for reading an unavailable date entry."""
    id: int
    doctor_id: int
    unavailable_date: date
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DoctorAvailableSlotsResponse(BaseModel):
    """Dynamically calculated available appointment time slots for a doctor on a specific date."""
    doctor_id: int
    date: date
    slot_duration_minutes: int
    available_slots: List[str]

    model_config = ConfigDict(from_attributes=True)
