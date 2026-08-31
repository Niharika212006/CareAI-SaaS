"""Comprehensive automated tests for Appointment Management Module."""
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.patient import PatientProfile
from app.models.appointment import Appointment, AppointmentStatus
from app.core.security import get_password_hash, create_access_token


def create_test_user(db: Session, email: str, role: UserRole, full_name: str) -> User:
    """Helper to create and persist a test user."""
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
        profile = PatientProfile(user_id=user.id, blood_group="O+", allergies="Penicillin")
        db.add(profile)
    elif role == UserRole.DOCTOR:
        profile = DoctorProfile(
            user_id=user.id,
            specialization="Cardiology",
            license_number=f"DOC-LIC-{user.id}",
            approval_status=DoctorApprovalStatus.APPROVED,
            consultation_fee=150.00,
        )
        db.add(profile)

    db.commit()
    db.refresh(user)
    return user


def get_auth_headers(user: User) -> dict:
    """Generate bearer token authorization headers for a given user."""
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Test 1: Patient can book appointment
# ---------------------------------------------------------------------------
def test_patient_can_book_appointment(client: TestClient, db_session: Session):
    patient = create_test_user(db_session, "patient1@example.com", UserRole.PATIENT, "Patient One")
    doctor = create_test_user(db_session, "doctor1@example.com", UserRole.DOCTOR, "Dr. Doctor One")
    doctor_profile = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()

    future_start = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    future_end = (datetime.now(timezone.utc) + timedelta(days=2, minutes=30)).isoformat()

    payload = {
        "doctor_id": doctor_profile.id,
        "scheduled_start": future_start,
        "scheduled_end": future_end,
        "reason": "Chest pain and palpitations",
    }

    response = client.post("/api/v1/appointments", json=payload, headers=get_auth_headers(patient))
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["reason_for_visit"] == "Chest pain and palpitations"
    assert data["doctor_id"] == doctor_profile.id
    assert "id" in data


# ---------------------------------------------------------------------------
# Test 2: Unauthenticated user cannot book
# ---------------------------------------------------------------------------
def test_unauthenticated_user_cannot_book(client: TestClient, db_session: Session):
    doctor = create_test_user(db_session, "doctor2@example.com", UserRole.DOCTOR, "Dr. Doctor Two")
    doctor_profile = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()

    future_start = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    payload = {
        "doctor_id": doctor_profile.id,
        "appointment_datetime": future_start,
        "reason": "Routine checkup",
    }

    response = client.post("/api/v1/appointments", json=payload)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Test 3: Patient cannot book unapproved doctor
# ---------------------------------------------------------------------------
def test_patient_cannot_book_unapproved_doctor(client: TestClient, db_session: Session):
    patient = create_test_user(db_session, "patient3@example.com", UserRole.PATIENT, "Patient Three")
    unapproved_doc = create_test_user(db_session, "unapproved@example.com", UserRole.DOCTOR, "Dr. Unapproved")
    doc_profile = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == unapproved_doc.id).first()
    doc_profile.approval_status = DoctorApprovalStatus.PENDING
    db_session.commit()

    future_start = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    payload = {
        "doctor_id": doc_profile.id,
        "appointment_datetime": future_start,
        "reason": "Consultation",
    }

    response = client.post("/api/v1/appointments", json=payload, headers=get_auth_headers(patient))
    assert response.status_code == 400
    assert "not been approved" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Test 4: Double booking is prevented
# ---------------------------------------------------------------------------
def test_double_booking_is_prevented(client: TestClient, db_session: Session):
    patient_a = create_test_user(db_session, "patient_a@example.com", UserRole.PATIENT, "Patient A")
    patient_b = create_test_user(db_session, "patient_b@example.com", UserRole.PATIENT, "Patient B")
    doctor = create_test_user(db_session, "doctor_shared@example.com", UserRole.DOCTOR, "Dr. Shared")
    doctor_profile = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()

    future_start = datetime.now(timezone.utc) + timedelta(days=5, hours=10)
    future_end = future_start + timedelta(minutes=30)

    # First booking
    payload_a = {
        "doctor_id": doctor_profile.id,
        "scheduled_start": future_start.isoformat(),
        "scheduled_end": future_end.isoformat(),
        "reason": "Appointment A",
    }
    res_a = client.post("/api/v1/appointments", json=payload_a, headers=get_auth_headers(patient_a))
    assert res_a.status_code == 201

    # Overlapping second booking for same doctor
    payload_b = {
        "doctor_id": doctor_profile.id,
        "scheduled_start": (future_start + timedelta(minutes=10)).isoformat(),
        "scheduled_end": (future_end + timedelta(minutes=10)).isoformat(),
        "reason": "Appointment B (Overlapping)",
    }
    res_b = client.post("/api/v1/appointments", json=payload_b, headers=get_auth_headers(patient_b))
    assert res_b.status_code == 409
    assert "already has a scheduled" in res_b.json()["detail"]


# ---------------------------------------------------------------------------
# Test 5: Patient sees only own appointments
# ---------------------------------------------------------------------------
def test_patient_sees_only_own_appointments(client: TestClient, db_session: Session):
    patient_1 = create_test_user(db_session, "patient_list1@example.com", UserRole.PATIENT, "Patient List 1")
    patient_2 = create_test_user(db_session, "patient_list2@example.com", UserRole.PATIENT, "Patient List 2")
    doctor = create_test_user(db_session, "doctor_list@example.com", UserRole.DOCTOR, "Dr. List")
    doctor_profile = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()

    # Patient 1 books
    client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": doctor_profile.id,
            "appointment_datetime": (datetime.now(timezone.utc) + timedelta(days=10)).isoformat(),
            "reason": "P1 Visit",
        },
        headers=get_auth_headers(patient_1),
    )

    # Patient 2 books
    client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": doctor_profile.id,
            "appointment_datetime": (datetime.now(timezone.utc) + timedelta(days=11)).isoformat(),
            "reason": "P2 Visit",
        },
        headers=get_auth_headers(patient_2),
    )

    # Patient 1 fetches appointments
    res_p1 = client.get("/api/v1/appointments/my", headers=get_auth_headers(patient_1))
    assert res_p1.status_code == 200
    p1_items = res_p1.json()
    assert len(p1_items) == 1
    assert p1_items[0]["reason"] == "P1 Visit"


# ---------------------------------------------------------------------------
# Test 6: Doctor sees only assigned appointments
# ---------------------------------------------------------------------------
def test_doctor_sees_only_assigned_appointments(client: TestClient, db_session: Session):
    patient = create_test_user(db_session, "patient_docview@example.com", UserRole.PATIENT, "Patient DocView")
    doctor_1 = create_test_user(db_session, "doctor_assigned1@example.com", UserRole.DOCTOR, "Dr. Assigned 1")
    doctor_2 = create_test_user(db_session, "doctor_assigned2@example.com", UserRole.DOCTOR, "Dr. Assigned 2")
    doc1_profile = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_1.id).first()
    doc2_profile = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_2.id).first()

    # Book with Doctor 1
    client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": doc1_profile.id,
            "appointment_datetime": (datetime.now(timezone.utc) + timedelta(days=12)).isoformat(),
            "reason": "Consult Doctor 1",
        },
        headers=get_auth_headers(patient),
    )

    # Doctor 1 checks appointments
    res_d1 = client.get("/api/v1/appointments/doctor/my", headers=get_auth_headers(doctor_1))
    assert res_d1.status_code == 200
    assert len(res_d1.json()) == 1
    assert res_d1.json()[0]["reason"] == "Consult Doctor 1"

    # Doctor 2 checks appointments
    res_d2 = client.get("/api/v1/appointments/doctor/my", headers=get_auth_headers(doctor_2))
    assert res_d2.status_code == 200
    assert len(res_d2.json()) == 0


# ---------------------------------------------------------------------------
# Test 7: Doctor can confirm appointment
# ---------------------------------------------------------------------------
def test_doctor_can_confirm_appointment(client: TestClient, db_session: Session):
    patient = create_test_user(db_session, "patient_confirm@example.com", UserRole.PATIENT, "Patient Confirm")
    doctor = create_test_user(db_session, "doctor_confirm@example.com", UserRole.DOCTOR, "Dr. Confirm")
    doctor_profile = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()

    create_res = client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": doctor_profile.id,
            "appointment_datetime": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
            "reason": "Confirm test",
        },
        headers=get_auth_headers(patient),
    )
    appointment_id = create_res.json()["id"]

    confirm_res = client.patch(
        f"/api/v1/appointments/{appointment_id}/confirm",
        headers=get_auth_headers(doctor),
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "CONFIRMED"


# ---------------------------------------------------------------------------
# Test 8: Doctor can reject appointment
# ---------------------------------------------------------------------------
def test_doctor_can_reject_appointment(client: TestClient, db_session: Session):
    patient = create_test_user(db_session, "patient_reject@example.com", UserRole.PATIENT, "Patient Reject")
    doctor = create_test_user(db_session, "doctor_reject@example.com", UserRole.DOCTOR, "Dr. Reject")
    doctor_profile = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()

    create_res = client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": doctor_profile.id,
            "appointment_datetime": (datetime.now(timezone.utc) + timedelta(days=15)).isoformat(),
            "reason": "Reject test",
        },
        headers=get_auth_headers(patient),
    )
    appointment_id = create_res.json()["id"]

    reject_payload = {"rejection_reason": "Doctor unavailable due to surgery schedule."}
    reject_res = client.patch(
        f"/api/v1/appointments/{appointment_id}/reject",
        json=reject_payload,
        headers=get_auth_headers(doctor),
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "REJECTED"
    assert reject_res.json()["rejection_reason"] == "Doctor unavailable due to surgery schedule."


# ---------------------------------------------------------------------------
# Test 9: Doctor can complete confirmed appointment
# ---------------------------------------------------------------------------
def test_doctor_can_complete_confirmed_appointment(client: TestClient, db_session: Session):
    patient = create_test_user(db_session, "patient_comp@example.com", UserRole.PATIENT, "Patient Complete")
    doctor = create_test_user(db_session, "doctor_comp@example.com", UserRole.DOCTOR, "Dr. Complete")
    doctor_profile = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()

    create_res = client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": doctor_profile.id,
            "appointment_datetime": (datetime.now(timezone.utc) + timedelta(days=16)).isoformat(),
            "reason": "Complete test",
        },
        headers=get_auth_headers(patient),
    )
    appointment_id = create_res.json()["id"]

    # Trying to complete before confirm should fail
    fail_comp = client.patch(
        f"/api/v1/appointments/{appointment_id}/complete",
        headers=get_auth_headers(doctor),
    )
    assert fail_comp.status_code == 400

    # Confirm first
    client.patch(f"/api/v1/appointments/{appointment_id}/confirm", headers=get_auth_headers(doctor))

    # Now complete with doctor notes
    complete_payload = {"doctor_notes": "Patient examined. Prescribed rest and hydration."}
    complete_res = client.patch(
        f"/api/v1/appointments/{appointment_id}/complete",
        json=complete_payload,
        headers=get_auth_headers(doctor),
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "COMPLETED"
    assert complete_res.json()["doctor_notes"] == "Patient examined. Prescribed rest and hydration."


# ---------------------------------------------------------------------------
# Test 10: Unauthorized role receives appropriate error & cancellation flow
# ---------------------------------------------------------------------------
def test_unauthorized_role_and_patient_cancellation(client: TestClient, db_session: Session):
    patient_1 = create_test_user(db_session, "patient_auth1@example.com", UserRole.PATIENT, "Patient Auth 1")
    patient_2 = create_test_user(db_session, "patient_auth2@example.com", UserRole.PATIENT, "Patient Auth 2")
    doctor_a = create_test_user(db_session, "doctor_autha@example.com", UserRole.DOCTOR, "Dr. Auth A")
    doctor_b = create_test_user(db_session, "doctor_authb@example.com", UserRole.DOCTOR, "Dr. Auth B")
    admin = create_test_user(db_session, "admin_user@example.com", UserRole.ADMIN, "System Admin")

    doc_a_profile = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_a.id).first()

    # Patient 1 books with Doctor A
    create_res = client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": doc_a_profile.id,
            "appointment_datetime": (datetime.now(timezone.utc) + timedelta(days=20)).isoformat(),
            "reason": "Auth test appointment",
        },
        headers=get_auth_headers(patient_1),
    )
    appointment_id = create_res.json()["id"]

    # 1. Doctor B (not assigned) tries to confirm -> 403 Forbidden
    doc_b_confirm = client.patch(
        f"/api/v1/appointments/{appointment_id}/confirm",
        headers=get_auth_headers(doctor_b),
    )
    assert doc_b_confirm.status_code == 403

    # 2. Patient 2 tries to cancel Patient 1's appointment -> 403 Forbidden
    p2_cancel = client.patch(
        f"/api/v1/appointments/{appointment_id}/cancel",
        json={"cancellation_reason": "Hacking attempt"},
        headers=get_auth_headers(patient_2),
    )
    assert p2_cancel.status_code == 403

    # 3. Patient 1 cancels own appointment -> 200 OK
    p1_cancel = client.patch(
        f"/api/v1/appointments/{appointment_id}/cancel",
        json={"cancellation_reason": "Schedule conflict"},
        headers=get_auth_headers(patient_1),
    )
    assert p1_cancel.status_code == 200
    assert p1_cancel.json()["status"] == "CANCELLED"
    assert p1_cancel.json()["cancellation_reason"] == "Schedule conflict"

    # 4. Admin monitors all appointments -> 200 OK
    admin_all = client.get("/api/v1/appointments/admin/all", headers=get_auth_headers(admin))
    assert admin_all.status_code == 200
    assert len(admin_all.json()) >= 1
