"""Doctor profile, credential verification, availability scheduling, and discovery endpoints."""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.models.doctor import DoctorProfile
from app.models.availability import DoctorAvailability, DoctorUnavailableDate
from app.schemas.doctor import DoctorProfileRead, DoctorProfileUpdate
from app.schemas.availability import (
    DoctorAvailabilityCreate,
    DoctorAvailabilityUpdate,
    DoctorAvailabilityRead,
    DoctorUnavailableDateCreate,
    DoctorUnavailableDateRead,
    DoctorAvailableSlotsResponse,
)
from app.services.doctor_service import doctor_service
from app.services.availability_service import availability_service

router = APIRouter(prefix="/doctors", tags=["Doctors & Availability"])


# ---------------------------------------------------------------------------
# Public Doctor Directory & Dynamic Slot Discovery
# ---------------------------------------------------------------------------

@router.get(
    "/directory",
    response_model=List[DoctorProfileRead],
    summary="Public discovery of approved doctors",
)
def get_doctors_directory(
    specialization: Optional[str] = Query(None, description="Filter by specialization"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[DoctorProfile]:
    """List approved doctors available for consultation."""
    return doctor_service.list_approved_doctors(
        db=db, specialization=specialization, skip=skip, limit=limit
    )


@router.get(
    "/{doctor_id}/available-slots",
    response_model=DoctorAvailableSlotsResponse,
    summary="Get dynamically generated available appointment slots for a doctor on a specific date",
)
def get_doctor_available_slots(
    doctor_id: int,
    query_date: date = Query(..., alias="date", description="Target consultation date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
) -> DoctorAvailableSlotsResponse:
    """
    Dynamically calculate unbooked consultation slots based on:
    - Weekly configured working hours
    - Configured slot duration
    - Exclusions for doctor leave / unavailable dates
    - Exclusions for existing active/confirmed appointments
    - Exclusions for past dates/times
    """
    return availability_service.get_available_slots(
        db=db, doctor_id=doctor_id, query_date=query_date
    )


# ---------------------------------------------------------------------------
# Doctor Profile Management
# ---------------------------------------------------------------------------

@router.get(
    "/me/profile",
    response_model=DoctorProfileRead,
    summary="Get current doctor's professional profile",
)
def get_my_doctor_profile(
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> DoctorProfile:
    """Retrieve logged-in doctor's credentials and profile."""
    profile = doctor_service.get_by_user_id(db=db, user_id=current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found.",
        )
    return profile


@router.put(
    "/me/profile",
    response_model=DoctorProfileRead,
    summary="Update current doctor's professional profile",
)
def update_my_doctor_profile(
    update_data: DoctorProfileUpdate,
    current_user: User = Depends(require_role(UserRole.DOCTOR)),
    db: Session = Depends(get_db),
) -> DoctorProfile:
    """Update doctor qualifications, bio, and fees."""
    profile = doctor_service.get_by_user_id(db=db, user_id=current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found.",
        )
    return doctor_service.update_profile(db=db, profile=profile, update_data=update_data)


# ---------------------------------------------------------------------------
# Doctor Weekly Availability Management
# ---------------------------------------------------------------------------

@router.post(
    "/availability",
    response_model=DoctorAvailabilityRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create weekly working schedule for logged-in doctor",
)
def create_doctor_availability(
    avail_in: DoctorAvailabilityCreate,
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> DoctorAvailability:
    """Add a weekly recurring availability window (e.g. Monday 09:00 - 13:00, 30 min slots)."""
    return availability_service.create_availability(
        db=db, doctor_user=current_user, avail_in=avail_in
    )


@router.get(
    "/availability/my",
    response_model=List[DoctorAvailabilityRead],
    summary="Get logged-in doctor's configured availability schedules",
)
def get_my_doctor_availability(
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> List[DoctorAvailability]:
    """Retrieve full weekly schedule configured by the authenticated physician."""
    return availability_service.get_my_availability(db=db, doctor_user=current_user)


@router.put(
    "/availability/{availability_id}",
    response_model=DoctorAvailabilityRead,
    summary="Update an existing availability schedule rule",
)
def update_doctor_availability(
    availability_id: int,
    update_in: DoctorAvailabilityUpdate,
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> DoctorAvailability:
    """Modify working hours, day of week, slot duration, or active toggle for a schedule rule."""
    return availability_service.update_availability(
        db=db,
        availability_id=availability_id,
        doctor_user=current_user,
        update_in=update_in,
    )


@router.delete(
    "/availability/{availability_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an availability schedule rule",
)
def delete_doctor_availability(
    availability_id: int,
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Remove a day availability window from the doctor's weekly calendar."""
    availability_service.delete_availability(
        db=db, availability_id=availability_id, doctor_user=current_user
    )
    return None


# ---------------------------------------------------------------------------
# Doctor Unavailable Dates (Time-off & Holidays)
# ---------------------------------------------------------------------------

@router.post(
    "/unavailable-dates",
    response_model=DoctorUnavailableDateRead,
    status_code=status.HTTP_201_CREATED,
    summary="Mark a specific calendar date as unavailable (leave / holiday)",
)
def add_doctor_unavailable_date(
    date_in: DoctorUnavailableDateCreate,
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> DoctorUnavailableDate:
    """Block a specific calendar date from patient appointment booking."""
    return availability_service.add_unavailable_date(
        db=db, doctor_user=current_user, date_in=date_in
    )


@router.get(
    "/unavailable-dates/my",
    response_model=List[DoctorUnavailableDateRead],
    summary="Get logged-in doctor's recorded unavailable dates",
)
def get_my_doctor_unavailable_dates(
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> List[DoctorUnavailableDate]:
    """Retrieve all upcoming leave and unavailable dates configured by the doctor."""
    return availability_service.get_my_unavailable_dates(db=db, doctor_user=current_user)


@router.delete(
    "/unavailable-dates/{unavailable_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an unavailable date entry",
)
def delete_doctor_unavailable_date(
    unavailable_id: int,
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Unblock a calendar date to resume normal weekly schedule."""
    availability_service.delete_unavailable_date(
        db=db, unavailable_id=unavailable_id, doctor_user=current_user
    )
    return None
