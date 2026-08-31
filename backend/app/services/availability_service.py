"""Doctor availability, schedule management, and dynamic slot generation domain service."""
from datetime import datetime, date, time, timedelta, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.availability import DoctorAvailability, DoctorUnavailableDate
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User, UserRole
from app.schemas.availability import (
    DoctorAvailabilityCreate,
    DoctorAvailabilityUpdate,
    DoctorUnavailableDateCreate,
    DoctorAvailableSlotsResponse,
)


class AvailabilityService:
    """Encapsulated business logic for doctor weekly schedules and dynamic appointment slot calculation."""

    @staticmethod
    def create_availability(
        db: Session,
        doctor_user: User,
        avail_in: DoctorAvailabilityCreate,
    ) -> DoctorAvailability:
        """Create a new weekly availability rule for the authenticated doctor."""
        doctor_profile = (
            db.query(DoctorProfile)
            .filter(DoctorProfile.user_id == doctor_user.id)
            .first()
        )
        if not doctor_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor profile not found.",
            )

        # Check for overlapping window for the same day
        existing = (
            db.query(DoctorAvailability)
            .filter(
                DoctorAvailability.doctor_id == doctor_profile.id,
                DoctorAvailability.day_of_week == avail_in.day_of_week,
                DoctorAvailability.is_active == True,
            )
            .all()
        )
        for rule in existing:
            if avail_in.start_time < rule.end_time and avail_in.end_time > rule.start_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Availability window overlaps with an existing schedule ({rule.start_time.strftime('%H:%M')} - {rule.end_time.strftime('%H:%M')}).",
                )

        availability = DoctorAvailability(
            doctor_id=doctor_profile.id,
            day_of_week=avail_in.day_of_week,
            start_time=avail_in.start_time,
            end_time=avail_in.end_time,
            slot_duration_minutes=avail_in.slot_duration_minutes,
            is_active=avail_in.is_active,
        )
        db.add(availability)
        db.commit()
        db.refresh(availability)
        return availability

    @staticmethod
    def get_my_availability(db: Session, doctor_user: User) -> List[DoctorAvailability]:
        """Retrieve all availability schedules configured by the authenticated doctor."""
        doctor_profile = (
            db.query(DoctorProfile)
            .filter(DoctorProfile.user_id == doctor_user.id)
            .first()
        )
        if not doctor_profile:
            return []

        return (
            db.query(DoctorAvailability)
            .filter(DoctorAvailability.doctor_id == doctor_profile.id)
            .order_by(DoctorAvailability.day_of_week.asc(), DoctorAvailability.start_time.asc())
            .all()
        )

    @staticmethod
    def update_availability(
        db: Session,
        availability_id: int,
        doctor_user: User,
        update_in: DoctorAvailabilityUpdate,
    ) -> DoctorAvailability:
        """Update an existing availability schedule rule with ownership enforcement."""
        availability = (
            db.query(DoctorAvailability)
            .options(joinedload(DoctorAvailability.doctor))
            .filter(DoctorAvailability.id == availability_id)
            .first()
        )
        if not availability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Availability schedule #{availability_id} not found.",
            )

        # RBAC ownership check
        if doctor_user.role != UserRole.ADMIN:
            if not availability.doctor or availability.doctor.user_id != doctor_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to modify this availability schedule.",
                )

        update_dict = update_in.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            setattr(availability, key, val)

        db.commit()
        db.refresh(availability)
        return availability

    @staticmethod
    def delete_availability(
        db: Session,
        availability_id: int,
        doctor_user: User,
    ) -> bool:
        """Remove a weekly availability schedule rule with ownership enforcement."""
        availability = (
            db.query(DoctorAvailability)
            .options(joinedload(DoctorAvailability.doctor))
            .filter(DoctorAvailability.id == availability_id)
            .first()
        )
        if not availability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Availability schedule #{availability_id} not found.",
            )

        if doctor_user.role != UserRole.ADMIN:
            if not availability.doctor or availability.doctor.user_id != doctor_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to delete this availability schedule.",
                )

        db.delete(availability)
        db.commit()
        return True

    @staticmethod
    def add_unavailable_date(
        db: Session,
        doctor_user: User,
        date_in: DoctorUnavailableDateCreate,
    ) -> DoctorUnavailableDate:
        """Mark a specific calendar date as unavailable for the authenticated doctor."""
        doctor_profile = (
            db.query(DoctorProfile)
            .filter(DoctorProfile.user_id == doctor_user.id)
            .first()
        )
        if not doctor_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor profile not found.",
            )

        existing = (
            db.query(DoctorUnavailableDate)
            .filter(
                DoctorUnavailableDate.doctor_id == doctor_profile.id,
                DoctorUnavailableDate.unavailable_date == date_in.unavailable_date,
            )
            .first()
        )
        if existing:
            existing.reason = date_in.reason
            db.commit()
            db.refresh(existing)
            return existing

        unavailable = DoctorUnavailableDate(
            doctor_id=doctor_profile.id,
            unavailable_date=date_in.unavailable_date,
            reason=date_in.reason,
        )
        db.add(unavailable)
        db.commit()
        db.refresh(unavailable)
        return unavailable

    @staticmethod
    def get_my_unavailable_dates(
        db: Session,
        doctor_user: User,
    ) -> List[DoctorUnavailableDate]:
        """Retrieve all unavailable/absence dates recorded by the authenticated doctor."""
        doctor_profile = (
            db.query(DoctorProfile)
            .filter(DoctorProfile.user_id == doctor_user.id)
            .first()
        )
        if not doctor_profile:
            return []

        return (
            db.query(DoctorUnavailableDate)
            .filter(DoctorUnavailableDate.doctor_id == doctor_profile.id)
            .order_by(DoctorUnavailableDate.unavailable_date.asc())
            .all()
        )

    @staticmethod
    def delete_unavailable_date(
        db: Session,
        unavailable_id: int,
        doctor_user: User,
    ) -> bool:
        """Remove an unavailable date entry with ownership enforcement."""
        entry = (
            db.query(DoctorUnavailableDate)
            .options(joinedload(DoctorUnavailableDate.doctor))
            .filter(DoctorUnavailableDate.id == unavailable_id)
            .first()
        )
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unavailable date entry #{unavailable_id} not found.",
            )

        if doctor_user.role != UserRole.ADMIN:
            if not entry.doctor or entry.doctor.user_id != doctor_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to delete this unavailable date entry.",
                )

        db.delete(entry)
        db.commit()
        return True

    @staticmethod
    def get_available_slots(
        db: Session,
        doctor_id: int,
        query_date: date,
    ) -> DoctorAvailableSlotsResponse:
        """
        Dynamically calculate valid, unbooked appointment time slots for a doctor on a specific date.
        Excludes:
        1. Past dates
        2. Times earlier than current time if querying today
        3. Calendar dates flagged in doctor_unavailable_dates
        4. Overlapping active (PENDING, CONFIRMED) appointments
        """
        doctor = (
            db.query(DoctorProfile)
            .filter(DoctorProfile.id == doctor_id)
            .first()
        )
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor #{doctor_id} not found.",
            )

        if doctor.approval_status != DoctorApprovalStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Consultation slots are only available for verified and approved medical practitioners.",
            )

        today = date.today()
        # If in the past, return empty slots
        if query_date < today:
            return DoctorAvailableSlotsResponse(
                doctor_id=doctor_id,
                date=query_date,
                slot_duration_minutes=30,
                available_slots=[],
            )

        # Check if doctor marked this date as unavailable (leave, holiday)
        is_unavailable_date = (
            db.query(DoctorUnavailableDate)
            .filter(
                DoctorUnavailableDate.doctor_id == doctor_id,
                DoctorUnavailableDate.unavailable_date == query_date,
            )
            .first()
        )
        if is_unavailable_date:
            return DoctorAvailableSlotsResponse(
                doctor_id=doctor_id,
                date=query_date,
                slot_duration_minutes=30,
                available_slots=[],
            )

        # Determine day of week (0 = Monday, 6 = Sunday)
        day_of_week = query_date.weekday()

        # Fetch active schedules for this day of week
        schedules = (
            db.query(DoctorAvailability)
            .filter(
                DoctorAvailability.doctor_id == doctor_id,
                DoctorAvailability.day_of_week == day_of_week,
                DoctorAvailability.is_active == True,
            )
            .order_by(DoctorAvailability.start_time.asc())
            .all()
        )

        if not schedules:
            return DoctorAvailableSlotsResponse(
                doctor_id=doctor_id,
                date=query_date,
                slot_duration_minutes=30,
                available_slots=[],
            )

        # Fetch all booked / pending appointments for this doctor on query_date
        # Define day boundaries
        day_start = datetime.combine(query_date, time.min)
        day_end = datetime.combine(query_date, time.max)

        existing_appointments = (
            db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
                Appointment.scheduled_start >= day_start,
                Appointment.scheduled_start <= day_end,
            )
            .all()
        )

        now_local = datetime.now()
        available_slots: List[str] = []
        default_duration = schedules[0].slot_duration_minutes

        for sched in schedules:
            duration = sched.slot_duration_minutes
            curr_dt = datetime.combine(query_date, sched.start_time)
            end_dt = datetime.combine(query_date, sched.end_time)

            while curr_dt + timedelta(minutes=duration) <= end_dt:
                slot_start = curr_dt
                slot_end = curr_dt + timedelta(minutes=duration)

                # If query_date is today, skip slots in the past
                if query_date == today and slot_start <= now_local:
                    curr_dt += timedelta(minutes=duration)
                    continue

                # Check if slot overlaps with any booked appointment
                is_overlap = False
                for app in existing_appointments:
                    app_start = app.scheduled_start.replace(tzinfo=None)
                    app_end = app.scheduled_end.replace(tzinfo=None)
                    if slot_start < app_end and slot_end > app_start:
                        is_overlap = True
                        break

                if not is_overlap:
                    slot_str = slot_start.strftime("%H:%M")
                    if slot_str not in available_slots:
                        available_slots.append(slot_str)

                curr_dt += timedelta(minutes=duration)

        return DoctorAvailableSlotsResponse(
            doctor_id=doctor_id,
            date=query_date,
            slot_duration_minutes=default_duration,
            available_slots=sorted(available_slots),
        )


availability_service = AvailabilityService()
