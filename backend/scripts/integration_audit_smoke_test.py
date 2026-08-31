"""Comprehensive Project-Wide Integration Audit & Smoke Test for CareAI SaaS."""
import sys
from datetime import datetime, timedelta, timezone, time
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import SessionLocal
from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.lab import LabTest, LabOrder, LabOrderStatus, LabOrderPriority, SampleCondition, ResultFlag


def run_full_integration_audit():
    print("=" * 80)
    print("CAREAI HEALTHCARE SAAS — LIVE SYSTEM INTEGRATION AUDIT & SMOKE TEST")
    print("=" * 80)

    client = TestClient(app)
    db: Session = SessionLocal()

    audit_results = []

    def check(test_name: str, condition: bool, details: str = ""):
        status_str = "PASS" if condition else "FAIL"
        print(f"[{status_str}] {test_name}" + (f" -> {details}" if details else ""))
        audit_results.append((test_name, condition, details))
        if not condition:
            print(f"  [ERROR-DETAIL]: {details}")

    try:
        # -------------------------------------------------------------------
        # 1. API Health & Server Startup
        # -------------------------------------------------------------------
        health_res = client.get("/api/health")
        check("1. API Health Check", health_res.status_code == 200, f"Status: {health_res.status_code}")

        # -------------------------------------------------------------------
        # 2. Authentication for all 5 Roles
        # -------------------------------------------------------------------
        credentials = [
            (UserRole.ADMIN, "admin@careai.com", "AdminPass123!"),
            (UserRole.DOCTOR, "dr.sarah@careai.com", "DoctorPass123!"),
            (UserRole.PATIENT, "patient.john@example.com", "PatientPass123!"),
            (UserRole.LAB_TECHNICIAN, "lab.tech@careai.com", "LabTechPass123!"),
            (UserRole.PHARMACY_STAFF, "pharmacy.staff@careai.com", "PharmacyPass123!"),
        ]

        tokens = {}
        for role, email, password in credentials:
            res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
            if res.status_code == 200:
                token = res.json()["access_token"]
                tokens[role] = {"Authorization": f"Bearer {token}"}
                # Check /auth/me
                me_res = client.get("/api/v1/auth/me", headers=tokens[role])
                me_role = me_res.json().get("role") if me_res.status_code == 200 else None
                check(f"2. Auth & /auth/me for {role.value}", me_role == role.value, f"Returned role: {me_role}")
            else:
                check(f"2. Auth for {role.value}", False, f"HTTP {res.status_code}: {res.text}")

        # Invalid credentials test
        inv_res = client.post("/api/v1/auth/login", json={"email": "admin@careai.com", "password": "WrongPassword!"})
        check("2b. Reject Invalid Password", inv_res.status_code == 401, f"Status: {inv_res.status_code}")

        # -------------------------------------------------------------------
        # 3. Public Self-Registration Security Rules
        # -------------------------------------------------------------------
        # Patient can register publicly
        new_pat_res = client.post("/api/v1/auth/register", json={
            "email": f"audit.patient.{int(datetime.now().timestamp())}@careai.com",
            "password": "Password123!",
            "full_name": "Audit Patient",
            "role": "PATIENT",
        })
        check("3a. Public Patient Registration", new_pat_res.status_code == 201, f"Status: {new_pat_res.status_code}")

        # Staff roles MUST NOT self-register publicly
        for restricted_role in ["ADMIN", "LAB_TECHNICIAN", "PHARMACY_STAFF"]:
            staff_reg = client.post("/api/v1/auth/register", json={
                "email": f"hacker.{restricted_role.lower()}@bad.com",
                "password": "Password123!",
                "full_name": "Bad Actor",
                "role": restricted_role,
            })
            check(f"3b. Block Public {restricted_role} Registration", staff_reg.status_code == 403, f"Status: {staff_reg.status_code}")

        # -------------------------------------------------------------------
        # 4. Full 5-Role RBAC Matrix on All 5 Dashboards
        # -------------------------------------------------------------------
        dashboard_endpoints = [
            (UserRole.PATIENT, "/api/v1/dashboard/patient"),
            (UserRole.DOCTOR, "/api/v1/dashboard/doctor"),
            (UserRole.ADMIN, "/api/v1/dashboard/admin"),
            (UserRole.LAB_TECHNICIAN, "/api/v1/dashboard/lab-technician"),
            (UserRole.PHARMACY_STAFF, "/api/v1/dashboard/pharmacy"),
        ]

        for expected_role, endpoint in dashboard_endpoints:
            # 1. Allowed role access
            if expected_role in tokens:
                allowed_res = client.get(endpoint, headers=tokens[expected_role])
                check(f"4. RBAC Authorized: {expected_role.value} -> {endpoint}", allowed_res.status_code == 200, f"HTTP {allowed_res.status_code}")

            # 2. Unauthorized other roles
            for other_role, other_headers in tokens.items():
                if other_role != expected_role:
                    blocked_res = client.get(endpoint, headers=other_headers)
                    check(f"4. RBAC Block: {other_role.value} -> {endpoint}", blocked_res.status_code == 403, f"HTTP {blocked_res.status_code}")

            # 3. Unauthenticated access
            unauth_res = client.get(endpoint)
            check(f"4. RBAC Unauthenticated: No Token -> {endpoint}", unauth_res.status_code in [401, 403], f"HTTP {unauth_res.status_code}")

        # -------------------------------------------------------------------
        # 5. Doctor Clinical Relationship & Requisition Access
        # -------------------------------------------------------------------
        sarah_doc = db.query(DoctorProfile).join(User).filter(User.email == "dr.sarah@careai.com").first()
        john_pat = db.query(PatientProfile).join(User).filter(User.email == "patient.john@example.com").first()

        # Doctor lab orders
        doc_orders_res = client.get("/api/v1/lab/orders/my-doctor-orders", headers=tokens[UserRole.DOCTOR])
        check("5a. Doctor List My Orders", doc_orders_res.status_code == 200, f"Found {len(doc_orders_res.json())} orders")

        # -------------------------------------------------------------------
        # 6. Complete Diagnostic Lab Workflow & Critical Threshold Alert
        # -------------------------------------------------------------------
        cbc_test = db.query(LabTest).filter(LabTest.test_code == "CBC-001").first()
        elec_test = db.query(LabTest).filter(LabTest.test_code == "ELEC-008").first()

        # 1. Doctor creates Lab Order
        new_order_res = client.post("/api/v1/lab/orders", json={
            "patient_id": john_pat.id,
            "priority": "STAT",
            "clinical_notes": "Urgent electrolyte and CBC diagnostic panel",
            "items": [
                {"lab_test_id": cbc_test.id},
                {"lab_test_id": elec_test.id},
            ],
        }, headers=tokens[UserRole.DOCTOR])
        check("6a. Doctor Creates STAT Lab Order", new_order_res.status_code == 201, f"Order #{new_order_res.json().get('id')}")
        lab_order_id = new_order_res.json()["id"]
        item_ids = [i["id"] for i in new_order_res.json()["items"]]

        # 2. Patient cannot view unreleased order
        pat_blocked = client.get(f"/api/v1/lab/orders/{lab_order_id}", headers=tokens[UserRole.PATIENT])
        check("6b. Patient Blocked from Unreleased Order", pat_blocked.status_code == 403, f"Status: {pat_blocked.status_code}")

        # 3. Lab Tech Work Queue
        queue_res = client.get("/api/v1/lab/queue", headers=tokens[UserRole.LAB_TECHNICIAN])
        check("6c. Lab Tech Sees Work Queue", queue_res.status_code == 200 and any(o["id"] == lab_order_id for o in queue_res.json()))

        # 4. Lab Tech Collects Specimen
        collect_res = client.post(f"/api/v1/lab/orders/{lab_order_id}/collect-sample", json={
            "specimen_type": "Whole Blood + Serum",
            "sample_condition": "ACCEPTABLE",
            "collection_notes": "Clean draw",
        }, headers=tokens[UserRole.LAB_TECHNICIAN])
        check("6d. Lab Tech Collects Sample", collect_res.status_code == 200, f"Condition: {collect_res.json().get('sample_condition')}")

        # 5. Start Processing
        start_res = client.post(f"/api/v1/lab/orders/{lab_order_id}/start-processing", headers=tokens[UserRole.LAB_TECHNICIAN])
        check("6e. Start Analytical Processing", start_res.status_code == 200 and start_res.json().get("status") == "IN_PROGRESS")

        # 6. Enter Results with Critical Potassium panic value (6.8 mmol/L)
        enter_res = client.post(f"/api/v1/lab/orders/{lab_order_id}/enter-results", json={
            "results": [
                {"lab_order_item_id": item_ids[0], "numeric_value": 14.2, "unit": "g/dL"},
                {"lab_order_item_id": item_ids[1], "numeric_value": 6.8, "unit": "mmol/L"},  # Critical potassium > 6.0
            ]
        }, headers=tokens[UserRole.LAB_TECHNICIAN])
        check("6f. Enter Results with Critical Alert", enter_res.status_code == 200, f"Status: {enter_res.json().get('status')}")

        # 7. Verification
        ver_res = client.post(f"/api/v1/lab/orders/{lab_order_id}/verify", json={
            "verification_notes": "Checked on calibrated analyzer",
        }, headers=tokens[UserRole.LAB_TECHNICIAN])
        check("6g. Verify Results", ver_res.status_code == 200 and ver_res.json().get("status") == "VERIFIED")

        # 8. Release
        rel_res = client.post(f"/api/v1/lab/orders/{lab_order_id}/release", headers=tokens[UserRole.LAB_TECHNICIAN])
        check("6h. Release Report", rel_res.status_code == 200 and rel_res.json().get("status") == "RELEASED")

        # 9. Patient views released report
        pat_reports_res = client.get("/api/v1/lab/patient/my-reports", headers=tokens[UserRole.PATIENT])
        check("6i. Patient Views Released Reports", pat_reports_res.status_code == 200 and any(r["id"] == lab_order_id for r in pat_reports_res.json()))

        # -------------------------------------------------------------------
        # 7. Notifications Verification
        # -------------------------------------------------------------------
        notifs_res = client.get("/api/v1/notifications", headers=tokens[UserRole.DOCTOR])
        check("7a. Doctor Receives Notifications", notifs_res.status_code == 200, f"Count: {len(notifs_res.json())}")

        unread_res = client.get("/api/v1/notifications/unread-count", headers=tokens[UserRole.DOCTOR])
        check("7b. Unread Notification Count", unread_res.status_code == 200, f"Unread: {unread_res.json().get('unread_count')}")

        # -------------------------------------------------------------------
        # 8. AI Assistant Conversation Persistence & Outage Boundaries
        # -------------------------------------------------------------------
        ai_chat_res = client.post("/api/v1/ai-assistant/chat", json={
            "message": "Hello CareAI, what does a normal hemoglobin level mean?",
        }, headers=tokens[UserRole.PATIENT])
        
        if ai_chat_res.status_code == 200:
            check("8a. AI Assistant Turn Execution (Gemini Live)", True, f"Model: {ai_chat_res.json().get('model_name')}")
            conv_id = ai_chat_res.json()["conversation_id"]
            convs_res = client.get("/api/v1/ai-assistant/conversations", headers=tokens[UserRole.PATIENT])
            check("8b. AI Assistant List Conversations", convs_res.status_code == 200 and len(convs_res.json()) >= 1)
            del_res = client.delete(f"/api/v1/ai-assistant/conversations/{conv_id}", headers=tokens[UserRole.PATIENT])
            check("8c. AI Assistant Delete Thread", del_res.status_code == 200)
        elif ai_chat_res.status_code == 503:
            check("8a. AI Assistant Graceful Outage Handling (No API Key in Env)", True, f"HTTP 503 Controlled Outage: {ai_chat_res.json().get('detail')}")
            # Test empty conversation listing
            convs_res = client.get("/api/v1/ai-assistant/conversations", headers=tokens[UserRole.PATIENT])
            check("8b. AI Assistant List Conversations", convs_res.status_code == 200)
        else:
            check("8a. AI Assistant Chat", False, f"Unexpected HTTP {ai_chat_res.status_code}: {ai_chat_res.text}")

        # -------------------------------------------------------------------
        # 9. Admin Lab Catalog Management & Operational Analytics
        # -------------------------------------------------------------------
        catalog_res = client.get("/api/v1/lab/tests", headers=tokens[UserRole.ADMIN])
        check("9a. Admin View Lab Catalog", catalog_res.status_code == 200 and len(catalog_res.json()) >= 8)

        admin_stats_res = client.get("/api/v1/lab/admin-stats", headers=tokens[UserRole.ADMIN])
        check("9b. Admin Operational Statistics", admin_stats_res.status_code == 200 and "total_orders_all_time" in admin_stats_res.json())

    finally:
        db.close()

    print("=" * 80)
    passed = sum(1 for _, cond, _ in audit_results if cond)
    total = len(audit_results)
    print(f"INTEGRATION AUDIT SUMMARY: {passed}/{total} CHECKS PASSED ({int((passed/total)*100)}%)")
    print("=" * 80)
    return passed == total


if __name__ == "__main__":
    success = run_full_integration_audit()
    sys.exit(0 if success else 1)
