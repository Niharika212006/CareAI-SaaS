"""Role-Based Real-Time Dashboard & Analytics Aggregation Service."""
from datetime import datetime, date, time, timezone
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session, joinedload

from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription, PrescriptionItem
from app.models.ai_report import AIAnalysisReport, InteractionSeverity
from app.models.availability import DoctorAvailability, DoctorUnavailableDate
from app.schemas.dashboard import (
    PatientDashboardResponse,
    PatientDashboardStats,
    PatientAISafetySummary,
    PatientMedicalProfileStatus,
    DashboardAppointmentItem,
    DashboardPrescriptionItem,
    DoctorDashboardResponse,
    DoctorDashboardStats,
    DoctorPendingActions,
    DoctorAvailabilitySummary,
    DashboardDoctorScheduleItem,
    AdminDashboardResponse,
    AdminPlatformStats,
    AdminDoctorSummary,
    AdminAppointmentSummary,
    AdminAISafetyMetrics,
    AdminRecentActivityItem,
)


class DashboardService:
    """Consolidated aggregation service powering role-based real-time platform dashboards."""

    # -----------------------------------------------------------------------
    # 1. Patient Dashboard
    # -----------------------------------------------------------------------
    @staticmethod
    def get_patient_dashboard(db: Session, patient_user: User) -> PatientDashboardResponse:
        """Aggregate real-time metrics, upcoming appointment, and health history for authenticated patient."""
        patient = (
            db.query(PatientProfile)
            .filter(PatientProfile.user_id == patient_user.id)
            .first()
        )
        if not patient:
            patient = PatientProfile(user_id=patient_user.id)
            db.add(patient)
            db.commit()
            db.refresh(patient)

        now = datetime.now()
        today = date.today()

        # Aggregate Appointment Stats
        total_appointments = (
            db.query(func.count(Appointment.id))
            .filter(Appointment.patient_id == patient.id)
            .scalar() or 0
        )
        upcoming_appointments = (
            db.query(func.count(Appointment.id))
            .filter(
                Appointment.patient_id == patient.id,
                Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
                Appointment.scheduled_start >= now,
            )
            .scalar() or 0
        )
        completed_appointments = (
            db.query(func.count(Appointment.id))
            .filter(
                Appointment.patient_id == patient.id,
                Appointment.status == AppointmentStatus.COMPLETED,
            )
            .scalar() or 0
        )

        # Active Prescriptions (valid_until >= today or valid_until IS NULL)
        active_prescriptions = (
            db.query(func.count(Prescription.id))
            .filter(
                Prescription.patient_id == patient.id,
                (Prescription.valid_until >= today) | (Prescription.valid_until.is_(None)),
            )
            .scalar() or 0
        )

        # Next Nearest Upcoming Appointment
        next_app_model = (
            db.query(Appointment)
            .options(
                joinedload(Appointment.doctor).joinedload(DoctorProfile.user),
                joinedload(Appointment.patient).joinedload(PatientProfile.user),
            )
            .filter(
                Appointment.patient_id == patient.id,
                Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
                Appointment.scheduled_start >= now,
            )
            .order_by(Appointment.scheduled_start.asc())
            .first()
        )
        next_appointment = None
        if next_app_model:
            doc = next_app_model.doctor
            doc_user = doc.user if doc else None
            next_appointment = DashboardAppointmentItem(
                id=next_app_model.id,
                doctor_id=next_app_model.doctor_id,
                doctor_name=f"Dr. {doc_user.full_name}" if doc_user else "Practitioner",
                doctor_specialization=doc.specialization if doc else "Specialist",
                doctor_consultation_fee=float(doc.consultation_fee) if doc and doc.consultation_fee else 0.0,
                patient_id=next_app_model.patient_id,
                patient_name=patient_user.full_name,
                scheduled_start=next_app_model.scheduled_start,
                scheduled_end=next_app_model.scheduled_end,
                status=next_app_model.status,
                reason=next_app_model.reason or next_app_model.reason_for_visit,
                meeting_link=next_app_model.meeting_link,
            )

        # Recent Prescriptions (Latest 5)
        recent_rx_models = (
            db.query(Prescription)
            .options(
                joinedload(Prescription.doctor).joinedload(DoctorProfile.user),
                joinedload(Prescription.items),
                joinedload(Prescription.ai_reports),
            )
            .filter(Prescription.patient_id == patient.id)
            .order_by(Prescription.created_at.desc())
            .limit(5)
            .all()
        )
        recent_prescriptions: List[DashboardPrescriptionItem] = []
        for rx in recent_rx_models:
            doc = rx.doctor
            doc_user = doc.user if doc else None
            latest_report = rx.ai_reports[0] if rx.ai_reports else None
            recent_prescriptions.append(
                DashboardPrescriptionItem(
                    id=rx.id,
                    appointment_id=rx.appointment_id,
                    doctor_name=f"Dr. {doc_user.full_name}" if doc_user else "Practitioner",
                    doctor_specialization=doc.specialization if doc else "Specialist",
                    diagnosis=rx.diagnosis,
                    medications_count=len(rx.items) if rx.items else 0,
                    created_at=rx.created_at,
                    valid_until=rx.valid_until,
                    has_ai_report=latest_report is not None,
                    ai_risk_level=latest_report.overall_risk_level if latest_report else None,
                )
            )

        # AI Safety Summary
        ai_reports = (
            db.query(AIAnalysisReport)
            .filter(AIAnalysisReport.patient_id == patient.id)
            .order_by(AIAnalysisReport.created_at.desc())
            .all()
        )
        total_analyzed = len(ai_reports)
        high_risk_count = sum(
            1 for r in ai_reports if r.overall_risk_level in [InteractionSeverity.HIGH, InteractionSeverity.CRITICAL]
        )
        latest_report = ai_reports[0] if ai_reports else None

        # Medical Profile Completion Status
        allergies_list = patient.get_allergy_names()
        conditions_list = patient.get_condition_names()
        medications_list = patient.get_current_medication_names()
        has_emergency = bool(patient.emergency_contact_phone or patient.emergency_contact_name or patient.emergency_contact)

        is_profile_complete = bool(
            allergies_list and conditions_list and medications_list and has_emergency and patient.blood_group
        )

        return PatientDashboardResponse(
            stats=PatientDashboardStats(
                total_appointments=total_appointments,
                upcoming_appointments=upcoming_appointments,
                completed_appointments=completed_appointments,
                active_prescriptions=active_prescriptions,
            ),
            next_appointment=next_appointment,
            recent_prescriptions=recent_prescriptions,
            ai_safety_summary=PatientAISafetySummary(
                total_analyzed_prescriptions=total_analyzed,
                high_risk_findings_count=high_risk_count,
                latest_analysis_status=latest_report.analysis_status if latest_report else None,
                latest_overall_risk=latest_report.overall_risk_level if latest_report else None,
            ),
            medical_profile_status=PatientMedicalProfileStatus(
                is_complete=is_profile_complete,
                has_allergies_recorded=len(allergies_list) > 0,
                allergies_count=len(allergies_list),
                has_conditions_recorded=len(conditions_list) > 0,
                conditions_count=len(conditions_list),
                has_medications_recorded=len(medications_list) > 0,
                medications_count=len(medications_list),
                has_emergency_contact=has_emergency,
            ),
        )

    # -----------------------------------------------------------------------
    # 2. Doctor Dashboard
    # -----------------------------------------------------------------------
    @staticmethod
    def get_doctor_dashboard(db: Session, doctor_user: User) -> DoctorDashboardResponse:
        """Aggregate operational clinical workload, today's schedule, and pending actions for treating doctor."""
        doctor = (
            db.query(DoctorProfile)
            .filter(DoctorProfile.user_id == doctor_user.id)
            .first()
        )
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor profile not found.",
            )

        now = datetime.now()
        today = date.today()
        day_start = datetime.combine(today, time.min)
        day_end = datetime.combine(today, time.max)

        # 1. Today's Appointments
        today_appointments_query = (
            db.query(Appointment)
            .options(joinedload(Appointment.patient).joinedload(PatientProfile.user))
            .filter(
                Appointment.doctor_id == doctor.id,
                Appointment.scheduled_start >= day_start,
                Appointment.scheduled_start <= day_end,
                Appointment.status.notin_([AppointmentStatus.CANCELLED, AppointmentStatus.REJECTED]),
            )
            .order_by(Appointment.scheduled_start.asc())
        )
        today_app_models = today_appointments_query.all()

        today_schedule: List[DashboardDoctorScheduleItem] = []
        for app in today_app_models:
            pat_name = app.patient.user.full_name if (app.patient and app.patient.user) else f"Patient #{app.patient_id}"
            is_past = app.scheduled_end < now
            today_schedule.append(
                DashboardDoctorScheduleItem(
                    id=app.id,
                    patient_id=app.patient_id,
                    patient_name=pat_name,
                    scheduled_start=app.scheduled_start,
                    scheduled_end=app.scheduled_end,
                    status=app.status,
                    reason=app.reason or app.reason_for_visit,
                    is_past=is_past,
                )
            )

        # 2. Overall Doctor Stats
        today_count = len(today_app_models)
        upcoming_count = (
            db.query(func.count(Appointment.id))
            .filter(
                Appointment.doctor_id == doctor.id,
                Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
                Appointment.scheduled_start >= now,
            )
            .scalar() or 0
        )
        completed_count = (
            db.query(func.count(Appointment.id))
            .filter(
                Appointment.doctor_id == doctor.id,
                Appointment.status == AppointmentStatus.COMPLETED,
            )
            .scalar() or 0
        )
        total_unique_patients = (
            db.query(func.count(distinct(Appointment.patient_id)))
            .filter(
                Appointment.doctor_id == doctor.id,
                Appointment.status.notin_([AppointmentStatus.REJECTED, AppointmentStatus.CANCELLED]),
            )
            .scalar() or 0
        )
        prescriptions_issued = (
            db.query(func.count(Prescription.id))
            .filter(Prescription.doctor_id == doctor.id)
            .scalar() or 0
        )

        # 3. Pending Actions
        pending_requests = (
            db.query(func.count(Appointment.id))
            .filter(
                Appointment.doctor_id == doctor.id,
                Appointment.status == AppointmentStatus.PENDING,
            )
            .scalar() or 0
        )
        confirmed_awaiting = (
            db.query(func.count(Appointment.id))
            .filter(
                Appointment.doctor_id == doctor.id,
                Appointment.status == AppointmentStatus.CONFIRMED,
                Appointment.scheduled_start >= now,
            )
            .scalar() or 0
        )

        # Completed visits that don't yet have a Prescription issued
        prescribed_appt_ids_subquery = (
            db.query(Prescription.appointment_id)
            .filter(Prescription.doctor_id == doctor.id)
            .scalar_subquery()
        )
        completed_awaiting_rx = (
            db.query(func.count(Appointment.id))
            .filter(
                Appointment.doctor_id == doctor.id,
                Appointment.status == AppointmentStatus.COMPLETED,
                Appointment.id.notin_(prescribed_appt_ids_subquery),
            )
            .scalar() or 0
        )

        # 4. Availability Summary
        active_availabilities = (
            db.query(DoctorAvailability)
            .filter(
                DoctorAvailability.doctor_id == doctor.id,
                DoctorAvailability.is_active == True,
            )
            .all()
        )
        next_leave = (
            db.query(DoctorUnavailableDate)
            .filter(
                DoctorUnavailableDate.doctor_id == doctor.id,
                DoctorUnavailableDate.unavailable_date >= today,
            )
            .order_by(DoctorUnavailableDate.unavailable_date.asc())
            .first()
        )
        avail_summary = DoctorAvailabilitySummary(
            has_active_schedule=len(active_availabilities) > 0,
            active_days_count=len(set(a.day_of_week for a in active_availabilities)),
            slot_duration_minutes=active_availabilities[0].slot_duration_minutes if active_availabilities else None,
            next_unavailable_date=next_leave.unavailable_date if next_leave else None,
            next_unavailable_reason=next_leave.reason if next_leave else None,
        )

        # 5. Recent Patient Activity (Latest 5 appointments)
        recent_apps_models = (
            db.query(Appointment)
            .options(joinedload(Appointment.patient).joinedload(PatientProfile.user))
            .filter(Appointment.doctor_id == doctor.id)
            .order_by(Appointment.scheduled_start.desc())
            .limit(5)
            .all()
        )
        recent_activity: List[DashboardAppointmentItem] = []
        for app in recent_apps_models:
            pat_name = app.patient.user.full_name if (app.patient and app.patient.user) else f"Patient #{app.patient_id}"
            recent_activity.append(
                DashboardAppointmentItem(
                    id=app.id,
                    doctor_id=doctor.id,
                    doctor_name=f"Dr. {doctor_user.full_name}",
                    doctor_specialization=doctor.specialization,
                    doctor_consultation_fee=float(doctor.consultation_fee) if doctor.consultation_fee else 0.0,
                    patient_id=app.patient_id,
                    patient_name=pat_name,
                    scheduled_start=app.scheduled_start,
                    scheduled_end=app.scheduled_end,
                    status=app.status,
                    reason=app.reason or app.reason_for_visit,
                    meeting_link=app.meeting_link,
                )
            )

        return DoctorDashboardResponse(
            stats=DoctorDashboardStats(
                today_appointments=today_count,
                upcoming_appointments=upcoming_count,
                completed_consultations=completed_count,
                total_patients=total_unique_patients,
                prescriptions_issued=prescriptions_issued,
            ),
            today_schedule=today_schedule,
            pending_actions=DoctorPendingActions(
                pending_appointment_requests=pending_requests,
                confirmed_awaiting_consultation=confirmed_awaiting,
                completed_awaiting_prescription=completed_awaiting_rx,
            ),
            availability_summary=avail_summary,
            recent_patient_activity=recent_activity,
        )

    # -----------------------------------------------------------------------
    # 3. Admin Dashboard
    # -----------------------------------------------------------------------
    @staticmethod
    def get_admin_dashboard(db: Session) -> AdminDashboardResponse:
        """Aggregate system-wide platform statistics, doctor verification summaries, and privacy-conscious activity feed."""
        # 1. User & Doctor Counts
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_patients = db.query(func.count(PatientProfile.id)).scalar() or 0
        total_doctors = db.query(func.count(DoctorProfile.id)).scalar() or 0

        approved_doctors = (
            db.query(func.count(DoctorProfile.id))
            .filter(DoctorProfile.approval_status == DoctorApprovalStatus.APPROVED)
            .scalar() or 0
        )
        pending_doctors = (
            db.query(func.count(DoctorProfile.id))
            .filter(DoctorProfile.approval_status == DoctorApprovalStatus.PENDING)
            .scalar() or 0
        )
        rejected_doctors = (
            db.query(func.count(DoctorProfile.id))
            .filter(DoctorProfile.approval_status == DoctorApprovalStatus.REJECTED)
            .scalar() or 0
        )

        # 2. Appointment Counts
        total_appointments = db.query(func.count(Appointment.id)).scalar() or 0
        appt_pending = db.query(func.count(Appointment.id)).filter(Appointment.status == AppointmentStatus.PENDING).scalar() or 0
        appt_confirmed = db.query(func.count(Appointment.id)).filter(Appointment.status == AppointmentStatus.CONFIRMED).scalar() or 0
        appt_completed = db.query(func.count(Appointment.id)).filter(Appointment.status == AppointmentStatus.COMPLETED).scalar() or 0
        appt_cancelled = db.query(func.count(Appointment.id)).filter(Appointment.status == AppointmentStatus.CANCELLED).scalar() or 0
        appt_rejected = db.query(func.count(Appointment.id)).filter(Appointment.status == AppointmentStatus.REJECTED).scalar() or 0

        total_prescriptions = db.query(func.count(Prescription.id)).scalar() or 0
        total_ai_reports = db.query(func.count(AIAnalysisReport.id)).scalar() or 0

        # 3. AI Safety Metrics Breakdown
        critical_risk = db.query(func.count(AIAnalysisReport.id)).filter(AIAnalysisReport.overall_risk_level == InteractionSeverity.CRITICAL).scalar() or 0
        high_risk = db.query(func.count(AIAnalysisReport.id)).filter(AIAnalysisReport.overall_risk_level == InteractionSeverity.HIGH).scalar() or 0
        moderate_risk = db.query(func.count(AIAnalysisReport.id)).filter(AIAnalysisReport.overall_risk_level == InteractionSeverity.MODERATE).scalar() or 0
        low_risk = db.query(func.count(AIAnalysisReport.id)).filter(AIAnalysisReport.overall_risk_level == InteractionSeverity.LOW).scalar() or 0
        none_risk = db.query(func.count(AIAnalysisReport.id)).filter(AIAnalysisReport.overall_risk_level == InteractionSeverity.NONE).scalar() or 0
        total_findings = db.query(func.sum(AIAnalysisReport.total_findings)).scalar() or 0

        # 4. Privacy-Sanitized Recent Platform Activity (Latest 10 combined events)
        recent_activity: List[AdminRecentActivityItem] = []

        # Recent User Registrations (Latest 4)
        latest_users = db.query(User).order_by(User.created_at.desc()).limit(4).all()
        for u in latest_users:
            recent_activity.append(
                AdminRecentActivityItem(
                    event_type="USER_REGISTERED",
                    title="New User Registered",
                    description=f"{u.full_name} joined platform as {u.role.value}.",
                    timestamp=u.created_at,
                )
            )

        # Recent Doctor Applications (Latest 3)
        latest_docs = (
            db.query(DoctorProfile)
            .options(joinedload(DoctorProfile.user))
            .order_by(DoctorProfile.created_at.desc())
            .limit(3)
            .all()
        )
        for d in latest_docs:
            d_name = d.user.full_name if d.user else f"Doctor #{d.id}"
            recent_activity.append(
                AdminRecentActivityItem(
                    event_type="DOCTOR_APPLICATION",
                    title=f"Doctor Credential Application ({d.approval_status.value})",
                    description=f"Dr. {d_name} submitted credentials for {d.specialization}.",
                    timestamp=d.created_at,
                )
            )

        # Recent Appointments (Latest 3)
        latest_appts = (
            db.query(Appointment)
            .options(joinedload(Appointment.doctor).joinedload(DoctorProfile.user))
            .order_by(Appointment.created_at.desc())
            .limit(3)
            .all()
        )
        for a in latest_appts:
            doc_name = a.doctor.user.full_name if (a.doctor and a.doctor.user) else "Practitioner"
            recent_activity.append(
                AdminRecentActivityItem(
                    event_type="APPOINTMENT_BOOKED",
                    title=f"Consultation Scheduled ({a.status.value})",
                    description=f"Appointment booked with Dr. {doc_name}.",
                    timestamp=a.created_at,
                )
            )

        # Sort combined activity chronologically descending
        recent_activity.sort(key=lambda x: x.timestamp, reverse=True)

        return AdminDashboardResponse(
            platform_stats=AdminPlatformStats(
                total_users=total_users,
                total_patients=total_patients,
                total_doctors=total_doctors,
                approved_doctors=approved_doctors,
                pending_doctor_approvals=pending_doctors,
                rejected_doctors=rejected_doctors,
                total_appointments=total_appointments,
                completed_appointments=appt_completed,
                cancelled_appointments=appt_cancelled,
                total_prescriptions=total_prescriptions,
                total_ai_analyses=total_ai_reports,
            ),
            doctor_summary=AdminDoctorSummary(
                pending_count=pending_doctors,
                approved_count=approved_doctors,
                rejected_count=rejected_doctors,
            ),
            appointment_summary=AdminAppointmentSummary(
                pending_count=appt_pending,
                confirmed_count=appt_confirmed,
                completed_count=appt_completed,
                cancelled_count=appt_cancelled,
                rejected_count=appt_rejected,
            ),
            ai_safety_metrics=AdminAISafetyMetrics(
                total_reports=total_ai_reports,
                critical_risk_count=critical_risk,
                high_risk_count=high_risk,
                moderate_risk_count=moderate_risk,
                low_risk_count=low_risk,
                none_risk_count=none_risk,
                total_findings_detected=int(total_findings),
            ),
            recent_activity=recent_activity[:10],
        )


dashboard_service = DashboardService()
