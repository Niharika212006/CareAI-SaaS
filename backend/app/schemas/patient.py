"""Patient profile and medical history schemas."""
from datetime import date, datetime
from typing import Optional, List, Union, Any, Dict
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.user import UserRead


class AllergyItem(BaseModel):
    """Structured clinical allergy record."""
    name: str = Field(..., min_length=1, description="Medication, food, or environmental allergen name")
    type: Optional[str] = Field("MEDICATION", description="MEDICATION, FOOD, ENVIRONMENTAL, OTHER")
    severity: Optional[str] = Field("MODERATE", description="CRITICAL, HIGH, MODERATE, LOW")
    reaction: Optional[str] = Field(None, description="Observed reaction e.g. Anaphylaxis, Rash, Urticaria")

    model_config = ConfigDict(from_attributes=True)


class CurrentMedicationItem(BaseModel):
    """Structured current active medication record."""
    name: str = Field(..., min_length=1, description="Medication or supplement name")
    dosage: Optional[str] = Field(None, description="Dosage e.g. 500 mg, 10 ml")
    frequency: Optional[str] = Field(None, description="Schedule e.g. Once daily, PRN")
    instructions: Optional[str] = Field(None, description="Instructions e.g. Take with breakfast")

    model_config = ConfigDict(from_attributes=True)


class EmergencyContactInfo(BaseModel):
    """Emergency contact demographic information."""
    name: Optional[str] = None
    phone: Optional[str] = None
    relationship: Optional[str] = None


class PatientProfileBase(BaseModel):
    """Base fields for patient profile."""
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact: Optional[str] = None
    allergies: Optional[Any] = None
    chronic_conditions: Optional[Any] = None
    medical_history_summary: Optional[str] = None


class PatientProfileCreate(PatientProfileBase):
    """Schema for creating a patient profile."""
    pass


class PatientProfileUpdate(BaseModel):
    """Schema for updating general patient profile."""
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    allergies: Optional[Any] = None
    chronic_conditions: Optional[Any] = None
    past_conditions: Optional[Any] = None
    surgeries: Optional[Any] = None
    current_medications: Optional[Any] = None
    smoking_status: Optional[str] = None
    alcohol_consumption: Optional[str] = None
    medical_history_summary: Optional[str] = None


class PatientMedicalProfileUpdate(BaseModel):
    """Schema for updating full patient medical profile."""
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    allergies: Optional[List[Union[AllergyItem, Dict[str, Any], str]]] = None
    chronic_conditions: Optional[List[str]] = None
    past_conditions: Optional[List[str]] = None
    surgeries: Optional[List[str]] = None
    current_medications: Optional[List[Union[CurrentMedicationItem, Dict[str, Any], str]]] = None
    smoking_status: Optional[str] = None
    alcohol_consumption: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    emergency_contact: Optional[str] = None
    medical_history_summary: Optional[str] = None


class PatientMedicalProfileRead(BaseModel):
    """Complete patient medical profile schema for patient view."""
    id: int
    user_id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    allergies: List[AllergyItem] = []
    chronic_conditions: List[str] = []
    past_conditions: List[str] = []
    surgeries: List[str] = []
    current_medications: List[CurrentMedicationItem] = []
    smoking_status: Optional[str] = None
    alcohol_consumption: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    emergency_contact: Optional[str] = None
    medical_history_summary: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DoctorPatientMedicalSummary(BaseModel):
    """Authorized clinical medical summary accessible to treating physicians."""
    patient_id: int
    full_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    allergies: List[AllergyItem] = []
    chronic_conditions: List[str] = []
    past_conditions: List[str] = []
    surgeries: List[str] = []
    current_medications: List[CurrentMedicationItem] = []
    smoking_status: Optional[str] = None
    alcohol_consumption: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    medical_history_summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PatientProfileRead(PatientProfileBase):
    """Legacy/general schema for reading patient profile."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    user: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)
