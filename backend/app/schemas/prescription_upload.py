"""Pydantic schemas for prescription and medical document upload and extraction."""
from typing import List, Optional
from pydantic import BaseModel, Field


class PrescriptionMedicationItem(BaseModel):
    """Structured medication item extracted from or confirmed on a prescription."""
    medication_name: str = Field(..., description="Name of medication / drug")
    dosage: str = Field(..., description="Dosage (e.g. 500 mg, 20 mg)")
    frequency: str = Field(..., description="Frequency (e.g. Twice daily, Once in the morning)")
    duration: str = Field(..., description="Duration (e.g. 7 days, 30 days)")
    route_of_administration: Optional[str] = Field("Oral", description="Route (e.g. Oral, Topical)")
    instructions: Optional[str] = Field(None, description="Special instructions e.g. Take after food")


class PrescriptionExtractionDraft(BaseModel):
    """Extracted prescription details returned for patient review before saving."""
    temp_file_token: str
    file_name: str
    file_size: int
    mime_type: str
    doctor_name: Optional[str] = None
    patient_name: Optional[str] = None
    date: Optional[str] = None
    diagnosis: Optional[str] = "Clinical Prescription"
    clinical_notes: Optional[str] = None
    medications: List[PrescriptionMedicationItem] = []
    confidence_score: float = 0.95
    raw_text_summary: Optional[str] = None
    disclaimer: str = (
        "CareAI extracted these details using multimodal AI. Please review and edit any values before confirming to ensure medical accuracy."
    )


class PrescriptionConfirmRequest(BaseModel):
    """Patient confirmation payload to commit extracted prescription to medical records."""
    temp_file_token: str
    file_name: str
    doctor_name: Optional[str] = None
    diagnosis: str = Field("Clinical Prescription", min_length=1)
    clinical_notes: Optional[str] = None
    medications: List[PrescriptionMedicationItem] = []


class PrescriptionConfirmResponse(BaseModel):
    """Confirmation output after prescription is successfully recorded in the database."""
    document_id: int
    prescription_id: Optional[int] = None
    message: str
    ai_explanation: str
    medication_schedule: List[str] = []
    interaction_warnings: List[str] = []
    disclaimer: str
