"""Comprehensive automated tests for AI Prescription & Drug Interaction Safety Engine."""
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.patient import PatientProfile
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription, PrescriptionItem
from app.models.ai_report import AIAnalysisReport, InteractionSeverity
from app.core.security import get_password_hash, create_access_token
from app.ai.normalizer import normalize_medication_name
from app.ai.interaction_checker import interaction_checker


def create_user_with_role(db: Session, email: str, role: UserRole, full_name: str, allergies: str = None) -> User:
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
        profile = PatientProfile(user_id=user.id, blood_group="O+", allergies=allergies)
        db.add(profile)
    elif role == UserRole.DOCTOR:
        profile = DoctorProfile(
            user_id=user.id,
            specialization="General Internal Medicine",
            license_number=f"DOC-AI-{user.id}",
            approval_status=DoctorApprovalStatus.APPROVED,
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


def create_prescription_with_meds(
    db: Session, patient_user: User, doctor_user: User, diagnosis: str, medications: list
) -> Prescription:
    """Helper to create prescription with items."""
    patient_profile = db.query(PatientProfile).filter(PatientProfile.user_id == patient_user.id).first()
    doctor_profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_user.id).first()

    now = datetime.now(timezone.utc)
    app = Appointment(
        patient_id=patient_profile.id,
        doctor_id=doctor_profile.id,
        scheduled_start=now - timedelta(hours=2),
        scheduled_end=now - timedelta(hours=1, minutes=30),
        status=AppointmentStatus.COMPLETED,
        reason=diagnosis,
    )
    db.add(app)
    db.flush()

    rx = Prescription(
        appointment_id=app.id,
        patient_id=patient_profile.id,
        doctor_id=doctor_profile.id,
        diagnosis=diagnosis,
        clinical_notes="Take as directed.",
    )
    db.add(rx)
    db.flush()

    for med in medications:
        item = PrescriptionItem(
            prescription_id=rx.id,
            medication_name=med.get("name"),
            drug_name=med.get("name"),
            dosage=med.get("dosage", "500 mg"),
            frequency=med.get("frequency", "Twice daily"),
            duration=med.get("duration", "7 days"),
            route_of_administration=med.get("route", "Oral"),
            instructions=med.get("instructions", "Take after food"),
        )
        db.add(item)

    db.commit()
    db.refresh(rx)
    return rx


# ---------------------------------------------------------------------------
# Test 1: Drug-Drug Interaction Detection
# ---------------------------------------------------------------------------
def test_drug_drug_interaction_detection(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "ai_pat1@example.com", UserRole.PATIENT, "AI Pat 1")
    doctor = create_user_with_role(db_session, "ai_doc1@example.com", UserRole.DOCTOR, "Dr. AI 1")

    rx = create_prescription_with_meds(
        db_session,
        patient,
        doctor,
        "Anticoagulation & Pain",
        [
            {"name": "Warfarin 5mg Tablet", "dosage": "5 mg", "frequency": "Once daily at bedtime"},
            {"name": "Aspirin 81mg", "dosage": "81 mg", "frequency": "Daily in morning"},
        ],
    )

    response = client.post(f"/api/v1/ai/prescriptions/{rx.id}/analyze", headers=get_token_header(patient))
    assert response.status_code == 200
    data = response.json()

    assert data["overall_risk_level"] == "HIGH"
    assert data["total_findings"] >= 1
    ddi = data["drug_drug_interactions"]
    assert len(ddi) >= 1
    assert any(
        any("warfarin" in m.lower() for m in item["medications"])
        and any("aspirin" in m.lower() for m in item["medications"])
        for item in ddi
    )
    assert "bleeding" in ddi[0]["explanation"].lower() or "hemorrhage" in ddi[0]["explanation"].lower()
    assert "disclaimer" in data
    assert "does not replace professional medical advice" in data["disclaimer"]


# ---------------------------------------------------------------------------
# Test 2: Drug-Food Interaction Detection
# ---------------------------------------------------------------------------
def test_drug_food_interaction_detection(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "ai_pat2@example.com", UserRole.PATIENT, "AI Pat 2")
    doctor = create_user_with_role(db_session, "ai_doc2@example.com", UserRole.DOCTOR, "Dr. AI 2")

    rx = create_prescription_with_meds(
        db_session,
        patient,
        doctor,
        "Hypercholesterolemia",
        [{"name": "Simvastatin 40mg Tab", "dosage": "40 mg", "frequency": "Nightly"}],
    )

    response = client.post(f"/api/v1/ai/prescriptions/{rx.id}/analyze", headers=get_token_header(doctor))
    assert response.status_code == 200
    data = response.json()

    assert data["overall_risk_level"] in ["MODERATE", "HIGH"]
    dfi = data["drug_food_interactions"]
    assert len(dfi) >= 1
    assert any("grapefruit" in item["explanation"].lower() for item in dfi)


# ---------------------------------------------------------------------------
# Test 3: Drug-Allergy Interaction Detection
# ---------------------------------------------------------------------------
def test_drug_allergy_interaction_detection(client: TestClient, db_session: Session):
    patient = create_user_with_role(
        db_session, "ai_pat3@example.com", UserRole.PATIENT, "AI Pat 3", allergies="Penicillin, Sulfa"
    )
    doctor = create_user_with_role(db_session, "ai_doc3@example.com", UserRole.DOCTOR, "Dr. AI 3")

    # Prescribing Amoxicillin (Penicillin class) to penicillin-allergic patient
    rx = create_prescription_with_meds(
        db_session,
        patient,
        doctor,
        "Upper Respiratory Infection",
        [{"name": "Amoxicillin 500mg Capsule", "dosage": "500 mg", "frequency": "TID"}],
    )

    response = client.post(f"/api/v1/ai/prescriptions/{rx.id}/analyze", headers=get_token_header(patient))
    assert response.status_code == 200
    data = response.json()

    assert data["overall_risk_level"] == "CRITICAL"
    dai = data["drug_allergy_interactions"]
    assert len(dai) >= 1
    assert any("penicillin" in item["explanation"].lower() or "allergy" in item["explanation"].lower() for item in dai)
    assert dai[0]["severity"] == "CRITICAL"


# ---------------------------------------------------------------------------
# Test 4: Duplicate Medication Detection
# ---------------------------------------------------------------------------
def test_duplicate_medication_detection(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "ai_pat4@example.com", UserRole.PATIENT, "AI Pat 4")
    doctor = create_user_with_role(db_session, "ai_doc4@example.com", UserRole.DOCTOR, "Dr. AI 4")

    # Advil and Ibuprofen resolve to identical active ingredient
    rx = create_prescription_with_meds(
        db_session,
        patient,
        doctor,
        "Arthritis Flare",
        [
            {"name": "Advil 200mg", "dosage": "200 mg", "frequency": "PRN"},
            {"name": "Ibuprofen 400mg Tab", "dosage": "400 mg", "frequency": "TID"},
        ],
    )

    response = client.post(f"/api/v1/ai/prescriptions/{rx.id}/analyze", headers=get_token_header(doctor))
    assert response.status_code == 200
    data = response.json()

    findings = data["findings"]
    dup = [f for f in findings if f["category"] == "DUPLICATE_MEDICATION"]
    assert len(dup) >= 1
    assert "duplicate" in dup[0]["title"].lower() or "ibuprofen" in dup[0]["explanation"].lower()


# ---------------------------------------------------------------------------
# Test 5: Risk Classification Hierarchy
# ---------------------------------------------------------------------------
def test_risk_classification_hierarchy():
    # 1. Critical test (Fluoxetine + Tramadol)
    res_crit = interaction_checker.run_safety_analysis(
        medications=["Fluoxetine 20mg", "Tramadol 50mg"],
        patient_allergies=[],
    )
    assert res_crit.overall_risk_level == InteractionSeverity.CRITICAL

    # 2. High test (Warfarin + Aspirin)
    res_high = interaction_checker.run_safety_analysis(
        medications=["Warfarin 5mg", "Aspirin 81mg"],
        patient_allergies=[],
    )
    assert res_high.overall_risk_level == InteractionSeverity.HIGH

    # 3. Moderate test (Clopidogrel + Omeprazole)
    res_mod = interaction_checker.run_safety_analysis(
        medications=["Clopidogrel 75mg", "Omeprazole 20mg"],
        patient_allergies=[],
    )
    assert res_mod.overall_risk_level == InteractionSeverity.MODERATE

    # 4. Low test (Levothyroxine alone -> food timing advisory)
    res_low = interaction_checker.run_safety_analysis(
        medications=["Levothyroxine 50mcg"],
        patient_allergies=[],
    )
    assert res_low.overall_risk_level == InteractionSeverity.LOW


# ---------------------------------------------------------------------------
# Test 6: No-Interaction Scenario
# ---------------------------------------------------------------------------
def test_no_interaction_scenario(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "ai_pat6@example.com", UserRole.PATIENT, "AI Pat 6")
    doctor = create_user_with_role(db_session, "ai_doc6@example.com", UserRole.DOCTOR, "Dr. AI 6")

    rx = create_prescription_with_meds(
        db_session,
        patient,
        doctor,
        "Routine Care",
        [{"name": "Cetirizine 10mg", "dosage": "10 mg", "frequency": "Once daily"}],
    )

    response = client.post(f"/api/v1/ai/prescriptions/{rx.id}/analyze", headers=get_token_header(patient))
    assert response.status_code == 200
    data = response.json()

    assert data["overall_risk_level"] == "NONE"
    assert data["total_findings"] == 0
    assert "No potential interactions" in data["clinical_summary"]
    assert "completely safe" not in data["clinical_summary"].lower()


# ---------------------------------------------------------------------------
# Test 7: Unauthorized user cannot analyze another user's prescription
# ---------------------------------------------------------------------------
def test_unauthorized_user_cannot_analyze_other_prescription(client: TestClient, db_session: Session):
    patient_a = create_user_with_role(db_session, "ai_pat7a@example.com", UserRole.PATIENT, "AI Pat 7A")
    patient_b = create_user_with_role(db_session, "ai_pat7b@example.com", UserRole.PATIENT, "AI Pat 7B")
    doctor = create_user_with_role(db_session, "ai_doc7@example.com", UserRole.DOCTOR, "Dr. AI 7")

    rx = create_prescription_with_meds(
        db_session,
        patient_a,
        doctor,
        "Confidential Condition",
        [{"name": "Metformin 500mg", "dosage": "500 mg"}],
    )

    # Patient B attempts to analyze Patient A's prescription -> 403 Forbidden
    hack_res = client.post(f"/api/v1/ai/prescriptions/{rx.id}/analyze", headers=get_token_header(patient_b))
    assert hack_res.status_code == 403
    assert "permission" in hack_res.json()["detail"]


# ---------------------------------------------------------------------------
# Test 8: Patient can analyze own prescription
# ---------------------------------------------------------------------------
def test_patient_can_analyze_own_prescription(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "ai_pat8@example.com", UserRole.PATIENT, "AI Pat 8")
    doctor = create_user_with_role(db_session, "ai_doc8@example.com", UserRole.DOCTOR, "Dr. AI 8")

    rx = create_prescription_with_meds(
        db_session,
        patient,
        doctor,
        "Type 2 Diabetes",
        [{"name": "Metformin 500mg", "dosage": "500 mg"}],
    )

    res = client.post(f"/api/v1/ai/prescriptions/{rx.id}/analyze", headers=get_token_header(patient))
    assert res.status_code == 200
    assert res.json()["prescription_id"] == rx.id


# ---------------------------------------------------------------------------
# Test 9: Doctor can analyze prescription they created
# ---------------------------------------------------------------------------
def test_doctor_can_analyze_created_prescription(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "ai_pat9@example.com", UserRole.PATIENT, "AI Pat 9")
    doctor = create_user_with_role(db_session, "ai_doc9@example.com", UserRole.DOCTOR, "Dr. AI 9")

    rx = create_prescription_with_meds(
        db_session,
        patient,
        doctor,
        "Hypertension",
        [{"name": "Lisinopril 10mg", "dosage": "10 mg"}],
    )

    res = client.post(f"/api/v1/ai/prescriptions/{rx.id}/analyze", headers=get_token_header(doctor))
    assert res.status_code == 200
    assert res.json()["prescription_id"] == rx.id


# ---------------------------------------------------------------------------
# Test 10: Analysis report is stored and retrievable via GET endpoint
# ---------------------------------------------------------------------------
def test_analysis_report_is_stored_and_retrievable(client: TestClient, db_session: Session):
    patient = create_user_with_role(db_session, "ai_pat10@example.com", UserRole.PATIENT, "AI Pat 10")
    doctor = create_user_with_role(db_session, "ai_doc10@example.com", UserRole.DOCTOR, "Dr. AI 10")

    rx = create_prescription_with_meds(
        db_session,
        patient,
        doctor,
        "Infection",
        [{"name": "Metronidazole 500mg", "dosage": "500 mg"}],
    )

    # 1. Post analysis
    post_res = client.post(f"/api/v1/ai/prescriptions/{rx.id}/analyze", headers=get_token_header(patient))
    assert post_res.status_code == 200
    report_id = post_res.json()["id"]
    assert report_id is not None

    # 2. Get report via GET /ai/prescriptions/{id}/report
    get_res = client.get(f"/api/v1/ai/prescriptions/{rx.id}/report", headers=get_token_header(patient))
    assert get_res.status_code == 200
    assert get_res.json()["id"] == report_id
    assert get_res.json()["prescription_id"] == rx.id

    # 3. Patient reports list via GET /ai/reports/my
    my_reports = client.get("/api/v1/ai/reports/my", headers=get_token_header(patient))
    assert my_reports.status_code == 200
    assert len(my_reports.json()) >= 1


# ---------------------------------------------------------------------------
# Test 11: Medication normalization accuracy
# ---------------------------------------------------------------------------
def test_medication_normalization():
    assert normalize_medication_name("Amoxicillin 500mg Capsule") == "amoxicillin"
    assert normalize_medication_name("Advil 200 mg Tablets") == "ibuprofen"
    assert normalize_medication_name("Coumadin 5mg Oral Tab") == "warfarin"
    assert normalize_medication_name("Tylenol Extra Strength 500mg") == "paracetamol"
    assert normalize_medication_name("Glucophage 850mg XR") == "metformin"
    assert normalize_medication_name("Lipitor 20mg") == "atorvastatin"
    assert normalize_medication_name("Zocor 40mg") == "simvastatin"
    assert normalize_medication_name("Flagyl 500 mg") == "metronidazole"


# ---------------------------------------------------------------------------
# Test 12: Missing or blank allergy data is handled safely
# ---------------------------------------------------------------------------
def test_missing_allergy_data_handled_safely():
    # Calling with None, empty list, and whitespace string
    res_none = interaction_checker.run_safety_analysis(
        medications=["Amoxicillin 500mg"],
        patient_allergies=None,
    )
    assert res_none.overall_risk_level == InteractionSeverity.NONE

    res_blank = interaction_checker.run_safety_analysis(
        medications=["Amoxicillin 500mg"],
        patient_allergies=["", "None", "nil", "   "],
    )
    assert res_blank.overall_risk_level == InteractionSeverity.NONE
    assert len(res_blank.drug_allergy_interactions) == 0
