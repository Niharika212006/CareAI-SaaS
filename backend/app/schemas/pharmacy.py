"""Pydantic schemas for Pharmacy Staff operations, prescription dispensing, and queue tracking."""
from datetime import datetime, date
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, field_validator

from app.models.prescription import PrescriptionStatus
from app.models.ai_report import InteractionSeverity
from app.schemas.prescription import PrescriptionItemRead
from app.schemas.patient import PatientProfileRead
from app.schemas.doctor import DoctorProfileRead
from app.schemas.ai import AISafetyReportResponse


class PrescriptionStatusUpdate(BaseModel):
    """Schema for updating prescription status in the pharmacy workflow."""
    status: PrescriptionStatus
    pharmacy_notes: Optional[str] = None


class PrescriptionDispenseRequest(BaseModel):
    """Schema for recording prescription dispensing action."""
    pharmacy_notes: Optional[str] = None


class PharmacyPrescriptionSummary(BaseModel):
    """Summarized prescription record for pharmacy work queue table."""
    id: int
    patient_id: int
    patient_name: str
    patient_gender: Optional[str] = None
    patient_age: Optional[int] = None
    doctor_id: int
    doctor_name: str
    doctor_specialization: Optional[str] = None
    diagnosis: str
    status: PrescriptionStatus
    medications_count: int
    medication_names: List[str] = []
    has_ai_report: bool = False
    ai_risk_level: Optional[InteractionSeverity] = None
    pharmacy_notes: Optional[str] = None
    created_at: datetime
    valid_until: Optional[date] = None
    dispensed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PharmacyPrescriptionDetail(BaseModel):
    """Full detail prescription record for dispensary review with AI safety insights."""
    id: int
    appointment_id: Optional[int] = None
    patient_id: int
    patient: Optional[PatientProfileRead] = None
    doctor_id: int
    doctor: Optional[DoctorProfileRead] = None
    diagnosis: str
    clinical_notes: Optional[str] = None
    valid_until: Optional[date] = None
    status: PrescriptionStatus
    pharmacy_notes: Optional[str] = None
    dispensed_at: Optional[datetime] = None
    dispensed_by_user_id: Optional[int] = None
    dispensed_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[PrescriptionItemRead] = []
    latest_ai_report: Optional[AISafetyReportResponse] = None

    model_config = ConfigDict(from_attributes=True)


class PharmacyStatsResponse(BaseModel):
    """Aggregated real-time operational statistics for pharmacy workspace."""
    pending_dispensations: int = 0
    under_review_count: int = 0
    ready_for_pickup_count: int = 0
    dispensed_today: int = 0
    total_medications_dispensed: int = 0
    high_risk_alerts_count: int = 0

    model_config = ConfigDict(from_attributes=True)
