"""Appointment management domain service."""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.user import User, UserRole
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate


class AppointmentService:
    """Encapsulated business logic for clinical consultations and appointments."""

    @staticmethod
    def get_by_id(db: Session, appointment_id: int) -> Optional[Appointment]:
        """Retrieve an appointment by primary ID with eager loaded relationships."""
        return (
            db.query(Appointment)
            .options(
                joinedload(Appointment.patient).joinedload(PatientProfile.user),
                joinedload(Appointment.doctor).joinedload(DoctorProfile.user),
            )
            .filter(Appointment.id == appointment_id)
            .first()
        )

    @staticmethod
    def create_appointment(
        db: Session,
        patient_user: User,
        appointment_in: AppointmentCreate,
    ) -> Appointment:
        """
        Create a new consultation appointment requested by an authenticated patient.
        Enforces:
        1. Patient profile availability
        2. Doctor existence and administrative verification approval
        3. Prevention of scheduling in the past
        4. Prevention of double-booking overlapping time slots
        """
        # Ensure patient profile exists
        patient_profile = (
            db.query(PatientProfile)
            .filter(PatientProfile.user_id == patient_user.id)
            .first()
        )
        if not patient_profile:
            patient_profile = PatientProfile(user_id=patient_user.id)
            db.add(patient_profile)
            db.flush()

        # Validate doctor profile
        doctor_profile = (
            db.query(DoctorProfile)
            .filter(DoctorProfile.id == appointment_in.doctor_id)
            .first()
        )
        if not doctor_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor profile with ID {appointment_in.doctor_id} not found.",
            )

        if doctor_profile.approval_status != DoctorApprovalStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot book an appointment with a doctor whose credentials have not been approved by an administrator.",
            )

        start_time = appointment_in.scheduled_start
        end_time = appointment_in.scheduled_end

        # Check for scheduling in the past
        now_utc = datetime.now(timezone.utc)
        start_compare = (
            start_time.replace(tzinfo=timezone.utc)
            if start_time.tzinfo is None
            else start_time
        )
        if start_compare < now_utc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot schedule an appointment in the past.",
            )

        # Check if doctor marked this date as unavailable (leave, holiday)
        from app.models.availability import DoctorAvailability, DoctorUnavailableDate
        appt_date = start_time.date()
        is_unavailable_date = (
            db.query(DoctorUnavailableDate)
            .filter(
                DoctorUnavailableDate.doctor_id == doctor_profile.id,
                DoctorUnavailableDate.unavailable_date == appt_date,
            )
            .first()
        )
        if is_unavailable_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The doctor is unavailable on this date ({is_unavailable_date.reason or 'Scheduled leave'}). Please choose another date.",
            )

        # Check if requested time falls within active weekly availability schedule (if configured)
        day_of_week = appt_date.weekday()
        schedules = (
            db.query(DoctorAvailability)
            .filter(
                DoctorAvailability.doctor_id == doctor_profile.id,
                DoctorAvailability.day_of_week == day_of_week,
                DoctorAvailability.is_active == True,
            )
            .all()
        )
        if schedules:
            appt_time = start_time.time()
            appt_end_time = end_time.time()
            within_schedule = any(
                sched.start_time <= appt_time and sched.end_time >= appt_end_time
                for sched in schedules
            )
            if not within_schedule:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Requested appointment time falls outside the doctor's scheduled availability hours for this day.",
                )

        # Prevent double-booking for the doctor
        # Check active appointments (PENDING or CONFIRMED) that overlap
        overlap = (
            db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_profile.id,
                Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
                Appointment.scheduled_start < end_time,
                Appointment.scheduled_end > start_time,
            )
            .first()
        )
        if overlap:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The doctor already has a scheduled or pending appointment during this time window. Please select another time slot.",
            )

        # Create appointment record
        appointment = Appointment(
            patient_id=patient_profile.id,
            doctor_id=doctor_profile.id,
            scheduled_start=start_time,
            scheduled_end=end_time,
            status=AppointmentStatus.PENDING,
            reason_for_visit=appointment_in.reason_for_visit or appointment_in.reason,
            reason=appointment_in.reason or appointment_in.reason_for_visit,
            patient_notes=appointment_in.patient_notes,
        )

        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        # In-App Notifications
        from app.services.notification_service import notification_service
        from app.models.notification import NotificationType, NotificationPriority

        doc_name = doctor_profile.user.full_name if doctor_profile.user else "Practitioner"
        formatted_time = appointment.scheduled_start.strftime("%b %d, %Y at %H:%M")

        # Notify Patient
        notification_service.create_notification(
            db=db,
            user_id=patient_user.id,
            title="Appointment Requested",
            message=f"Your consultation request with Dr. {doc_name} has been submitted for {formatted_time}.",
            notification_type=NotificationType.APPOINTMENT,
            priority=NotificationPriority.NORMAL,
            metadata_json={"appointment_id": appointment.id},
        )

        # Notify Doctor
        if doctor_profile.user_id:
            notification_service.create_notification(
                db=db,
                user_id=doctor_profile.user_id,
                title="New Appointment Request",
                message=f"Patient {patient_user.full_name} requested a consultation for {formatted_time}.",
                notification_type=NotificationType.APPOINTMENT,
                priority=NotificationPriority.NORMAL,
                metadata_json={"appointment_id": appointment.id},
            )

        return AppointmentService.get_by_id(db=db, appointment_id=appointment.id)

    @staticmethod
    def get_patient_appointments(
        db: Session,
        patient_user: User,
        status_filter: Optional[AppointmentStatus] = None,
    ) -> List[Appointment]:
        """Retrieve all appointments booked by the authenticated patient."""
        patient_profile = (
            db.query(PatientProfile)
            .filter(PatientProfile.user_id == patient_user.id)
            .first()
        )
        if not patient_profile:
            return []

        query = (
            db.query(Appointment)
            .options(
                joinedload(Appointment.patient).joinedload(PatientProfile.user),
                joinedload(Appointment.doctor).joinedload(DoctorProfile.user),
            )
            .filter(Appointment.patient_id == patient_profile.id)
        )

        if status_filter:
            query = query.filter(Appointment.status == status_filter)

        return query.order_by(Appointment.scheduled_start.desc()).all()

    @staticmethod
    def get_doctor_appointments(
        db: Session,
        doctor_user: User,
        status_filter: Optional[AppointmentStatus] = None,
    ) -> List[Appointment]:
        """Retrieve all appointments assigned to the authenticated doctor."""
        doctor_profile = (
            db.query(DoctorProfile)
            .filter(DoctorProfile.user_id == doctor_user.id)
            .first()
        )
        if not doctor_profile:
            return []

        query = (
            db.query(Appointment)
            .options(
                joinedload(Appointment.patient).joinedload(PatientProfile.user),
                joinedload(Appointment.doctor).joinedload(DoctorProfile.user),
            )
            .filter(Appointment.doctor_id == doctor_profile.id)
        )

        if status_filter:
            query = query.filter(Appointment.status == status_filter)

        return query.order_by(Appointment.scheduled_start.desc()).all()

    @staticmethod
    def get_all_appointments(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[AppointmentStatus] = None,
    ) -> List[Appointment]:
        """Admin query to retrieve and monitor all platform consultations."""
        query = (
            db.query(Appointment)
            .options(
                joinedload(Appointment.patient).joinedload(PatientProfile.user),
                joinedload(Appointment.doctor).joinedload(DoctorProfile.user),
            )
        )

        if status_filter:
            query = query.filter(Appointment.status == status_filter)

        return query.order_by(Appointment.scheduled_start.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def cancel_appointment(
        db: Session,
        appointment_id: int,
        current_user: User,
        cancellation_reason: Optional[str] = None,
    ) -> Appointment:
        """
        Cancel an appointment.
        Allowed for the patient who booked the appointment or a platform administrator.
        Allowed only if appointment status is PENDING or CONFIRMED.
        """
        appointment = AppointmentService.get_by_id(db=db, appointment_id=appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment #{appointment_id} not found.",
            )

        # Authorization check
        if current_user.role != UserRole.ADMIN:
            patient_profile = (
                db.query(PatientProfile)
                .filter(PatientProfile.user_id == current_user.id)
                .first()
            )
            doctor_profile = (
                db.query(DoctorProfile)
                .filter(DoctorProfile.user_id == current_user.id)
                .first()
            )
            is_patient_owner = patient_profile and appointment.patient_id == patient_profile.id
            is_doctor_owner = doctor_profile and appointment.doctor_id == doctor_profile.id

            if not (is_patient_owner or is_doctor_owner):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to cancel this appointment.",
                )

        # Status transition check
        if appointment.status in [
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.REJECTED,
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel an appointment that is already {appointment.status.value.lower()}.",
            )

        appointment.status = AppointmentStatus.CANCELLED
        if cancellation_reason:
            appointment.cancellation_reason = cancellation_reason

        db.commit()
        db.refresh(appointment)

        # Notify Parties of Cancellation
        from app.services.notification_service import notification_service
        from app.models.notification import NotificationType, NotificationPriority

        formatted_time = appointment.scheduled_start.strftime("%b %d, %Y at %H:%M")
        doc_user_id = appointment.doctor.user_id if appointment.doctor else None
        pat_user_id = appointment.patient.user_id if appointment.patient else None

        if pat_user_id:
            notification_service.create_notification(
                db=db,
                user_id=pat_user_id,
                title="Appointment Cancelled",
                message=f"Your appointment scheduled for {formatted_time} was cancelled.",
                notification_type=NotificationType.APPOINTMENT,
                priority=NotificationPriority.NORMAL,
                metadata_json={"appointment_id": appointment.id},
            )
        if doc_user_id:
            notification_service.create_notification(
                db=db,
                user_id=doc_user_id,
                title="Appointment Cancelled",
                message=f"The appointment scheduled for {formatted_time} was cancelled.",
                notification_type=NotificationType.APPOINTMENT,
                priority=NotificationPriority.NORMAL,
                metadata_json={"appointment_id": appointment.id},
            )

        return appointment

    @staticmethod
    def confirm_appointment(
        db: Session,
        appointment_id: int,
        current_user: User,
    ) -> Appointment:
        """
        Confirm a pending appointment.
        Allowed for the assigned doctor or administrator.
        Allowed only if appointment status is PENDING.
        """
        appointment = AppointmentService.get_by_id(db=db, appointment_id=appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment #{appointment_id} not found.",
            )

        # Authorization check
        if current_user.role != UserRole.ADMIN:
            doctor_profile = (
                db.query(DoctorProfile)
                .filter(DoctorProfile.user_id == current_user.id)
                .first()
            )
            if not doctor_profile or appointment.doctor_id != doctor_profile.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to confirm this appointment.",
                )

        # Status transition check
        if appointment.status != AppointmentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot confirm appointment with status '{appointment.status.value}'. Only PENDING appointments can be confirmed.",
            )

        appointment.status = AppointmentStatus.CONFIRMED
        db.commit()
        db.refresh(appointment)

        # Notify Patient of Confirmation
        from app.services.notification_service import notification_service
        from app.models.notification import NotificationType, NotificationPriority

        if appointment.patient and appointment.patient.user_id:
            doc_name = appointment.doctor.user.full_name if (appointment.doctor and appointment.doctor.user) else "your doctor"
            formatted_time = appointment.scheduled_start.strftime("%b %d, %Y at %H:%M")
            notification_service.create_notification(
                db=db,
                user_id=appointment.patient.user_id,
                title="Appointment Confirmed",
                message=f"Your consultation with Dr. {doc_name} on {formatted_time} has been confirmed.",
                notification_type=NotificationType.APPOINTMENT,
                priority=NotificationPriority.HIGH,
                metadata_json={"appointment_id": appointment.id},
            )

        return appointment

    @staticmethod
    def reject_appointment(
        db: Session,
        appointment_id: int,
        current_user: User,
        rejection_reason: Optional[str] = None,
    ) -> Appointment:
        """
        Reject a pending consultation request with an optional justification.
        Allowed for the assigned doctor or administrator.
        Allowed only if appointment status is PENDING.
        """
        appointment = AppointmentService.get_by_id(db=db, appointment_id=appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment #{appointment_id} not found.",
            )

        # Authorization check
        if current_user.role != UserRole.ADMIN:
            doctor_profile = (
                db.query(DoctorProfile)
                .filter(DoctorProfile.user_id == current_user.id)
                .first()
            )
            if not doctor_profile or appointment.doctor_id != doctor_profile.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to reject this appointment.",
                )

        # Status transition check
        if appointment.status != AppointmentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject appointment with status '{appointment.status.value}'. Only PENDING appointments can be rejected.",
            )

        appointment.status = AppointmentStatus.REJECTED
        if rejection_reason:
            appointment.rejection_reason = rejection_reason

        db.commit()
        db.refresh(appointment)

        # Notify Patient of Declined Consultation
        from app.services.notification_service import notification_service
        from app.models.notification import NotificationType, NotificationPriority

        if appointment.patient and appointment.patient.user_id:
            formatted_time = appointment.scheduled_start.strftime("%b %d, %Y at %H:%M")
            notification_service.create_notification(
                db=db,
                user_id=appointment.patient.user_id,
                title="Appointment Declined",
                message=f"Your consultation request for {formatted_time} was declined.",
                notification_type=NotificationType.APPOINTMENT,
                priority=NotificationPriority.NORMAL,
                metadata_json={"appointment_id": appointment.id},
            )

        return appointment

    @staticmethod
    def complete_appointment(
        db: Session,
        appointment_id: int,
        current_user: User,
        doctor_notes: Optional[str] = None,
    ) -> Appointment:
        """
        Mark a consultation as completed.
        Allowed for the assigned doctor or administrator.
        Allowed only if appointment status is CONFIRMED.
        """
        appointment = AppointmentService.get_by_id(db=db, appointment_id=appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment #{appointment_id} not found.",
            )

        # Authorization check
        if current_user.role != UserRole.ADMIN:
            doctor_profile = (
                db.query(DoctorProfile)
                .filter(DoctorProfile.user_id == current_user.id)
                .first()
            )
            if not doctor_profile or appointment.doctor_id != doctor_profile.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to mark this appointment as completed.",
                )

        # Status transition check
        if appointment.status == AppointmentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment must be confirmed before it can be marked as completed.",
            )

        if appointment.status != AppointmentStatus.CONFIRMED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot complete appointment with status '{appointment.status.value}'.",
            )

        appointment.status = AppointmentStatus.COMPLETED
        if doctor_notes:
            appointment.doctor_notes = doctor_notes

        db.commit()
        db.refresh(appointment)
        return appointment


appointment_service = AppointmentService()
