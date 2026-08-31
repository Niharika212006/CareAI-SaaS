"""Comprehensive automated tests for Doctor Availability & Appointment Time Slot Management."""
from datetime import date, time, datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.patient import PatientProfile
from app.models.appointment import Appointment, AppointmentStatus
from app.models.availability import DoctorAvailability, DoctorUnavailableDate
from app.core.security import get_password_hash, create_access_token


def create_user_with_role(
    db: Session,
    email: str,
    role: UserRole,
    full_name: str,
    approval_status: DoctorApprovalStatus = DoctorApprovalStatus.APPROVED,
) -> User:
    """Helper to persist user and appropriate profile."""
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
        profile = PatientProfile(user_id=user.id)
        db.add(profile)
    elif role == UserRole.DOCTOR:
        profile = DoctorProfile(
            user_id=user.id,
            specialization="General Medicine",
            license_number=f"DOC-SCHED-{user.id}",
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
# Test 1: Doctor can create availability schedule
# ---------------------------------------------------------------------------
def test_doctor_can_create_availability(client: TestClient, db_session: Session):
    doctor = create_user_with_role(db_session, "avail_doc1@example.com", UserRole.DOCTOR, "Dr. Avail 1")

    payload = {
        "day_of_week": 0,  # Monday
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "slot_duration_minutes": 30,
        "is_active": True,
    }

    res = client.post("/api/v1/doctors/availability", json=payload, headers=get_token_header(doctor))
    assert res.status_code == 201
    data = res.json()

    assert data["day_of_week"] == 0
    assert data["day_name"] == "Monday"
    assert data["slot_duration_minutes"] == 30
    assert data["is_active"] is True


# ---------------------------------------------------------------------------
# Test 2: Doctor cannot modify another doctor's availability (403)
# ---------------------------------------------------------------------------
def test_doctor_cannot_modify_other_doctor_availability(client: TestClient, db_session: Session):
    doc_a = create_user_with_role(db_session, "avail_doc2a@example.com", UserRole.DOCTOR, "Dr. 2A")
    doc_b = create_user_with_role(db_session, "avail_doc2b@example.com", UserRole.DOCTOR, "Dr. 2B")

    # Doc A creates availability
    create_res = client.post(
        "/api/v1/doctors/availability",
        json={"day_of_week": 1, "start_time": "10:00:00", "end_time": "14:00:00", "slot_duration_minutes": 30},
        headers=get_token_header(doc_a),
    )
    avail_id = create_res.json()["id"]

    # Doc B attempts to update Doc A's schedule -> 403 Forbidden
    update_res = client.put(
        f"/api/v1/doctors/availability/{avail_id}",
        json={"start_time": "08:00:00"},
        headers=get_token_header(doc_b),
    )
    assert update_res.status_code == 403

    # Doc B attempts to delete Doc A's schedule -> 403 Forbidden
    del_res = client.delete(
        f"/api/v1/doctors/availability/{avail_id}",
        headers=get_token_header(doc_b),
    )
    assert del_res.status_code == 403


# ---------------------------------------------------------------------------
# Test 3 & 4: Patient can retrieve dynamically calculated slots
# ---------------------------------------------------------------------------
def test_patient_can_retrieve_available_slots(client: TestClient, db_session: Session):
    doc = create_user_with_role(db_session, "avail_doc3@example.com", UserRole.DOCTOR, "Dr. Avail 3")
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doc.id).first()

    # Find next Monday (in the future)
    today = date.today()
    days_ahead = (0 - today.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_monday = today + timedelta(days=days_ahead)

    # Configure Monday 09:00 - 11:00 (30 min slots -> 09:00, 09:30, 10:00, 10:30)
    avail = DoctorAvailability(
        doctor_id=doc_prof.id,
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(11, 0),
        slot_duration_minutes=30,
        is_active=True,
    )
    db_session.add(avail)
    db_session.commit()

    # Query available slots for next Monday
    res = client.get(f"/api/v1/doctors/{doc_prof.id}/available-slots?date={next_monday.isoformat()}")
    assert res.status_code == 200
    data = res.json()

    assert data["doctor_id"] == doc_prof.id
    assert data["date"] == next_monday.isoformat()
    assert data["slot_duration_minutes"] == 30
    assert data["available_slots"] == ["09:00", "09:30", "10:00", "10:30"]


# ---------------------------------------------------------------------------
# Test 5: Already booked/pending slots are excluded
# ---------------------------------------------------------------------------
def test_booked_slots_are_excluded(client: TestClient, db_session: Session):
    doc = create_user_with_role(db_session, "avail_doc5@example.com", UserRole.DOCTOR, "Dr. Avail 5")
    patient = create_user_with_role(db_session, "avail_pat5@example.com", UserRole.PATIENT, "Pat 5")
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doc.id).first()
    pat_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()

    today = date.today()
    days_ahead = (2 - today.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_wednesday = today + timedelta(days=days_ahead)

    # Wed 14:00 - 16:00 (30 min slots -> 14:00, 14:30, 15:00, 15:30)
    avail = DoctorAvailability(
        doctor_id=doc_prof.id,
        day_of_week=2,
        start_time=time(14, 0),
        end_time=time(16, 0),
        slot_duration_minutes=30,
        is_active=True,
    )
    db_session.add(avail)

    # Book 14:30 slot
    app = Appointment(
        patient_id=pat_prof.id,
        doctor_id=doc_prof.id,
        scheduled_start=datetime.combine(next_wednesday, time(14, 30)),
        scheduled_end=datetime.combine(next_wednesday, time(15, 0)),
        status=AppointmentStatus.CONFIRMED,
        reason="Follow up",
    )
    db_session.add(app)
    db_session.commit()

    # Query available slots -> 14:30 must be excluded
    res = client.get(f"/api/v1/doctors/{doc_prof.id}/available-slots?date={next_wednesday.isoformat()}")
    assert res.status_code == 200
    slots = res.json()["available_slots"]
    assert "14:00" in slots
    assert "14:30" not in slots  # Excluded!
    assert "15:00" in slots
    assert "15:30" in slots


# ---------------------------------------------------------------------------
# Test 6: Past dates return 0 available slots
# ---------------------------------------------------------------------------
def test_past_date_returns_no_slots(client: TestClient, db_session: Session):
    doc = create_user_with_role(db_session, "avail_doc6@example.com", UserRole.DOCTOR, "Dr. Avail 6")
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doc.id).first()

    past_date = date.today() - timedelta(days=2)
    res = client.get(f"/api/v1/doctors/{doc_prof.id}/available-slots?date={past_date.isoformat()}")
    assert res.status_code == 200
    assert res.json()["available_slots"] == []


# ---------------------------------------------------------------------------
# Test 7: Doctor unavailable date blocks all slots on that date
# ---------------------------------------------------------------------------
def test_unavailable_date_blocks_slots(client: TestClient, db_session: Session):
    doc = create_user_with_role(db_session, "avail_doc7@example.com", UserRole.DOCTOR, "Dr. Avail 7")
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doc.id).first()

    target_date = date.today() + timedelta(days=5)
    day_idx = target_date.weekday()

    # Add schedule
    avail = DoctorAvailability(
        doctor_id=doc_prof.id,
        day_of_week=day_idx,
        start_time=time(9, 0),
        end_time=time(17, 0),
        slot_duration_minutes=30,
        is_active=True,
    )
    db_session.add(avail)

    # Doctor adds unavailable date (annual leave)
    leave = DoctorUnavailableDate(
        doctor_id=doc_prof.id,
        unavailable_date=target_date,
        reason="Medical Conference",
    )
    db_session.add(leave)
    db_session.commit()

    # Query available slots -> must be empty
    res = client.get(f"/api/v1/doctors/{doc_prof.id}/available-slots?date={target_date.isoformat()}")
    assert res.status_code == 200
    assert res.json()["available_slots"] == []


# ---------------------------------------------------------------------------
# Test 8: Patient cannot book outside doctor's active availability (400)
# ---------------------------------------------------------------------------
def test_patient_cannot_book_outside_doctor_availability(client: TestClient, db_session: Session):
    doc = create_user_with_role(db_session, "avail_doc8@example.com", UserRole.DOCTOR, "Dr. Avail 8")
    patient = create_user_with_role(db_session, "avail_pat8@example.com", UserRole.PATIENT, "Pat 8")
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doc.id).first()

    today = date.today()
    target_date = today + timedelta(days=4)
    day_idx = target_date.weekday()

    # Doctor only works 09:00 - 12:00
    avail = DoctorAvailability(
        doctor_id=doc_prof.id,
        day_of_week=day_idx,
        start_time=time(9, 0),
        end_time=time(12, 0),
        slot_duration_minutes=30,
        is_active=True,
    )
    db_session.add(avail)
    db_session.commit()

    # Patient attempts to book for 15:00 -> 400 Bad Request
    invalid_time = datetime.combine(target_date, time(15, 0))
    res = client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": doc_prof.id,
            "scheduled_start": invalid_time.isoformat(),
            "reason": "After hours booking attempt",
        },
        headers=get_token_header(patient),
    )
    assert res.status_code == 400
    assert "outside" in res.json()["detail"].lower() or "availability" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Test 9: Unapproved doctor does not expose slots
# ---------------------------------------------------------------------------
def test_unapproved_doctor_does_not_expose_slots(client: TestClient, db_session: Session):
    doc_unapproved = create_user_with_role(
        db_session,
        "avail_doc9_pending@example.com",
        UserRole.DOCTOR,
        "Dr. Pending",
        approval_status=DoctorApprovalStatus.PENDING,
    )
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doc_unapproved.id).first()

    res = client.get(f"/api/v1/doctors/{doc_prof.id}/available-slots?date={date.today().isoformat()}")
    assert res.status_code == 400


# ---------------------------------------------------------------------------
# Test 10: Doctor can update and delete availability
# ---------------------------------------------------------------------------
def test_doctor_update_and_delete_availability(client: TestClient, db_session: Session):
    doctor = create_user_with_role(db_session, "avail_doc10@example.com", UserRole.DOCTOR, "Dr. Avail 10")

    # 1. Create
    create_res = client.post(
        "/api/v1/doctors/availability",
        json={"day_of_week": 4, "start_time": "09:00:00", "end_time": "13:00:00", "slot_duration_minutes": 30},
        headers=get_token_header(doctor),
    )
    assert create_res.status_code == 201
    avail_id = create_res.json()["id"]

    # 2. Update
    update_res = client.put(
        f"/api/v1/doctors/availability/{avail_id}",
        json={"slot_duration_minutes": 45, "end_time": "14:00:00"},
        headers=get_token_header(doctor),
    )
    assert update_res.status_code == 200
    assert update_res.json()["slot_duration_minutes"] == 45

    # 3. Delete
    del_res = client.delete(f"/api/v1/doctors/availability/{avail_id}", headers=get_token_header(doctor))
    assert del_res.status_code == 204

    # 4. List my availability -> empty
    list_res = client.get("/api/v1/doctors/availability/my", headers=get_token_header(doctor))
    assert list_res.status_code == 200
    assert len(list_res.json()) == 0


# ---------------------------------------------------------------------------
# Test 11: Doctor can manage unavailable dates
# ---------------------------------------------------------------------------
def test_doctor_manage_unavailable_dates(client: TestClient, db_session: Session):
    doctor = create_user_with_role(db_session, "avail_doc11@example.com", UserRole.DOCTOR, "Dr. Avail 11")

    future_date = (date.today() + timedelta(days=10)).isoformat()

    # 1. Add unavailable date
    add_res = client.post(
        "/api/v1/doctors/unavailable-dates",
        json={"unavailable_date": future_date, "reason": "Personal Leave"},
        headers=get_token_header(doctor),
    )
    assert add_res.status_code == 201
    entry_id = add_res.json()["id"]

    # 2. List
    get_res = client.get("/api/v1/doctors/unavailable-dates/my", headers=get_token_header(doctor))
    assert get_res.status_code == 200
    assert len(get_res.json()) == 1
    assert get_res.json()[0]["reason"] == "Personal Leave"

    # 3. Delete
    del_res = client.delete(f"/api/v1/doctors/unavailable-dates/{entry_id}", headers=get_token_header(doctor))
    assert del_res.status_code == 204
