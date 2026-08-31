"""Appointment and clinical consultation scheduling endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user, require_role
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User, UserRole
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentRead,
    AppointmentCancelRequest,
    AppointmentRejectRequest,
    AppointmentCompleteRequest,
)
from app.services.appointment_service import appointment_service

router = APIRouter(prefix="/appointments", tags=["Appointments"])


# ---------------------------------------------------------------------------
# Patient Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=AppointmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Book a new consultation appointment (Patient)",
)
@router.post(
    "/",
    response_model=AppointmentRead,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_appointment(
    appointment_in: AppointmentCreate,
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> Appointment:
    """
    Schedule a consultation slot with an approved doctor.
    Enforces doctor verification, valid future time windows, and double-booking checks.
    """
    return appointment_service.create_appointment(
        db=db,
        patient_user=current_user,
        appointment_in=appointment_in,
    )


@router.get(
    "/my",
    response_model=List[AppointmentRead],
    summary="List consultations for logged-in patient",
)
def get_my_patient_appointments(
    status_filter: Optional[AppointmentStatus] = Query(None, alias="status"),
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> List[Appointment]:
    """Retrieve all consultation bookings for the authenticated patient."""
    return appointment_service.get_patient_appointments(
        db=db,
        patient_user=current_user,
        status_filter=status_filter,
    )


@router.patch(
    "/{appointment_id}/cancel",
    response_model=AppointmentRead,
    summary="Cancel an appointment (Patient or Admin)",
)
def cancel_appointment(
    appointment_id: int,
    cancel_payload: Optional[AppointmentCancelRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Appointment:
    """
    Cancel an appointment. Allowed for the patient who booked it, the assigned doctor, or an admin.
    Allowed only if the appointment is in PENDING or CONFIRMED status.
    """
    reason = cancel_payload.cancellation_reason if cancel_payload else None
    return appointment_service.cancel_appointment(
        db=db,
        appointment_id=appointment_id,
        current_user=current_user,
        cancellation_reason=reason,
    )


# ---------------------------------------------------------------------------
# Doctor Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/doctor/my",
    response_model=List[AppointmentRead],
    summary="List consultations assigned to logged-in doctor",
)
def get_my_doctor_appointments(
    status_filter: Optional[AppointmentStatus] = Query(None, alias="status"),
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> List[Appointment]:
    """Retrieve all patient appointments scheduled with the authenticated doctor."""
    return appointment_service.get_doctor_appointments(
        db=db,
        doctor_user=current_user,
        status_filter=status_filter,
    )


@router.patch(
    "/{appointment_id}/confirm",
    response_model=AppointmentRead,
    summary="Confirm a pending appointment (Doctor)",
)
def confirm_appointment(
    appointment_id: int,
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> Appointment:
    """Accept and confirm a pending patient consultation booking."""
    return appointment_service.confirm_appointment(
        db=db,
        appointment_id=appointment_id,
        current_user=current_user,
    )


@router.patch(
    "/{appointment_id}/reject",
    response_model=AppointmentRead,
    summary="Reject a pending appointment (Doctor)",
)
def reject_appointment(
    appointment_id: int,
    reject_payload: Optional[AppointmentRejectRequest] = None,
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> Appointment:
    """Decline a pending patient appointment request with an optional reason."""
    reason = reject_payload.rejection_reason if reject_payload else None
    return appointment_service.reject_appointment(
        db=db,
        appointment_id=appointment_id,
        current_user=current_user,
        rejection_reason=reason,
    )


@router.patch(
    "/{appointment_id}/complete",
    response_model=AppointmentRead,
    summary="Mark a confirmed appointment as completed (Doctor)",
)
def complete_appointment(
    appointment_id: int,
    complete_payload: Optional[AppointmentCompleteRequest] = None,
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> Appointment:
    """Mark a confirmed consultation as completed and record clinical summary notes."""
    notes = complete_payload.doctor_notes if complete_payload else None
    return appointment_service.complete_appointment(
        db=db,
        appointment_id=appointment_id,
        current_user=current_user,
        doctor_notes=notes,
    )


# ---------------------------------------------------------------------------
# Admin Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/admin/all",
    response_model=List[AppointmentRead],
    summary="List all platform appointments (Admin oversight)",
)
def get_all_appointments_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    status_filter: Optional[AppointmentStatus] = Query(None, alias="status"),
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> List[Appointment]:
    """Administrator audit and monitoring endpoint for all appointments."""
    return appointment_service.get_all_appointments(
        db=db,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
    )


# ---------------------------------------------------------------------------
# General / Polymorphic Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=List[AppointmentRead],
    summary="List appointments for the current authenticated user by role",
)
@router.get(
    "/",
    response_model=List[AppointmentRead],
    include_in_schema=False,
)
def get_current_user_appointments(
    status_filter: Optional[AppointmentStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[Appointment]:
    """Retrieve appointments for the authenticated user based on their active role."""
    if current_user.role == UserRole.PATIENT:
        return appointment_service.get_patient_appointments(
            db=db, patient_user=current_user, status_filter=status_filter
        )
    elif current_user.role == UserRole.DOCTOR:
        return appointment_service.get_doctor_appointments(
            db=db, doctor_user=current_user, status_filter=status_filter
        )
    elif current_user.role == UserRole.ADMIN:
        return appointment_service.get_all_appointments(
            db=db, status_filter=status_filter
        )
    return []


@router.get(
    "/{appointment_id}",
    response_model=AppointmentRead,
    summary="Get appointment details by ID",
)
def get_appointment_by_id(
    appointment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Appointment:
    """Retrieve detailed consultation record by ID with access control validation."""
    appointment = appointment_service.get_by_id(db=db, appointment_id=appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment #{appointment_id} not found.",
        )

    # RBAC verification
    if current_user.role != UserRole.ADMIN:
        is_patient = appointment.patient and appointment.patient.user_id == current_user.id
        is_doctor = appointment.doctor and appointment.doctor.user_id == current_user.id
        if not (is_patient or is_doctor):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this appointment.",
            )

    return appointment
