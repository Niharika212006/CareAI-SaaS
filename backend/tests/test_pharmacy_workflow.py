"""Comprehensive automated tests for Pharmacy Staff workflow, dispensing, and safety alerts."""
from datetime import datetime, date, timedelta
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.patient import PatientProfile
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription, PrescriptionItem, PrescriptionStatus
from app.models.ai_report import AIAnalysisReport, InteractionSeverity
from app.core.security import get_password_hash, create_access_token


def create_test_user(
    db: Session,
    email: str,
    role: UserRole,
    full_name: str,
    specialization: str = "General Medicine",
) -> User:
    """Helper to persist user and domain profile."""
    user = User(
        email=email.lower(),
        hashed_password=get_password_hash("SecretPass123!"),
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
            gender="Female",
            date_of_birth=date(1990, 5, 15),
            blood_group="A+",
            allergies=[{"name": "Amoxicillin", "severity": "HIGH"}],
            chronic_conditions=["Asthma"],
            current_medications=[{"name": "Albuterol"}],
        )
        db.add(profile)

    elif role == UserRole.DOCTOR:
        profile = DoctorProfile(
            user_id=user.id,
            specialization=specialization,
            license_number=f"LIC-PHARM-{user.id}",
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


class TestPharmacyWorkflow:
    """Test verification for Pharmacy Staff clinical dispensary operations."""

    @pytest.fixture(autouse=True)
    def setup_pharmacy_fixtures(self, db_session: Session):
        """Seed test database with pharmacy staff, doctor, patient, and clinical prescription."""
        self.pharm_user = create_test_user(
            db_session, "pharmacy.elena@careai.com", UserRole.PHARMACY_STAFF, "Elena Rostova"
        )
        self.doctor_user = create_test_user(
            db_session, "dr.watson@careai.com", UserRole.DOCTOR, "Dr. John Watson", "Cardiology"
        )
        self.patient_user = create_test_user(
            db_session, "patient.clara@example.com", UserRole.PATIENT, "Clara Oswald"
        )
        self.admin_user = create_test_user(
            db_session, "admin.gov@careai.com", UserRole.ADMIN, "Platform Admin"
        )

        pat_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == self.patient_user.id).first()
        doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == self.doctor_user.id).first()

        # Create consultation appointment
        self.appt = Appointment(
            patient_id=pat_prof.id,
            doctor_id=doc_prof.id,
            scheduled_start=datetime.now() - timedelta(days=1),
            scheduled_end=datetime.now() - timedelta(days=1, minutes=30),
            status=AppointmentStatus.COMPLETED,
            reason="Hypertension Followup",
        )
        db_session.add(self.appt)
        db_session.flush()

        # Create Prescription
        self.rx = Prescription(
            patient_id=pat_prof.id,
            doctor_id=doc_prof.id,
            appointment_id=self.appt.id,
            diagnosis="Essential Primary Hypertension",
            clinical_notes="Patient instructed on low sodium diet and regular blood pressure monitoring.",
            status=PrescriptionStatus.PRESCRIBED,
            valid_until=date.today() + timedelta(days=30),
        )
        db_session.add(self.rx)
        db_session.flush()

        # Add medication items
        self.item1 = PrescriptionItem(
            prescription_id=self.rx.id,
            medication_name="Lisinopril",
            drug_name="Lisinopril",
            dosage="10 mg",
            frequency="Once daily in the morning",
            duration="30 days",
            route_of_administration="Oral",
            instructions="Take with a full glass of water.",
        )
        self.item2 = PrescriptionItem(
            prescription_id=self.rx.id,
            medication_name="Hydrochlorothiazide",
            drug_name="Hydrochlorothiazide",
            dosage="12.5 mg",
            frequency="Once daily",
            duration="30 days",
            route_of_administration="Oral",
            instructions="Take in the morning.",
        )
        db_session.add(self.item1)
        db_session.add(self.item2)

        # Add AI safety report with HIGH risk
        self.ai_report = AIAnalysisReport(
            prescription_id=self.rx.id,
            patient_id=pat_prof.id,
            overall_risk_level=InteractionSeverity.HIGH,
            total_findings=1,
            findings=[
                {
                    "category": "DRUG_DRUG",
                    "severity": "HIGH",
                    "medications": ["Lisinopril", "Hydrochlorothiazide"],
                    "title": "Lisinopril + Hydrochlorothiazide Synergy",
                    "explanation": "Additive hypotensive effect. Monitor blood pressure and electrolytes.",
                    "recommended_action": "Counsel patient regarding postural hypotension.",
                }
            ],
            drug_drug_interactions=[
                {
                    "category": "DRUG_DRUG",
                    "severity": "HIGH",
                    "medications": ["Lisinopril", "Hydrochlorothiazide"],
                    "title": "Lisinopril + Hydrochlorothiazide Synergy",
                    "explanation": "Additive hypotensive effect. Monitor blood pressure and electrolytes.",
                    "recommended_action": "Counsel patient regarding postural hypotension.",
                }
            ],
            drug_food_interactions=[],
            drug_allergy_interactions=[],
            clinical_summary="Combination requires baseline renal panel and electrolyte monitoring.",
            ai_recommendations="Counsel patient regarding postural hypotension symptoms.",
            disclaimer="AI safety insights are informational decision-support tools and do not replace professional clinical judgment.",
            analysis_status="COMPLETED",
        )
        db_session.add(self.ai_report)
        db_session.commit()


    def test_pharmacy_dashboard_real_statistics(self, client: TestClient):
        """Verify Pharmacy dashboard returns real database-backed metrics and queue items."""
        headers = get_token_header(self.pharm_user)
        res = client.get("/api/v1/pharmacy/dashboard", headers=headers)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()

        assert data["role"] == "PHARMACY_STAFF"
        assert "stats" in data
        assert data["stats"]["pending_dispensations"] >= 1
        assert data["stats"]["high_risk_alerts_count"] >= 1
        assert len(data["pending_dispensations"]) >= 1
        assert data["pending_dispensations"][0]["patient_name"] == "Clara Oswald"

    def test_pharmacy_queue_listing_and_filtering(self, client: TestClient):
        """Verify pharmacy staff can list, search, and filter prescriptions."""
        headers = get_token_header(self.pharm_user)

        # 1. List all
        res_all = client.get("/api/v1/pharmacy/prescriptions", headers=headers)
        assert res_all.status_code == status.HTTP_200_OK
        items = res_all.json()
        assert len(items) >= 1
        assert items[0]["id"] == self.rx.id
        assert items[0]["status"] == "PRESCRIBED"
        assert items[0]["has_ai_report"] is True
        assert items[0]["ai_risk_level"] == "HIGH"

        # 2. Filter by status
        res_filtered = client.get("/api/v1/pharmacy/prescriptions?status=PRESCRIBED", headers=headers)
        assert res_filtered.status_code == status.HTTP_200_OK
        assert len(res_filtered.json()) >= 1

        # 3. Filter by non-matching status
        res_empty = client.get("/api/v1/pharmacy/prescriptions?status=DISPENSED", headers=headers)
        assert res_empty.status_code == status.HTTP_200_OK
        assert len(res_empty.json()) == 0

        # 4. Search by patient name
        res_search = client.get("/api/v1/pharmacy/prescriptions?search=Clara", headers=headers)
        assert res_search.status_code == status.HTTP_200_OK
        assert len(res_search.json()) >= 1

    def test_pharmacy_prescription_details_with_safety_report(self, client: TestClient):
        """Verify pharmacy staff can view full prescription record with AI safety insights."""
        headers = get_token_header(self.pharm_user)
        res = client.get(f"/api/v1/pharmacy/prescriptions/{self.rx.id}", headers=headers)
        assert res.status_code == status.HTTP_200_OK
        detail = res.json()

        assert detail["id"] == self.rx.id
        assert detail["diagnosis"] == "Essential Primary Hypertension"
        assert len(detail["items"]) == 2
        assert detail["items"][0]["medication_name"] == "Lisinopril"
        assert detail["items"][1]["medication_name"] == "Hydrochlorothiazide"
        assert detail["latest_ai_report"] is not None
        assert detail["latest_ai_report"]["overall_risk_level"] == "HIGH"
        assert "decision-support" in detail["latest_ai_report"]["disclaimer"].lower()

    def test_pharmacy_status_transitions_and_dispense_action(self, client: TestClient):
        """Verify complete status lifecycle: PRESCRIBED -> UNDER_REVIEW -> READY -> DISPENSED."""
        headers = get_token_header(self.pharm_user)

        # 1. Move to UNDER_REVIEW
        r1 = client.patch(
            f"/api/v1/pharmacy/prescriptions/{self.rx.id}/status",
            headers=headers,
            json={"status": "UNDER_REVIEW", "pharmacy_notes": "Pharmacist reviewing drug interactions."},
        )
        assert r1.status_code == status.HTTP_200_OK
        assert r1.json()["status"] == "UNDER_REVIEW"
        assert r1.json()["pharmacy_notes"] == "Pharmacist reviewing drug interactions."

        # 2. Move to READY
        r2 = client.patch(
            f"/api/v1/pharmacy/prescriptions/{self.rx.id}/status",
            headers=headers,
            json={"status": "READY", "pharmacy_notes": "Packaged and staged in Bin #12."},
        )
        assert r2.status_code == status.HTTP_200_OK
        assert r2.json()["status"] == "READY"

        # 3. Dispense
        r3 = client.post(
            f"/api/v1/pharmacy/prescriptions/{self.rx.id}/dispense",
            headers=headers,
            json={"pharmacy_notes": "Dispensed to patient in person. Verified ID."},
        )
        assert r3.status_code == status.HTTP_200_OK
        assert r3.json()["status"] == "DISPENSED"
        assert r3.json()["dispensed_at"] is not None
        assert r3.json()["dispensed_by_name"] == "Elena Rostova"

    def test_doctor_prescription_immutability_by_pharmacy(self, client: TestClient):
        """Verify pharmacy staff cannot create prescriptions or alter doctor clinical diagnosis/dosages."""
        pharm_headers = get_token_header(self.pharm_user)

        # Attempt to create a prescription as pharmacy staff (Forbidden 403)
        res_create = client.post(
            "/api/v1/prescriptions",
            headers=pharm_headers,
            json={
                "appointment_id": self.appt.id,
                "diagnosis": "Tampered Diagnosis",
                "items": [{"medication_name": "Unauthorized Drug", "dosage": "100mg", "frequency": "Daily", "duration": "10d"}],
            },
        )
        assert res_create.status_code == status.HTTP_403_FORBIDDEN

    def test_rbac_cross_role_access_rejections(self, client: TestClient):
        """Verify patients and doctors cannot access or mutate pharmacy-only endpoints."""
        pat_headers = get_token_header(self.patient_user)
        doc_headers = get_token_header(self.doctor_user)

        # Patient -> Pharmacy Queue (403)
        assert client.get("/api/v1/pharmacy/prescriptions", headers=pat_headers).status_code == status.HTTP_403_FORBIDDEN
        # Patient -> Pharmacy Status Mutation (403)
        assert client.patch(
            f"/api/v1/pharmacy/prescriptions/{self.rx.id}/status",
            headers=pat_headers,
            json={"status": "DISPENSED"},
        ).status_code == status.HTTP_403_FORBIDDEN

        # Doctor -> Pharmacy Status Mutation (403)
        assert client.patch(
            f"/api/v1/pharmacy/prescriptions/{self.rx.id}/status",
            headers=doc_headers,
            json={"status": "DISPENSED"},
        ).status_code == status.HTTP_403_FORBIDDEN

        # Unauthenticated -> 401
        assert client.get("/api/v1/pharmacy/prescriptions").status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
