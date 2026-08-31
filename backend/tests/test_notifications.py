"""Comprehensive automated tests for In-App Notifications and Alerts."""
from datetime import date, time, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.patient import PatientProfile
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription, PrescriptionItem
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.models.ai_report import InteractionSeverity
from app.core.security import get_password_hash, create_access_token
from app.services.notification_service import notification_service
from app.services.appointment_service import appointment_service
from app.services.doctor_service import doctor_service
from app.services.prescription_service import prescription_service
from app.services.ai_service import ai_service
from app.schemas.appointment import AppointmentCreate
from app.schemas.doctor import DoctorApprovalUpdate
from app.schemas.prescription import PrescriptionCreate, PrescriptionItemCreate


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
            blood_group="A+",
            allergies=[{"name": "Penicillin", "type": "MEDICATION", "severity": "CRITICAL"}],
        )
        db.add(profile)
    elif role == UserRole.DOCTOR:
        profile = DoctorProfile(
            user_id=user.id,
            specialization="General Medicine",
            license_number=f"LIC-NOTIF-{user.id}",
            approval_status=approval_status,
            consultation_fee=100.00,
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
# Core Notification CRUD & Ordering Tests
# ---------------------------------------------------------------------------

def test_user_receives_own_notifications_ordered_newest_first(client: TestClient, db_session: Session):
    user1 = create_user(db_session, "notif_user1@example.com", UserRole.PATIENT, "User One")
    user2 = create_user(db_session, "notif_user2@example.com", UserRole.PATIENT, "User Two")

    # Seed notifications for user1
    n1 = notification_service.create_notification(
        db=db_session,
        user_id=user1.id,
        title="First Notice",
        message="Older message",
        notification_type=NotificationType.SYSTEM,
    )
    n2 = notification_service.create_notification(
        db=db_session,
        user_id=user1.id,
        title="Second Notice",
        message="Newer message",
        notification_type=NotificationType.APPOINTMENT,
    )
    # Seed notification for user2
    notification_service.create_notification(
        db=db_session,
        user_id=user2.id,
        title="User 2 Notice",
        message="Private to user 2",
    )

    res = client.get("/api/v1/notifications", headers=get_token_header(user1))
    assert res.status_code == 200
    data = res.json()

    assert data["total"] == 2
    assert data["unread_count"] == 2
    assert len(data["items"]) == 2
    # Check ordering: newest (n2) first
    assert data["items"][0]["title"] == "Second Notice"
    assert data["items"][1]["title"] == "First Notice"


def test_unread_count_endpoint(client: TestClient, db_session: Session):
    user = create_user(db_session, "notif_unread@example.com", UserRole.PATIENT, "Unread Tester")

    notification_service.create_notification(db=db_session, user_id=user.id, title="Alert 1", message="Unread 1")
    notification_service.create_notification(db=db_session, user_id=user.id, title="Alert 2", message="Unread 2")

    res = client.get("/api/v1/notifications/unread-count", headers=get_token_header(user))
    assert res.status_code == 200
    assert res.json()["unread_count"] == 2


def test_mark_single_notification_as_read(client: TestClient, db_session: Session):
    user = create_user(db_session, "notif_mark_single@example.com", UserRole.PATIENT, "Mark Single")

    notif = notification_service.create_notification(
        db=db_session,
        user_id=user.id,
        title="Read Me",
        message="Please read",
    )
    assert notif.is_read is False

    res = client.patch(f"/api/v1/notifications/{notif.id}/read", headers=get_token_header(user))
    assert res.status_code == 200
    data = res.json()
    assert data["is_read"] is True
    assert data["read_at"] is not None

    # Check unread count is now 0
    count_res = client.get("/api/v1/notifications/unread-count", headers=get_token_header(user))
    assert count_res.json()["unread_count"] == 0


def test_mark_all_notifications_read(client: TestClient, db_session: Session):
    user = create_user(db_session, "notif_mark_all@example.com", UserRole.PATIENT, "Mark All")

    notification_service.create_notification(db=db_session, user_id=user.id, title="Alert A", message="Msg A")
    notification_service.create_notification(db=db_session, user_id=user.id, title="Alert B", message="Msg B")

    res = client.patch("/api/v1/notifications/read-all", headers=get_token_header(user))
    assert res.status_code == 200
    assert res.json()["updated_count"] == 2

    # Verify unread count is 0
    count_res = client.get("/api/v1/notifications/unread-count", headers=get_token_header(user))
    assert count_res.json()["unread_count"] == 0


# ---------------------------------------------------------------------------
# Security & Ownership Isolation Tests
# ---------------------------------------------------------------------------

def test_user_cannot_modify_or_read_another_users_notification(client: TestClient, db_session: Session):
    victim = create_user(db_session, "notif_victim@example.com", UserRole.PATIENT, "Victim")
    attacker = create_user(db_session, "notif_attacker@example.com", UserRole.PATIENT, "Attacker")

    victim_notif = notification_service.create_notification(
        db=db_session,
        user_id=victim.id,
        title="Confidential",
        message="Personal clinical notice",
    )

    # Attacker tries to mark victim's notification as read -> 403 Forbidden
    res = client.patch(
        f"/api/v1/notifications/{victim_notif.id}/read",
        headers=get_token_header(attacker),
    )
    assert res.status_code == 403

    # Attacker tries to delete victim's notification -> 403 Forbidden
    res_del = client.delete(
        f"/api/v1/notifications/{victim_notif.id}",
        headers=get_token_header(attacker),
    )
    assert res_del.status_code == 403


def test_unauthenticated_access_is_rejected(client: TestClient):
    assert client.get("/api/v1/notifications").status_code in [401, 403]
    assert client.get("/api/v1/notifications/unread-count").status_code in [401, 403]
    assert client.patch("/api/v1/notifications/1/read").status_code in [401, 403]
    assert client.patch("/api/v1/notifications/read-all").status_code in [401, 403]


# ---------------------------------------------------------------------------
# Lifecycle Integration Tests (Event Triggers)
# ---------------------------------------------------------------------------

def test_appointment_booking_creates_notifications_for_patient_and_doctor(client: TestClient, db_session: Session):
    patient = create_user(db_session, "notif_book_pat@example.com", UserRole.PATIENT, "Booking Patient")
    doctor = create_user(db_session, "notif_book_doc@example.com", UserRole.DOCTOR, "Dr. Bookable")
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()

    future_start = datetime.now() + timedelta(days=3)
    appt_in = AppointmentCreate(
        doctor_id=doc_prof.id,
        scheduled_start=future_start,
        scheduled_end=future_start + timedelta(minutes=30),
        reason="General Health Consultation",
    )

    appointment_service.create_appointment(
        db=db_session,
        patient_user=patient,
        appointment_in=appt_in,
    )

    # Check Patient notifications
    pat_res = client.get("/api/v1/notifications", headers=get_token_header(patient))
    assert pat_res.status_code == 200
    pat_data = pat_res.json()
    assert pat_data["total"] >= 1
    assert any("Appointment Requested" in item["title"] for item in pat_data["items"])

    # Check Doctor notifications
    doc_res = client.get("/api/v1/notifications", headers=get_token_header(doctor))
    assert doc_res.status_code == 200
    doc_data = doc_res.json()
    assert doc_data["total"] >= 1
    assert any("New Appointment Request" in item["title"] for item in doc_data["items"])


def test_appointment_confirmation_creates_high_priority_notification(client: TestClient, db_session: Session):
    patient = create_user(db_session, "notif_conf_pat@example.com", UserRole.PATIENT, "Confirm Patient")
    doctor = create_user(db_session, "notif_conf_doc@example.com", UserRole.DOCTOR, "Dr. Confirmer")
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()

    future_start = datetime.now() + timedelta(days=2)
    appt_in = AppointmentCreate(
        doctor_id=doc_prof.id,
        scheduled_start=future_start,
        scheduled_end=future_start + timedelta(minutes=30),
        reason="Follow Up",
    )
    appt = appointment_service.create_appointment(
        db=db_session,
        patient_user=patient,
        appointment_in=appt_in,
    )

    # Clear prior notifications
    notification_service.mark_all_notifications_read(db_session, patient.id)

    # Doctor confirms appointment
    appointment_service.confirm_appointment(db=db_session, appointment_id=appt.id, current_user=doctor)

    # Check patient notification
    res = client.get("/api/v1/notifications", headers=get_token_header(patient))
    assert res.status_code == 200
    items = res.json()["items"]
    confirmed_notif = next((i for i in items if i["title"] == "Appointment Confirmed"), None)
    assert confirmed_notif is not None
    assert confirmed_notif["priority"] == "HIGH"


def test_appointment_cancellation_creates_notifications(client: TestClient, db_session: Session):
    patient = create_user(db_session, "notif_canc_pat@example.com", UserRole.PATIENT, "Cancel Patient")
    doctor = create_user(db_session, "notif_canc_doc@example.com", UserRole.DOCTOR, "Dr. Canceller")
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()

    future_start = datetime.now() + timedelta(days=4)
    appt = appointment_service.create_appointment(
        db=db_session,
        patient_user=patient,
        appointment_in=AppointmentCreate(
            doctor_id=doc_prof.id,
            scheduled_start=future_start,
            scheduled_end=future_start + timedelta(minutes=30),
            reason="Checkup",
        ),
    )

    appointment_service.cancel_appointment(
        db=db_session,
        appointment_id=appt.id,
        current_user=patient,
        cancellation_reason="Schedule conflict",
    )

    # Both patient and doctor should have cancellation notifications
    pat_res = client.get("/api/v1/notifications", headers=get_token_header(patient))
    assert any(i["title"] == "Appointment Cancelled" for i in pat_res.json()["items"])

    doc_res = client.get("/api/v1/notifications", headers=get_token_header(doctor))
    assert any(i["title"] == "Appointment Cancelled" for i in doc_res.json()["items"])


def test_doctor_approval_creates_notification(client: TestClient, db_session: Session):
    doctor = create_user(
        db_session,
        "notif_pending_doc@example.com",
        UserRole.DOCTOR,
        "Dr. Pending",
        approval_status=DoctorApprovalStatus.PENDING,
    )
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()

    # Admin reviews and approves
    doctor_service.review_approval(
        db=db_session,
        profile=doc_prof,
        approval_data=DoctorApprovalUpdate(approval_status=DoctorApprovalStatus.APPROVED),
    )

    doc_res = client.get("/api/v1/notifications", headers=get_token_header(doctor))
    assert doc_res.status_code == 200
    items = doc_res.json()["items"]
    approval_notif = next((i for i in items if i["title"] == "Doctor Profile Approved"), None)
    assert approval_notif is not None
    assert approval_notif["priority"] == "HIGH"


def test_prescription_creation_creates_notification(client: TestClient, db_session: Session):
    patient = create_user(db_session, "notif_rx_pat@example.com", UserRole.PATIENT, "Rx Patient")
    doctor = create_user(db_session, "notif_rx_doc@example.com", UserRole.DOCTOR, "Dr. Prescriber")
    pat_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()

    past_start = datetime.now() - timedelta(days=1)
    appt = Appointment(
        patient_id=pat_prof.id,
        doctor_id=doc_prof.id,
        scheduled_start=past_start,
        scheduled_end=past_start + timedelta(minutes=30),
        status=AppointmentStatus.COMPLETED,
    )
    db_session.add(appt)
    db_session.commit()

    rx_in = PrescriptionCreate(
        appointment_id=appt.id,
        diagnosis="Bacterial Pharyngitis",
        items=[
            PrescriptionItemCreate(
                medication_name="Azithromycin",
                drug_name="Azithromycin",
                dosage="500mg",
                frequency="Once daily",
                duration="3 days",
            )
        ],
    )
    prescription_service.create_prescription(db=db_session, doctor_user=doctor, prescription_in=rx_in)

    pat_res = client.get("/api/v1/notifications", headers=get_token_header(patient))
    assert pat_res.status_code == 200
    items = pat_res.json()["items"]
    rx_notif = next((i for i in items if i["title"] == "New Prescription Available"), None)
    assert rx_notif is not None
    assert rx_notif["notification_type"] == "PRESCRIPTION"


def test_high_risk_ai_safety_result_creates_alert_notification(client: TestClient, db_session: Session):
    patient = create_user(db_session, "notif_ai_pat@example.com", UserRole.PATIENT, "AI Patient")
    doctor = create_user(db_session, "notif_ai_doc@example.com", UserRole.DOCTOR, "Dr. AI Reviewer")
    pat_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()

    # Patient has Penicillin allergy recorded
    past_start = datetime.now() - timedelta(days=1)
    appt = Appointment(
        patient_id=pat_prof.id,
        doctor_id=doc_prof.id,
        scheduled_start=past_start,
        scheduled_end=past_start + timedelta(minutes=30),
        status=AppointmentStatus.COMPLETED,
    )
    db_session.add(appt)
    db_session.flush()

    # Prescribe Amoxicillin (Penicillin class -> triggers CRITICAL/HIGH allergy alert)
    rx = Prescription(
        appointment_id=appt.id,
        doctor_id=doc_prof.id,
        patient_id=pat_prof.id,
        diagnosis="Otitis Media",
    )
    db_session.add(rx)
    db_session.flush()

    item = PrescriptionItem(
        prescription_id=rx.id,
        medication_name="Amoxicillin",
        dosage="500mg",
        frequency="Twice daily",
        duration="7 days",
    )
    db_session.add(item)
    db_session.commit()

    # Execute AI safety analysis
    ai_service.analyze_prescription(db=db_session, prescription_id=rx.id, current_user=doctor)

    # Check that high-priority safety alert notification was dispatched
    pat_res = client.get("/api/v1/notifications", headers=get_token_header(patient))
    assert pat_res.status_code == 200
    items = pat_res.json()["items"]
    safety_notif = next((i for i in items if i["title"] == "Prescription Safety Alert"), None)
    assert safety_notif is not None
    assert safety_notif["priority"] in ["HIGH", "CRITICAL"]
    assert "Potential medication safety concern detected" in safety_notif["message"]


def test_empty_notification_list_works(client: TestClient, db_session: Session):
    fresh_user = create_user(db_session, "notif_fresh@example.com", UserRole.PATIENT, "Fresh User")

    res = client.get("/api/v1/notifications", headers=get_token_header(fresh_user))
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["unread_count"] == 0
    assert data["items"] == []
