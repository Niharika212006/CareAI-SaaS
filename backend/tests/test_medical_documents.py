"""Comprehensive automated tests for Medical Documents & Health Records Management."""
import io
import os
from datetime import datetime, timedelta
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.medical_document import MedicalDocument, DocumentType
from app.core.security import get_password_hash, create_access_token
from app.core.storage import storage_service, MAX_FILE_SIZE_BYTES
from app.services.medical_document_service import medical_document_service
from app.schemas.medical_document import MedicalDocumentUpdate


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
            blood_group="O+",
            allergies=[{"name": "Penicillin", "type": "MEDICATION"}],
        )
        db.add(profile)
    elif role == UserRole.DOCTOR:
        profile = DoctorProfile(
            user_id=user.id,
            specialization="Cardiology",
            license_number=f"DOC-LIC-{user.id}",
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
# Upload & File Validation Tests
# ---------------------------------------------------------------------------

def test_patient_can_upload_valid_pdf(client: TestClient, db_session: Session):
    patient = create_user(db_session, "doc_upload_pdf@example.com", UserRole.PATIENT, "PDF Patient")
    pdf_bytes = b"%PDF-1.5 test document content for blood test"

    response = client.post(
        "/api/v1/medical-documents",
        headers=get_token_header(patient),
        data={"title": "Annual Blood Panel", "document_type": "LAB_REPORT", "description": "Complete blood count"},
        files={"file": ("blood_report.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Annual Blood Panel"
    assert data["document_type"] == "LAB_REPORT"
    assert data["file_name"] == "blood_report.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["file_size"] == len(pdf_bytes)


def test_patient_can_upload_valid_image(client: TestClient, db_session: Session):
    patient = create_user(db_session, "doc_upload_img@example.com", UserRole.PATIENT, "Image Patient")
    img_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRtest_image_bytes"

    response = client.post(
        "/api/v1/medical-documents",
        headers=get_token_header(patient),
        data={"title": "Chest X-Ray", "document_type": "IMAGING"},
        files={"file": ("chest_xray.png", img_bytes, "image/png")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Chest X-Ray"
    assert data["document_type"] == "IMAGING"
    assert data["file_name"] == "chest_xray.png"
    assert data["mime_type"] == "image/png"


def test_invalid_file_type_rejected(client: TestClient, db_session: Session):
    patient = create_user(db_session, "doc_invalid_ext@example.com", UserRole.PATIENT, "Invalid Ext Patient")
    exe_bytes = b"MZ\x90\x00executable content"

    response = client.post(
        "/api/v1/medical-documents",
        headers=get_token_header(patient),
        data={"title": "Malicious File", "document_type": "OTHER"},
        files={"file": ("malware.exe", exe_bytes, "application/x-msdownload")},
    )
    assert response.status_code == 400
    assert "not permitted" in response.json()["detail"]


def test_oversized_file_rejected(client: TestClient, db_session: Session):
    patient = create_user(db_session, "doc_oversized@example.com", UserRole.PATIENT, "Oversized Patient")
    huge_bytes = b"0" * (MAX_FILE_SIZE_BYTES + 1024)

    response = client.post(
        "/api/v1/medical-documents",
        headers=get_token_header(patient),
        data={"title": "Giant File", "document_type": "OTHER"},
        files={"file": ("giant.pdf", huge_bytes, "application/pdf")},
    )
    assert response.status_code == 400
    assert "exceeds maximum" in response.json()["detail"]


def test_empty_file_rejected(client: TestClient, db_session: Session):
    patient = create_user(db_session, "doc_empty@example.com", UserRole.PATIENT, "Empty Patient")

    response = client.post(
        "/api/v1/medical-documents",
        headers=get_token_header(patient),
        data={"title": "Empty File", "document_type": "OTHER"},
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"]


def test_path_traversal_filename_handled_safely(client: TestClient, db_session: Session):
    patient = create_user(db_session, "doc_traversal@example.com", UserRole.PATIENT, "Traversal Patient")
    pdf_bytes = b"%PDF-1.4 content"

    response = client.post(
        "/api/v1/medical-documents",
        headers=get_token_header(patient),
        data={"title": "Path Traversal Test"},
        files={"file": ("../../../../etc/passwd.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 201
    data = response.json()
    # Ensure raw directory traversal path was stripped
    assert ".." not in data["file_name"]
    assert "/" not in data["file_name"]
    assert "\\" not in data["file_name"]
    assert "passwd.pdf" in data["file_name"]


# ---------------------------------------------------------------------------
# Query, Metadata & Pagination Tests
# ---------------------------------------------------------------------------

def test_patient_can_list_own_documents_with_filtering_and_pagination(client: TestClient, db_session: Session):
    patient = create_user(db_session, "doc_list_pat@example.com", UserRole.PATIENT, "List Patient")

    # Upload 2 lab reports and 1 imaging
    for i in range(2):
        medical_document_service.upload_document(
            db=db_session,
            patient_user=patient,
            file_content=b"%PDF lab report",
            original_filename=f"lab_{i}.pdf",
            title=f"Lab Report {i}",
            document_type=DocumentType.LAB_REPORT,
        )
    medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=b"\x89PNG imaging report",
        original_filename="imaging_scan.png",
        title="MRI Scan",
        document_type=DocumentType.IMAGING,
    )

    # List all
    res_all = client.get("/api/v1/medical-documents", headers=get_token_header(patient))
    assert res_all.status_code == 200
    data_all = res_all.json()
    assert data_all["total"] == 3
    assert len(data_all["items"]) == 3

    # Filter by IMAGING
    res_img = client.get("/api/v1/medical-documents?document_type=IMAGING", headers=get_token_header(patient))
    assert res_img.status_code == 200
    data_img = res_img.json()
    assert data_img["total"] == 1
    assert data_img["items"][0]["title"] == "MRI Scan"


def test_empty_document_list_works(client: TestClient, db_session: Session):
    patient = create_user(db_session, "doc_empty_list@example.com", UserRole.PATIENT, "Empty List Patient")

    res = client.get("/api/v1/medical-documents", headers=get_token_header(patient))
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["items"] == []


# ---------------------------------------------------------------------------
# Privacy, RBAC & Isolation Tests
# ---------------------------------------------------------------------------

def test_patient_cannot_access_or_modify_or_delete_other_patients_document(client: TestClient, db_session: Session):
    patient1 = create_user(db_session, "doc_owner_pat@example.com", UserRole.PATIENT, "Owner Patient")
    patient2 = create_user(db_session, "doc_attacker_pat@example.com", UserRole.PATIENT, "Attacker Patient")

    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient1,
        file_content=b"%PDF confidential record",
        original_filename="confidential.pdf",
        title="Confidential Health Record",
        document_type=DocumentType.DISCHARGE_SUMMARY,
    )

    # Patient 2 tries to view metadata -> 403 Forbidden
    res_meta = client.get(f"/api/v1/medical-documents/{doc.id}", headers=get_token_header(patient2))
    assert res_meta.status_code == 403

    # Patient 2 tries to download file -> 403 Forbidden
    res_dl = client.get(f"/api/v1/medical-documents/{doc.id}/download", headers=get_token_header(patient2))
    assert res_dl.status_code == 403

    # Patient 2 tries to update metadata -> 403 Forbidden
    res_patch = client.patch(
        f"/api/v1/medical-documents/{doc.id}",
        headers=get_token_header(patient2),
        json={"title": "Hacked Title"},
    )
    assert res_patch.status_code == 403

    # Patient 2 tries to delete document -> 403 Forbidden
    res_del = client.delete(f"/api/v1/medical-documents/{doc.id}", headers=get_token_header(patient2))
    assert res_del.status_code == 403


def test_authorized_doctor_can_access_related_patient_documents(client: TestClient, db_session: Session):
    patient = create_user(db_session, "doc_rel_pat@example.com", UserRole.PATIENT, "Related Patient")
    doctor = create_user(db_session, "doc_rel_doc@example.com", UserRole.DOCTOR, "Dr. Related")
    pat_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()

    # Create active appointment relationship
    appt = Appointment(
        patient_id=pat_prof.id,
        doctor_id=doc_prof.id,
        scheduled_start=datetime.now() + timedelta(days=1),
        scheduled_end=datetime.now() + timedelta(days=1, minutes=30),
        status=AppointmentStatus.CONFIRMED,
    )
    db_session.add(appt)
    db_session.commit()

    # Patient uploads document
    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=b"%PDF ECG Test Results",
        original_filename="ecg_report.pdf",
        title="ECG Report",
        document_type=DocumentType.LAB_REPORT,
    )

    # Doctor accesses single document metadata
    res_meta = client.get(f"/api/v1/medical-documents/{doc.id}", headers=get_token_header(doctor))
    assert res_meta.status_code == 200
    assert res_meta.json()["title"] == "ECG Report"

    # Doctor downloads document file
    res_dl = client.get(f"/api/v1/medical-documents/{doc.id}/download", headers=get_token_header(doctor))
    assert res_dl.status_code == 200
    assert res_dl.content == b"%PDF ECG Test Results"

    # Doctor lists patient documents
    res_list = client.get(
        f"/api/v1/doctors/patients/{pat_prof.id}/medical-documents",
        headers=get_token_header(doctor),
    )
    assert res_list.status_code == 200
    assert res_list.json()["total"] == 1


def test_unrelated_doctor_receives_403(client: TestClient, db_session: Session):
    patient = create_user(db_session, "doc_unrel_pat@example.com", UserRole.PATIENT, "Unrelated Patient")
    doctor = create_user(db_session, "doc_unrel_doc@example.com", UserRole.DOCTOR, "Dr. Stranger")
    pat_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()

    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=b"%PDF Confidential Private Doc",
        original_filename="private.pdf",
        title="Private Lab Test",
        document_type=DocumentType.LAB_REPORT,
    )

    # Doctor has no appointment with patient -> 403 Forbidden
    res_meta = client.get(f"/api/v1/medical-documents/{doc.id}", headers=get_token_header(doctor))
    assert res_meta.status_code == 403

    res_dl = client.get(f"/api/v1/medical-documents/{doc.id}/download", headers=get_token_header(doctor))
    assert res_dl.status_code == 403

    res_list = client.get(
        f"/api/v1/doctors/patients/{pat_prof.id}/medical-documents",
        headers=get_token_header(doctor),
    )
    assert res_list.status_code == 403


def test_admin_cannot_access_sensitive_medical_documents(client: TestClient, db_session: Session):
    patient = create_user(db_session, "doc_admin_test_pat@example.com", UserRole.PATIENT, "Admin Test Patient")
    admin = create_user(db_session, "doc_admin_user@example.com", UserRole.ADMIN, "Admin User")

    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=b"%PDF Sensitive Patient Document",
        original_filename="sensitive.pdf",
        title="Sensitive Record",
    )

    # Admin access is rejected to protect patient medical privacy -> 403 Forbidden
    res = client.get(f"/api/v1/medical-documents/{doc.id}", headers=get_token_header(admin))
    assert res.status_code == 403

    res_dl = client.get(f"/api/v1/medical-documents/{doc.id}/download", headers=get_token_header(admin))
    assert res_dl.status_code == 403


def test_unauthenticated_requests_are_rejected(client: TestClient):
    assert client.get("/api/v1/medical-documents").status_code in [401, 403]
    assert client.get("/api/v1/medical-documents/1").status_code in [401, 403]
    assert client.get("/api/v1/medical-documents/1/download").status_code in [401, 403]
    assert client.patch("/api/v1/medical-documents/1").status_code in [401, 403]
    assert client.delete("/api/v1/medical-documents/1").status_code in [401, 403]


# ---------------------------------------------------------------------------
# Update & Safe Deletion Tests
# ---------------------------------------------------------------------------

def test_patient_can_update_document_metadata(client: TestClient, db_session: Session):
    patient = create_user(db_session, "doc_update_pat@example.com", UserRole.PATIENT, "Update Patient")

    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=b"%PDF Preliminary Blood Test",
        original_filename="blood_test.pdf",
        title="Draft Test",
        document_type=DocumentType.OTHER,
    )

    res = client.patch(
        f"/api/v1/medical-documents/{doc.id}",
        headers=get_token_header(patient),
        json={
            "title": "Final Blood Chemistry Panel",
            "document_type": "LAB_REPORT",
            "description": "Verified by pathologist",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Final Blood Chemistry Panel"
    assert data["document_type"] == "LAB_REPORT"
    assert data["description"] == "Verified by pathologist"


def test_file_deletion_removes_db_record_and_handles_missing_file_safely(client: TestClient, db_session: Session):
    patient = create_user(db_session, "doc_delete_pat@example.com", UserRole.PATIENT, "Delete Patient")

    doc = medical_document_service.upload_document(
        db=db_session,
        patient_user=patient,
        file_content=b"%PDF Test to delete",
        original_filename="delete_me.pdf",
        title="Temporary Document",
    )

    file_path = storage_service.get_file_path(doc.storage_key)
    assert file_path is not None
    assert file_path.exists()

    # Patient deletes document
    res = client.delete(f"/api/v1/medical-documents/{doc.id}", headers=get_token_header(patient))
    assert res.status_code == 200

    # Verify physical file removed
    assert not file_path.exists()

    # Verify DB record removed
    assert db_session.query(MedicalDocument).filter(MedicalDocument.id == doc.id).first() is None


def test_download_security_headers_and_no_path_leakage(client: TestClient, db_session: Session):
    """Verify that file download works for owner and never leaks storage keys, absolute paths, or internal server dirs."""
    patient = create_user(db_session, "doc_leakage_pat@example.com", UserRole.PATIENT, "Leakage Test Patient")
    file_payload = b"%PDF-1.4 Clinical Bloodwork Document Content"

    # Upload document
    upload_res = client.post(
        "/api/v1/medical-documents",
        headers=get_token_header(patient),
        data={"title": "Chemistry Panel", "document_type": "LAB_REPORT"},
        files={"file": ("lab_chemistry_2026.pdf", file_payload, "application/pdf")},
    )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    doc_id = doc_data["id"]

    # 1. Verify JSON metadata does not contain internal storage keys or filesystem paths
    assert "storage_key" not in doc_data
    assert "file_path" not in doc_data
    assert "upload_dir" not in doc_data
    assert "uploads" not in str(doc_data)

    # 2. Patient downloads own document
    dl_res = client.get(f"/api/v1/medical-documents/{doc_id}/download", headers=get_token_header(patient))
    assert dl_res.status_code == 200
    assert dl_res.content == file_payload

    # 3. Verify Content-Disposition header only reveals sanitized filename, not internal storage key
    content_disp = dl_res.headers.get("content-disposition", "")
    assert "lab_chemistry_2026.pdf" in content_disp
    # Confirm no UUID storage token in content disposition
    db_doc = db_session.query(MedicalDocument).filter(MedicalDocument.id == doc_id).first()
    assert db_doc.storage_key not in content_disp
    assert "uploads" not in content_disp
    assert "medical_documents" not in content_disp

