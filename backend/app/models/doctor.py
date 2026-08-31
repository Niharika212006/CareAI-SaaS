"""Doctor profile and verification model."""
import enum
from sqlalchemy import Column, String, Integer, Text, Numeric, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.base import TimeStampedModel


class DoctorApprovalStatus(str, enum.Enum):
    """Approval status for doctor credentials review by Admin."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DoctorProfile(Base, TimeStampedModel):
    """Doctor professional profile and verification details."""
    __tablename__ = "doctor_profiles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    specialization = Column(String(100), nullable=False, index=True)
    license_number = Column(String(100), unique=True, nullable=False)
    experience_years = Column(Integer, default=0, nullable=False)
    bio = Column(Text, nullable=True)
    hospital_affiliation = Column(String(255), nullable=True)
    consultation_fee = Column(Numeric(10, 2), default=0.00, nullable=False)
    
    approval_status = Column(
        Enum(DoctorApprovalStatus),
        default=DoctorApprovalStatus.PENDING,
        nullable=False,
        index=True,
    )
    rejection_reason = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="doctor_profile")
    appointments = relationship("Appointment", back_populates="doctor", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="doctor", cascade="all, delete-orphan")
    availabilities = relationship("DoctorAvailability", back_populates="doctor", cascade="all, delete-orphan")
    unavailable_dates = relationship("DoctorUnavailableDate", back_populates="doctor", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<DoctorProfile(id={self.id}, specialization='{self.specialization}', status='{self.approval_status}')>"
