"""Doctor availability and schedule models."""
from datetime import time, date
from sqlalchemy import Column, Integer, Time, Date, Boolean, ForeignKey, String, Index
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.base import TimeStampedModel


class DoctorAvailability(Base, TimeStampedModel):
    """
    Weekly recurring availability window configured by an approved doctor.
    day_of_week: 0 = Monday, 1 = Tuesday, 2 = Wednesday, 3 = Thursday, 4 = Friday, 5 = Saturday, 6 = Sunday
    """
    __tablename__ = "doctor_availabilities"

    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False, doc="0=Monday, 6=Sunday")
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_duration_minutes = Column(Integer, default=30, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    doctor = relationship("DoctorProfile", back_populates="availabilities")

    __table_args__ = (
        Index("ix_doctor_availability_lookup", "doctor_id", "day_of_week", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<DoctorAvailability(id={self.id}, doctor_id={self.doctor_id}, day={self.day_of_week}, {self.start_time}-{self.end_time})>"


class DoctorUnavailableDate(Base, TimeStampedModel):
    """Specific calendar date when a doctor is absent/unavailable (e.g. leave, holiday)."""
    __tablename__ = "doctor_unavailable_dates"

    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    unavailable_date = Column(Date, nullable=False, index=True)
    reason = Column(String(255), nullable=True)

    # Relationships
    doctor = relationship("DoctorProfile", back_populates="unavailable_dates")

    __table_args__ = (
        Index("ix_doctor_unavailable_date_lookup", "doctor_id", "unavailable_date"),
    )

    def __repr__(self) -> str:
        return f"<DoctorUnavailableDate(id={self.id}, doctor_id={self.doctor_id}, date={self.unavailable_date})>"
