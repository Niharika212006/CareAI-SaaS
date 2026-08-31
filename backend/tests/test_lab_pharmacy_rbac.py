"""Test Suite for Lab Technician and Pharmacy Staff Authentication and RBAC Foundation."""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.core.security import get_password_hash


def create_test_user(
    db: Session,
    email: str,
    password: str,
    role: UserRole,
    full_name: str,
) -> User:
    """Helper to persist user in test database."""
    user = User(
        email=email.lower(),
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=role,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestLabPharmacyAuthAndRBAC:
    """Test verification for Lab Technician and Pharmacy Staff roles."""

    @pytest.fixture(autouse=True)
    def setup_users(self, db_session: Session):
        """Seed test database with 5 roles for RBAC verification."""
        create_test_user(
            db_session, "lab.tech@careai.com", "LabTechPass123!", UserRole.LAB_TECHNICIAN, "Alex Rivera"
        )
        create_test_user(
            db_session, "pharmacy.staff@careai.com", "PharmacyPass123!", UserRole.PHARMACY_STAFF, "Elena Rostova"
        )
        create_test_user(
            db_session, "patient.john@example.com", "PatientPass123!", UserRole.PATIENT, "John Doe"
        )
        create_test_user(
            db_session, "dr.sarah@careai.com", "DoctorPass123!", UserRole.DOCTOR, "Dr. Sarah"
        )
        create_test_user(
            db_session, "admin@careai.com", "AdminPass123!", UserRole.ADMIN, "Admin User"
        )

    def test_lab_technician_login_and_me(self, client: TestClient, db_session: Session):
        """Verify lab technician can login and /auth/me returns LAB_TECHNICIAN role."""
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "lab.tech@careai.com", "password": "LabTechPass123!"},
        )
        assert login_res.status_code == status.HTTP_200_OK
        data = login_res.json()
        assert data["role"] == "LAB_TECHNICIAN"
        assert "access_token" in data
        token = data["access_token"]

        me_res = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == status.HTTP_200_OK
        me_data = me_res.json()
        assert me_data["role"] == "LAB_TECHNICIAN"
        assert me_data["email"] == "lab.tech@careai.com"

    def test_pharmacy_staff_login_and_me(self, client: TestClient, db_session: Session):
        """Verify pharmacy staff can login and /auth/me returns PHARMACY_STAFF role."""
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "pharmacy.staff@careai.com", "password": "PharmacyPass123!"},
        )
        assert login_res.status_code == status.HTTP_200_OK
        data = login_res.json()
        assert data["role"] == "PHARMACY_STAFF"
        assert "access_token" in data
        token = data["access_token"]

        me_res = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == status.HTTP_200_OK
        me_data = me_res.json()
        assert me_data["role"] == "PHARMACY_STAFF"
        assert me_data["email"] == "pharmacy.staff@careai.com"

    def test_lab_technician_dashboard_access(self, client: TestClient, db_session: Session):
        """Verify lab technician gets 200 on /dashboard/lab-technician."""
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "lab.tech@careai.com", "password": "LabTechPass123!"},
        )
        token = login_res.json()["access_token"]

        dash_res = client.get(
            "/api/v1/dashboard/lab-technician",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert dash_res.status_code == status.HTTP_200_OK
        dash_data = dash_res.json()
        assert dash_data["role"] == "LAB_TECHNICIAN"
        assert "stats" in dash_data
        assert "pending_tasks" in dash_data

    def test_pharmacy_dashboard_access(self, client: TestClient, db_session: Session):
        """Verify pharmacy staff gets 200 on /dashboard/pharmacy."""
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "pharmacy.staff@careai.com", "password": "PharmacyPass123!"},
        )
        token = login_res.json()["access_token"]

        dash_res = client.get(
            "/api/v1/dashboard/pharmacy",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert dash_res.status_code == status.HTTP_200_OK
        dash_data = dash_res.json()
        assert dash_data["role"] == "PHARMACY_STAFF"
        assert "stats" in dash_data
        assert "pending_dispensations" in dash_data

    def test_lab_technician_cross_role_restrictions(self, client: TestClient, db_session: Session):
        """Verify lab technician cannot access other roles' dashboards (403)."""
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "lab.tech@careai.com", "password": "LabTechPass123!"},
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Denied from pharmacy
        r_pharm = client.get("/api/v1/dashboard/pharmacy", headers=headers)
        assert r_pharm.status_code == status.HTTP_403_FORBIDDEN

        # Denied from patient
        r_patient = client.get("/api/v1/dashboard/patient", headers=headers)
        assert r_patient.status_code == status.HTTP_403_FORBIDDEN

        # Denied from doctor
        r_doc = client.get("/api/v1/dashboard/doctor", headers=headers)
        assert r_doc.status_code == status.HTTP_403_FORBIDDEN

        # Denied from admin
        r_admin = client.get("/api/v1/dashboard/admin", headers=headers)
        assert r_admin.status_code == status.HTTP_403_FORBIDDEN

    def test_pharmacy_staff_cross_role_restrictions(self, client: TestClient, db_session: Session):
        """Verify pharmacy staff cannot access other roles' dashboards (403)."""
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "pharmacy.staff@careai.com", "password": "PharmacyPass123!"},
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Denied from lab
        r_lab = client.get("/api/v1/dashboard/lab-technician", headers=headers)
        assert r_lab.status_code == status.HTTP_403_FORBIDDEN

        # Denied from patient
        r_patient = client.get("/api/v1/dashboard/patient", headers=headers)
        assert r_patient.status_code == status.HTTP_403_FORBIDDEN

        # Denied from doctor
        r_doc = client.get("/api/v1/dashboard/doctor", headers=headers)
        assert r_doc.status_code == status.HTTP_403_FORBIDDEN

        # Denied from admin
        r_admin = client.get("/api/v1/dashboard/admin", headers=headers)
        assert r_admin.status_code == status.HTTP_403_FORBIDDEN

    def test_patient_doctor_admin_cannot_access_lab_or_pharmacy(self, client: TestClient, db_session: Session):
        """Verify Patient, Doctor, and Admin cannot access lab or pharmacy endpoints."""
        # 1. Patient
        pat_login = client.post(
            "/api/v1/auth/login",
            json={"email": "patient.john@example.com", "password": "PatientPass123!"},
        )
        pat_headers = {"Authorization": f"Bearer {pat_login.json()['access_token']}"}
        assert client.get("/api/v1/dashboard/lab-technician", headers=pat_headers).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/dashboard/pharmacy", headers=pat_headers).status_code == status.HTTP_403_FORBIDDEN

        # 2. Doctor
        doc_login = client.post(
            "/api/v1/auth/login",
            json={"email": "dr.sarah@careai.com", "password": "DoctorPass123!"},
        )
        doc_headers = {"Authorization": f"Bearer {doc_login.json()['access_token']}"}
        assert client.get("/api/v1/dashboard/lab-technician", headers=doc_headers).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/dashboard/pharmacy", headers=doc_headers).status_code == status.HTTP_403_FORBIDDEN

        # 3. Admin
        adm_login = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@careai.com", "password": "AdminPass123!"},
        )
        adm_headers = {"Authorization": f"Bearer {adm_login.json()['access_token']}"}
        assert client.get("/api/v1/dashboard/lab-technician", headers=adm_headers).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/dashboard/pharmacy", headers=adm_headers).status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_access_rejected(self, client: TestClient):
        """Verify unauthenticated requests to lab and pharmacy dashboards are rejected (401)."""
        assert client.get("/api/v1/dashboard/lab-technician").status_code == status.HTTP_401_UNAUTHORIZED
        assert client.get("/api/v1/dashboard/pharmacy").status_code == status.HTTP_401_UNAUTHORIZED
