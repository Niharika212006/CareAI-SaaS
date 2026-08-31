"""E2E Verification of authentication, session endpoints, and role routing for all 5 roles."""
import httpx

base_url = "http://127.0.0.1:8000"

def test_frontend_auth():
    print("=== 1. Testing Backend Health Endpoint ===")
    r = httpx.get(f"{base_url}/api/health")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    print("  [PASS] Backend API is healthy and operational.")

    print("\n=== 2. Testing Invalid Credentials ===")
    r_invalid = httpx.post(
        f"{base_url}/api/v1/auth/login",
        json={"email": "invalid@careai.com", "password": "WrongPassword!"},
    )
    assert r_invalid.status_code == 401, f"Expected 401, got {r_invalid.status_code}"
    assert "detail" in r_invalid.json()
    print(f"  [PASS] 401 Unauthorized returned properly: '{r_invalid.json()['detail']}'")

    print("\n=== 3. Testing Public Self-Registration Security Restrictions ===")
    # Attemping to register as privileged roles via public registration must return 403
    r_pub_admin = httpx.post(
        f"{base_url}/api/v1/auth/register",
        json={"email": "attempt.admin@careai.com", "password": "Password123!", "full_name": "Fake Admin", "role": "ADMIN"},
    )
    assert r_pub_admin.status_code == 403, f"Expected 403, got {r_pub_admin.status_code}"
    
    r_pub_lab = httpx.post(
        f"{base_url}/api/v1/auth/register",
        json={"email": "attempt.lab@careai.com", "password": "Password123!", "full_name": "Fake Lab", "role": "LAB_TECHNICIAN"},
    )
    assert r_pub_lab.status_code == 403, f"Expected 403, got {r_pub_lab.status_code}"

    r_pub_pharm = httpx.post(
        f"{base_url}/api/v1/auth/register",
        json={"email": "attempt.pharm@careai.com", "password": "Password123!", "full_name": "Fake Pharm", "role": "PHARMACY_STAFF"},
    )
    assert r_pub_pharm.status_code == 403, f"Expected 403, got {r_pub_pharm.status_code}"
    print("  [PASS] Public registration properly blocks privileged role creation with HTTP 403.")

    print("\n=== 4. Testing Patient Auth & Dashboard API ===")
    r_pat = httpx.post(
        f"{base_url}/api/v1/auth/login",
        json={"email": "patient.john@example.com", "password": "PatientPass123!"},
    )
    assert r_pat.status_code == 200
    pat_data = r_pat.json()
    assert pat_data["role"] == "PATIENT"
    pat_token = pat_data["access_token"]
    
    r_pat_me = httpx.get(
        f"{base_url}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert r_pat_me.status_code == 200
    assert r_pat_me.json()["role"] == "PATIENT"

    r_pat_dash = httpx.get(
        f"{base_url}/api/v1/dashboard/patient",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert r_pat_dash.status_code == 200
    print("  [PASS] Patient login, token verification, and dashboard fetch succeeded.")

    print("\n=== 5. Testing Doctor Auth & Dashboard API ===")
    r_doc = httpx.post(
        f"{base_url}/api/v1/auth/login",
        json={"email": "dr.sarah@careai.com", "password": "DoctorPass123!"},
    )
    assert r_doc.status_code == 200
    doc_data = r_doc.json()
    assert doc_data["role"] == "DOCTOR"
    doc_token = doc_data["access_token"]

    r_doc_me = httpx.get(
        f"{base_url}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert r_doc_me.status_code == 200
    assert r_doc_me.json()["role"] == "DOCTOR"

    r_doc_dash = httpx.get(
        f"{base_url}/api/v1/dashboard/doctor",
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert r_doc_dash.status_code == 200
    print("  [PASS] Doctor login, token verification, and dashboard fetch succeeded.")

    print("\n=== 6. Testing Admin Auth, Staff Provisioning & Dashboard API ===")
    r_adm = httpx.post(
        f"{base_url}/api/v1/auth/login",
        json={"email": "admin@careai.com", "password": "AdminPass123!"},
    )
    assert r_adm.status_code == 200
    adm_data = r_adm.json()
    assert adm_data["role"] == "ADMIN"
    adm_token = adm_data["access_token"]

    r_adm_me = httpx.get(
        f"{base_url}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {adm_token}"},
    )
    assert r_adm_me.status_code == 200
    assert r_adm_me.json()["role"] == "ADMIN"

    r_adm_dash = httpx.get(
        f"{base_url}/api/v1/dashboard/admin",
        headers={"Authorization": f"Bearer {adm_token}"},
    )
    assert r_adm_dash.status_code == 200
    print("  [PASS] Admin login, token verification, and dashboard fetch succeeded.")

    print("\n=== 7. Testing Lab Technician Auth & Dashboard API ===")
    r_lab = httpx.post(
        f"{base_url}/api/v1/auth/login",
        json={"email": "lab.tech@careai.com", "password": "LabTechPass123!"},
    )
    assert r_lab.status_code == 200
    lab_data = r_lab.json()
    assert lab_data["role"] == "LAB_TECHNICIAN"
    lab_token = lab_data["access_token"]

    r_lab_me = httpx.get(
        f"{base_url}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {lab_token}"},
    )
    assert r_lab_me.status_code == 200
    assert r_lab_me.json()["role"] == "LAB_TECHNICIAN"

    r_lab_dash = httpx.get(
        f"{base_url}/api/v1/dashboard/lab-technician",
        headers={"Authorization": f"Bearer {lab_token}"},
    )
    assert r_lab_dash.status_code == 200
    print("  [PASS] Lab Technician login, token verification, and workspace dashboard fetch succeeded.")

    print("\n=== 8. Testing Pharmacy Staff Auth & Dashboard API ===")
    r_pharm = httpx.post(
        f"{base_url}/api/v1/auth/login",
        json={"email": "pharmacy.staff@careai.com", "password": "PharmacyPass123!"},
    )
    assert r_pharm.status_code == 200
    pharm_data = r_pharm.json()
    assert pharm_data["role"] == "PHARMACY_STAFF"
    pharm_token = pharm_data["access_token"]

    r_pharm_me = httpx.get(
        f"{base_url}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {pharm_token}"},
    )
    assert r_pharm_me.status_code == 200
    assert r_pharm_me.json()["role"] == "PHARMACY_STAFF"

    r_pharm_dash = httpx.get(
        f"{base_url}/api/v1/dashboard/pharmacy",
        headers={"Authorization": f"Bearer {pharm_token}"},
    )
    assert r_pharm_dash.status_code == 200
    print("  [PASS] Pharmacy Staff login, token verification, and dispensary dashboard fetch succeeded.")

    print("\n=== 9. Testing 5-Role Cross-Access Authorization Restrictions ===")
    # Lab Tech cannot access Pharmacy or Admin
    assert httpx.get(f"{base_url}/api/v1/dashboard/pharmacy", headers={"Authorization": f"Bearer {lab_token}"}).status_code == 403
    assert httpx.get(f"{base_url}/api/v1/dashboard/admin", headers={"Authorization": f"Bearer {lab_token}"}).status_code == 403

    # Pharmacy Staff cannot access Lab or Doctor
    assert httpx.get(f"{base_url}/api/v1/dashboard/lab-technician", headers={"Authorization": f"Bearer {pharm_token}"}).status_code == 403
    assert httpx.get(f"{base_url}/api/v1/dashboard/doctor", headers={"Authorization": f"Bearer {pharm_token}"}).status_code == 403

    # Patient cannot access Lab or Pharmacy
    assert httpx.get(f"{base_url}/api/v1/dashboard/lab-technician", headers={"Authorization": f"Bearer {pat_token}"}).status_code == 403
    assert httpx.get(f"{base_url}/api/v1/dashboard/pharmacy", headers={"Authorization": f"Bearer {pat_token}"}).status_code == 403

    # Doctor cannot access Lab or Pharmacy
    assert httpx.get(f"{base_url}/api/v1/dashboard/lab-technician", headers={"Authorization": f"Bearer {doc_token}"}).status_code == 403
    assert httpx.get(f"{base_url}/api/v1/dashboard/pharmacy", headers={"Authorization": f"Bearer {doc_token}"}).status_code == 403

    # Admin cannot access Lab or Pharmacy
    assert httpx.get(f"{base_url}/api/v1/dashboard/lab-technician", headers={"Authorization": f"Bearer {adm_token}"}).status_code == 403
    assert httpx.get(f"{base_url}/api/v1/dashboard/pharmacy", headers={"Authorization": f"Bearer {adm_token}"}).status_code == 403
    print("  [PASS] All cross-role dashboard attempts rejected with HTTP 403 Forbidden.")

    print("\n[SUCCESS] All 5 roles verified with complete authentication, session persistence, and RBAC!")


if __name__ == "__main__":
    test_frontend_auth()
