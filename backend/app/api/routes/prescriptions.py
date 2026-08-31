"""Prescription authoring, retrieval, and digital medical record endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user, require_role
from app.models.prescription import Prescription
from app.models.user import User, UserRole
from app.schemas.prescription import PrescriptionCreate, PrescriptionRead
from app.services.prescription_service import prescription_service

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])


# ---------------------------------------------------------------------------
# Doctor Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=PrescriptionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create and issue a digital prescription (Doctor)",
)
@router.post(
    "/",
    response_model=PrescriptionRead,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_prescription(
    prescription_in: PrescriptionCreate,
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> Prescription:
    """
    Author and issue a digital prescription for a completed clinical appointment.
    Enforces appointment status verification, assignment validation, and non-empty medication items.
    """
    return prescription_service.create_prescription(
        db=db,
        doctor_user=current_user,
        prescription_in=prescription_in,
    )


@router.get(
    "/doctor/my",
    response_model=List[PrescriptionRead],
    summary="List prescriptions authored by logged-in doctor",
)
def get_my_doctor_prescriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> List[Prescription]:
    """Retrieve historical digital prescriptions issued by the authenticated doctor."""
    return prescription_service.get_doctor_prescriptions(
        db=db,
        doctor_user=current_user,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Patient Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/my",
    response_model=List[PrescriptionRead],
    summary="List prescriptions issued to logged-in patient",
)
def get_my_patient_prescriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> List[Prescription]:
    """Retrieve all digital prescriptions issued to the authenticated patient."""
    return prescription_service.get_patient_prescriptions(
        db=db,
        patient_user=current_user,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Shared & Detailed Lookup Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/appointment/{appointment_id}",
    response_model=Optional[PrescriptionRead],
    summary="Retrieve prescription associated with a consultation appointment",
)
def get_prescription_by_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Optional[Prescription]:
    """Retrieve prescription issued for a specific appointment with access validation."""
    prescription = prescription_service.get_prescription_for_appointment(
        db=db,
        appointment_id=appointment_id,
        current_user=current_user,
    )
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No prescription found for appointment #{appointment_id}.",
        )
    return prescription


@router.get(
    "",
    response_model=List[PrescriptionRead],
    summary="List prescriptions for current authenticated user by active role",
)
@router.get(
    "/",
    response_model=List[PrescriptionRead],
    include_in_schema=False,
)
def get_current_user_prescriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[Prescription]:
    """Retrieve digital prescriptions for the authenticated user based on role."""
    if current_user.role == UserRole.DOCTOR:
        return prescription_service.get_doctor_prescriptions(
            db=db, doctor_user=current_user, skip=skip, limit=limit
        )
    elif current_user.role == UserRole.PATIENT:
        return prescription_service.get_patient_prescriptions(
            db=db, patient_user=current_user, skip=skip, limit=limit
        )
    elif current_user.role == UserRole.ADMIN:
        return prescription_service.get_all_prescriptions(
            db=db, skip=skip, limit=limit
        )
    return []


@router.get(
    "/{prescription_id}",
    response_model=PrescriptionRead,
    summary="Get detailed prescription record by ID",
)
def get_prescription_by_id(
    prescription_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Prescription:
    """Retrieve detailed digital prescription record by ID with RBAC security validation."""
    prescription = prescription_service.get_by_id(db=db, prescription_id=prescription_id)
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription #{prescription_id} not found.",
        )

    # RBAC security check
    if current_user.role != UserRole.ADMIN:
        is_patient_owner = prescription.patient and prescription.patient.user_id == current_user.id
        is_doctor_owner = prescription.doctor and prescription.doctor.user_id == current_user.id
        if not (is_patient_owner or is_doctor_owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this prescription record.",
            )

    return prescription
