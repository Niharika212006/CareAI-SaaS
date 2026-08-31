"""Patient medical profile, clinical history, and physician summary endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.schemas.patient import (
    PatientProfileRead,
    PatientProfileUpdate,
    PatientMedicalProfileRead,
    PatientMedicalProfileUpdate,
    DoctorPatientMedicalSummary,
)
from app.services.patient_service import patient_service

router = APIRouter(prefix="/patients", tags=["Patient Medical Profiles & History"])


@router.get(
    "/medical-profile",
    response_model=PatientMedicalProfileRead,
    summary="Get current patient's comprehensive medical profile",
)
def get_my_medical_profile(
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> PatientMedicalProfileRead:
    """Retrieve full structured medical profile including allergies, medical conditions, medications, and lifestyle."""
    profile = patient_service.get_or_create_patient_profile(db=db, user_id=current_user.id)
    return patient_service.serialize_medical_profile(profile)


@router.put(
    "/medical-profile",
    response_model=PatientMedicalProfileRead,
    summary="Create or replace current patient's medical profile",
)
def update_my_medical_profile(
    update_data: PatientMedicalProfileUpdate,
    current_user: User = Depends(require_role(UserRole.PATIENT)),
    db: Session = Depends(get_db),
) -> PatientMedicalProfileRead:
    """Full update of patient medical profile, allergies list, chronic illnesses, and emergency contact details."""
    profile = patient_service.get_or_create_patient_profile(db=db, user_id=current_user.id)
    updated_profile = patient_service.update_profile(db=db, profile=profile, update_data=update_data)
    return patient_service.serialize_medical_profile(updated_profile)


@router.patch(
    "/medical-profile",
    response_model=PatientMedicalProfileRead,
    summary="Partially update current patient's medical profile",
)
def patch_my_medical_profile(
    update_data: PatientMedicalProfileUpdate,
    current_user: User = Depends(require_role(UserRole.PATIENT)),
    db: Session = Depends(get_db),
) -> PatientMedicalProfileRead:
    """Partial update of specified patient medical profile fields."""
    profile = patient_service.get_or_create_patient_profile(db=db, user_id=current_user.id)
    updated_profile = patient_service.update_profile(db=db, profile=profile, update_data=update_data)
    return patient_service.serialize_medical_profile(updated_profile)


@router.get(
    "/me/profile",
    response_model=PatientProfileRead,
    summary="Get current patient's profile (compatible endpoint)",
)
def get_my_patient_profile(
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> PatientProfile:
    """Retrieve logged-in patient demographic and medical profile."""
    return patient_service.get_or_create_patient_profile(db=db, user_id=current_user.id)


@router.put(
    "/me/profile",
    response_model=PatientProfileRead,
    summary="Update current patient's profile (compatible endpoint)",
)
def update_my_patient_profile(
    update_data: PatientProfileUpdate,
    current_user: User = Depends(require_role(UserRole.PATIENT)),
    db: Session = Depends(get_db),
) -> PatientProfile:
    """Update patient demographic and medical details."""
    profile = patient_service.get_or_create_patient_profile(db=db, user_id=current_user.id)
    return patient_service.update_profile(db=db, profile=profile, update_data=update_data)


@router.get(
    "/{patient_id}/medical-summary",
    response_model=DoctorPatientMedicalSummary,
    summary="Doctor access to patient clinical medical summary",
)
def get_patient_medical_summary_for_doctor(
    patient_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DoctorPatientMedicalSummary:
    """
    Access patient medical summary with strict relationship enforcement:
    Only treating physicians with a scheduled, active, or past appointment with this patient (or Admins) are authorized.
    """
    return patient_service.get_doctor_patient_summary(
        db=db, doctor_user=current_user, patient_id=patient_id
    )
