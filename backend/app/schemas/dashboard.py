"""Schemas for Role-Based Real-Time Dashboard & Analytics."""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

from app.models.appointment import AppointmentStatus
from app.models.ai_report import InteractionSeverity


# ---------------------------------------------------------------------------
# Common / Sub-Items
# ---------------------------------------------------------------------------

class DashboardAppointmentItem(BaseModel):
    """Summarized appointment view for dashboards."""
    id: int
    doctor_id: int
    doctor_name: str
    doctor_specialization: str
    doctor_consultation_fee: float
    patient_id: int
    patient_name: str
    scheduled_start: datetime
    scheduled_end: datetime
    status: AppointmentStatus
    reason: Optional[str] = None
    meeting_link: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DashboardPrescriptionItem(BaseModel):
    """Summarized prescription item for patient dashboard."""
    id: int
    appointment_id: int
    doctor_name: str
    doctor_specialization: str
    diagnosis: str
    medications_count: int
    created_at: datetime
    valid_until: Optional[date] = None
    has_ai_report: bool = False
    ai_risk_level: Optional[InteractionSeverity] = None

    model_config = ConfigDict(from_attributes=True)


class DashboardDoctorScheduleItem(BaseModel):
    """Today's schedule appointment item for doctor dashboard."""
    id: int
    patient_id: int
    patient_name: str
    scheduled_start: datetime
    scheduled_end: datetime
    status: AppointmentStatus
    reason: Optional[str] = None
    is_past: bool = False

    model_config = ConfigDict(from_attributes=True)


class AdminRecentActivityItem(BaseModel):
    """Sanitized recent platform activity event for admin dashboard."""
    event_type: str  # "USER_REGISTERED", "DOCTOR_APPLICATION", "APPOINTMENT_BOOKED", "AI_ANALYSIS"
    title: str
    description: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Patient Dashboard Schemas
# ---------------------------------------------------------------------------

class PatientDashboardStats(BaseModel):
    total_appointments: int
    upcoming_appointments: int
    completed_appointments: int
    active_prescriptions: int


class PatientAISafetySummary(BaseModel):
    total_analyzed_prescriptions: int
    high_risk_findings_count: int
    latest_analysis_status: Optional[str] = None
    latest_overall_risk: Optional[InteractionSeverity] = None


class PatientMedicalProfileStatus(BaseModel):
    is_complete: bool
    has_allergies_recorded: bool
    allergies_count: int
    has_conditions_recorded: bool
    conditions_count: int
    has_medications_recorded: bool
    medications_count: int
    has_emergency_contact: bool


class PatientDashboardResponse(BaseModel):
    stats: PatientDashboardStats
    next_appointment: Optional[DashboardAppointmentItem] = None
    recent_prescriptions: List[DashboardPrescriptionItem] = []
    ai_safety_summary: PatientAISafetySummary
    medical_profile_status: PatientMedicalProfileStatus

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Doctor Dashboard Schemas
# ---------------------------------------------------------------------------

class DoctorDashboardStats(BaseModel):
    today_appointments: int
    upcoming_appointments: int
    completed_consultations: int
    total_patients: int
    prescriptions_issued: int


class DoctorPendingActions(BaseModel):
    pending_appointment_requests: int
    confirmed_awaiting_consultation: int
    completed_awaiting_prescription: int


class DoctorAvailabilitySummary(BaseModel):
    has_active_schedule: bool
    active_days_count: int
    slot_duration_minutes: Optional[int] = None
    next_unavailable_date: Optional[date] = None
    next_unavailable_reason: Optional[str] = None


class DoctorDashboardResponse(BaseModel):
    stats: DoctorDashboardStats
    today_schedule: List[DashboardDoctorScheduleItem] = []
    pending_actions: DoctorPendingActions
    availability_summary: DoctorAvailabilitySummary
    recent_patient_activity: List[DashboardAppointmentItem] = []

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Admin Dashboard Schemas
# ---------------------------------------------------------------------------

class AdminPlatformStats(BaseModel):
    total_users: int
    total_patients: int
    total_doctors: int
    approved_doctors: int
    pending_doctor_approvals: int
    rejected_doctors: int
    total_appointments: int
    completed_appointments: int
    cancelled_appointments: int
    total_prescriptions: int
    total_ai_analyses: int


class AdminDoctorSummary(BaseModel):
    pending_count: int
    approved_count: int
    rejected_count: int


class AdminAppointmentSummary(BaseModel):
    pending_count: int
    confirmed_count: int
    completed_count: int
    cancelled_count: int
    rejected_count: int


class AdminAISafetyMetrics(BaseModel):
    total_reports: int
    critical_risk_count: int
    high_risk_count: int
    moderate_risk_count: int
    low_risk_count: int
    none_risk_count: int
    total_findings_detected: int


class AdminDashboardResponse(BaseModel):
    platform_stats: AdminPlatformStats
    doctor_summary: AdminDoctorSummary
    appointment_summary: AdminAppointmentSummary
    ai_safety_metrics: AdminAISafetyMetrics
    recent_activity: List[AdminRecentActivityItem] = []

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Lab Technician Dashboard Schemas
# ---------------------------------------------------------------------------

class LabTechnicianStats(BaseModel):
    pending_samples: int = 0
    samples_collected_today: int = 0
    tests_in_progress: int = 0
    results_awaiting_verification: int = 0
    critical_alerts_count: int = 0
    completed_tests_today: int = 0
    total_samples_processed: int = 0
    # Backward compatible aliases
    pending_lab_tests: int = 0
    critical_alerts: int = 0


class LabTechnicianDashboardResponse(BaseModel):
    role: str = "LAB_TECHNICIAN"
    message: str = "Lab Technician Clinical Workspace Active"
    stats: LabTechnicianStats = LabTechnicianStats()
    pending_tasks: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Pharmacy Staff Dashboard Schemas
# ---------------------------------------------------------------------------

class PharmacyStats(BaseModel):
    pending_dispensations: int = 0
    under_review_count: int = 0
    ready_for_pickup_count: int = 0
    dispensed_today: int = 0
    prescriptions_verified_today: int = 0
    low_stock_alerts: int = 0
    total_medications_dispensed: int = 0
    high_risk_alerts_count: int = 0


class PharmacyDashboardResponse(BaseModel):
    role: str = "PHARMACY_STAFF"
    message: str = "Pharmacy Staff Clinical Workspace Active"
    stats: PharmacyStats = PharmacyStats()
    pending_dispensations: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)


