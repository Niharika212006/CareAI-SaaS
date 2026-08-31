"""Appointment model definition for clinical scheduling."""
import enum
from sqlalchemy import Column, Integer, DateTime, Text, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.base import TimeStampedModel


class AppointmentStatus(str, enum.Enum):
    """Lifecycle status of a consultation appointment."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class Appointment(Base, TimeStampedModel):
    """Consultation appointment connecting a Patient with a Doctor."""
    __tablename__ = "appointments"

    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    scheduled_start = Column(DateTime, nullable=False, index=True)
    scheduled_end = Column(DateTime, nullable=False)
    
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING, nullable=False, index=True)
    reason_for_visit = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    patient_notes = Column(Text, nullable=True)
    doctor_notes = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    meeting_link = Column(String(500), nullable=True)

    # Relationships
    patient = relationship("PatientProfile", back_populates="appointments")
    doctor = relationship("DoctorProfile", back_populates="appointments")
    prescription = relationship("Prescription", back_populates="appointment", uselist=False)

    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, doctor_id={self.doctor_id}, patient_id={self.patient_id}, status='{self.status}')>"

