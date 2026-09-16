"""Comprehensive test suite verifying the CareAI Clinical Intelligence Engine and AI configuration."""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.ai.client import ai_client
from app.ai.clinical_engine import clinical_engine, ClinicalEngine


def create_user(db: Session, email: str, role: UserRole, full_name: str) -> User:
    """Helper to persist user for testing."""
    user = User(
        email=email.lower(),
        hashed_password=get_password_hash("Pass123!"),
        full_name=full_name,
        role=role,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_token(client: TestClient, email: str, password: str = "Pass123!") -> str:
    """Obtain JWT token for user."""
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == status.HTTP_200_OK
    return res.json()["access_token"]


class TestClinicalEngine:
    """Unit tests for the Clinical Intelligence Engine."""

    def test_different_conditions_produce_distinct_content(self):
        """Verify that fever, headache, diabetes, asthma, dengue produce unique, distinct responses."""
        resp_fever = clinical_engine.generate_clinical_response("What causes fever and how to treat it?", UserRole.PATIENT)
        resp_headache = clinical_engine.generate_clinical_response("What causes severe headache?", UserRole.PATIENT)
        resp_diabetes = clinical_engine.generate_clinical_response("What is diabetes and fasting blood sugar?", UserRole.PATIENT)
        resp_dengue = clinical_engine.generate_clinical_response("What are warning signs of dengue fever?", UserRole.PATIENT)

        # Confirm non-empty
        assert len(resp_fever) > 100
        assert len(resp_headache) > 100
        assert len(resp_diabetes) > 100
        assert len(resp_dengue) > 100

        # Confirm content specificity
        assert "Pyrexia" in resp_fever or "Fever" in resp_fever
        assert "Paracetamol" in resp_fever
        assert "Headache" in resp_headache or "Cephalea" in resp_headache
        assert "Diabetes" in resp_diabetes or "Hyperglycemia" in resp_diabetes
        assert "Dengue" in resp_dengue
        assert "Aedes" in resp_dengue or "Platelet" in resp_dengue

        # Ensure responses are distinct from each other
        assert resp_fever != resp_headache
        assert resp_fever != resp_diabetes
        assert resp_headache != resp_dengue

    def test_role_adapted_guidance(self):
        """Verify that the same clinical entity yields role-tailored content."""
        query = "What should I know about hypertension?"

        resp_patient = clinical_engine.generate_clinical_response(query, UserRole.PATIENT)
        resp_doctor = clinical_engine.generate_clinical_response(query, UserRole.DOCTOR)
        resp_lab = clinical_engine.generate_clinical_response(query, UserRole.LAB_TECHNICIAN)
        resp_pharmacy = clinical_engine.generate_clinical_response(query, UserRole.PHARMACY_STAFF)

        # Patient sees DASH diet / lifestyle
        assert "DASH" in resp_patient or "lifestyle" in resp_patient.lower()

        # Doctor sees stage classification / clinical management
        assert "Stage" in resp_doctor or "ACC/AHA" in resp_doctor or "Physician Clinical Decision Support" in resp_doctor

        # Lab tech sees baseline tests and specimen requirements
        assert "Laboratory" in resp_lab or "Creatinine" in resp_lab

        # Pharmacist sees drug classes / pharmacology
        assert "ACE Inhibitors" in resp_pharmacy or "Pharmacotherapeutic" in resp_pharmacy

    def test_medication_query_coverage(self):
        """Verify medications like Paracetamol, Ibuprofen, Metformin, Amoxicillin provide deep profiles."""
        resp_para = clinical_engine.generate_clinical_response("What is paracetamol dosage and side effects?", UserRole.PATIENT)
        resp_metformin = clinical_engine.generate_clinical_response("How to take metformin?", UserRole.PATIENT)
        resp_amox = clinical_engine.generate_clinical_response("What is amoxicillin used for?", UserRole.PATIENT)

        assert "Paracetamol" in resp_para
        assert "500 mg" in resp_para or "4000 mg" in resp_para
        assert "Metformin" in resp_metformin
        assert "Amoxicillin" in resp_amox

    def test_lab_test_query_coverage(self):
        """Verify diagnostic tests like CBC, CMP, HbA1c, Troponin provide reference ranges and interpretations."""
        resp_cbc = clinical_engine.generate_clinical_response("Explain complete blood count CBC results", UserRole.PATIENT)
        resp_hba1c = clinical_engine.generate_clinical_response("What does my HbA1c result mean?", UserRole.PATIENT)
        resp_troponin = clinical_engine.generate_clinical_response("What is cardiac troponin I?", UserRole.DOCTOR)

        assert "Complete Blood Count" in resp_cbc or "CBC" in resp_cbc
        assert "Reference Interval" in resp_cbc
        assert "HbA1c" in resp_hba1c
        assert "Troponin" in resp_troponin

    def test_emergency_red_flag_alert_banner(self):
        """Verify acute emergency queries trigger emergency alert banner."""
        resp = clinical_engine.generate_clinical_response("I have severe crushing chest pain and shortness of breath", UserRole.PATIENT)
        assert "CRITICAL EMERGENCY MEDICAL ALERT" in resp
        assert "Call emergency services" in resp

    def test_arbitrary_unmatched_query_synthesizer(self):
        """Verify unmatched questions do not return static 3-bullet templates, but synthesize dynamic clinical insights."""
        q1 = "What are the benefits of staying hydrated during physical exercise?"
        q2 = "Can chronic lack of sleep impact cognitive focus and memory retention?"

        resp1 = clinical_engine.generate_clinical_response(q1, UserRole.PATIENT)
        resp2 = clinical_engine.generate_clinical_response(q2, UserRole.PATIENT)

        assert "Hydrated" in resp1 or "Exercise" in resp1 or "Clinical Insights" in resp1
        assert "Sleep" in resp2 or "Cognitive" in resp2 or "Clinical Insights" in resp2
        assert resp1 != resp2


class TestAIConfigEndpoints:
    """Integration tests for AI Assistant status and configuration endpoints."""

    def test_get_ai_config(self, client: TestClient, db_session: Session):
        """Verify GET /api/v1/ai-assistant/config returns operational metadata."""
        user = create_user(db_session, "pat.config@careai.com", UserRole.PATIENT, "Pat Config")
        token = get_auth_token(client, "pat.config@careai.com")

        res = client.get("/api/v1/ai-assistant/config", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert "provider" in data
        assert "model_name" in data
        assert "has_live_credentials" in data
        assert "active_engine" in data
        assert "is_live_ai" in data

    def test_update_ai_config_runtime(self, client: TestClient, db_session: Session):
        """Verify POST /api/v1/ai-assistant/config dynamically updates the AI key."""
        user = create_user(db_session, "admin.config@careai.com", UserRole.ADMIN, "Admin Config")
        token = get_auth_token(client, "admin.config@careai.com")

        # Set mock key
        test_key = "AIzaSyFakeTestKeyForValidation123456"
        res = client.post(
            "/api/v1/ai-assistant/config",
            headers={"Authorization": f"Bearer {token}"},
            json={"api_key": test_key},
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["status"] == "success"
        assert data["config"]["has_live_credentials"] is True

        # Clear key
        res_clear = client.post(
            "/api/v1/ai-assistant/config",
            headers={"Authorization": f"Bearer {token}"},
            json={"api_key": ""},
        )
        assert res_clear.status_code == status.HTTP_200_OK
        assert res_clear.json()["config"]["has_live_credentials"] is False

    def test_chat_uses_clinical_engine_dynamically(self, client: TestClient, db_session: Session):
        """Verify live chat turn invokes Clinical Engine and returns distinct, tailored answers."""
        user = create_user(db_session, "patient.dynamic@careai.com", UserRole.PATIENT, "Dynamic Patient")
        token = get_auth_token(client, "patient.dynamic@careai.com")

        # Query 1: Dengue
        r1 = client.post(
            "/api/v1/ai-assistant/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "What should I know about dengue fever and hydration?"},
        )
        assert r1.status_code == status.HTTP_200_OK
        text1 = r1.json()["assistant_response"]
        assert "Dengue" in text1
        assert "Hydration" in text1 or "fluids" in text1.lower()

        # Query 2: Migraine
        r2 = client.post(
            "/api/v1/ai-assistant/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "What triggers a migraine and how can I prevent it?"},
        )
        assert r2.status_code == status.HTTP_200_OK
        text2 = r2.json()["assistant_response"]
        assert "Migraine" in text2

        # Verify they are completely different
        assert text1 != text2
