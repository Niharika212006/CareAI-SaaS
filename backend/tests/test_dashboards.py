"""Comprehensive automated tests for Role-Based Real-Time Dashboards & Analytics."""
from datetime import date, time, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.patient import PatientProfile
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription, PrescriptionItem
from app.models.ai_report import AIAnalysisReport, InteractionSeverity
from app.models.availability import DoctorAvailability, DoctorUnavailableDate
from app.core.security import get_password_hash, create_access_token


def create_user(
    db: Session,
    email: str,
    role: UserRole,
    full_name: str,
    approval_status: DoctorApprovalStatus = DoctorApprovalStatus.APPROVED,
) -> User:
    """Helper to persist user and corresponding profile."""
    user = User(
        email=email.lower(),
        hashed_password=get_password_hash("TestPassword123!"),
        full_name=full_name,
        role=role,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.flush()

    if role == UserRole.PATIENT:
        profile = PatientProfile(
            user_id=user.id,
            blood_group="O+",
            allergies=[{"name": "Penicillin", "type": "MEDICATION", "severity": "CRITICAL"}],
            chronic_conditions=["Hypertension"],
            current_medications=[{"name": "Lisinopril", "dosage": "10mg"}],
            emergency_contact_phone="+1-555-123-4567",
        )
        db.add(profile)
    elif role == UserRole.DOCTOR:
        profile = DoctorProfile(
            user_id=user.id,
            specialization="Cardiology",
            license_number=f"LIC-DASH-{user.id}",
            approval_status=approval_status,
            consultation_fee=150.00,
        )
        db.add(profile)

    db.commit()
    db.refresh(user)
    return user


def get_token_header(user: User) -> dict:
    """Generate bearer token headers."""
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Patient Dashboard Tests
# ---------------------------------------------------------------------------

def test_patient_can_access_own_dashboard(client: TestClient, db_session: Session):
    patient = create_user(db_session, "dash_patient1@example.com", UserRole.PATIENT, "Patient One")
    doc = create_user(db_session, "dash_doc1@example.com", UserRole.DOCTOR, "Dr. Cardio")

    pat_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doc.id).first()

    # Create 1 future upcoming appointment and 1 completed
    future_time = datetime.now() + timedelta(days=2)
    past_time = datetime.now() - timedelta(days=2)

    appt_upcoming = Appointment(
        patient_id=pat_prof.id,
        doctor_id=doc_prof.id,
        scheduled_start=future_time,
        scheduled_end=future_time + timedelta(minutes=30),
        status=AppointmentStatus.CONFIRMED,
        reason="Routine Checkup",
    )
    appt_completed = Appointment(
        patient_id=pat_prof.id,
        doctor_id=doc_prof.id,
        scheduled_start=past_time,
        scheduled_end=past_time + timedelta(minutes=30),
        status=AppointmentStatus.COMPLETED,
        reason="Blood Pressure Review",
    )
    db_session.add(appt_upcoming)
    db_session.add(appt_completed)
    db_session.commit()

    res = client.get("/api/v1/dashboard/patient", headers=get_token_header(patient))
    assert res.status_code == 200
    data = res.json()

    assert "stats" in data
    assert data["stats"]["total_appointments"] == 2
    assert data["stats"]["upcoming_appointments"] == 1
    assert data["stats"]["completed_appointments"] == 1

    assert data["next_appointment"] is not None
    assert data["next_appointment"]["doctor_specialization"] == "Cardiology"
    assert data["next_appointment"]["reason"] == "Routine Checkup"

    assert data["medical_profile_status"]["is_complete"] is True
    assert data["medical_profile_status"]["has_allergies_recorded"] is True
    assert data["medical_profile_status"]["allergies_count"] == 1


def test_patient_dashboard_recent_prescriptions(client: TestClient, db_session: Session):
    patient = create_user(db_session, "dash_patient2@example.com", UserRole.PATIENT, "Patient Two")
    doc = create_user(db_session, "dash_doc2@example.com", UserRole.DOCTOR, "Dr. Specialist")
    pat_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doc.id).first()

    # Create completed appointment & prescription
    appt = Appointment(
        patient_id=pat_prof.id,
        doctor_id=doc_prof.id,
        scheduled_start=datetime.now() - timedelta(days=1),
        scheduled_end=datetime.now() - timedelta(days=1, minutes=-30),
        status=AppointmentStatus.COMPLETED,
    )
    db_session.add(appt)
    db_session.flush()

    rx = Prescription(
        appointment_id=appt.id,
        doctor_id=doc_prof.id,
        patient_id=pat_prof.id,
        diagnosis="Acute Bronchitis",
        valid_until=date.today() + timedelta(days=30),
    )
    db_session.add(rx)
    db_session.flush()

    item = PrescriptionItem(
        prescription_id=rx.id,
        medication_name="Amoxicillin",
        drug_name="Amoxicillin",
        dosage="500mg",
        frequency="Three times daily",
        duration="7 days",
    )
    db_session.add(item)

    report = AIAnalysisReport(
        prescription_id=rx.id,
        patient_id=pat_prof.id,
        overall_risk_level=InteractionSeverity.HIGH,
        total_findings=1,
        clinical_summary="Allergy alert",
        analysis_status="COMPLETED",
    )
    db_session.add(report)
    db_session.commit()

    res = client.get("/api/v1/dashboard/patient", headers=get_token_header(patient))
    assert res.status_code == 200
    data = res.json()

    assert data["stats"]["active_prescriptions"] == 1
    assert len(data["recent_prescriptions"]) == 1
    assert data["recent_prescriptions"][0]["diagnosis"] == "Acute Bronchitis"
    assert data["recent_prescriptions"][0]["medications_count"] == 1
    assert data["recent_prescriptions"][0]["has_ai_report"] is True
    assert data["recent_prescriptions"][0]["ai_risk_level"] == "HIGH"
    assert data["ai_safety_summary"]["high_risk_findings_count"] == 1


# ---------------------------------------------------------------------------
# Doctor Dashboard Tests
# ---------------------------------------------------------------------------

def test_doctor_can_access_own_dashboard(client: TestClient, db_session: Session):
    doc = create_user(db_session, "dash_doc3@example.com", UserRole.DOCTOR, "Dr. Marcus")
    patient = create_user(db_session, "dash_patient3@example.com", UserRole.PATIENT, "Pat Three")
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doc.id).first()
    pat_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()

    # 1 today appointment, 1 pending request
    now = datetime.now()
    appt_today = Appointment(
        patient_id=pat_prof.id,
        doctor_id=doc_prof.id,
        scheduled_start=now.replace(hour=14, minute=0, second=0),
        scheduled_end=now.replace(hour=14, minute=30, second=0),
        status=AppointmentStatus.CONFIRMED,
        reason="Follow up",
    )
    appt_pending = Appointment(
        patient_id=pat_prof.id,
        doctor_id=doc_prof.id,
        scheduled_start=now + timedelta(days=1),
        scheduled_end=now + timedelta(days=1, minutes=30),
        status=AppointmentStatus.PENDING,
        reason="Consultation Request",
    )
    db_session.add(appt_today)
    db_session.add(appt_pending)

    # Doctor availability schedule
    avail = DoctorAvailability(
        doctor_id=doc_prof.id,
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(17, 0),
        slot_duration_minutes=30,
        is_active=True,
    )
    db_session.add(avail)
    db_session.commit()

    res = client.get("/api/v1/dashboard/doctor", headers=get_token_header(doc))
    assert res.status_code == 200
    data = res.json()

    assert data["stats"]["today_appointments"] == 1
    assert data["stats"]["total_patients"] == 1
    assert len(data["today_schedule"]) == 1
    assert data["today_schedule"][0]["patient_name"] == "Pat Three"

    assert data["pending_actions"]["pending_appointment_requests"] == 1
    assert data["availability_summary"]["has_active_schedule"] is True
    assert data["availability_summary"]["active_days_count"] == 1


# ---------------------------------------------------------------------------
# Admin Dashboard Tests
# ---------------------------------------------------------------------------

def test_admin_platform_metrics(client: TestClient, db_session: Session):
    admin = create_user(db_session, "dash_admin1@example.com", UserRole.ADMIN, "Admin Super")

    res = client.get("/api/v1/dashboard/admin", headers=get_token_header(admin))
    assert res.status_code == 200
    data = res.json()

    assert "platform_stats" in data
    assert "doctor_summary" in data
    assert "appointment_summary" in data
    assert "ai_safety_metrics" in data
    assert "recent_activity" in data
    assert isinstance(data["platform_stats"]["total_users"], int)
    assert isinstance(data["recent_activity"], list)


# ---------------------------------------------------------------------------
# Security & RBAC Isolation Tests
# ---------------------------------------------------------------------------

def test_patient_cannot_access_doctor_or_admin_dashboard(client: TestClient, db_session: Session):
    patient = create_user(db_session, "dash_sec_pat@example.com", UserRole.PATIENT, "Pat Sec")

    # Patient -> Doctor Dashboard (403 Forbidden)
    res_doc = client.get("/api/v1/dashboard/doctor", headers=get_token_header(patient))
    assert res_doc.status_code == 403

    # Patient -> Admin Dashboard (403 Forbidden)
    res_adm = client.get("/api/v1/dashboard/admin", headers=get_token_header(patient))
    assert res_adm.status_code == 403


def test_doctor_cannot_access_patient_or_admin_dashboard(client: TestClient, db_session: Session):
    doc = create_user(db_session, "dash_sec_doc@example.com", UserRole.DOCTOR, "Dr. Sec")

    # Doctor -> Patient Dashboard (403 Forbidden)
    res_pat = client.get("/api/v1/dashboard/patient", headers=get_token_header(doc))
    assert res_pat.status_code == 403

    # Doctor -> Admin Dashboard (403 Forbidden)
    res_adm = client.get("/api/v1/dashboard/admin", headers=get_token_header(doc))
    assert res_adm.status_code == 403


def test_admin_cannot_access_patient_or_doctor_dashboard(client: TestClient, db_session: Session):
    admin = create_user(db_session, "dash_sec_admin@example.com", UserRole.ADMIN, "Admin Sec")

    # Admin -> Patient Dashboard (403 Forbidden)
    res_pat = client.get("/api/v1/dashboard/patient", headers=get_token_header(admin))
    assert res_pat.status_code == 403

    # Admin -> Doctor Dashboard (403 Forbidden)
    res_doc = client.get("/api/v1/dashboard/doctor", headers=get_token_header(admin))
    assert res_doc.status_code == 403


def test_unauthenticated_dashboard_rejected(client: TestClient):
    assert client.get("/api/v1/dashboard/patient").status_code in [401, 403]
    assert client.get("/api/v1/dashboard/doctor").status_code in [401, 403]
    assert client.get("/api/v1/dashboard/admin").status_code in [401, 403]
