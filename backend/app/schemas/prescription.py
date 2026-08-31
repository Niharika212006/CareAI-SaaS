"""Prescription and medication schemas for request validation and response serialization."""
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.schemas.patient import PatientProfileRead
from app.schemas.doctor import DoctorProfileRead


class PrescriptionItemBase(BaseModel):
    """Base fields for an individual prescribed medication item."""
    medication_name: Optional[str] = None
    drug_name: Optional[str] = None
    dosage: str
    frequency: str
    duration: str
    route_of_administration: Optional[str] = "Oral"
    route: Optional[str] = None
    instructions: Optional[str] = None

    @model_validator(mode="after")
    def normalize_medication_fields(self):
        # Normalize medication/drug name
        name = self.medication_name or self.drug_name
        if not name or not name.strip():
            raise ValueError("Medication name cannot be empty.")
        self.medication_name = name.strip()
        self.drug_name = self.medication_name

        # Normalize route of administration
        r = self.route_of_administration or self.route or "Oral"
        self.route_of_administration = r.strip()
        self.route = self.route_of_administration

        return self


class PrescriptionItemCreate(PrescriptionItemBase):
    """Schema for creating a medication item during prescription authoring."""
    pass


class PrescriptionItemRead(PrescriptionItemBase):
    """Schema for reading a persisted medication item."""
    id: int
    prescription_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PrescriptionBase(BaseModel):
    """Base metadata fields for a clinical prescription."""
    appointment_id: int
    patient_id: Optional[int] = None
    diagnosis: Optional[str] = None
    clinical_summary: Optional[str] = None
    clinical_notes: Optional[str] = None
    notes: Optional[str] = None
    valid_until: Optional[date] = None


class PrescriptionCreate(PrescriptionBase):
    """Schema for doctor authoring and issuing a digital prescription."""
    items: List[PrescriptionItemCreate]

    @model_validator(mode="after")
    def validate_prescription_payload(self):
        # Enforce at least one medication
        if not self.items or len(self.items) == 0:
            raise ValueError("A prescription must contain at least one medication item.")

        # Normalize diagnosis / clinical summary
        diag = self.diagnosis or self.clinical_summary
        if not diag or not diag.strip():
            raise ValueError("Diagnosis or clinical summary is required.")
        self.diagnosis = diag.strip()
        self.clinical_summary = self.diagnosis

        # Normalize notes
        n = self.clinical_notes or self.notes
        if n:
            self.clinical_notes = n.strip()
            self.notes = self.clinical_notes

        return self


class PrescriptionRead(BaseModel):
    """Schema for reading a comprehensive digital prescription with items and doctor details."""
    id: int
    appointment_id: Optional[int] = None
    patient_id: int
    doctor_id: int
    diagnosis: str
    clinical_summary: Optional[str] = None
    clinical_notes: Optional[str] = None
    notes: Optional[str] = None
    valid_until: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    items: List[PrescriptionItemRead] = []
    patient: Optional[PatientProfileRead] = None
    doctor: Optional[DoctorProfileRead] = None

    @model_validator(mode="after")
    def populate_aliases(self):
        if not self.clinical_summary and self.diagnosis:
            self.clinical_summary = self.diagnosis
        if not self.notes and self.clinical_notes:
            self.notes = self.clinical_notes
        elif not self.clinical_notes and self.notes:
            self.clinical_notes = self.notes
        return self

    model_config = ConfigDict(from_attributes=True)
