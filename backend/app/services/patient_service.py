"""Patient profile and medical history service."""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone
import json
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile
from app.models.appointment import Appointment
from app.models.user import User, UserRole
from app.schemas.patient import (
    PatientProfileUpdate,
    PatientMedicalProfileUpdate,
    PatientMedicalProfileRead,
    DoctorPatientMedicalSummary,
    AllergyItem,
    CurrentMedicationItem,
)


class PatientService:
    """Business logic for patient profile management, authorization, and clinical summaries."""

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Optional[PatientProfile]:
        """Fetch patient profile for a user."""
        return (
            db.query(PatientProfile)
            .options(joinedload(PatientProfile.user))
            .filter(PatientProfile.user_id == user_id)
            .first()
        )

    @staticmethod
    def get_by_id(db: Session, profile_id: int) -> Optional[PatientProfile]:
        """Fetch patient profile by profile ID."""
        return (
            db.query(PatientProfile)
            .options(joinedload(PatientProfile.user))
            .filter(PatientProfile.id == profile_id)
            .first()
        )

    @staticmethod
    def get_or_create_patient_profile(db: Session, user_id: int) -> PatientProfile:
        """Fetch existing patient profile or create empty profile if missing."""
        profile = PatientService.get_by_user_id(db=db, user_id=user_id)
        if not profile:
            profile = PatientProfile(
                user_id=user_id,
                allergies=[],
                chronic_conditions=[],
                past_conditions=[],
                surgeries=[],
                current_medications=[],
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile

    @staticmethod
    def update_profile(
        db: Session, profile: PatientProfile, update_data: Union[PatientProfileUpdate, PatientMedicalProfileUpdate]
    ) -> PatientProfile:
        """Update patient medical details."""
        update_dict = update_data.model_dump(exclude_unset=True)

        # Normalize structured allergies if provided
        if "allergies" in update_dict and update_dict["allergies"] is not None:
            update_dict["allergies"] = PatientService._normalize_allergies(update_dict["allergies"])

        # Normalize current medications if provided
        if "current_medications" in update_dict and update_dict["current_medications"] is not None:
            update_dict["current_medications"] = PatientService._normalize_medications(update_dict["current_medications"])

        # Sync emergency contact string if component names are supplied
        if "emergency_contact_name" in update_dict or "emergency_contact_phone" in update_dict:
            name = update_dict.get("emergency_contact_name") or profile.emergency_contact_name or ""
            phone = update_dict.get("emergency_contact_phone") or profile.emergency_contact_phone or ""
            rel = update_dict.get("emergency_contact_relationship") or profile.emergency_contact_relationship or ""
            if name or phone:
                contact_str = f"{name} ({rel}): {phone}".replace(" ():", "").replace(" :", "")
                profile.emergency_contact = contact_str.strip()

        for key, value in update_dict.items():
            setattr(profile, key, value)

        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def serialize_medical_profile(profile: PatientProfile) -> PatientMedicalProfileRead:
        """Convert PatientProfile ORM to structured PatientMedicalProfileRead response."""
        allergies_list = [AllergyItem(**a) for a in PatientService._normalize_allergies(profile.allergies)]
        meds_list = [CurrentMedicationItem(**m) for m in PatientService._normalize_medications(profile.current_medications)]

        chronic = PatientService._normalize_string_list(profile.chronic_conditions)
        past = PatientService._normalize_string_list(profile.past_conditions)
        surgeries = PatientService._normalize_string_list(profile.surgeries)

        user_name = profile.user.full_name if profile.user else None
        user_email = profile.user.email if profile.user else None

        return PatientMedicalProfileRead(
            id=profile.id,
            user_id=profile.user_id,
            full_name=user_name,
            email=user_email,
            date_of_birth=profile.date_of_birth,
            gender=profile.gender,
            blood_group=profile.blood_group,
            allergies=allergies_list,
            chronic_conditions=chronic,
            past_conditions=past,
            surgeries=surgeries,
            current_medications=meds_list,
            smoking_status=profile.smoking_status,
            alcohol_consumption=profile.alcohol_consumption,
            emergency_contact_name=profile.emergency_contact_name,
            emergency_contact_phone=profile.emergency_contact_phone,
            emergency_contact_relationship=profile.emergency_contact_relationship,
            emergency_contact=profile.emergency_contact,
            medical_history_summary=profile.medical_history_summary,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    @staticmethod
    def verify_doctor_patient_relationship(db: Session, doctor_user_id: int, patient_id: int) -> bool:
        """
        Verify whether an active or completed clinical appointment relationship exists
        between a doctor and a specific patient.
        """
        doctor_profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_user_id).first()
        if not doctor_profile:
            return False

        exists = (
            db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_profile.id,
                Appointment.patient_id == patient_id,
            )
            .first()
        )
        return exists is not None

    @staticmethod
    def get_doctor_patient_summary(
        db: Session, doctor_user: User, patient_id: int
    ) -> DoctorPatientMedicalSummary:
        """
        Retrieve patient medical summary with strict RBAC:
        Ensures doctor has a legitimate clinical appointment relationship with the patient.
        """
        if doctor_user.role != UserRole.ADMIN:
            if doctor_user.role != UserRole.DOCTOR:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only verified medical practitioners can access clinical patient summaries.",
                )

            is_authorized = PatientService.verify_doctor_patient_relationship(
                db=db, doctor_user_id=doctor_user.id, patient_id=patient_id
            )
            if not is_authorized:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. You do not have an active or scheduled consultation relationship with this patient.",
                )

        profile = PatientService.get_by_id(db=db, profile_id=patient_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient record #{patient_id} not found.",
            )

        allergies_list = [AllergyItem(**a) for a in PatientService._normalize_allergies(profile.allergies)]
        meds_list = [CurrentMedicationItem(**m) for m in PatientService._normalize_medications(profile.current_medications)]

        return DoctorPatientMedicalSummary(
            patient_id=profile.id,
            full_name=profile.user.full_name if profile.user else f"Patient #{profile.id}",
            date_of_birth=profile.date_of_birth,
            gender=profile.gender,
            blood_group=profile.blood_group,
            allergies=allergies_list,
            chronic_conditions=PatientService._normalize_string_list(profile.chronic_conditions),
            past_conditions=PatientService._normalize_string_list(profile.past_conditions),
            surgeries=PatientService._normalize_string_list(profile.surgeries),
            current_medications=meds_list,
            smoking_status=profile.smoking_status,
            alcohol_consumption=profile.alcohol_consumption,
            emergency_contact=profile.emergency_contact,
            emergency_contact_phone=profile.emergency_contact_phone,
            medical_history_summary=profile.medical_history_summary,
        )

    # -----------------------------------------------------------------------
    # Helper Data Normalizers
    # -----------------------------------------------------------------------
    @staticmethod
    def _normalize_allergies(raw: Any) -> List[Dict[str, Any]]:
        """Ensure allergies is always returned as a list of dicts {name, type, severity, reaction}."""
        if not raw:
            return []
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return PatientService._normalize_allergies(parsed)
            except Exception:
                pass
            items = [a.strip() for a in raw.replace(";", ",").split(",") if a.strip()]
            return [{"name": item, "type": "MEDICATION", "severity": "MODERATE", "reaction": None} for item in items]

        if isinstance(raw, list):
            result = []
            for item in raw:
                if isinstance(item, dict):
                    name = item.get("name", "").strip()
                    if name:
                        result.append({
                            "name": name,
                            "type": item.get("type", "MEDICATION"),
                            "severity": item.get("severity", "MODERATE"),
                            "reaction": item.get("reaction"),
                        })
                elif isinstance(item, str) and item.strip():
                    result.append({
                        "name": item.strip(),
                        "type": "MEDICATION",
                        "severity": "MODERATE",
                        "reaction": None,
                    })
                elif hasattr(item, "model_dump"):
                    dumped = item.model_dump()
                    if dumped.get("name"):
                        result.append(dumped)
            return result
        return []

    @staticmethod
    def _normalize_medications(raw: Any) -> List[Dict[str, Any]]:
        """Ensure current medications is returned as a list of dicts {name, dosage, frequency, instructions}."""
        if not raw:
            return []
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return PatientService._normalize_medications(parsed)
            except Exception:
                pass
            items = [m.strip() for m in raw.split(",") if m.strip()]
            return [{"name": m, "dosage": None, "frequency": None, "instructions": None} for m in items]

        if isinstance(raw, list):
            result = []
            for item in raw:
                if isinstance(item, dict):
                    name = item.get("name", "").strip()
                    if name:
                        result.append({
                            "name": name,
                            "dosage": item.get("dosage"),
                            "frequency": item.get("frequency"),
                            "instructions": item.get("instructions"),
                        })
                elif isinstance(item, str) and item.strip():
                    result.append({
                        "name": item.strip(),
                        "dosage": None,
                        "frequency": None,
                        "instructions": None,
                    })
                elif hasattr(item, "model_dump"):
                    dumped = item.model_dump()
                    if dumped.get("name"):
                        result.append(dumped)
            return result
        return []

    @staticmethod
    def _normalize_string_list(raw: Any) -> List[str]:
        """Convert comma strings or JSON lists to a list of strings."""
        if not raw:
            return []
        if isinstance(raw, list):
            return [str(item).strip() for item in raw if str(item).strip()]
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except Exception:
                pass
            return [s.strip() for s in raw.split(",") if s.strip()]
        return []


patient_service = PatientService()
