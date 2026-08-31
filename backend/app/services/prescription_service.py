"""Digital Prescription domain service handling clinical authoring, validation, and patient history."""
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.prescription import Prescription, PrescriptionItem
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.patient import PatientProfile
from app.models.user import User, UserRole
from app.schemas.prescription import PrescriptionCreate


class PrescriptionService:
    """Encapsulated business logic for clinical prescriptions and medications."""

    @staticmethod
    def get_by_id(db: Session, prescription_id: int) -> Optional[Prescription]:
        """Retrieve a prescription by ID with eager loaded relationships."""
        return (
            db.query(Prescription)
            .options(
                joinedload(Prescription.patient).joinedload(PatientProfile.user),
                joinedload(Prescription.doctor).joinedload(DoctorProfile.user),
                joinedload(Prescription.items),
                joinedload(Prescription.appointment),
            )
            .filter(Prescription.id == prescription_id)
            .first()
        )

    @staticmethod
    def create_prescription(
        db: Session,
        doctor_user: User,
        prescription_in: PrescriptionCreate,
    ) -> Prescription:
        """
        Author and issue a digital prescription for a completed consultation appointment.
        Enforces:
        1. Doctor credentials and approval status
        2. Appointment existence and assignment to calling doctor
        3. Appointment completion requirement (must be COMPLETED)
        4. Minimum of 1 medication item with non-empty details
        5. Duplicate prescription prevention for the same appointment
        6. Consistent patient and doctor association matching the consultation
        """
        # Validate doctor profile
        doctor_profile = (
            db.query(DoctorProfile)
            .filter(DoctorProfile.user_id == doctor_user.id)
            .first()
        )
        if not doctor_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only registered doctors can create prescriptions.",
            )

        if doctor_profile.approval_status != DoctorApprovalStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Doctor credentials must be approved by an administrator to issue prescriptions.",
            )

        # Validate appointment
        appointment = (
            db.query(Appointment)
            .filter(Appointment.id == prescription_in.appointment_id)
            .first()
        )
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment with ID {prescription_in.appointment_id} not found.",
            )

        # Verify doctor owns this appointment
        if appointment.doctor_id != doctor_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create prescriptions for appointments assigned to you.",
            )

        # Enforce appointment must be COMPLETED
        if appointment.status != AppointmentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Prescriptions can only be authored for completed consultations. "
                    f"Current appointment status is '{appointment.status.value}'."
                ),
            )

        # Prevent duplicate prescriptions for same appointment
        existing_prescription = (
            db.query(Prescription)
            .filter(Prescription.appointment_id == appointment.id)
            .first()
        )
        if existing_prescription:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A prescription has already been issued for appointment #{appointment.id} (Prescription ID #{existing_prescription.id}).",
            )

        # Validate items
        if not prescription_in.items or len(prescription_in.items) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A prescription must contain at least one medication item.",
            )

        # Create Prescription header
        prescription = Prescription(
            appointment_id=appointment.id,
            patient_id=appointment.patient_id,
            doctor_id=doctor_profile.id,
            diagnosis=prescription_in.diagnosis,
            clinical_notes=prescription_in.clinical_notes,
            notes=prescription_in.notes or prescription_in.clinical_notes,
            valid_until=prescription_in.valid_until,
        )
        db.add(prescription)
        db.flush()  # Populate prescription.id

        # Attach medication items
        for item_in in prescription_in.items:
            med_name = (item_in.medication_name or item_in.drug_name or "").strip()
            if not med_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Medication name cannot be blank.",
                )

            item = PrescriptionItem(
                prescription_id=prescription.id,
                medication_name=med_name,
                drug_name=med_name,
                dosage=item_in.dosage.strip(),
                frequency=item_in.frequency.strip(),
                duration=item_in.duration.strip(),
                route_of_administration=item_in.route_of_administration or "Oral",
                instructions=item_in.instructions,
            )
            db.add(item)

        db.commit()
        db.refresh(prescription)

        # Notify Patient of New Prescription
        from app.services.notification_service import notification_service
        from app.models.notification import NotificationType, NotificationPriority

        if appointment.patient and appointment.patient.user_id:
            doc_name = doctor_user.full_name or "your doctor"
            notification_service.create_notification(
                db=db,
                user_id=appointment.patient.user_id,
                title="New Prescription Available",
                message=f"Dr. {doc_name} has issued a digital prescription for your consultation ({prescription.diagnosis}).",
                notification_type=NotificationType.PRESCRIPTION,
                priority=NotificationPriority.NORMAL,
                metadata_json={
                    "prescription_id": prescription.id,
                    "appointment_id": prescription.appointment_id,
                },
            )

        return PrescriptionService.get_by_id(db=db, prescription_id=prescription.id)

    @staticmethod
    def get_doctor_prescriptions(
        db: Session,
        doctor_user: User,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Prescription]:
        """List all digital prescriptions authored by the authenticated doctor."""
        doctor_profile = (
            db.query(DoctorProfile)
            .filter(DoctorProfile.user_id == doctor_user.id)
            .first()
        )
        if not doctor_profile:
            return []

        return (
            db.query(Prescription)
            .options(
                joinedload(Prescription.patient).joinedload(PatientProfile.user),
                joinedload(Prescription.doctor).joinedload(DoctorProfile.user),
                joinedload(Prescription.items),
                joinedload(Prescription.appointment),
            )
            .filter(Prescription.doctor_id == doctor_profile.id)
            .order_by(Prescription.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_patient_prescriptions(
        db: Session,
        patient_user: User,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Prescription]:
        """List all digital prescriptions issued to the authenticated patient."""
        patient_profile = (
            db.query(PatientProfile)
            .filter(PatientProfile.user_id == patient_user.id)
            .first()
        )
        if not patient_profile:
            return []

        return (
            db.query(Prescription)
            .options(
                joinedload(Prescription.patient).joinedload(PatientProfile.user),
                joinedload(Prescription.doctor).joinedload(DoctorProfile.user),
                joinedload(Prescription.items),
                joinedload(Prescription.appointment),
            )
            .filter(Prescription.patient_id == patient_profile.id)
            .order_by(Prescription.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_prescription_for_appointment(
        db: Session,
        appointment_id: int,
        current_user: User,
    ) -> Optional[Prescription]:
        """Retrieve prescription linked with an appointment with access control check."""
        prescription = (
            db.query(Prescription)
            .options(
                joinedload(Prescription.patient).joinedload(PatientProfile.user),
                joinedload(Prescription.doctor).joinedload(DoctorProfile.user),
                joinedload(Prescription.items),
                joinedload(Prescription.appointment),
            )
            .filter(Prescription.appointment_id == appointment_id)
            .first()
        )
        if not prescription:
            return None

        # Check access permission
        if current_user.role != UserRole.ADMIN:
            is_patient = prescription.patient and prescription.patient.user_id == current_user.id
            is_doctor = prescription.doctor and prescription.doctor.user_id == current_user.id
            if not (is_patient or is_doctor):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view this prescription.",
                )

        return prescription

    @staticmethod
    def get_all_prescriptions(
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Prescription]:
        """Admin overview of prescriptions across the platform."""
        return (
            db.query(Prescription)
            .options(
                joinedload(Prescription.patient).joinedload(PatientProfile.user),
                joinedload(Prescription.doctor).joinedload(DoctorProfile.user),
                joinedload(Prescription.items),
            )
            .order_by(Prescription.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )


prescription_service = PrescriptionService()
