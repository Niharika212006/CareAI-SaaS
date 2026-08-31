"""MedicalDocument model definition for patient health records management."""
import enum
from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.base import TimeStampedModel


class DocumentType(str, enum.Enum):
    """Categorization of healthcare documents."""
    LAB_REPORT = "LAB_REPORT"
    IMAGING = "IMAGING"
    PRESCRIPTION = "PRESCRIPTION"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    MEDICAL_CERTIFICATE = "MEDICAL_CERTIFICATE"
    OTHER = "OTHER"


class MedicalDocument(Base, TimeStampedModel):
    """Medical record metadata and file pointer entity."""
    __tablename__ = "medical_documents"

    patient_id = Column(
        Integer,
        ForeignKey("patient_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    document_type = Column(
        Enum(DocumentType),
        default=DocumentType.OTHER,
        nullable=False,
        index=True,
    )
    description = Column(Text, nullable=True)

    # File Storage Metadata
    file_name = Column(String(255), nullable=False)  # Sanitized original display name
    storage_key = Column(String(500), unique=True, nullable=False, index=True)  # File key in storage
    file_size = Column(Integer, nullable=False)  # Size in bytes
    mime_type = Column(String(100), nullable=False)

    # Relationships
    patient = relationship("PatientProfile", back_populates="documents")
    uploaded_by = relationship("User", back_populates="uploaded_documents")
    analyses = relationship("MedicalDocumentAnalysis", back_populates="document", cascade="all, delete-orphan", order_by="desc(MedicalDocumentAnalysis.created_at)")

    def __repr__(self) -> str:
        return f"<MedicalDocument(id={self.id}, patient_id={self.patient_id}, title='{self.title}', type='{self.document_type}')>"
