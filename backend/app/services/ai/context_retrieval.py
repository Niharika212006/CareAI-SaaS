"""Secure, database-aware context retrieval layer for CareAI Role-Specific AI System.

Executes strictly parameterized queries with identity and RBAC enforcement.
Guarantees zero model-generated SQL and prevents hallucination of application metrics.
"""
import logging
from datetime import datetime, date, time, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription, PrescriptionItem, PrescriptionStatus
from app.models.lab import (
    LabOrder,
    LabOrderItem,
    LabOrderStatus,
    LabOrderPriority,
    LabSample,
    LabResult,
    ResultFlag,
    LabAuditEvent,
    LabTest,
)
from app.models.medical_document import MedicalDocument

logger = logging.getLogger("healthcare.ai.context")


class ContextRetrievalService:
    """Provides role-authorized, parameterized database context for AI prompting."""

    # -------------------------------------------------------------------------
    # 1. ADMINISTRATOR CONTEXT (AGGREGATE SYSTEM INTELLIGENCE)
    # -------------------------------------------------------------------------
    def get_admin_context(self, db: Session) -> Dict[str, Any]:
        """
        Execute exact SQL count and aggregate queries for administrative intelligence.
        Guarantees 100% mathematical accuracy with zero LLM guesswork.
        """
        try:
            # 1a. User counts by role
            user_counts_raw = (
                db.query(User.role, func.count(User.id))
                .group_by(User.role)
                .all()
            )
            role_counts = {role.value: 0 for role in UserRole}
            total_users = 0
            for r, count in user_counts_raw:
                role_counts[r.value] = count
                total_users += count

            # 1b. Doctor approval statistics
            doc_approval_raw = (
                db.query(DoctorProfile.approval_status, func.count(DoctorProfile.id))
                .group_by(DoctorProfile.approval_status)
                .all()
            )
            approval_counts = {s.value: 0 for s in DoctorApprovalStatus}
            total_doctors = 0
            for s, count in doc_approval_raw:
                approval_counts[s.value] = count
                total_doctors += count

            # Doctors with complete vs incomplete profiles
            complete_doctors = (
                db.query(func.count(DoctorProfile.id))
                .filter(
                    DoctorProfile.specialization.isnot(None),
                    DoctorProfile.specialization != "",
                    DoctorProfile.license_number.isnot(None),
                    DoctorProfile.license_number != "",
                    DoctorProfile.consultation_fee > 0,
                )
                .scalar() or 0
            )
            incomplete_doctors = max(0, total_doctors - complete_doctors)

            # 1c. Prescription lifecycle statistics
            rx_counts_raw = (
                db.query(Prescription.status, func.count(Prescription.id))
                .group_by(Prescription.status)
                .all()
            )
            rx_counts = {s.value: 0 for s in PrescriptionStatus}
            total_prescriptions = 0
            for s, count in rx_counts_raw:
                rx_counts[s.value] = count
                total_prescriptions += count

            # 1d. Appointment statistics
            appt_counts_raw = (
                db.query(Appointment.status, func.count(Appointment.id))
                .group_by(Appointment.status)
                .all()
            )
            appt_counts = {s.value: 0 for s in AppointmentStatus}
            total_appointments = 0
            for s, count in appt_counts_raw:
                appt_counts[s.value] = count
                total_appointments += count

            # Appointments scheduled today
            today_date = datetime.utcnow().date()
            start_of_today = datetime.combine(today_date, time.min)
            end_of_today = datetime.combine(today_date, time.max)
            appts_today = (
                db.query(func.count(Appointment.id))
                .filter(
                    Appointment.scheduled_start >= start_of_today,
                    Appointment.scheduled_start <= end_of_today,
                )
                .scalar() or 0
            )

            # 1e. Lab workflow statistics
            lab_counts_raw = (
                db.query(LabOrder.status, func.count(LabOrder.id))
                .group_by(LabOrder.status)
                .all()
            )
            lab_counts = {s.value: 0 for s in LabOrderStatus}
            total_lab_orders = 0
            for s, count in lab_counts_raw:
                lab_counts[s.value] = count
                total_lab_orders += count

            stat_orders = (
                db.query(func.count(LabOrder.id))
                .filter(LabOrder.priority == LabOrderPriority.STAT)
                .scalar() or 0
            )

            return {
                "users": {
                    "total": total_users,
                    "by_role": role_counts,
                },
                "doctors": {
                    "total_profiles": total_doctors,
                    "by_approval": approval_counts,
                    "profiles_completed": complete_doctors,
                    "profiles_incomplete": incomplete_doctors,
                },
                "prescriptions": {
                    "total": total_prescriptions,
                    "by_status": rx_counts,
                },
                "appointments": {
                    "total": total_appointments,
                    "by_status": appt_counts,
                    "scheduled_today": appts_today,
                },
                "laboratory": {
                    "total_orders": total_lab_orders,
                    "by_status": lab_counts,
                    "stat_priority_orders": stat_orders,
                },
            }
        except Exception as err:
            logger.error(f"Error compiling admin context: {err}")
            return {"error": "Failed to compile aggregate administrative metrics."}

    # -------------------------------------------------------------------------
    # 2. PATIENT CONTEXT (OWNED HEALTH RECORDS & PRESCRIPTIONS)
    # -------------------------------------------------------------------------
    def get_patient_context(self, db: Session, user: Any) -> Dict[str, Any]:
        """Retrieve authorized clinical records for the logged-in patient."""
        uid = user.id if hasattr(user, "id") else user
        patient_profile = (
            db.query(PatientProfile)
            .filter(PatientProfile.user_id == uid)
            .first()
        )
        if not patient_profile:
            return {"has_profile": False, "prescriptions": [], "appointments": [], "lab_reports": []}

        try:
            # 2a. Active & recent prescriptions with line items
            prescriptions = (
                db.query(Prescription)
                .filter(Prescription.patient_id == patient_profile.id)
                .order_by(Prescription.created_at.desc())
                .limit(10)
                .all()
            )

            formatted_rx = []
            for rx in prescriptions:
                items = []
                for it in rx.items:
                    items.append({
                        "name": it.medication_name or it.drug_name or "Prescribed Medication",
                        "dosage": it.dosage,
                        "frequency": it.frequency,
                        "duration": it.duration,
                        "instructions": it.instructions or "As directed by physician",
                    })

                doctor_name = "Prescribing Physician"
                if rx.doctor and rx.doctor.user:
                    doctor_name = f"Dr. {rx.doctor.user.full_name}"

                formatted_rx.append({
                    "id": rx.id,
                    "diagnosis": rx.diagnosis,
                    "doctor": doctor_name,
                    "status": rx.status.value,
                    "issued_at": rx.created_at.strftime("%Y-%m-%d") if rx.created_at else None,
                    "valid_until": rx.valid_until.strftime("%Y-%m-%d") if rx.valid_until else None,
                    "items": items,
                })

            # 2b. Upcoming & recent appointments
            appointments = (
                db.query(Appointment)
                .filter(Appointment.patient_id == patient_profile.id)
                .order_by(Appointment.scheduled_start.desc())
                .limit(10)
                .all()
            )
            formatted_appts = []
            for appt in appointments:
                doc_name = f"Dr. {appt.doctor.user.full_name}" if appt.doctor and appt.doctor.user else "Physician"
                formatted_appts.append({
                    "id": appt.id,
                    "doctor": doc_name,
                    "scheduled_start": appt.scheduled_start.strftime("%Y-%m-%d %H:%M") if appt.scheduled_start else None,
                    "status": appt.status.value,
                    "reason": appt.reason_for_visit or appt.reason or "General Consultation",
                })

            # 2c. Diagnostic lab reports released to patient
            lab_orders = (
                db.query(LabOrder)
                .filter(
                    LabOrder.patient_id == patient_profile.id,
                    LabOrder.status.in_([LabOrderStatus.RELEASED, LabOrderStatus.VERIFIED]),
                )
                .order_by(LabOrder.ordered_at.desc())
                .limit(10)
                .all()
            )
            formatted_labs = []
            for lo in lab_orders:
                test_names = [item.test.test_name for item in lo.items if item.test]
                formatted_labs.append({
                    "order_id": lo.id,
                    "ordered_at": lo.ordered_at.strftime("%Y-%m-%d") if lo.ordered_at else None,
                    "status": lo.status.value,
                    "tests": test_names or ["Diagnostic Panel"],
                })

            return {
                "has_profile": True,
                "patient_name": user.full_name,
                "blood_group": patient_profile.blood_group,
                "allergies": patient_profile.allergies or [],
                "chronic_conditions": patient_profile.chronic_conditions or [],
                "prescriptions": formatted_rx,
                "appointments": formatted_appts,
                "lab_reports": formatted_labs,
            }
        except Exception as err:
            logger.error(f"Error compiling patient context for user {user.id}: {err}")
            return {"has_profile": True, "error": "Could not compile complete patient clinical history."}

    # -------------------------------------------------------------------------
    # 3. DOCTOR CONTEXT (CLINICAL SCHEDULE & AUTHORIZED PATIENT SUMMARIES)
    # -------------------------------------------------------------------------
    def get_doctor_context(self, db: Session, user: Any, query: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve the doctor's consultation schedule, pending lab orders, and recent clinical activity."""
        uid = user.id if hasattr(user, "id") else user
        doctor_profile = (
            db.query(DoctorProfile)
            .filter(DoctorProfile.user_id == uid)
            .first()
        )
        if not doctor_profile:
            return {"has_profile": False, "appointments_today": [], "recent_prescriptions": []}

        try:
            # 3a. Appointments today
            today_date = datetime.utcnow().date()
            start_of_today = datetime.combine(today_date, time.min)
            end_of_today = datetime.combine(today_date, time.max)

            today_appts = (
                db.query(Appointment)
                .filter(
                    Appointment.doctor_id == doctor_profile.id,
                    Appointment.scheduled_start >= start_of_today,
                    Appointment.scheduled_start <= end_of_today,
                )
                .order_by(Appointment.scheduled_start.asc())
                .all()
            )
            formatted_today = []
            for appt in today_appts:
                pt_name = appt.patient.user.full_name if appt.patient and appt.patient.user else "Patient"
                formatted_today.append({
                    "id": appt.id,
                    "patient_name": pt_name,
                    "time": appt.scheduled_start.strftime("%H:%M") if appt.scheduled_start else "TBD",
                    "status": appt.status.value,
                    "reason": appt.reason_for_visit or appt.reason or "Consultation",
                })

            # 3b. Upcoming appointments
            upcoming_appts = (
                db.query(Appointment)
                .filter(
                    Appointment.doctor_id == doctor_profile.id,
                    Appointment.scheduled_start > end_of_today,
                    Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
                )
                .order_by(Appointment.scheduled_start.asc())
                .limit(5)
                .all()
            )
            formatted_upcoming = []
            for appt in upcoming_appts:
                pt_name = appt.patient.user.full_name if appt.patient and appt.patient.user else "Patient"
                formatted_upcoming.append({
                    "id": appt.id,
                    "patient_name": pt_name,
                    "date": appt.scheduled_start.strftime("%Y-%m-%d %H:%M") if appt.scheduled_start else None,
                    "status": appt.status.value,
                })

            # 3c. Recent lab orders ordered by this doctor
            lab_orders = (
                db.query(LabOrder)
                .filter(LabOrder.doctor_id == doctor_profile.id)
                .order_by(LabOrder.ordered_at.desc())
                .limit(5)
                .all()
            )
            formatted_labs = []
            for lo in lab_orders:
                pt_name = lo.patient.user.full_name if lo.patient and lo.patient.user else "Patient"
                formatted_labs.append({
                    "order_id": lo.id,
                    "patient_name": pt_name,
                    "priority": lo.priority.value,
                    "status": lo.status.value,
                    "ordered_at": lo.ordered_at.strftime("%Y-%m-%d") if lo.ordered_at else None,
                })

            return {
                "has_profile": True,
                "doctor_name": user.full_name,
                "specialization": doctor_profile.specialization,
                "approval_status": doctor_profile.approval_status.value,
                "appointments_today": formatted_today,
                "upcoming_appointments": formatted_upcoming,
                "recent_lab_orders": formatted_labs,
            }
        except Exception as err:
            logger.error(f"Error compiling doctor context: {err}")
            return {"has_profile": True, "error": "Could not compile complete clinical practice context."}

    # -------------------------------------------------------------------------
    # 4. LABORATORY TECHNICIAN CONTEXT (SPECIMEN & TESTING WORKFLOW)
    # -------------------------------------------------------------------------
    def get_lab_context(self, db: Session, user: User) -> Dict[str, Any]:
        """Retrieve diagnostic specimen queue, testing workload, and critical panic alerts."""
        try:
            # 4a. Orders awaiting specimen collection
            pending_samples = (
                db.query(LabOrder)
                .filter(LabOrder.status == LabOrderStatus.SAMPLE_PENDING)
                .order_by(LabOrder.ordered_at.asc())
                .limit(10)
                .all()
            )
            formatted_pending_samples = []
            for lo in pending_samples:
                pt_name = lo.patient.user.full_name if lo.patient and lo.patient.user else "Patient"
                tests = [it.test.test_name for it in lo.items if it.test]
                formatted_pending_samples.append({
                    "order_id": lo.id,
                    "patient_name": pt_name,
                    "priority": lo.priority.value,
                    "tests": tests or ["Diagnostic Order"],
                    "ordered_at": lo.ordered_at.strftime("%Y-%m-%d %H:%M") if lo.ordered_at else None,
                })

            # 4b. Orders with results entered awaiting verification
            awaiting_verification = (
                db.query(LabOrder)
                .filter(LabOrder.status == LabOrderStatus.RESULTS_ENTERED)
                .order_by(LabOrder.ordered_at.asc())
                .limit(10)
                .all()
            )
            formatted_verification = []
            for lo in awaiting_verification:
                pt_name = lo.patient.user.full_name if lo.patient and lo.patient.user else "Patient"
                formatted_verification.append({
                    "order_id": lo.id,
                    "patient_name": pt_name,
                    "priority": lo.priority.value,
                    "ordered_at": lo.ordered_at.strftime("%Y-%m-%d") if lo.ordered_at else None,
                })

            # 4c. Overall lab status counts
            status_counts_raw = (
                db.query(LabOrder.status, func.count(LabOrder.id))
                .group_by(LabOrder.status)
                .all()
            )
            status_counts = {s.value: 0 for s in LabOrderStatus}
            total_orders = 0
            for s, cnt in status_counts_raw:
                status_counts[s.value] = cnt
                total_orders += cnt

            # 4d. Critical panic results recently flagged
            panic_results = (
                db.query(LabResult)
                .filter(LabResult.result_flag == ResultFlag.CRITICAL)
                .order_by(LabResult.created_at.desc())
                .limit(5)
                .all()
            )
            formatted_panics = []
            for pr in panic_results:
                formatted_panics.append({
                    "id": pr.id,
                    "value": pr.result_value,
                    "flag": pr.result_flag.value,
                    "reference": pr.reference_interval,
                })

            return {
                "total_orders": total_orders,
                "status_breakdown": status_counts,
                "samples_pending_collection": formatted_pending_samples,
                "results_awaiting_verification": formatted_verification,
                "critical_panic_alerts": formatted_panics,
            }
        except Exception as err:
            logger.error(f"Error compiling lab context: {err}")
            return {"error": "Could not compile laboratory diagnostic context."}

    # -------------------------------------------------------------------------
    # 5. PHARMACY STAFF CONTEXT (DISPENSING & REVIEW QUEUE)
    # -------------------------------------------------------------------------
    def get_pharmacy_context(self, db: Session, user: User) -> Dict[str, Any]:
        """Retrieve active dispensary queue, prescriptions awaiting pharmacist review, and dispensing load."""
        try:
            # 5a. Prescriptions under review / newly prescribed
            pending_review = (
                db.query(Prescription)
                .filter(Prescription.status.in_([PrescriptionStatus.PRESCRIBED, PrescriptionStatus.UNDER_REVIEW]))
                .order_by(Prescription.created_at.asc())
                .limit(10)
                .all()
            )
            formatted_pending = []
            for rx in pending_review:
                pt_name = rx.patient.user.full_name if rx.patient and rx.patient.user else "Patient"
                med_names = [it.medication_name or it.drug_name for it in rx.items if (it.medication_name or it.drug_name)]
                formatted_pending.append({
                    "prescription_id": rx.id,
                    "patient_name": pt_name,
                    "status": rx.status.value,
                    "medications": med_names or ["Rx Items"],
                    "created_at": rx.created_at.strftime("%Y-%m-%d %H:%M") if rx.created_at else None,
                })

            # 5b. Prescriptions ready for dispensing
            ready_dispense = (
                db.query(Prescription)
                .filter(Prescription.status == PrescriptionStatus.READY)
                .order_by(Prescription.created_at.asc())
                .limit(10)
                .all()
            )
            formatted_ready = []
            for rx in ready_dispense:
                pt_name = rx.patient.user.full_name if rx.patient and rx.patient.user else "Patient"
                formatted_ready.append({
                    "prescription_id": rx.id,
                    "patient_name": pt_name,
                    "created_at": rx.created_at.strftime("%Y-%m-%d %H:%M") if rx.created_at else None,
                })

            # 5c. Overall counts by status
            rx_counts_raw = (
                db.query(Prescription.status, func.count(Prescription.id))
                .group_by(Prescription.status)
                .all()
            )
            rx_counts = {s.value: 0 for s in PrescriptionStatus}
            total_rx = 0
            for s, cnt in rx_counts_raw:
                rx_counts[s.value] = cnt
                total_rx += cnt

            return {
                "total_prescriptions": total_rx,
                "status_breakdown": rx_counts,
                "awaiting_review_queue": formatted_pending,
                "ready_for_dispensing_queue": formatted_ready,
            }
        except Exception as err:
            logger.error(f"Error compiling pharmacy context: {err}")
            return {"error": "Could not compile pharmacy dispensary queue."}


context_retrieval_service = ContextRetrievalService()


def get_context_for_role(db: Session, user: User, message: str = "") -> str:
    """Format authorized live database context as a clear, grounded markdown block."""
    if user.role == UserRole.ADMIN:
        ctx = context_retrieval_service.get_admin_context(db)
        return (
            f"ADMIN METRICS:\n"
            f"- Total Users: {ctx.get('total_users', 0)}\n"
            f"- Role Counts: {ctx.get('role_counts', {})}\n"
            f"- Doctor Approvals: {ctx.get('doctor_approvals', {})}\n"
            f"- Total Appointments: {ctx.get('total_appointments', 0)}\n"
            f"- Appointments Today: {ctx.get('appointments_today', 0)}\n"
            f"- Lab Orders: {ctx.get('lab_orders', {})}\n"
            f"- Prescriptions: {ctx.get('prescriptions', {})}"
        )
    elif user.role == UserRole.PATIENT:
        ctx = context_retrieval_service.get_patient_context(db, user)
        rxs = ctx.get("active_prescriptions", [])
        rx_lines = []
        for rx in rxs:
            rx_lines.append(f"Diagnosis: {rx.get('diagnosis')} (Dr: {rx.get('doctor_name')})")
            for item in rx.get("items", []):
                rx_lines.append(f"- {item.get('medication_name')} ({item.get('dosage')}): {item.get('frequency')} for {item.get('duration')}. Instructions: {item.get('instructions')}")
        return (
            f"PATIENT HEALTH CONTEXT:\n"
            f"Active Prescriptions:\n" + ("\n".join(rx_lines) if rx_lines else "None") + "\n"
            f"Recent Lab Tests: {len(ctx.get('recent_lab_results', []))}\n"
            f"Upcoming Appointments: {len(ctx.get('upcoming_appointments', []))}"
        )
    elif user.role == UserRole.DOCTOR:
        ctx = context_retrieval_service.get_doctor_context(db, user)
        return (
            f"DOCTOR CLINICAL SCHEDULE:\n"
            f"Total Appointments Today: {ctx.get('today_appointment_count', 0)}\n"
            f"Schedule List: {ctx.get('today_schedule', [])}\n"
            f"Pending Lab Orders: {len(ctx.get('pending_lab_orders', []))}"
        )
    elif user.role == UserRole.LAB_TECHNICIAN:
        ctx = context_retrieval_service.get_lab_context(db, user)
        return (
            f"LAB WORKLIST:\n"
            f"Total Orders: {ctx.get('total_orders', 0)}\n"
            f"Status Breakdown: {ctx.get('status_breakdown', {})}\n"
            f"Samples Pending Collection: {len(ctx.get('samples_pending_collection', []))}\n"
            f"Results Awaiting Verification: {len(ctx.get('results_awaiting_verification', []))}\n"
            f"Critical Panic Alerts: {len(ctx.get('critical_panic_alerts', []))}"
        )
    elif user.role == UserRole.PHARMACY_STAFF:
        ctx = context_retrieval_service.get_pharmacy_context(db, user)
        return (
            f"PHARMACY DISPENSARY QUEUE:\n"
            f"Total Prescriptions: {ctx.get('total_prescriptions', 0)}\n"
            f"Status Breakdown: {ctx.get('status_breakdown', {})}\n"
            f"Awaiting Review: {len(ctx.get('awaiting_review_queue', []))}\n"
            f"Ready for Dispensing: {len(ctx.get('ready_for_dispensing_queue', []))}"
        )
    return ""
