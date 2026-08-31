"""Comprehensive automated tests for Digital Prescription Management Module."""
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.patient import PatientProfile
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription, PrescriptionItem
from app.core.security import get_password_hash, create_access_token


def create_user_with_role(db: Session, email: str, role: UserRole, full_name: str) -> User:
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
        profile = PatientProfile(user_id=user.id, blood_group="A+", allergies="Penicillin")
        db.add(profile)
    elif role == UserRole.DOCTOR:
        profile = DoctorProfile(
            user_id=user.id,
            specialization="Internal Medicine",
            license_number=f"DOC-LIC-RX-{user.id}",
            approval_status=DoctorApprovalStatus.APPROVED,
            consultation_fee=120.00,
        )
        db.add(profile)

    db.commit()
    db.refresh(user)
    return user


def get_token_header(user: User) -> dict:
    """Generate bearer token headers."""
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


def create_completed_appointment(db: Session, patient_user: User, doctor_user: User) -> Appointment:
    """Helper to create a completed consultation appointment."""
    patient_profile = db.query(PatientProfile).filter(PatientProfile.user_id == patient_user.id).first()
    doctor_profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_user.id).first()

    now = datetime.now(timezone.utc)
    app = Appointment(
        patient_id=patient_profile.id,
        doctor_id=doctor_profile.id,
        scheduled_start=now - timedelta(hours=2),
        scheduled_end=now - timedelta(hours=1, minutes=30),
        status=AppointmentStatus.COMPLETED,
        reason="Acute Bacterial Infection",
        doctor_notes="Patient presented with acute pharyngitis. Prescribed oral antibiotic course.",
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


# ---------------------------------------------------------------------------
# Test 1: Doctor can create prescription for completed appointment
# ---------------------------------------------------------------------------
def test_doctor_can_create_prescription_for_completed_appointment(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "rx_pat1@example.com", UserRole.PATIENT, "Rx Patient 1")
    doctor = create_user_with_role(db_session, "rx_doc1@example.com", UserRole.DOCTOR, "Dr. Rx Doctor 1")
    appointment = create_completed_appointment(db_session, patient, doctor)

    payload = {
        "appointment_id": appointment.id,
        "diagnosis": "Acute Pharyngitis",
        "clinical_notes": "Take full antibiotic course with plenty of water.",
        "items": [
            {
                "medication_name": "Amoxicillin",
                "dosage": "500 mg",
                "frequency": "Twice daily",
                "duration": "7 days",
                "route_of_administration": "Oral",
                "instructions": "Take after food",
            },
            {
                "medication_name": "Paracetamol",
                "dosage": "650 mg",
                "frequency": "As needed every 6 hours",
                "duration": "3 days",
                "route_of_administration": "Oral",
                "instructions": "For fever and pain relief",
            },
        ],
    }

    response = client.post("/api/v1/prescriptions", json=payload, headers=get_token_header(doctor))
    assert response.status_code == 201
    data = response.json()
    assert data["appointment_id"] == appointment.id
    assert data["diagnosis"] == "Acute Pharyngitis"
    assert len(data["items"]) == 2
    assert data["items"][0]["medication_name"] == "Amoxicillin"
    assert data["items"][0]["dosage"] == "500 mg"
    assert data["items"][1]["medication_name"] == "Paracetamol"


# ---------------------------------------------------------------------------
# Test 2: Doctor cannot create prescription for another doctor's appointment
# ---------------------------------------------------------------------------
def test_doctor_cannot_create_prescription_for_other_doctors_appointment(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "rx_pat2@example.com", UserRole.PATIENT, "Rx Patient 2")
    doctor_owner = create_user_with_role(db_session, "rx_owner@example.com", UserRole.DOCTOR, "Dr. Owner")
    doctor_intruder = create_user_with_role(db_session, "rx_intruder@example.com", UserRole.DOCTOR, "Dr. Intruder")
    appointment = create_completed_appointment(db_session, patient, doctor_owner)

    payload = {
        "appointment_id": appointment.id,
        "diagnosis": "Intruder Diagnosis",
        "items": [
            {
                "medication_name": "Ciprofloxacin",
                "dosage": "500 mg",
                "frequency": "Once daily",
                "duration": "5 days",
            }
        ],
    }

    response = client.post("/api/v1/prescriptions", json=payload, headers=get_token_header(doctor_intruder))
    assert response.status_code == 403
    assert "assigned to you" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Test 3: Doctor cannot prescribe before appointment completion
# ---------------------------------------------------------------------------
def test_doctor_cannot_prescribe_before_appointment_completion(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "rx_pat3@example.com", UserRole.PATIENT, "Rx Patient 3")
    doctor = create_user_with_role(db_session, "rx_doc3@example.com", UserRole.DOCTOR, "Dr. Rx Doctor 3")
    doctor_profile = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()
    patient_profile = db_session.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()

    # Create appointment in PENDING or CONFIRMED status
    app = Appointment(
        patient_id=patient_profile.id,
        doctor_id=doctor_profile.id,
        scheduled_start=datetime.now(timezone.utc) + timedelta(days=1),
        scheduled_end=datetime.now(timezone.utc) + timedelta(days=1, minutes=30),
        status=AppointmentStatus.CONFIRMED,
        reason="Follow up",
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)

    payload = {
        "appointment_id": app.id,
        "diagnosis": "Premature Prescription",
        "items": [
            {
                "medication_name": "Ibuprofen",
                "dosage": "400 mg",
                "frequency": "Three times daily",
                "duration": "3 days",
            }
        ],
    }

    response = client.post("/api/v1/prescriptions", json=payload, headers=get_token_header(doctor))
    assert response.status_code == 400
    assert "completed consultations" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Test 4: Prescription must contain medication items
# ---------------------------------------------------------------------------
def test_prescription_must_contain_medication_items(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "rx_pat4@example.com", UserRole.PATIENT, "Rx Patient 4")
    doctor = create_user_with_role(db_session, "rx_doc4@example.com", UserRole.DOCTOR, "Dr. Rx Doctor 4")
    appointment = create_completed_appointment(db_session, patient, doctor)

    # Empty items list
    payload = {
        "appointment_id": appointment.id,
        "diagnosis": "Diagnosis without medication",
        "items": [],
    }

    response = client.post("/api/v1/prescriptions", json=payload, headers=get_token_header(doctor))
    assert response.status_code in [400, 422]


# ---------------------------------------------------------------------------
# Test 5: Duplicate prescription for same appointment is prevented
# ---------------------------------------------------------------------------
def test_duplicate_prescription_is_prevented(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "rx_pat5@example.com", UserRole.PATIENT, "Rx Patient 5")
    doctor = create_user_with_role(db_session, "rx_doc5@example.com", UserRole.DOCTOR, "Dr. Rx Doctor 5")
    appointment = create_completed_appointment(db_session, patient, doctor)

    payload = {
        "appointment_id": appointment.id,
        "diagnosis": "First Prescription",
        "items": [
            {
                "medication_name": "Azithromycin",
                "dosage": "500 mg",
                "frequency": "Once daily",
                "duration": "3 days",
            }
        ],
    }

    # First attempt -> 201 Created
    res1 = client.post("/api/v1/prescriptions", json=payload, headers=get_token_header(doctor))
    assert res1.status_code == 201

    # Second attempt for same appointment -> 409 Conflict
    res2 = client.post("/api/v1/prescriptions", json=payload, headers=get_token_header(doctor))
    assert res2.status_code == 409
    assert "already been issued" in res2.json()["detail"]


# ---------------------------------------------------------------------------
# Test 6: Patient can view own prescriptions
# ---------------------------------------------------------------------------
def test_patient_can_view_own_prescriptions(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "rx_pat6@example.com", UserRole.PATIENT, "Rx Patient 6")
    doctor = create_user_with_role(db_session, "rx_doc6@example.com", UserRole.DOCTOR, "Dr. Rx Doctor 6")
    appointment = create_completed_appointment(db_session, patient, doctor)

    # Doctor issues prescription
    client.post(
        "/api/v1/prescriptions",
        json={
            "appointment_id": appointment.id,
            "diagnosis": "Seasonal Rhinitis",
            "items": [
                {
                    "medication_name": "Cetirizine",
                    "dosage": "10 mg",
                    "frequency": "Once at bedtime",
                    "duration": "10 days",
                }
            ],
        },
        headers=get_token_header(doctor),
    )

    # Patient retrieves their prescription history
    res = client.get("/api/v1/prescriptions/my", headers=get_token_header(patient))
    assert res.status_code == 200
    prescriptions = res.json()
    assert len(prescriptions) == 1
    assert prescriptions[0]["diagnosis"] == "Seasonal Rhinitis"
    assert prescriptions[0]["items"][0]["medication_name"] == "Cetirizine"


# ---------------------------------------------------------------------------
# Test 7: Patient cannot view another patient's prescription
# ---------------------------------------------------------------------------
def test_patient_cannot_view_another_patients_prescription(client: TestClient, db_session: Session):
    patient_a = create_user_with_role(db_session, "rx_pat7a@example.com", UserRole.PATIENT, "Patient 7A")
    patient_b = create_user_with_role(db_session, "rx_pat7b@example.com", UserRole.PATIENT, "Patient 7B")
    doctor = create_user_with_role(db_session, "rx_doc7@example.com", UserRole.DOCTOR, "Dr. Rx Doctor 7")
    appointment = create_completed_appointment(db_session, patient_a, doctor)

    # Issue prescription for Patient A
    create_res = client.post(
        "/api/v1/prescriptions",
        json={
            "appointment_id": appointment.id,
            "diagnosis": "Hypertension Stage 1",
            "items": [
                {
                    "medication_name": "Lisinopril",
                    "dosage": "10 mg",
                    "frequency": "Once daily morning",
                    "duration": "30 days",
                }
            ],
        },
        headers=get_token_header(doctor),
    )
    prescription_id = create_res.json()["id"]

    # Patient B tries to access Patient A's prescription by ID -> 403 Forbidden
    hack_res = client.get(f"/api/v1/prescriptions/{prescription_id}", headers=get_token_header(patient_b))
    assert hack_res.status_code == 403
    assert "permission" in hack_res.json()["detail"]


# ---------------------------------------------------------------------------
# Test 8: Doctor can view prescriptions they created
# ---------------------------------------------------------------------------
def test_doctor_can_view_prescriptions_they_created(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "rx_pat8@example.com", UserRole.PATIENT, "Rx Patient 8")
    doctor = create_user_with_role(db_session, "rx_doc8@example.com", UserRole.DOCTOR, "Dr. Rx Doctor 8")
    appointment = create_completed_appointment(db_session, patient, doctor)

    client.post(
        "/api/v1/prescriptions",
        json={
            "appointment_id": appointment.id,
            "diagnosis": "Gastritis",
            "items": [
                {
                    "medication_name": "Omeprazole",
                    "dosage": "20 mg",
                    "frequency": "Once daily before breakfast",
                    "duration": "14 days",
                }
            ],
        },
        headers=get_token_header(doctor),
    )

    doc_res = client.get("/api/v1/prescriptions/doctor/my", headers=get_token_header(doctor))
    assert doc_res.status_code == 200
    doc_prescriptions = doc_res.json()
    assert len(doc_prescriptions) == 1
    assert doc_prescriptions[0]["diagnosis"] == "Gastritis"


# ---------------------------------------------------------------------------
# Test 9: Unauthorized users are rejected
# ---------------------------------------------------------------------------
def test_unauthorized_users_are_rejected(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "rx_pat9@example.com", UserRole.PATIENT, "Rx Patient 9")
    doctor = create_user_with_role(db_session, "rx_doc9@example.com", UserRole.DOCTOR, "Dr. Rx Doctor 9")
    appointment = create_completed_appointment(db_session, patient, doctor)

    # 1. Unauthenticated request to create prescription -> 401 Unauthorized
    unauth_post = client.post(
        "/api/v1/prescriptions",
        json={
            "appointment_id": appointment.id,
            "diagnosis": "Unauth Test",
            "items": [{"medication_name": "Aspirin", "dosage": "81 mg", "frequency": "Daily", "duration": "30 days"}],
        },
    )
    assert unauth_post.status_code == 401

    # 2. Patient role attempting to create prescription -> 403 Forbidden
    patient_post = client.post(
        "/api/v1/prescriptions",
        json={
            "appointment_id": appointment.id,
            "diagnosis": "Patient Self-Prescribe",
            "items": [{"medication_name": "Aspirin", "dosage": "81 mg", "frequency": "Daily", "duration": "30 days"}],
        },
        headers=get_token_header(patient),
    )
    assert patient_post.status_code == 403


# ---------------------------------------------------------------------------
# Test 10: Prescription items are correctly stored and retrieved
# ---------------------------------------------------------------------------
def test_prescription_items_correctly_stored_and_retrieved(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "rx_pat10@example.com", UserRole.PATIENT, "Rx Patient 10")
    doctor = create_user_with_role(db_session, "rx_doc10@example.com", UserRole.DOCTOR, "Dr. Rx Doctor 10")
    appointment = create_completed_appointment(db_session, patient, doctor)

    payload = {
        "appointment_id": appointment.id,
        "diagnosis": "Type 2 Diabetes Mellitus",
        "clinical_notes": "Monitor fasting blood glucose daily.",
        "items": [
            {
                "medication_name": "Metformin",
                "dosage": "500 mg",
                "frequency": "Twice daily with meals",
                "duration": "30 days",
                "route_of_administration": "Oral",
                "instructions": "Take with meals to minimize GI distress.",
            },
            {
                "medication_name": "Glimepiride",
                "dosage": "1 mg",
                "frequency": "Once daily with breakfast",
                "duration": "30 days",
                "route_of_administration": "Oral",
                "instructions": "Do not skip breakfast after taking.",
            },
        ],
    }

    create_res = client.post("/api/v1/prescriptions", json=payload, headers=get_token_header(doctor))
    assert create_res.status_code == 201
    rx_id = create_res.json()["id"]

    get_res = client.get(f"/api/v1/prescriptions/{rx_id}", headers=get_token_header(doctor))
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == rx_id
    assert len(data["items"]) == 2

    item1 = next(item for item in data["items"] if item["medication_name"] == "Metformin")
    assert item1["dosage"] == "500 mg"
    assert item1["frequency"] == "Twice daily with meals"
    assert item1["route_of_administration"] == "Oral"

    item2 = next(item for item in data["items"] if item["medication_name"] == "Glimepiride")
    assert item2["dosage"] == "1 mg"
    assert item2["instructions"] == "Do not skip breakfast after taking."
