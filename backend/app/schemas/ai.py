"""AI interaction checker and patient safety report schemas."""
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field
from app.models.ai_report import InteractionSeverity


class SafetyFinding(BaseModel):
    """Structured clinical safety finding for an individual hazard or advisory."""
    category: str  # "DRUG_DRUG", "DRUG_FOOD", "DRUG_ALLERGY", "DUPLICATE_MEDICATION"
    severity: InteractionSeverity
    medications: List[str]
    title: Optional[str] = None
    explanation: str
    recommended_action: str

    model_config = ConfigDict(from_attributes=True)


class InteractionItem(BaseModel):
    """Legacy compatibility schema for payload interactions."""
    interaction_type: str
    severity: InteractionSeverity
    entities: List[str]
    description: str
    clinical_recommendation: str


class AIInteractionCheckRequest(BaseModel):
    """Request payload for arbitrary medication list and allergy checks."""
    prescription_id: Optional[int] = None
    patient_id: Optional[int] = None
    medications: List[str]
    patient_allergies: Optional[List[str]] = []
    patient_conditions: Optional[List[str]] = []


class AISafetyReportResponse(BaseModel):
    """Comprehensive structured AI safety report response."""
    id: Optional[int] = None
    prescription_id: Optional[int] = None
    patient_id: Optional[int] = None
    overall_risk_level: InteractionSeverity
    total_findings: int = 0
    findings: List[SafetyFinding] = []
    drug_drug_interactions: List[SafetyFinding] = []
    drug_food_interactions: List[SafetyFinding] = []
    drug_allergy_interactions: List[SafetyFinding] = []
    clinical_summary: str
    summary: Optional[str] = None
    ai_recommendations: List[str] = []
    disclaimer: str = (
        "This analysis is intended for informational and clinical decision support purposes only. "
        "It does not replace professional medical advice, diagnosis, or treatment. "
        "Consult a qualified healthcare professional before making decisions about medications."
    )
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)
