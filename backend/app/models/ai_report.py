"""AI Analysis Report model for drug-drug, drug-food, and drug-allergy interactions."""
import enum
from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.base import TimeStampedModel


class InteractionSeverity(str, enum.Enum):
    """Severity classification for clinical drug safety checks."""
    NONE = "NONE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AIAnalysisReport(Base, TimeStampedModel):
    """Stores AI-assisted safety analysis reports for a prescription or drug combination."""
    __tablename__ = "ai_analysis_reports"

    prescription_id = Column(Integer, ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=True, index=True)
    analyzed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    overall_risk_level = Column(
        Enum(InteractionSeverity),
        default=InteractionSeverity.NONE,
        nullable=False,
        index=True,
    )
    total_findings = Column(Integer, default=0, nullable=False)
    
    # JSON payloads containing structured findings and categorized insights
    findings = Column(JSON, nullable=True)
    drug_drug_interactions = Column(JSON, nullable=True)
    drug_food_interactions = Column(JSON, nullable=True)
    drug_allergy_interactions = Column(JSON, nullable=True)
    
    clinical_summary = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    ai_recommendations = Column(Text, nullable=True)
    disclaimer = Column(Text, nullable=True)
    analysis_status = Column(String(50), default="COMPLETED", nullable=False)
    raw_ai_response = Column(Text, nullable=True)

    # Relationships
    prescription = relationship("Prescription", back_populates="ai_reports")
    patient = relationship("PatientProfile")
    analyzed_by = relationship("User")

    def __repr__(self) -> str:
        return f"<AIAnalysisReport(id={self.id}, prescription_id={self.prescription_id}, risk='{self.overall_risk_level}')>"
