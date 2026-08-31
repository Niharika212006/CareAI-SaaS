"""Pydantic schemas for AI-Powered Medical Document Analysis."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

from app.models.document_analysis import AnalysisStatus


class MedicationItem(BaseModel):
    """Detected medication name and dosage extracted from record."""
    name: str
    dosage: Optional[str] = None


class TestValueItem(BaseModel):
    """Detected clinical test, numerical value, and reference flag context."""
    test: str
    value: str
    reference_context: Optional[str] = None


class PotentialConcernItem(BaseModel):
    """Identified clinical observation or potential concern with responsible severity."""
    level: str = "low"  # low, medium, high
    message: str


class DocumentAnalysisRead(BaseModel):
    """Structured response schema for AI medical document analysis."""
    id: int
    document_id: int
    requested_by_user_id: int
    analysis_status: AnalysisStatus
    summary: str
    document_category: Optional[str] = None
    key_findings: List[str] = Field(default_factory=list)
    detected_medications: List[MedicationItem] = Field(default_factory=list)
    detected_test_values: List[TestValueItem] = Field(default_factory=list)
    potential_concerns: List[PotentialConcernItem] = Field(default_factory=list)
    patient_friendly_explanation: Optional[str] = None
    recommended_next_step: Optional[str] = None
    disclaimer: str
    ai_model_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
