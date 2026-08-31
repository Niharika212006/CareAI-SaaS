"""MedicalDocumentAnalysis model for storing structured AI insights for patient documents."""
import enum
from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.base import TimeStampedModel


class AnalysisStatus(str, enum.Enum):
    """Execution status of document analysis."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MedicalDocumentAnalysis(Base, TimeStampedModel):
    """Persisted AI-generated clinical analysis for a medical document."""
    __tablename__ = "medical_document_analyses"

    document_id = Column(
        Integer,
        ForeignKey("medical_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requested_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    extracted_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=False)
    document_category = Column(String(100), nullable=True)

    # Structured Findings
    key_findings = Column(JSON, nullable=True)  # List[str]
    detected_medications = Column(JSON, nullable=True)  # List[Dict[str, str]]
    detected_test_values = Column(JSON, nullable=True)  # List[Dict[str, str]]
    potential_concerns = Column(JSON, nullable=True)  # List[Dict[str, str]]

    patient_friendly_explanation = Column(Text, nullable=True)
    recommended_next_step = Column(Text, nullable=True)
    disclaimer = Column(Text, nullable=False)

    analysis_status = Column(
        Enum(AnalysisStatus),
        default=AnalysisStatus.COMPLETED,
        nullable=False,
        index=True,
    )
    ai_model_name = Column(String(100), default="CareAI-Clinical-Insight-v1", nullable=False)

    # Relationships
    document = relationship("MedicalDocument", back_populates="analyses")
    requested_by = relationship("User", back_populates="document_analyses")

    def __repr__(self) -> str:
        return f"<MedicalDocumentAnalysis(id={self.id}, document_id={self.document_id}, status='{self.analysis_status}')>"
