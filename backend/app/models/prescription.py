import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.base import TimeStampedModel


class PrescriptionStatus(str, enum.Enum):
    """Fulfillment lifecycle status for clinical prescriptions."""
    PRESCRIBED = "PRESCRIBED"
    UNDER_REVIEW = "UNDER_REVIEW"
    READY = "READY"
    DISPENSED = "DISPENSED"
    CANCELLED = "CANCELLED"


class Prescription(Base, TimeStampedModel):
    """Clinical prescription issued by a Doctor to a Patient."""
    __tablename__ = "prescriptions"

    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, unique=True)
    
    diagnosis = Column(Text, nullable=False)
    clinical_notes = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    valid_until = Column(Date, nullable=True)

    # Pharmacy workflow fields
    status = Column(
        SQLEnum(PrescriptionStatus),
        default=PrescriptionStatus.PRESCRIBED,
        nullable=False,
        index=True,
    )
    pharmacy_notes = Column(Text, nullable=True)
    dispensed_at = Column(DateTime, nullable=True)
    dispensed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    patient = relationship("PatientProfile", back_populates="prescriptions")
    doctor = relationship("DoctorProfile", back_populates="prescriptions")
    appointment = relationship("Appointment", back_populates="prescription")
    dispensed_by = relationship("User", foreign_keys=[dispensed_by_user_id])
    items = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")
    ai_reports = relationship("AIAnalysisReport", back_populates="prescription", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Prescription(id={self.id}, patient_id={self.patient_id}, doctor_id={self.doctor_id}, status='{self.status}')>"


class PrescriptionItem(Base, TimeStampedModel):
    """Individual drug item within a prescription."""
    __tablename__ = "prescription_items"

    prescription_id = Column(Integer, ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    medication_name = Column(String(200), nullable=True, index=True)
    drug_name = Column(String(200), nullable=True, index=True)
    dosage = Column(String(100), nullable=False)  # e.g., "500 mg"
    frequency = Column(String(100), nullable=False)  # e.g., "Twice daily"
    duration = Column(String(100), nullable=False)  # e.g., "5 days"
    route_of_administration = Column(String(100), nullable=True)  # e.g., "Oral", "Intravenous"
    instructions = Column(Text, nullable=True)

    # Relationship
    prescription = relationship("Prescription", back_populates="items")

    def __repr__(self) -> str:
        name = self.medication_name or self.drug_name
        return f"<PrescriptionItem(id={self.id}, medication_name='{name}', dosage='{self.dosage}')>"
