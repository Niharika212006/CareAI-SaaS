"""Comprehensive automated tests for genuine LLM-Powered Medical Document Analysis."""
import os
import io
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.medical_document import MedicalDocument, DocumentType
from app.models.document_analysis import MedicalDocumentAnalysis, AnalysisStatus
from app.core.security import get_password_hash, create_access_token
from app.services.medical_document_service import medical_document_service
from app.services.document_analysis_service import document_analysis_service
from app.ai.document_analyzer import DOCUMENT_ANALYSIS_DISCLAIMER, document_analyzer
from app.ai.client import ai_client, AIProviderUnavailableError, AIInvalidResponseError


MOCK_LLM_VALID_RESPONSE = json.dumps({
    "summary": "This laboratory document presents a comprehensive metabolic panel evaluating blood glucose and glycated hemoglobin.",
    "document_category": "Clinical Biochemistry / Metabolic Panel",
    "key_findings": [
        "Fasting glucose measured at 135 mg/dL (elevated).",
        "HbA1c recorded at 7.2% indicating diabetic range glycemic control.",
        "Daily prescription for Metformin 500mg noted."
    ],
    "detected_medications": [
        {"name": "Metformin", "dosage": "500mg"}
    ],
    "detected_test_values": [
        {"test": "Glucose", "value": "135 mg/dL", "reference_context": "Flagged: Higher than standard reference range"},
        {"test": "HbA1c", "value": "7.2%", "reference_context": "Flagged: Elevated"}
    ],
    "potential_concerns": [
        {"level": "medium", "message": "Glucose and HbA1c appear above standard target ranges. Review with physician."}
    ],
    "patient_friendly_explanation": "These laboratory findings reflect blood sugar measurements over recent weeks.",
    "recommended_next_step": "Discuss glycemic management and current medications with your doctor.",
    "disclaimer": DOCUMENT_ANALYSIS_DISCLAIMER
})


@pytest.fixture(autouse=True)
def mock_default_llm():
    """Default fixture to mock AIClient LLM response to prevent live network calls during test execution."""
    with patch.object(ai_client, "generate_completion", return_value=MOCK_LLM_VALID_RESPONSE):
        yield


def create_user(
    db: Session,
    email: str,
    role: UserRole,
    full_name: str,
    approval_status: DoctorApprovalStatus = DoctorApprovalStatus.APPROVED,
) -> User:
    """Helper to persist user and profile."""
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
            blood_group="B+",
            allergies=[{"name": "Aspirin", "type": "MEDICATION"}],
        )
        db.add(profile)
    elif role == UserRole.DOCTOR:
        profile = DoctorProfile(
            user_id=user.id,
            specialization="Endocrinology",
            license_number=f"DOC-AI-{user.id}",
            approval_status=approval_status,
            consultation_fee=160.00,
        )
        db.add(profile)

    db.commit()
    db.refresh(user)
    return user


def get_token_header(user: User) -> dict:
    """Generate bearer token headers."""
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


def create_mock_pdf_with_text(text: str) -> bytes:
    """Generate minimal valid PDF bytes with extractable text."""
    clean_text = text.replace("(", "").replace(")", "")
    stream_data = f"BT\n/F1 12 Tf\n50 250 Td\n({clean_text}) Tj\nET\n".encode("latin-1")
    length = len(stream_data)
    pdf_template = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 400 400] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length " + str(length).encode("ascii") + b" >>\nstream\n"
        + stream_data +
        b"endstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n500\n%%EOF\n"
    )
    return pdf_template


# ---------------------------------------------------------------------------
# Core Analysis Request & LLM Verification Tests
# ---------------------------------------------------------------------------

def test_patient_can_request_ai_analysis_with_genuine_llm(client: TestClient, db_session: Session):
    patient = create_user(db_session, "ai_owner_pat@example.com", UserRole.PATIENT, "AI Owner Patient")
    
    pdf_bytes = create_mock_pdf_with_text("Fasting Glucose: 135 mg/dL. HbA1c: 7.2%. Daily Metformin 500mg.")
    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=pdf_bytes,
        original_filename="metabolic_panel.pdf",
        title="Comprehensive Metabolic Panel",
        document_type=DocumentType.LAB_REPORT,
    )

    response = client.post(
        f"/api/v1/medical-documents/{doc.id}/analyze",
        headers=get_token_header(patient),
    )
    assert response.status_code == 200
    data = response.json()

    assert data["document_id"] == doc.id
    assert data["analysis_status"] == "COMPLETED"
    assert data["disclaimer"] == DOCUMENT_ANALYSIS_DISCLAIMER
    # Confirm real model identifier is populated (not hardcoded fake moniker)
    assert data["ai_model_name"] == ai_client.model_name
    assert len(data["key_findings"]) >= 1
    assert any(t["test"] == "Glucose" for t in data["detected_test_values"])
    assert any(m["name"] == "Metformin" for m in data["detected_medications"])
    assert "medical diagnosis" in data["disclaimer"].lower()

    # Verify DB persistence
    saved_analysis = db_session.query(MedicalDocumentAnalysis).filter(MedicalDocumentAnalysis.document_id == doc.id).first()
    assert saved_analysis is not None
    assert saved_analysis.ai_model_name == ai_client.model_name


def test_ai_provider_unavailable_returns_http_503_and_saves_no_record(client: TestClient, db_session: Session):
    """When LLM provider is down/unconfigured, returns 503 and persists no fake record."""
    patient = create_user(db_session, "ai_unavail_pat@example.com", UserRole.PATIENT, "Unavail Pat")
    pdf_bytes = create_mock_pdf_with_text("Glucose: 110 mg/dL.")
    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=pdf_bytes,
        original_filename="glucose.pdf",
        title="Glucose Test",
    )

    with patch.object(ai_client, "generate_completion", side_effect=AIProviderUnavailableError("Gemini provider down")):
        res = client.post(f"/api/v1/medical-documents/{doc.id}/analyze", headers=get_token_header(patient))
        assert res.status_code == 503
        assert "temporarily unavailable" in res.json()["detail"].lower()

        # Confirm no record was persisted
        saved = db_session.query(MedicalDocumentAnalysis).filter(MedicalDocumentAnalysis.document_id == doc.id).first()
        assert saved is None


def test_malformed_llm_json_returns_http_502_and_saves_no_record(client: TestClient, db_session: Session):
    """When LLM returns corrupted or invalid JSON, returns 502 without saving to DB."""
    patient = create_user(db_session, "ai_malformed_pat@example.com", UserRole.PATIENT, "Malformed Pat")
    pdf_bytes = create_mock_pdf_with_text("BUN: 20 mg/dL.")
    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=pdf_bytes,
        original_filename="bun.pdf",
        title="BUN Test",
    )

    with patch.object(ai_client, "generate_completion", return_value="INVALID NON-JSON OUTPUT FROM MODEL"):
        res = client.post(f"/api/v1/medical-documents/{doc.id}/analyze", headers=get_token_header(patient))
        assert res.status_code == 502
        assert "unparseable response" in res.json()["detail"].lower()

        saved = db_session.query(MedicalDocumentAnalysis).filter(MedicalDocumentAnalysis.document_id == doc.id).first()
        assert saved is None


def test_missing_required_fields_in_llm_json_fails_validation(client: TestClient, db_session: Session):
    """When LLM response misses required fields, Pydantic validation catches it."""
    patient = create_user(db_session, "ai_missing_fields_pat@example.com", UserRole.PATIENT, "Missing Fields Pat")
    pdf_bytes = create_mock_pdf_with_text("Cholesterol: 190 mg/dL.")
    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=pdf_bytes,
        original_filename="chol.pdf",
        title="Cholesterol Test",
    )

    # Incomplete JSON (missing summary, patient_friendly_explanation, etc.)
    incomplete_json = json.dumps({"key_findings": ["Test finding"]})
    with patch.object(ai_client, "generate_completion", return_value=incomplete_json):
        res = client.post(f"/api/v1/medical-documents/{doc.id}/analyze", headers=get_token_header(patient))
        assert res.status_code == 502


def test_explicit_heuristic_fallback_labels_model_transparently(db_session: Session):
    """Verify deterministic fallback engine transparently labels ai_model_name as CareAI-Heuristic-Ruleset-v1."""
    res = document_analyzer.analyze_with_heuristic_rules(
        clean_text="Fasting Blood Glucose: 140 mg/dL. Metformin 500mg.",
        document_title="Metabolic Lab",
    )
    assert res.ai_model_name == "CareAI-Heuristic-Ruleset-v1"
    assert len(res.detected_test_values) >= 1
    assert res.disclaimer == DOCUMENT_ANALYSIS_DISCLAIMER


def test_duplicate_analysis_requests_reuse_completed_record(client: TestClient, db_session: Session):
    patient = create_user(db_session, "ai_dup_pat@example.com", UserRole.PATIENT, "Dup Patient")
    pdf_bytes = create_mock_pdf_with_text("Total Cholesterol: 240 mg/dL. Triglycerides: 180 mg/dL.")
    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=pdf_bytes,
        original_filename="lipid_panel.pdf",
        title="Lipid Profile",
        document_type=DocumentType.LAB_REPORT,
    )

    # First request
    res1 = client.post(f"/api/v1/medical-documents/{doc.id}/analyze", headers=get_token_header(patient))
    assert res1.status_code == 200
    id1 = res1.json()["id"]

    # Second request
    res2 = client.post(f"/api/v1/medical-documents/{doc.id}/analyze", headers=get_token_header(patient))
    assert res2.status_code == 200
    id2 = res2.json()["id"]

    assert id1 == id2
    total_analyses = db_session.query(MedicalDocumentAnalysis).filter(MedicalDocumentAnalysis.document_id == doc.id).count()
    assert total_analyses == 1


def test_empty_or_scanned_pdf_without_text_handled_cleanly(client: TestClient, db_session: Session):
    patient = create_user(db_session, "ai_empty_pat@example.com", UserRole.PATIENT, "Empty Patient")
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    blank_pdf = buf.getvalue()

    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=blank_pdf,
        original_filename="blank.pdf",
        title="Blank PDF",
        document_type=DocumentType.OTHER,
    )

    response = client.post(
        f"/api/v1/medical-documents/{doc.id}/analyze",
        headers=get_token_header(patient),
    )
    assert response.status_code == 400
    assert "No readable text" in response.json()["detail"]


def test_image_file_returns_clean_unsupported_ocr_message(client: TestClient, db_session: Session):
    patient = create_user(db_session, "ai_img_pat@example.com", UserRole.PATIENT, "Image Patient")
    img_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRtest_image"

    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=img_bytes,
        original_filename="scan.png",
        title="Scanned Image",
        document_type=DocumentType.IMAGING,
    )

    response = client.post(
        f"/api/v1/medical-documents/{doc.id}/analyze",
        headers=get_token_header(patient),
    )
    assert response.status_code == 400
    assert "OCR" in response.json()["detail"]


# ---------------------------------------------------------------------------
# RBAC & Authorization Tests
# ---------------------------------------------------------------------------

def test_other_patient_cannot_request_analysis(client: TestClient, db_session: Session):
    owner = create_user(db_session, "ai_owner2@example.com", UserRole.PATIENT, "Owner")
    attacker = create_user(db_session, "ai_attacker2@example.com", UserRole.PATIENT, "Attacker")

    pdf_bytes = create_mock_pdf_with_text("Platelets: 250 k/uL. Hemoglobin: 14.5 g/dL.")
    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=owner,
        file_content=pdf_bytes,
        original_filename="cbc.pdf",
        title="CBC Results",
    )

    res = client.post(f"/api/v1/medical-documents/{doc.id}/analyze", headers=get_token_header(attacker))
    assert res.status_code == 403


def test_doctor_cannot_trigger_analysis_request(client: TestClient, db_session: Session):
    patient = create_user(db_session, "ai_pat3@example.com", UserRole.PATIENT, "Patient")
    doctor = create_user(db_session, "ai_doc3@example.com", UserRole.DOCTOR, "Doctor")

    pdf_bytes = create_mock_pdf_with_text("TSH: 2.5 mIU/L.")
    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=pdf_bytes,
        original_filename="thyroid.pdf",
        title="Thyroid Panel",
    )

    res = client.post(f"/api/v1/medical-documents/{doc.id}/analyze", headers=get_token_header(doctor))
    assert res.status_code == 403


def test_authorized_doctor_can_view_completed_analysis(client: TestClient, db_session: Session):
    patient = create_user(db_session, "ai_view_pat@example.com", UserRole.PATIENT, "View Patient")
    doctor = create_user(db_session, "ai_view_doc@example.com", UserRole.DOCTOR, "Dr. Viewer")
    pat_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()

    appt = Appointment(
        patient_id=pat_prof.id,
        doctor_id=doc_prof.id,
        scheduled_start=datetime.now() + timedelta(days=2),
        scheduled_end=datetime.now() + timedelta(days=2, minutes=30),
        status=AppointmentStatus.CONFIRMED,
    )
    db_session.add(appt)
    db_session.commit()

    pdf_bytes = create_mock_pdf_with_text("Blood Pressure: 120/80 mmHg. Fasting Glucose: 95 mg/dL.")
    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=pdf_bytes,
        original_filename="vitals.pdf",
        title="Routine Vitals",
    )
    analysis_res = client.post(f"/api/v1/medical-documents/{doc.id}/analyze", headers=get_token_header(patient))
    assert analysis_res.status_code == 200
    analysis_id = analysis_res.json()["id"]

    doc_res = client.get(f"/api/v1/medical-documents/{doc.id}/analysis", headers=get_token_header(doctor))
    assert doc_res.status_code == 200
    assert doc_res.json()["id"] == analysis_id

    byId_res = client.get(f"/api/v1/document-analyses/{analysis_id}", headers=get_token_header(doctor))
    assert byId_res.status_code == 200
    assert byId_res.json()["id"] == analysis_id


def test_unrelated_doctor_receives_403(client: TestClient, db_session: Session):
    patient = create_user(db_session, "ai_priv_pat@example.com", UserRole.PATIENT, "Private Patient")
    unrelated_doctor = create_user(db_session, "ai_unrel_doc@example.com", UserRole.DOCTOR, "Dr. Unrelated")

    pdf_bytes = create_mock_pdf_with_text("Creatinine: 1.1 mg/dL. BUN: 18 mg/dL.")
    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=pdf_bytes,
        original_filename="renal.pdf",
        title="Renal Panel",
    )
    analysis_res = client.post(f"/api/v1/medical-documents/{doc.id}/analyze", headers=get_token_header(patient))
    assert analysis_res.status_code == 200
    analysis_id = analysis_res.json()["id"]

    res1 = client.get(f"/api/v1/medical-documents/{doc.id}/analysis", headers=get_token_header(unrelated_doctor))
    assert res1.status_code == 403

    res2 = client.get(f"/api/v1/document-analyses/{analysis_id}", headers=get_token_header(unrelated_doctor))
    assert res2.status_code == 403


def test_admin_cannot_access_patient_analyses(client: TestClient, db_session: Session):
    patient = create_user(db_session, "ai_admin_test_pat@example.com", UserRole.PATIENT, "Admin Test Pat")
    admin = create_user(db_session, "ai_admin_user@example.com", UserRole.ADMIN, "Admin User")

    pdf_bytes = create_mock_pdf_with_text("White Blood Cells: 6.5 x10^3/uL.")
    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=pdf_bytes,
        original_filename="wbc.pdf",
        title="WBC Count",
    )
    analysis_res = client.post(f"/api/v1/medical-documents/{doc.id}/analyze", headers=get_token_header(patient))
    assert analysis_res.status_code == 200
    analysis_id = analysis_res.json()["id"]

    res = client.get(f"/api/v1/medical-documents/{doc.id}/analysis", headers=get_token_header(admin))
    assert res.status_code == 403


def test_analysis_payload_does_not_leak_internal_paths(client: TestClient, db_session: Session):
    patient = create_user(db_session, "ai_leak_pat@example.com", UserRole.PATIENT, "Leak Test Patient")
    pdf_bytes = create_mock_pdf_with_text("ALT: 25 U/L. AST: 22 U/L.")
    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=pdf_bytes,
        original_filename="hepatic.pdf",
        title="Hepatic Panel",
    )
    analysis_res = client.post(f"/api/v1/medical-documents/{doc.id}/analyze", headers=get_token_header(patient))
    assert analysis_res.status_code == 200
    data = analysis_res.json()

    assert "storage_key" not in data
    assert "file_path" not in data
    assert "uploads" not in str(data)


def test_unauthenticated_analysis_requests_are_rejected(client: TestClient, db_session: Session):
    patient = create_user(db_session, "ai_unauth_pat@example.com", UserRole.PATIENT, "Unauth Patient")
    pdf_bytes = create_mock_pdf_with_text("Glucose: 100 mg/dL.")
    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=pdf_bytes,
        original_filename="sugar.pdf",
        title="Blood Sugar",
    )

    res1 = client.post(f"/api/v1/medical-documents/{doc.id}/analyze")
    assert res1.status_code == 401

    res2 = client.get(f"/api/v1/medical-documents/{doc.id}/analysis")
    assert res2.status_code == 401


def test_successful_analysis_creates_in_app_notification(client: TestClient, db_session: Session):
    from app.models.notification import Notification
    patient = create_user(db_session, "ai_notif_pat@example.com", UserRole.PATIENT, "Notif Patient")
    pdf_bytes = create_mock_pdf_with_text("Hemoglobin: 13.2 g/dL. WBC: 5.8 k/uL.")
    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=pdf_bytes,
        original_filename="cbc_notif.pdf",
        title="Complete Blood Profile",
    )

    client.post(f"/api/v1/medical-documents/{doc.id}/analyze", headers=get_token_header(patient))

    notif = db_session.query(Notification).filter(Notification.user_id == patient.id).order_by(Notification.created_at.desc()).first()
    assert notif is not None
    assert "Analysis Ready" in notif.title
    assert "Complete Blood Profile" in notif.message


def test_nonexistent_document_analysis_returns_404(client: TestClient, db_session: Session):
    patient = create_user(db_session, "ai_404_pat@example.com", UserRole.PATIENT, "404 Patient")

    res = client.post("/api/v1/medical-documents/999999/analyze", headers=get_token_header(patient))
    assert res.status_code == 404

    res2 = client.get("/api/v1/medical-documents/999999/analysis", headers=get_token_header(patient))
    assert res2.status_code == 404
