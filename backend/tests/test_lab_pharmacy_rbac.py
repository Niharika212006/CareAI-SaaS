"""Comprehensive Test Suite for 5-Role Authentication, RBAC, and Secure Role Provisioning."""
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


class Test5RoleAuthAndRBAC:
    """Test verification for 5-Role RBAC and secure role creation architecture."""

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

    # -----------------------------------------------------------------------
    # 1. Secure Role Creation Strategy Tests
    # -----------------------------------------------------------------------
    def test_public_registration_rejects_privileged_roles(self, client: TestClient):
        """Verify public registration rejects ADMIN, LAB_TECHNICIAN, and PHARMACY_STAFF (403)."""
        # Attempt to register as ADMIN
        r_admin = client.post(
            "/api/v1/auth/register",
            json={
                "email": "hacker.admin@careai.com",
                "password": "Password123!",
                "full_name": "Fake Admin",
                "role": "ADMIN",
            },
        )
        assert r_admin.status_code == status.HTTP_403_FORBIDDEN
        assert "Public registration is restricted" in r_admin.json()["detail"]

        # Attempt to register as LAB_TECHNICIAN
        r_lab = client.post(
            "/api/v1/auth/register",
            json={
                "email": "fake.lab@careai.com",
                "password": "Password123!",
                "full_name": "Fake Lab",
                "role": "LAB_TECHNICIAN",
            },
        )
        assert r_lab.status_code == status.HTTP_403_FORBIDDEN

        # Attempt to register as PHARMACY_STAFF
        r_pharm = client.post(
            "/api/v1/auth/register",
            json={
                "email": "fake.pharm@careai.com",
                "password": "Password123!",
                "full_name": "Fake Pharm",
                "role": "PHARMACY_STAFF",
            },
        )
        assert r_pharm.status_code == status.HTTP_403_FORBIDDEN

    def test_public_registration_permits_patient_and_doctor(self, client: TestClient):
        """Verify public registration succeeds for standard PATIENT and DOCTOR roles."""
        # Register PATIENT
        r_pat = client.post(
            "/api/v1/auth/register",
            json={
                "email": "new.patient@example.com",
                "password": "Password123!",
                "full_name": "New Patient",
                "role": "PATIENT",
            },
        )
        assert r_pat.status_code == status.HTTP_201_CREATED
        assert r_pat.json()["role"] == "PATIENT"

        # Register DOCTOR
        r_doc = client.post(
            "/api/v1/auth/register",
            json={
                "email": "new.doctor@careai.com",
                "password": "Password123!",
                "full_name": "New Doctor",
                "role": "DOCTOR",
            },
        )
        assert r_doc.status_code == status.HTTP_201_CREATED
        assert r_doc.json()["role"] == "DOCTOR"

    def test_admin_can_provision_staff_accounts(self, client: TestClient):
        """Verify admin can provision LAB_TECHNICIAN and PHARMACY_STAFF accounts via /admin/staff."""
        # 1. Admin login
        adm_login = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@careai.com", "password": "AdminPass123!"},
        )
        adm_token = adm_login.json()["access_token"]
        adm_headers = {"Authorization": f"Bearer {adm_token}"}

        # 2. Provision new Lab Tech
        r_prov_lab = client.post(
            "/api/v1/admin/staff",
            headers=adm_headers,
            json={
                "email": "lab.specialist@careai.com",
                "password": "SpecialistPass123!",
                "full_name": "Dr. Clara Oswald",
                "role": "LAB_TECHNICIAN",
            },
        )
        assert r_prov_lab.status_code == status.HTTP_201_CREATED
        assert r_prov_lab.json()["role"] == "LAB_TECHNICIAN"

        # 3. Provision new Pharmacy Staff
        r_prov_pharm = client.post(
            "/api/v1/admin/staff",
            headers=adm_headers,
            json={
                "email": "pharm.dispenser@careai.com",
                "password": "DispenserPass123!",
                "full_name": "Rory Williams",
                "role": "PHARMACY_STAFF",
            },
        )
        assert r_prov_pharm.status_code == status.HTTP_201_CREATED
        assert r_prov_pharm.json()["role"] == "PHARMACY_STAFF"

        # 4. Verify newly provisioned staff can log in
        login_check = client.post(
            "/api/v1/auth/login",
            json={"email": "lab.specialist@careai.com", "password": "SpecialistPass123!"},
        )
        assert login_check.status_code == status.HTTP_200_OK
        assert login_check.json()["role"] == "LAB_TECHNICIAN"

    def test_non_admins_cannot_provision_staff(self, client: TestClient):
        """Verify non-admin users cannot call /admin/staff (403)."""
        # Patient attempt
        pat_login = client.post(
            "/api/v1/auth/login",
            json={"email": "patient.john@example.com", "password": "PatientPass123!"},
        )
        pat_token = pat_login.json()["access_token"]
        r = client.post(
            "/api/v1/admin/staff",
            headers={"Authorization": f"Bearer {pat_token}"},
            json={
                "email": "escalated@careai.com",
                "password": "Password123!",
                "full_name": "Escalated User",
                "role": "ADMIN",
            },
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    # -----------------------------------------------------------------------
    # 2. 5-Role Authentication & Token Verification Tests
    # -----------------------------------------------------------------------
    @pytest.mark.parametrize(
        "email,password,expected_role",
        [
            ("patient.john@example.com", "PatientPass123!", "PATIENT"),
            ("dr.sarah@careai.com", "DoctorPass123!", "DOCTOR"),
            ("admin@careai.com", "AdminPass123!", "ADMIN"),
            ("lab.tech@careai.com", "LabTechPass123!", "LAB_TECHNICIAN"),
            ("pharmacy.staff@careai.com", "PharmacyPass123!", "PHARMACY_STAFF"),
        ],
    )
    def test_login_and_token_for_all_5_roles(self, client: TestClient, email, password, expected_role):
        """Verify successful login, token issuance, and /auth/me profile role for all 5 roles."""
        login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login_res.status_code == status.HTTP_200_OK
        data = login_res.json()
        assert data["role"] == expected_role
        assert "access_token" in data
        token = data["access_token"]

        me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == status.HTTP_200_OK
        assert me_res.json()["role"] == expected_role
        assert me_res.json()["email"] == email

    # -----------------------------------------------------------------------
    # 3. 5-Role Dashboard Access & Cross-Role Rejections
    # -----------------------------------------------------------------------
    def test_lab_technician_dashboard_access_and_isolation(self, client: TestClient):
        """Verify Lab Tech has 200 on /dashboard/lab-technician and 403 on all others."""
        login_res = client.post("/api/v1/auth/login", json={"email": "lab.tech@careai.com", "password": "LabTechPass123!"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Allowed
        assert client.get("/api/v1/dashboard/lab-technician", headers=headers).status_code == status.HTTP_200_OK

        # Denied
        assert client.get("/api/v1/dashboard/pharmacy", headers=headers).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/dashboard/patient", headers=headers).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/dashboard/doctor", headers=headers).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/dashboard/admin", headers=headers).status_code == status.HTTP_403_FORBIDDEN

    def test_pharmacy_staff_dashboard_access_and_isolation(self, client: TestClient):
        """Verify Pharmacy Staff has 200 on /dashboard/pharmacy and 403 on all others."""
        login_res = client.post("/api/v1/auth/login", json={"email": "pharmacy.staff@careai.com", "password": "PharmacyPass123!"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Allowed
        assert client.get("/api/v1/dashboard/pharmacy", headers=headers).status_code == status.HTTP_200_OK

        # Denied
        assert client.get("/api/v1/dashboard/lab-technician", headers=headers).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/dashboard/patient", headers=headers).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/dashboard/doctor", headers=headers).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/dashboard/admin", headers=headers).status_code == status.HTTP_403_FORBIDDEN

    def test_patient_doctor_admin_cross_role_isolation(self, client: TestClient):
        """Verify Patient, Doctor, and Admin cannot access lab or pharmacy endpoints."""
        for email, password in [
            ("patient.john@example.com", "PatientPass123!"),
            ("dr.sarah@careai.com", "DoctorPass123!"),
            ("admin@careai.com", "AdminPass123!"),
        ]:
            token = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            assert client.get("/api/v1/dashboard/lab-technician", headers=headers).status_code == status.HTTP_403_FORBIDDEN
            assert client.get("/api/v1/dashboard/pharmacy", headers=headers).status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_access_rejected(self, client: TestClient):
        """Verify unauthenticated requests are rejected (401)."""
        assert client.get("/api/v1/dashboard/patient").status_code == status.HTTP_401_UNAUTHORIZED
        assert client.get("/api/v1/dashboard/doctor").status_code == status.HTTP_401_UNAUTHORIZED
        assert client.get("/api/v1/dashboard/admin").status_code == status.HTTP_401_UNAUTHORIZED
        assert client.get("/api/v1/dashboard/lab-technician").status_code == status.HTTP_401_UNAUTHORIZED
        assert client.get("/api/v1/dashboard/pharmacy").status_code == status.HTTP_401_UNAUTHORIZED
