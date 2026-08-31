"""Comprehensive automated test suite for Lab Management and Diagnostic Workflows."""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.lab import (
    LabTest,
    LabOrder,
    LabOrderItem,
    LabSample,
    LabResult,
    LabAuditEvent,
    LabOrderPriority,
    LabOrderStatus,
    SampleCondition,
    ResultFlag,
)
from app.core.security import create_access_token


@pytest.fixture
def auth_headers(db_session: Session):
    """Helper fixture providing verified JWT auth headers for all 5 roles."""
    def _get_headers(role: UserRole, email_prefix: str = "test"):
        unique_email = f"{email_prefix}.{role.value.lower()}@careai-test.com"
        user = db_session.query(User).filter(User.email == unique_email).first()
        if not user:
            user = User(
                email=unique_email,
                hashed_password="hashed_test_password",
                full_name=f"Test {role.value.title()}",
                role=role,
                is_active=True,
                is_verified=True,
            )
            db_session.add(user)
            db_session.flush()

            if role == UserRole.DOCTOR:
                doc_prof = DoctorProfile(
                    user_id=user.id,
                    specialization="Cardiology",
                    license_number=f"LIC-{user.id}-DOC",
                    experience_years=10,
                    consultation_fee=100.0,
                    approval_status=DoctorApprovalStatus.APPROVED,
                )
                db_session.add(doc_prof)
                db_session.flush()
            elif role == UserRole.PATIENT:
                pat_prof = PatientProfile(
                    user_id=user.id,
                    date_of_birth=datetime(1990, 1, 1).date(),
                    gender="MALE",
                    blood_group="O+",
                )
                db_session.add(pat_prof)
                db_session.flush()
            db_session.commit()
            db_session.refresh(user)

        token = create_access_token(subject=str(user.id), role=user.role.value)
        return {"Authorization": f"Bearer {token}"}, user

    return _get_headers


@pytest.fixture
def standard_tests(db_session: Session):
    """Ensure standard catalog tests exist."""
    tests = [
        ("CBC-TEST", "Complete Blood Count", "Hematology", "Whole Blood (EDTA)", "12.0 - 17.5", "g/dL"),
        ("GLU-TEST", "Fasting Blood Glucose", "Biochemistry", "Serum", "70 - 99", "mg/dL"),
        ("POT-TEST", "Serum Potassium", "Biochemistry", "Serum", "3.5 - 5.0", "mmol/L"),
    ]
    created = []
    for code, name, cat, spec, ref, unit in tests:
        t = db_session.query(LabTest).filter(LabTest.test_code == code).first()
        if not t:
            t = LabTest(
                test_name=name,
                test_code=code,
                category=cat,
                specimen_type=spec,
                reference_range=ref,
                unit=unit,
                is_active=True,
            )
            db_session.add(t)
            db_session.flush()
        created.append(t)
    db_session.commit()
    return created


# ---------------------------------------------------------------------------
# 1. CATALOG MANAGEMENT & RBAC TESTS
# ---------------------------------------------------------------------------
def test_admin_can_create_and_update_lab_test(client: TestClient, auth_headers):
    admin_h, _ = auth_headers(UserRole.ADMIN, "cat1")

    payload = {
        "test_name": "Thyroid Stimulating Hormone Alpha",
        "test_code": "TSH-ALPHA-01",
        "category": "Hormonal Tests",
        "specimen_type": "Serum",
        "reference_range": "0.4 - 4.0",
        "unit": "uIU/mL",
        "preparation_instructions": "Fasting optional",
        "estimated_turnaround_time": "4 hours",
        "is_active": True,
    }
    res = client.post("/api/v1/lab/tests", json=payload, headers=admin_h)
    assert res.status_code == 201
    data = res.json()
    assert data["test_code"] == "TSH-ALPHA-01"
    test_id = data["id"]

    # Update
    res_up = client.put(
        f"/api/v1/lab/tests/{test_id}",
        json={"test_name": "TSH Super Sensitive", "reference_range": "0.3 - 4.5"},
        headers=admin_h,
    )
    assert res_up.status_code == 200
    assert res_up.json()["test_name"] == "TSH Super Sensitive"


def test_patient_cannot_create_lab_test(client: TestClient, auth_headers):
    pat_h, _ = auth_headers(UserRole.PATIENT, "cat2")
    payload = {
        "test_name": "Unauthorized Test",
        "test_code": "UNAUTH-01",
        "category": "General",
        "specimen_type": "Serum",
    }
    res = client.post("/api/v1/lab/tests", json=payload, headers=pat_h)
    assert res.status_code == 403


def test_doctor_and_tech_can_list_tests(client: TestClient, auth_headers, standard_tests):
    doc_h, _ = auth_headers(UserRole.DOCTOR, "cat3")
    res = client.get("/api/v1/lab/tests", headers=doc_h)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) >= 3


# ---------------------------------------------------------------------------
# 2. DOCTOR LAB ORDERING & CLINICAL RELATIONSHIP TESTS
# ---------------------------------------------------------------------------
def test_doctor_order_creation_success_with_relationship(client: TestClient, db_session: Session, auth_headers, standard_tests):
    doc_h, doc_user = auth_headers(UserRole.DOCTOR, "doc1")
    pat_h, pat_user = auth_headers(UserRole.PATIENT, "pat1")

    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doc_user.id).first()
    pat_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == pat_user.id).first()

    # Establish legitimate clinical consultation appointment
    appt = Appointment(
        patient_id=pat_prof.id,
        doctor_id=doc_prof.id,
        scheduled_start=datetime.now(timezone.utc),
        scheduled_end=datetime.now(timezone.utc),
        status=AppointmentStatus.COMPLETED,
        reason="Follow up cardiology workup",
    )
    db_session.add(appt)
    db_session.commit()

    order_payload = {
        "patient_id": pat_prof.id,
        "priority": "URGENT",
        "clinical_notes": "Evaluate sudden onset dizziness and anemia.",
        "items": [
            {"lab_test_id": standard_tests[0].id, "instructions": "Check differential counts"},
            {"lab_test_id": standard_tests[1].id, "instructions": "Fasting glucose level"},
        ],
    }

    res = client.post("/api/v1/lab/orders", json=order_payload, headers=doc_h)
    assert res.status_code == 201
    order_data = res.json()
    assert order_data["priority"] == "URGENT"
    assert order_data["status"] == "SAMPLE_PENDING"
    assert len(order_data["items"]) == 2


def test_doctor_cannot_order_for_unrelated_patient(client: TestClient, db_session: Session, auth_headers, standard_tests):
    doc_h, _ = auth_headers(UserRole.DOCTOR, "doc2_unrel")
    pat_h, pat_user = auth_headers(UserRole.PATIENT, "pat2_unrel")
    pat_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == pat_user.id).first()

    # No appointment or prescription relationship exists
    order_payload = {
        "patient_id": pat_prof.id,
        "priority": "ROUTINE",
        "items": [{"lab_test_id": standard_tests[0].id}],
    }
    res = client.post("/api/v1/lab/orders", json=order_payload, headers=doc_h)
    assert res.status_code == 403
    assert "Clinical authorization failed" in res.json()["detail"]


# ---------------------------------------------------------------------------
# 3. SAMPLE COLLECTION, WORK QUEUE, & SPECIMEN INTEGRITY TESTS
# ---------------------------------------------------------------------------
def test_lab_technician_work_queue_and_sample_collection(client: TestClient, db_session: Session, auth_headers, standard_tests):
    doc_h, doc_user = auth_headers(UserRole.DOCTOR, "doc3")
    pat_h, pat_user = auth_headers(UserRole.PATIENT, "pat3")
    tech_h, tech_user = auth_headers(UserRole.LAB_TECHNICIAN, "tech1")

    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doc_user.id).first()
    pat_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == pat_user.id).first()

    appt = Appointment(
        patient_id=pat_prof.id,
        doctor_id=doc_prof.id,
        scheduled_start=datetime.now(timezone.utc),
        scheduled_end=datetime.now(timezone.utc),
        status=AppointmentStatus.COMPLETED,
    )
    db_session.add(appt)
    db_session.commit()

    order_payload = {
        "patient_id": pat_prof.id,
        "priority": "STAT",
        "items": [{"lab_test_id": standard_tests[0].id}],
    }
    order_res = client.post("/api/v1/lab/orders", json=order_payload, headers=doc_h)
    order_id = order_res.json()["id"]

    # Tech views work queue
    queue_res = client.get("/api/v1/lab/queue", headers=tech_h)
    assert queue_res.status_code == 200
    queue_data = queue_res.json()
    assert any(o["id"] == order_id for o in queue_data)

    # Tech collects sample with ACCEPTABLE condition
    sample_payload = {
        "specimen_type": "Whole Blood (EDTA)",
        "sample_condition": "ACCEPTABLE",
        "collection_notes": "Successful antecubital draw, 5mL lavender top tube.",
    }
    sample_res = client.post(f"/api/v1/lab/orders/{order_id}/collect-sample", json=sample_payload, headers=tech_h)
    assert sample_res.status_code == 200
    assert sample_res.json()["sample_condition"] == "ACCEPTABLE"

    # Verify order transitioned to SAMPLE_COLLECTED
    order_chk = client.get(f"/api/v1/lab/orders/{order_id}", headers=tech_h)
    assert order_chk.json()["status"] == "SAMPLE_COLLECTED"


def test_compromised_sample_rejection_requires_recollection(client: TestClient, db_session: Session, auth_headers, standard_tests):
    doc_h, doc_user = auth_headers(UserRole.DOCTOR, "doc4")
    pat_h, pat_user = auth_headers(UserRole.PATIENT, "pat4")
    tech_h, _ = auth_headers(UserRole.LAB_TECHNICIAN, "tech2")

    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doc_user.id).first()
    pat_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == pat_user.id).first()

    db_session.add(Appointment(
        patient_id=pat_prof.id,
        doctor_id=doc_prof.id,
        scheduled_start=datetime.now(timezone.utc),
        scheduled_end=datetime.now(timezone.utc),
        status=AppointmentStatus.COMPLETED,
    ))
    db_session.commit()

    order_res = client.post(
        "/api/v1/lab/orders",
        json={"patient_id": pat_prof.id, "priority": "ROUTINE", "items": [{"lab_test_id": standard_tests[0].id}]},
        headers=doc_h,
    )
    order_id = order_res.json()["id"]

    # Tech records HEMOLYZED specimen
    sample_res = client.post(
        f"/api/v1/lab/orders/{order_id}/collect-sample",
        json={"specimen_type": "Whole Blood", "sample_condition": "HEMOLYZED", "collection_notes": "Severe hemolysis observed."},
        headers=tech_h,
    )
    assert sample_res.status_code == 200

    # Order must remain in SAMPLE_PENDING for recollection
    order_chk = client.get(f"/api/v1/lab/orders/{order_id}", headers=tech_h)
    assert order_chk.json()["status"] == "SAMPLE_PENDING"


# ---------------------------------------------------------------------------
# 4. RESULT ENTRY, CRITICAL VALUE ALERTS, VERIFICATION & RELEASE
# ---------------------------------------------------------------------------
def test_full_lab_workflow_with_critical_alert_and_patient_release(client: TestClient, db_session: Session, auth_headers, standard_tests):
    doc_h, doc_user = auth_headers(UserRole.DOCTOR, "doc5_crit")
    pat_h, pat_user = auth_headers(UserRole.PATIENT, "pat5_crit")
    tech_h, tech_user = auth_headers(UserRole.LAB_TECHNICIAN, "tech3_crit")

    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == doc_user.id).first()
    pat_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == pat_user.id).first()

    db_session.add(Appointment(
        patient_id=pat_prof.id,
        doctor_id=doc_prof.id,
        scheduled_start=datetime.now(timezone.utc),
        scheduled_end=datetime.now(timezone.utc),
        status=AppointmentStatus.COMPLETED,
    ))
    db_session.commit()

    # 1. Doctor creates order with Potassium and Glucose tests
    order_res = client.post(
        "/api/v1/lab/orders",
        json={
            "patient_id": pat_prof.id,
            "priority": "STAT",
            "clinical_notes": "Suspected acute electrolyte imbalance.",
            "items": [
                {"lab_test_id": standard_tests[1].id},  # Glucose
                {"lab_test_id": standard_tests[2].id},  # Potassium
            ],
        },
        headers=doc_h,
    )
    assert order_res.status_code == 201
    order_id = order_res.json()["id"]
    item_ids = [item["id"] for item in order_res.json()["items"]]

    # 2. Patient CANNOT view unreleased order
    pat_view = client.get(f"/api/v1/lab/orders/{order_id}", headers=pat_h)
    assert pat_view.status_code == 403

    # 3. Tech collects sample
    client.post(
        f"/api/v1/lab/orders/{order_id}/collect-sample",
        json={"specimen_type": "Serum", "sample_condition": "ACCEPTABLE"},
        headers=tech_h,
    )

    # 4. Tech starts processing
    proc_res = client.post(f"/api/v1/lab/orders/{order_id}/start-processing", headers=tech_h)
    assert proc_res.status_code == 200
    assert proc_res.json()["status"] == "IN_PROGRESS"

    # 5. Tech enters results with Critical Potassium (6.8 mmol/L -> Critical High) and Normal Glucose (85 mg/dL)
    results_batch = {
        "results": [
            {
                "lab_order_item_id": item_ids[0],
                "numeric_value": 85.0,
                "unit": "mg/dL",
                "reference_range": "70 - 99",
            },
            {
                "lab_order_item_id": item_ids[1],
                "numeric_value": 6.8,  # Critical potassium > 6.0!
                "unit": "mmol/L",
                "reference_range": "3.5 - 5.0",
            },
        ]
    }
    enter_res = client.post(f"/api/v1/lab/orders/{order_id}/enter-results", json=results_batch, headers=tech_h)
    assert enter_res.status_code == 200
    order_data = enter_res.json()
    assert order_data["status"] == "RESULTS_ENTERED"

    # Verify critical result was flagged
    pot_res = next(i["result"] for i in order_data["items"] if i["id"] == item_ids[1])
    assert pot_res["result_flag"] == "CRITICAL"
    assert pot_res["is_critical"] is True

    # 6. Verify cannot release directly without verification
    bad_rel = client.post(f"/api/v1/lab/orders/{order_id}/release", headers=tech_h)
    assert bad_rel.status_code == 400

    # 7. Tech verifies results
    ver_res = client.post(
        f"/api/v1/lab/orders/{order_id}/verify",
        json={"verification_notes": "Repeated run verified on analyzer #2. Critical alert communicated."},
        headers=tech_h,
    )
    assert ver_res.status_code == 200
    assert ver_res.json()["status"] == "VERIFIED"

    # 8. Tech releases results
    rel_res = client.post(f"/api/v1/lab/orders/{order_id}/release", headers=tech_h)
    assert rel_res.status_code == 200
    assert rel_res.json()["status"] == "RELEASED"

    # 9. Patient CAN NOW view released report
    pat_reports = client.get("/api/v1/lab/patient/my-reports", headers=pat_h)
    assert pat_reports.status_code == 200
    reports_list = pat_reports.json()
    assert any(r["id"] == order_id for r in reports_list)

    # 10. Patient views report detail
    report_detail = client.get(f"/api/v1/lab/patient/my-reports/{order_id}", headers=pat_h)
    assert report_detail.status_code == 200
    rep_data = report_detail.json()
    assert len(rep_data["results"]) == 2
    assert rep_data["status"] == "RELEASED"


# ---------------------------------------------------------------------------
# 5. DASHBOARD STATS TESTS
# ---------------------------------------------------------------------------
def test_dashboard_stats_endpoints(client: TestClient, auth_headers):
    tech_h, _ = auth_headers(UserRole.LAB_TECHNICIAN, "stats_tech")
    admin_h, _ = auth_headers(UserRole.ADMIN, "stats_admin")

    tech_stats = client.get("/api/v1/lab/stats", headers=tech_h)
    assert tech_stats.status_code == 200
    assert "pending_samples" in tech_stats.json()
    assert "critical_alerts_count" in tech_stats.json()

    admin_stats = client.get("/api/v1/lab/admin-stats", headers=admin_h)
    assert admin_stats.status_code == 200
    assert "total_orders_all_time" in admin_stats.json()
    assert "active_test_catalog_count" in admin_stats.json()
