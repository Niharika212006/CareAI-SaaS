"""E2E Verification of authentication, session endpoints, and role routing."""
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

    print("\n=== 3. Testing Patient Auth & Dashboard API ===")
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
    print("  [PASS] Patient login, token session verification, and patient dashboard fetch succeeded.")

    print("\n=== 4. Testing Doctor Auth & Dashboard API ===")
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
    print("  [PASS] Doctor login, token session verification, and clinical dashboard fetch succeeded.")

    print("\n=== 5. Testing Admin Auth & Dashboard API ===")
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
    print("  [PASS] Admin login, token session verification, and oversight dashboard fetch succeeded.")

    print("\n=== 6. Testing Cross-Role Authorization Enforcement ===")
    # Patient trying to access Doctor dashboard API
    r_unauth_doc = httpx.get(
        f"{base_url}/api/v1/dashboard/doctor",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert r_unauth_doc.status_code == 403, f"Expected 403, got {r_unauth_doc.status_code}"

    # Patient trying to access Admin dashboard API
    r_unauth_adm = httpx.get(
        f"{base_url}/api/v1/dashboard/admin",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert r_unauth_adm.status_code == 403, f"Expected 403, got {r_unauth_adm.status_code}"

    # Doctor trying to access Admin dashboard API
    r_doc_unauth_adm = httpx.get(
        f"{base_url}/api/v1/dashboard/admin",
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert r_doc_unauth_adm.status_code == 403, f"Expected 403, got {r_doc_unauth_adm.status_code}"
    print("  [PASS] Cross-role access properly rejected with HTTP 403 Forbidden.")

    print("\n[SUCCESS] All authentication, token verification, role routing, and RBAC permissions verified 100% operational!")


if __name__ == "__main__":
    test_frontend_auth()
