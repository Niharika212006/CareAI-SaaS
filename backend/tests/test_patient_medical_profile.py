"""Comprehensive automated tests for Patient Medical Profile & Health History Module."""
from datetime import date, datetime, timedelta, timezone
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
        profile = PatientProfile(user_id=user.id)
        db.add(profile)
    elif role == UserRole.DOCTOR:
        profile = DoctorProfile(
            user_id=user.id,
            specialization="Cardiology",
            license_number=f"DOC-MED-{user.id}",
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


# ---------------------------------------------------------------------------
# Test 1: Patient can fetch initial medical profile
# ---------------------------------------------------------------------------
def test_patient_can_get_medical_profile(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "med_pat1@example.com", UserRole.PATIENT, "Med Pat 1")

    res = client.get("/api/v1/patients/medical-profile", headers=get_token_header(patient))
    assert res.status_code == 200
    data = res.json()

    assert data["user_id"] == patient.id
    assert data["full_name"] == "Med Pat 1"
    assert "allergies" in data
    assert "chronic_conditions" in data
    assert "current_medications" in data


# ---------------------------------------------------------------------------
# Test 2: Patient can update full medical profile
# ---------------------------------------------------------------------------
def test_patient_can_update_full_medical_profile(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "med_pat2@example.com", UserRole.PATIENT, "Med Pat 2")

    payload = {
        "date_of_birth": "1992-05-15",
        "gender": "Female",
        "blood_group": "A+",
        "allergies": [
            {"name": "Penicillin", "type": "MEDICATION", "severity": "HIGH", "reaction": "Hives and swelling"},
            {"name": "Peanuts", "type": "FOOD", "severity": "CRITICAL", "reaction": "Anaphylaxis"},
        ],
        "chronic_conditions": ["Hypertension", "Asthma"],
        "past_conditions": ["COVID-19 (2021)"],
        "surgeries": ["Appendectomy (2015)"],
        "current_medications": [
            {"name": "Lisinopril 10mg", "dosage": "10 mg", "frequency": "Daily in morning", "instructions": "With water"},
            {"name": "Albuterol Inhaler", "dosage": "90 mcg", "frequency": "PRN", "instructions": "For wheezing"},
        ],
        "smoking_status": "NEVER",
        "alcohol_consumption": "OCCASIONAL",
        "emergency_contact_name": "John Doe",
        "emergency_contact_phone": "+1-555-0199",
        "emergency_contact_relationship": "Spouse",
        "medical_history_summary": "Patient has well-managed hypertension and asthma.",
    }

    res = client.put("/api/v1/patients/medical-profile", json=payload, headers=get_token_header(patient))
    assert res.status_code == 200
    data = res.json()

    assert data["gender"] == "Female"
    assert data["blood_group"] == "A+"
    assert len(data["allergies"]) == 2
    assert data["allergies"][0]["name"] == "Penicillin"
    assert data["allergies"][0]["severity"] == "HIGH"
    assert len(data["chronic_conditions"]) == 2
    assert len(data["current_medications"]) == 2
    assert data["emergency_contact_name"] == "John Doe"
    assert data["smoking_status"] == "NEVER"


# ---------------------------------------------------------------------------
# Test 3: Patient can partially update medical profile (PATCH)
# ---------------------------------------------------------------------------
def test_patient_can_patch_medical_profile(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "med_pat3@example.com", UserRole.PATIENT, "Med Pat 3")

    # Initial update
    client.put(
        "/api/v1/patients/medical-profile",
        json={"blood_group": "O-", "smoking_status": "NEVER"},
        headers=get_token_header(patient),
    )

    # Patch only smoking status and add chronic condition
    patch_payload = {
        "smoking_status": "FORMER",
        "chronic_conditions": ["Type 2 Diabetes"],
    }
    res = client.patch("/api/v1/patients/medical-profile", json=patch_payload, headers=get_token_header(patient))
    assert res.status_code == 200
    data = res.json()

    assert data["blood_group"] == "O-"  # Preserved
    assert data["smoking_status"] == "FORMER"  # Updated
    assert "Type 2 Diabetes" in data["chronic_conditions"]


# ---------------------------------------------------------------------------
# Test 4: Doctor with valid appointment relationship can access patient summary
# ---------------------------------------------------------------------------
def test_doctor_with_appointment_can_access_patient_summary(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "med_pat4@example.com", UserRole.PATIENT, "Med Pat 4")
    doctor = create_user_with_role(db_session, "med_doc4@example.com", UserRole.DOCTOR, "Dr. Med 4")

    patient_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()
    doctor_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()

    # Populate patient medical profile
    patient_prof.blood_group = "B+"
    patient_prof.allergies = [{"name": "Aspirin", "type": "MEDICATION", "severity": "HIGH", "reaction": "GI Bleeding"}]
    patient_prof.chronic_conditions = ["Atrial Fibrillation"]
    patient_prof.current_medications = [{"name": "Warfarin 5mg", "dosage": "5 mg", "frequency": "Daily"}]
    db_session.commit()

    # Create scheduled appointment between them
    now = datetime.now(timezone.utc)
    app = Appointment(
        patient_id=patient_prof.id,
        doctor_id=doctor_prof.id,
        scheduled_start=now + timedelta(days=1),
        scheduled_end=now + timedelta(days=1, minutes=30),
        status=AppointmentStatus.CONFIRMED,
        reason="Arrhythmia consultation",
    )
    db_session.add(app)
    db_session.commit()

    # Doctor requests patient medical summary
    res = client.get(f"/api/v1/patients/{patient_prof.id}/medical-summary", headers=get_token_header(doctor))
    assert res.status_code == 200
    data = res.json()

    assert data["patient_id"] == patient_prof.id
    assert data["full_name"] == "Med Pat 4"
    assert data["blood_group"] == "B+"
    assert len(data["allergies"]) == 1
    assert data["allergies"][0]["name"] == "Aspirin"
    assert "Atrial Fibrillation" in data["chronic_conditions"]
    assert len(data["current_medications"]) == 1


# ---------------------------------------------------------------------------
# Test 5: Unauthorized doctor cannot access unrelated patient summary (403)
# ---------------------------------------------------------------------------
def test_unrelated_doctor_cannot_access_patient_summary(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "med_pat5@example.com", UserRole.PATIENT, "Med Pat 5")
    doctor_stranger = create_user_with_role(db_session, "med_doc5_stranger@example.com", UserRole.DOCTOR, "Dr. Stranger")

    patient_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()

    # Doctor Stranger has no appointment relationship with patient
    res = client.get(f"/api/v1/patients/{patient_prof.id}/medical-summary", headers=get_token_header(doctor_stranger))
    assert res.status_code == 403
    assert "relationship" in res.json()["detail"].lower() or "access denied" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Test 6: Another patient cannot access unrelated patient summary
# ---------------------------------------------------------------------------
def test_patient_cannot_access_other_patient_summary(client: TestClient, db_session: Session):
    patient_a = create_user_with_role(db_session, "med_pat6a@example.com", UserRole.PATIENT, "Med Pat 6A")
    patient_b = create_user_with_role(db_session, "med_pat6b@example.com", UserRole.PATIENT, "Med Pat 6B")

    patient_a_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == patient_a.id).first()

    # Patient B attempts to fetch Patient A's summary
    res = client.get(f"/api/v1/patients/{patient_a_prof.id}/medical-summary", headers=get_token_header(patient_b))
    assert res.status_code == 403


# ---------------------------------------------------------------------------
# Test 7: AI Safety Engine detects allergy from structured profile
# ---------------------------------------------------------------------------
def test_ai_safety_detects_allergy_from_structured_profile(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "med_pat7@example.com", UserRole.PATIENT, "Med Pat 7")
    doctor = create_user_with_role(db_session, "med_doc7@example.com", UserRole.DOCTOR, "Dr. Med 7")

    patient_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()
    doctor_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()

    # Save structured allergy record
    patient_prof.allergies = [
        {"name": "Penicillin", "type": "MEDICATION", "severity": "CRITICAL", "reaction": "Anaphylaxis"}
    ]
    db_session.commit()

    # Doctor prescribes Amoxicillin (Penicillin class)
    now = datetime.now(timezone.utc)
    app = Appointment(
        patient_id=patient_prof.id,
        doctor_id=doctor_prof.id,
        scheduled_start=now - timedelta(hours=1),
        scheduled_end=now - timedelta(minutes=30),
        status=AppointmentStatus.COMPLETED,
        reason="Dental Infection",
    )
    db_session.add(app)
    db_session.flush()

    rx = Prescription(
        appointment_id=app.id,
        patient_id=patient_prof.id,
        doctor_id=doctor_prof.id,
        diagnosis="Severe Odontogenic Infection",
    )
    db_session.add(rx)
    db_session.flush()

    item = PrescriptionItem(
        prescription_id=rx.id,
        medication_name="Amoxicillin 500mg Capsule",
        dosage="500 mg",
        frequency="Three times daily",
        duration="7 days",
    )
    db_session.add(item)
    db_session.commit()

    # Run AI safety check on prescription
    res = client.post(f"/api/v1/ai/prescriptions/{rx.id}/analyze", headers=get_token_header(patient))
    assert res.status_code == 200
    data = res.json()

    assert data["overall_risk_level"] == "CRITICAL"
    dai = data["drug_allergy_interactions"]
    assert len(dai) >= 1
    assert any("penicillin" in item["explanation"].lower() or "allergy" in item["explanation"].lower() for item in dai)


# ---------------------------------------------------------------------------
# Test 8: Medical profile data persists correctly
# ---------------------------------------------------------------------------
def test_medical_profile_persistence(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "med_pat8@example.com", UserRole.PATIENT, "Med Pat 8")

    update_body = {
        "blood_group": "AB+",
        "allergies": [{"name": "Sulfa drugs", "type": "MEDICATION", "severity": "MODERATE"}],
        "surgeries": ["Knee Arthroscopy (2020)"],
    }
    client.put("/api/v1/patients/medical-profile", json=update_body, headers=get_token_header(patient))

    # Fetch again to verify persistence
    get_res = client.get("/api/v1/patients/medical-profile", headers=get_token_header(patient))
    assert get_res.status_code == 200
    assert get_res.json()["blood_group"] == "AB+"
    assert get_res.json()["allergies"][0]["name"] == "Sulfa drugs"
    assert "Knee Arthroscopy (2020)" in get_res.json()["surgeries"]


# ---------------------------------------------------------------------------
# Test 9: Unauthenticated request is rejected
# ---------------------------------------------------------------------------
def test_unauthenticated_request_rejected(client: TestClient):
    res = client.get("/api/v1/patients/medical-profile")
    assert res.status_code == 401
