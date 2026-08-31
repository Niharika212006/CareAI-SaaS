"""Patient profile entity definition."""
import json
from typing import List, Optional, Any, Dict
from sqlalchemy import Column, String, Date, Text, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.base import TimeStampedModel


class PatientProfile(Base, TimeStampedModel):
    """Patient medical, lifestyle, and demographic profile."""
    __tablename__ = "patient_profiles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Personal & Demographic
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    blood_group = Column(String(10), nullable=True)

    # Structured Allergies: List[Dict] e.g. [{"name": "Penicillin", "type": "MEDICATION", "severity": "HIGH", "reaction": "Rash"}]
    allergies = Column(JSON, nullable=True, doc="Structured list or legacy string of patient allergies")

    # Medical History: List[str]
    chronic_conditions = Column(JSON, nullable=True, doc="List of active chronic conditions")
    past_conditions = Column(JSON, nullable=True, doc="List of resolved past illnesses")
    surgeries = Column(JSON, nullable=True, doc="List of past surgical procedures")

    # Current Health & Medications
    current_medications = Column(JSON, nullable=True, doc="List of active daily medications")
    smoking_status = Column(String(30), nullable=True, doc="NEVER, FORMER, OCCASIONAL, CURRENT")
    alcohol_consumption = Column(String(30), nullable=True, doc="NONE, OCCASIONAL, MODERATE, HEAVY")

    # Emergency Contact Details
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(30), nullable=True)
    emergency_contact_relationship = Column(String(50), nullable=True)
    emergency_contact = Column(String(100), nullable=True, doc="Legacy contact string")

    # Summary
    medical_history_summary = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="patient_profile")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="patient", cascade="all, delete-orphan")
    documents = relationship("MedicalDocument", back_populates="patient", cascade="all, delete-orphan", order_by="desc(MedicalDocument.created_at)")

    def get_allergy_names(self) -> List[str]:
        """Extract plain allergy names regardless of whether data is JSON list, dict, or comma-separated string."""
        if not self.allergies:
            return []
        
        if isinstance(self.allergies, list):
            names = []
            for item in self.allergies:
                if isinstance(item, dict) and "name" in item and item["name"]:
                    names.append(str(item["name"]).strip())
                elif isinstance(item, str) and item.strip():
                    names.append(item.strip())
            return names
        
        if isinstance(self.allergies, dict):
            return [str(v) for v in self.allergies.values() if v]
            
        if isinstance(self.allergies, str):
            # Check if JSON encoded string
            try:
                parsed = json.loads(self.allergies)
                if isinstance(parsed, list):
                    return [
                        item["name"].strip() if isinstance(item, dict) and "name" in item else str(item).strip()
                        for item in parsed if item
                    ]
            except Exception:
                pass
            return [a.strip() for a in self.allergies.replace(";", ",").split(",") if a.strip()]
            
        return []

    def get_condition_names(self) -> List[str]:
        """Extract chronic condition names."""
        if not self.chronic_conditions:
            return []
        if isinstance(self.chronic_conditions, list):
            return [str(c).strip() for c in self.chronic_conditions if str(c).strip()]
        if isinstance(self.chronic_conditions, str):
            try:
                parsed = json.loads(self.chronic_conditions)
                if isinstance(parsed, list):
                    return [str(c).strip() for c in parsed if str(c).strip()]
            except Exception:
                pass
            return [c.strip() for c in self.chronic_conditions.split(",") if c.strip()]
        return []

    def get_current_medication_names(self) -> List[str]:
        """Extract medication names from current medications list."""
        if not self.current_medications:
            return []
        if isinstance(self.current_medications, list):
            meds = []
            for item in self.current_medications:
                if isinstance(item, dict) and "name" in item and item["name"]:
                    meds.append(str(item["name"]).strip())
                elif isinstance(item, str) and item.strip():
                    meds.append(item.strip())
            return meds
        if isinstance(self.current_medications, str):
            try:
                parsed = json.loads(self.current_medications)
                if isinstance(parsed, list):
                    return [
                        item["name"].strip() if isinstance(item, dict) and "name" in item else str(item).strip()
                        for item in parsed if item
                    ]
            except Exception:
                pass
            return [m.strip() for m in self.current_medications.split(",") if m.strip()]
        return []

    def __repr__(self) -> str:
        return f"<PatientProfile(id={self.id}, user_id={self.user_id}, blood_group='{self.blood_group}')>"
