"""User model and Role Enum definition."""
import enum
from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.base import TimeStampedModel


class UserRole(str, enum.Enum):
    """User roles for role-based access control."""
    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    ADMIN = "ADMIN"
    LAB_TECHNICIAN = "LAB_TECHNICIAN"
    PHARMACY_STAFF = "PHARMACY_STAFF"


class User(Base, TimeStampedModel):
    """User account entity."""
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.PATIENT, nullable=False, index=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Relationships
    patient_profile = relationship("PatientProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor_profile = relationship("DoctorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan", order_by="desc(Notification.created_at)")
    uploaded_documents = relationship("MedicalDocument", back_populates="uploaded_by", cascade="all, delete-orphan", order_by="desc(MedicalDocument.created_at)")
    document_analyses = relationship("MedicalDocumentAnalysis", back_populates="requested_by", cascade="all, delete-orphan", order_by="desc(MedicalDocumentAnalysis.created_at)")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
