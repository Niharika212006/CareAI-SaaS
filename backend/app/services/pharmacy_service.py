"""Pharmacy Staff domain service managing fulfillment workflows, prescription queue, and safety alerts."""
from datetime import datetime, date, time, timezone
from typing import List, Optional, Tuple, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.prescription import Prescription, PrescriptionItem, PrescriptionStatus
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile
from app.models.user import User, UserRole
from app.models.ai_report import AIAnalysisReport, InteractionSeverity
from app.models.notification import NotificationType, NotificationPriority
from app.schemas.pharmacy import (
    PharmacyPrescriptionSummary,
    PharmacyPrescriptionDetail,
    PharmacyStatsResponse,
)
from app.schemas.ai import AISafetyReportResponse
from app.services.notification_service import notification_service


class PharmacyService:
    """Encapsulated business logic and database operations for Pharmacy Staff operations."""

    @staticmethod
    def get_pharmacy_dashboard(db: Session, pharmacy_user: User) -> Dict[str, Any]:
        """Compute live operational metrics and pending dispensation items for the pharmacy workspace."""
        today = date.today()
        day_start = datetime.combine(today, time.min)

        # 1. Real SQL count queries
        pending_prescribed = (
            db.query(func.count(Prescription.id))
            .filter(Prescription.status == PrescriptionStatus.PRESCRIBED)
            .scalar() or 0
        )
        under_review = (
            db.query(func.count(Prescription.id))
            .filter(Prescription.status == PrescriptionStatus.UNDER_REVIEW)
            .scalar() or 0
        )
        ready_for_pickup = (
            db.query(func.count(Prescription.id))
            .filter(Prescription.status == PrescriptionStatus.READY)
            .scalar() or 0
        )
        dispensed_today = (
            db.query(func.count(Prescription.id))
            .filter(
                Prescription.status == PrescriptionStatus.DISPENSED,
                Prescription.dispensed_at >= day_start,
            )
            .scalar() or 0
        )
        total_dispensed = (
            db.query(func.count(Prescription.id))
            .filter(Prescription.status == PrescriptionStatus.DISPENSED)
            .scalar() or 0
        )

        # High-risk safety alerts count
        high_risk_alerts = (
            db.query(func.count(AIAnalysisReport.id))
            .filter(
                AIAnalysisReport.overall_risk_level.in_(
                    [InteractionSeverity.HIGH, InteractionSeverity.CRITICAL]
                )
            )
            .scalar() or 0
        )

        # 2. Recent Active Prescriptions Queue (Latest 10 non-dispensed / recently updated)
        recent_prescriptions_query = (
            db.query(Prescription)
            .options(
                joinedload(Prescription.patient).joinedload(PatientProfile.user),
                joinedload(Prescription.doctor).joinedload(DoctorProfile.user),
                joinedload(Prescription.items),
                joinedload(Prescription.ai_reports),
            )
            .order_by(Prescription.created_at.desc())
            .limit(10)
        )
        recent_models = recent_prescriptions_query.all()

        recent_items = []
        for rx in recent_models:
            patient_name = rx.patient.user.full_name if rx.patient and rx.patient.user else f"Patient #{rx.patient_id}"
            doctor_name = rx.doctor.user.full_name if rx.doctor and rx.doctor.user else f"Dr. #{rx.doctor_id}"
            med_names = [item.medication_name or item.drug_name for item in rx.items if (item.medication_name or item.drug_name)]
            latest_report = rx.ai_reports[0] if rx.ai_reports else None

            recent_items.append({
                "id": rx.id,
                "patient_name": patient_name,
                "doctor_name": doctor_name,
                "medication": med_names[0] if med_names else "Prescribed Medication",
                "medications_count": len(rx.items),
                "medication_names": med_names,
                "status": rx.status.value,
                "has_ai_report": latest_report is not None,
                "ai_risk_level": latest_report.overall_risk_level.value if latest_report else None,
                "created_at": rx.created_at.isoformat() if rx.created_at else None,
            })

        return {
            "role": "PHARMACY_STAFF",
            "message": f"Welcome, {pharmacy_user.full_name}. Pharmacy Dispensary Workspace is active.",
            "stats": {
                "pending_dispensations": pending_prescribed,
                "under_review_count": under_review,
                "ready_for_pickup_count": ready_for_pickup,
                "dispensed_today": dispensed_today,
                "prescriptions_verified_today": dispensed_today,
                "low_stock_alerts": high_risk_alerts,
                "total_medications_dispensed": total_dispensed,
                "high_risk_alerts_count": high_risk_alerts,
            },
            "pending_dispensations": recent_items,
        }

    @staticmethod
    def get_pharmacy_queue(
        db: Session,
        status_filter: Optional[PrescriptionStatus] = None,
        search: Optional[str] = None,
        risk_level: Optional[InteractionSeverity] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[PharmacyPrescriptionSummary], int]:
        """Query and filter clinical prescriptions awaiting pharmacy processing."""
        query = (
            db.query(Prescription)
            .options(
                joinedload(Prescription.patient).joinedload(PatientProfile.user),
                joinedload(Prescription.doctor).joinedload(DoctorProfile.user),
                joinedload(Prescription.items),
                joinedload(Prescription.ai_reports),
            )
        )

        if status_filter:
            query = query.filter(Prescription.status == status_filter)

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.join(Prescription.patient).join(PatientProfile.user).filter(
                or_(
                    User.full_name.ilike(term),
                    Prescription.diagnosis.ilike(term),
                )
            )

        total_count = query.count()
        prescriptions = query.order_by(Prescription.created_at.desc()).offset(skip).limit(limit).all()

        summaries: List[PharmacyPrescriptionSummary] = []
        for rx in prescriptions:
            pat_user = rx.patient.user if rx.patient else None
            doc_user = rx.doctor.user if rx.doctor else None
            patient_name = pat_user.full_name if pat_user else f"Patient #{rx.patient_id}"
            doctor_name = doc_user.full_name if doc_user else f"Dr. #{rx.doctor_id}"
            med_names = [item.medication_name or item.drug_name for item in rx.items if (item.medication_name or item.drug_name)]
            latest_report = rx.ai_reports[0] if rx.ai_reports else None

            # Filter by risk level if specified
            if risk_level and (not latest_report or latest_report.overall_risk_level != risk_level):
                continue

            # Calculate patient age safely if date_of_birth is present
            patient_age = None
            if rx.patient and rx.patient.date_of_birth:
                today_d = date.today()
                dob = rx.patient.date_of_birth
                patient_age = today_d.year - dob.year - ((today_d.month, today_d.day) < (dob.month, dob.day))

            summaries.append(
                PharmacyPrescriptionSummary(
                    id=rx.id,
                    patient_id=rx.patient_id,
                    patient_name=patient_name,
                    patient_gender=rx.patient.gender if rx.patient else None,
                    patient_age=patient_age,
                    doctor_id=rx.doctor_id,
                    doctor_name=doctor_name,
                    doctor_specialization=rx.doctor.specialization if rx.doctor else None,
                    diagnosis=rx.diagnosis,

                    status=rx.status,
                    medications_count=len(rx.items),
                    medication_names=med_names,
                    has_ai_report=latest_report is not None,
                    ai_risk_level=latest_report.overall_risk_level if latest_report else None,
                    pharmacy_notes=rx.pharmacy_notes,
                    created_at=rx.created_at,
                    valid_until=rx.valid_until,
                    dispensed_at=rx.dispensed_at,
                )
            )

        return summaries, total_count

    @staticmethod
    def get_prescription_detail(
        db: Session,
        prescription_id: int,
        current_user: User,
    ) -> Prescription:
        """Fetch full prescription record with items, doctor/patient profiles, and latest AI safety report."""
        rx = (
            db.query(Prescription)
            .options(
                joinedload(Prescription.patient).joinedload(PatientProfile.user),
                joinedload(Prescription.doctor).joinedload(DoctorProfile.user),
                joinedload(Prescription.dispensed_by),
                joinedload(Prescription.items),
                joinedload(Prescription.ai_reports),
            )
            .filter(Prescription.id == prescription_id)
            .first()
        )
        if not rx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prescription #{prescription_id} not found.",
            )

        # RBAC verification
        if current_user.role not in [UserRole.PHARMACY_STAFF, UserRole.ADMIN]:
            is_pat = rx.patient and rx.patient.user_id == current_user.id
            is_doc = rx.doctor and rx.doctor.user_id == current_user.id
            if not (is_pat or is_doc):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Unauthorized to view this prescription.",
                )

        return rx

    @staticmethod
    def update_prescription_status(
        db: Session,
        prescription_id: int,
        current_user: User,
        new_status: PrescriptionStatus,
        pharmacy_notes: Optional[str] = None,
    ) -> Prescription:
        """Update fulfillment status of a prescription in the dispensary workflow."""
        if current_user.role not in [UserRole.PHARMACY_STAFF, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Pharmacy Staff or Admins can update prescription dispensing status.",
            )

        rx = db.query(Prescription).filter(Prescription.id == prescription_id).first()
        if not rx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prescription #{prescription_id} not found.",
            )

        old_status = rx.status
        rx.status = new_status
        if pharmacy_notes is not None:
            rx.pharmacy_notes = pharmacy_notes.strip() if pharmacy_notes else None

        if new_status == PrescriptionStatus.DISPENSED:
            rx.dispensed_at = datetime.now(timezone.utc)
            rx.dispensed_by_user_id = current_user.id

        db.commit()
        db.refresh(rx)

        # Notifications
        doc_user_id = rx.doctor.user_id if rx.doctor else None
        pat_user_id = rx.patient.user_id if rx.patient else None

        if new_status == PrescriptionStatus.READY and pat_user_id:
            notification_service.create_notification(
                db=db,
                user_id=pat_user_id,
                title="Prescription Ready for Pickup",
                message=f"Your prescription (#{rx.id}) has been prepared and is ready for pickup at the pharmacy.",
                notification_type=NotificationType.PRESCRIPTION,
                priority=NotificationPriority.HIGH,
                metadata_json={"prescription_id": rx.id, "status": "READY"},
            )

        elif new_status == PrescriptionStatus.DISPENSED:
            if pat_user_id:
                notification_service.create_notification(
                    db=db,
                    user_id=pat_user_id,
                    title="Medication Dispensed",
                    message=f"Your prescription (#{rx.id}) has been dispensed by the pharmacy.",
                    notification_type=NotificationType.PRESCRIPTION,
                    priority=NotificationPriority.NORMAL,
                    metadata_json={"prescription_id": rx.id, "status": "DISPENSED"},
                )
            if doc_user_id:
                notification_service.create_notification(
                    db=db,
                    user_id=doc_user_id,
                    title="Prescription Dispensed",
                    message=f"Prescription (#{rx.id}) for patient #{rx.patient_id} has been dispensed by pharmacy staff.",
                    notification_type=NotificationType.PRESCRIPTION,
                    priority=NotificationPriority.LOW,
                    metadata_json={"prescription_id": rx.id, "status": "DISPENSED"},
                )

        return rx


pharmacy_service = PharmacyService()
