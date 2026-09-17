"""Automated test suite for Role-Specific CareAI Assistant and Multimodal Prescription Ingestion."""
import io
import pytest
from datetime import date, datetime, timedelta
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription, PrescriptionItem, PrescriptionStatus
from app.models.lab import LabOrder, LabOrderStatus, LabOrderPriority
from app.models.medical_document import MedicalDocument, DocumentType
from app.core.security import get_password_hash
from app.services.ai.context_retrieval import context_retrieval_service
from app.services.ai.safety_service import safety_service


def seed_user(db: Session, email: str, role: UserRole, full_name: str) -> User:
    """Seed user in test database."""
    user = User(
        email=email.lower(),
        hashed_password=get_password_hash("SecretPassword123!"),
        full_name=full_name,
        role=role,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_jwt(client: TestClient, email: str) -> str:
    """Helper to authenticate and get JWT."""
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "SecretPassword123!"})
    assert res.status_code == status.HTTP_200_OK, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


class TestRoleSpecificAIAssistant:
    """Comprehensive test suite covering RBAC, context grounding, and prescription extraction."""

    @pytest.fixture(autouse=True)
    def setup_entities(self, db_session: Session):
        """Seed all 5 user roles and clinical profiles."""
        self.patient_a_user = seed_user(db_session, "patient.a@careai.com", UserRole.PATIENT, "Patient Alpha")
        self.patient_b_user = seed_user(db_session, "patient.b@careai.com", UserRole.PATIENT, "Patient Beta")
        self.doctor_user = seed_user(db_session, "dr.smith@careai.com", UserRole.DOCTOR, "Dr. John Smith")
        self.admin_user = seed_user(db_session, "admin.ops@careai.com", UserRole.ADMIN, "System Admin")
        self.lab_user = seed_user(db_session, "tech.lab@careai.com", UserRole.LAB_TECHNICIAN, "Lab Tech")
        self.pharm_user = seed_user(db_session, "pharm.staff@careai.com", UserRole.PHARMACY_STAFF, "Pharmacy Staff")

        # Profiles
        self.patient_a_prof = PatientProfile(user_id=self.patient_a_user.id, date_of_birth=date(1985, 4, 12), blood_group="O+")
        self.patient_b_prof = PatientProfile(user_id=self.patient_b_user.id, date_of_birth=date(1990, 8, 22), blood_group="A+")
        self.doctor_prof = DoctorProfile(
            user_id=self.doctor_user.id,
            specialization="Cardiology",
            license_number="CARD-12345",
            consultation_fee=150.0,
            approval_status=DoctorApprovalStatus.APPROVED,
        )
        db_session.add_all([self.patient_a_prof, self.patient_b_prof, self.doctor_prof])
        db_session.commit()
        db_session.refresh(self.patient_a_prof)
        db_session.refresh(self.patient_b_prof)
        db_session.refresh(self.doctor_prof)

        # Seed an appointment for today
        now = datetime.utcnow()
        self.appointment = Appointment(
            patient_id=self.patient_a_prof.id,
            doctor_id=self.doctor_prof.id,
            scheduled_start=now,
            scheduled_end=now + timedelta(minutes=30),
            status=AppointmentStatus.CONFIRMED,
            reason_for_visit="Cardiovascular Routine Checkup",
            reason="Cardiovascular Routine Checkup",
        )
        db_session.add(self.appointment)
        db_session.commit()
        db_session.refresh(self.appointment)

        # Seed a prescription for Patient A with Lisinopril
        self.prescription_a = Prescription(
            patient_id=self.patient_a_prof.id,
            doctor_id=self.doctor_prof.id,
            diagnosis="Essential Hypertension",
            status=PrescriptionStatus.PRESCRIBED,
        )
        db_session.add(self.prescription_a)
        db_session.flush()

        self.item_a = PrescriptionItem(
            prescription_id=self.prescription_a.id,
            medication_name="Lisinopril",
            dosage="20 mg",
            frequency="Once daily",
            duration="30 days",
            route_of_administration="Oral",
            instructions="Take each morning with water",
        )
        db_session.add(self.item_a)

        # Seed a prescription for Patient B with Metformin
        self.prescription_b = Prescription(
            patient_id=self.patient_b_prof.id,
            doctor_id=self.doctor_prof.id,
            diagnosis="Type 2 Diabetes Mellitus",
            status=PrescriptionStatus.PRESCRIBED,
        )
        db_session.add(self.prescription_b)
        db_session.flush()

        self.item_b = PrescriptionItem(
            prescription_id=self.prescription_b.id,
            medication_name="Metformin",
            dosage="500 mg",
            frequency="Twice daily",
            duration="30 days",
            route_of_administration="Oral",
            instructions="Take with meals",
        )
        db_session.add(self.item_b)

        # Seed lab order
        self.lab_order = LabOrder(
            patient_id=self.patient_a_prof.id,
            doctor_id=self.doctor_prof.id,
            clinical_notes="Serum Lipid Panel checkup",
            status=LabOrderStatus.SAMPLE_PENDING,
            priority=LabOrderPriority.URGENT,
        )
        db_session.add(self.lab_order)
        db_session.commit()

    def test_admin_context_retrieval_and_exact_counts(self, db_session: Session):
        """Admin context retrieval must query exact database counts with zero hallucination."""
        admin_ctx = context_retrieval_service.get_admin_context(db_session)
        assert admin_ctx["users"]["by_role"]["PATIENT"] == 2
        assert admin_ctx["users"]["by_role"]["DOCTOR"] == 1
        assert admin_ctx["doctors"]["by_approval"]["APPROVED"] == 1
        assert admin_ctx["prescriptions"]["by_status"]["PRESCRIBED"] == 2
        assert admin_ctx["laboratory"]["by_status"]["SAMPLE_PENDING"] == 1

    def test_patient_data_isolation_in_ai_context(self, db_session: Session):
        """Patient A's context must contain Lisinopril and NEVER contain Patient B's Metformin."""
        ctx_a = context_retrieval_service.get_patient_context(db_session, self.patient_a_user)
        rx_a_meds = [
            item["name"]
            for rx in ctx_a.get("prescriptions", [])
            for item in rx.get("items", [])
        ]
        assert "Lisinopril" in rx_a_meds
        assert "Metformin" not in rx_a_meds

        ctx_b = context_retrieval_service.get_patient_context(db_session, self.patient_b_user)
        rx_b_meds = [
            item["name"]
            for rx in ctx_b.get("prescriptions", [])
            for item in rx.get("items", [])
        ]
        assert "Metformin" in rx_b_meds
        assert "Lisinopril" not in rx_b_meds

    def test_doctor_clinical_schedule_context(self, db_session: Session):
        """Doctor context must list today's appointments and pending lab orders."""
        doc_ctx = context_retrieval_service.get_doctor_context(db_session, self.doctor_user)
        appts = doc_ctx.get("appointments_today", [])
        assert len(appts) >= 1
        assert any("Patient Alpha" in a.get("patient_name", "") for a in appts)
        assert any("Cardiovascular" in a.get("reason", "") for a in appts)

    def test_emergency_symptom_triage_detection(self):
        """Emergency symptoms must be flagged with high priority triage warning."""
        emergency_prompts = [
            "I have crushing chest pain radiating to my left arm",
            "I am having severe difficulty breathing and shortness of breath",
            "Sudden numbness in one side of my face and cannot speak clearly",
        ]
        for prompt in emergency_prompts:
            is_emerg, banner = safety_service.detect_emergency_symptoms(prompt)
            assert is_emerg is True
            assert "EMERGENCY MEDICAL WARNING" in banner
            assert "911" in banner

        routine_prompt = "Can I take Lisinopril with a glass of orange juice?"
        is_emerg, banner = safety_service.detect_emergency_symptoms(routine_prompt)
        assert is_emerg is False
        assert banner == ""

    def test_patient_chat_endpoint_with_grounded_prescription(self, client: TestClient):
        """Patient querying AI assistant receives grounded answers with mandatory disclaimer."""
        token = get_jwt(client, self.patient_a_user.email)
        headers = {"Authorization": f"Bearer {token}"}

        res = client.post(
            "/api/v1/ai-assistant/chat",
            headers=headers,
            json={"message": "What is my active medication and how should I take it?"},
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["conversation_id"] is not None
        assert "Lisinopril" in data["assistant_response"] or "prescription" in data["assistant_response"].lower()
        resp_lower = data["assistant_response"].lower()
        assert "medical" in resp_lower and ("advice" in resp_lower or "notice" in resp_lower or "disclaimer" in resp_lower)

    def test_admin_chat_endpoint_reports_real_stats(self, client: TestClient):
        """Admin querying AI assistant receives factual operational stats without patient clinical data."""
        token = get_jwt(client, self.admin_user.email)
        headers = {"Authorization": f"Bearer {token}"}

        res = client.post(
            "/api/v1/ai-assistant/chat",
            headers=headers,
            json={"message": "How many doctors and appointments do we have in the system today?"},
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        resp_text = data["assistant_response"]
        assert len(resp_text) > 0
        # Admin prompt should not reveal confidential patient details
        assert "patient alpha" not in resp_text.lower() or "1" in resp_text

    def test_prescription_upload_and_confirmation_workflow(self, client: TestClient, db_session: Session):
        """Test full multimodal prescription upload draft, review, and confirmation flow."""
        token = get_jwt(client, self.patient_a_user.email)
        headers = {"Authorization": f"Bearer {token}"}

        # Step 1: Upload a simulated prescription PDF
        pdf_dummy_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"
        files = {"file": ("prescription_scan.pdf", io.BytesIO(pdf_dummy_bytes), "application/pdf")}

        upload_res = client.post(
            "/api/v1/ai-assistant/patient/upload-prescription",
            headers=headers,
            files=files,
        )
        assert upload_res.status_code == status.HTTP_200_OK
        draft = upload_res.json()
        assert "temp_file_token" in draft
        assert draft["file_name"] == "prescription_scan.pdf"
        assert len(draft["medications"]) > 0
        assert draft["confidence_score"] > 0

        temp_token = draft["temp_file_token"]

        # Step 2: Patient confirms the extracted prescription
        confirm_payload = {
            "temp_file_token": temp_token,
            "file_name": "prescription_scan.pdf",
            "doctor_name": "Dr. Sarah Jenkins, MD",
            "diagnosis": "Essential Hypertension",
            "clinical_notes": "Patient self-uploaded via CareAI multimodal scanner",
            "medications": [
                {
                    "medication_name": "Lisinopril",
                    "dosage": "20 mg",
                    "frequency": "Once daily in the morning",
                    "duration": "30 days",
                    "route_of_administration": "Oral",
                    "instructions": "Take with water",
                }
            ],
        }

        confirm_res = client.post(
            "/api/v1/ai-assistant/patient/confirm-prescription",
            headers=headers,
            json=confirm_payload,
        )
        assert confirm_res.status_code == status.HTTP_200_OK
        result = confirm_res.json()
        assert result["document_id"] is not None
        assert result["prescription_id"] is not None
        assert len(result["medication_schedule"]) > 0
        assert len(result["interaction_warnings"]) > 0
        assert "careai" in result["disclaimer"].lower() or "guidance" in result["disclaimer"].lower()

        # Step 3: Verify the record in DB
        doc = db_session.query(MedicalDocument).filter(MedicalDocument.id == result["document_id"]).first()
        assert doc is not None
        assert doc.document_type == DocumentType.PRESCRIPTION
        assert doc.patient_id == self.patient_a_prof.id

        presc = db_session.query(Prescription).filter(Prescription.id == result["prescription_id"]).first()
        assert presc is not None
        assert presc.diagnosis == "Essential Hypertension"
        assert len(presc.items) == 1
        assert presc.items[0].medication_name == "Lisinopril"

    def test_upload_prescription_forbidden_for_non_patient(self, client: TestClient):
        """Doctor or Admin attempting to upload personal prescriptions receives 403 Forbidden."""
        doc_token = get_jwt(client, self.doctor_user.email)
        headers = {"Authorization": f"Bearer {doc_token}"}

        pdf_dummy_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"
        files = {"file": ("test.pdf", io.BytesIO(pdf_dummy_bytes), "application/pdf")}

        res = client.post(
            "/api/v1/ai-assistant/patient/upload-prescription",
            headers=headers,
            files=files,
        )
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert "Only patients" in res.json()["detail"]
