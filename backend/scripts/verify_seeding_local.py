"""Comprehensive local verification script for CareAI demo seeding.

Tests:
1. Fresh database creation and Alembic migration execution
2. Seeding run #1 and row counts recording
3. Seeding run #2 and row counts verification (100% Idempotency)
4. Authentication verification for all 5 primary demo accounts
5. Doctor Directory & Admin pending verification
6. Doctor availability schedules verification
"""
import os
import sys
from decimal import Decimal
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.availability import DoctorAvailability
from app.models.patient import PatientProfile
from app.models.appointment import Appointment
from app.models.prescription import Prescription
from app.models.lab import LabOrder, LabResult, LabAuditEvent, LabOrderPriority
from app.models.notification import Notification
from app.core.security import verify_password
from seed import seed_database


def run_full_verification():
    print("=================================================================")
    print("CAREAI DEMO SEEDING COMPREHENSIVE LOCAL VERIFICATION")
    print("=================================================================")

    test_db_filename = "fresh_test_verify.db"
    if os.path.exists(test_db_filename):
        os.remove(test_db_filename)
    test_db_url = f"sqlite:///./{test_db_filename}"

    # 1. Run migrations on fresh database
    print("\n[STEP 1] Running Alembic migrations on a fresh database...")
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)
    command.upgrade(alembic_cfg, "head")
    print("  --> Fresh database initialized and migrated to HEAD successfully.")

    # Create session to fresh db
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # 2. Run seed.py #1
    print("\n[STEP 2] Running seed_database() - Pass 1...")
    seed_database(db=db)
    print("  --> Pass 1 completed successfully.")

    # Record counts
    def get_counts(s):
        return {
            "users": s.query(func.count(User.id)).scalar(),
            "doctor_profiles": s.query(func.count(DoctorProfile.id)).scalar(),
            "doctor_availabilities": s.query(func.count(DoctorAvailability.id)).scalar(),
            "patient_profiles": s.query(func.count(PatientProfile.id)).scalar(),
            "appointments": s.query(func.count(Appointment.id)).scalar(),
            "prescriptions": s.query(func.count(Prescription.id)).scalar(),
            "lab_orders": s.query(func.count(LabOrder.id)).scalar(),
            "lab_results": s.query(func.count(LabResult.id)).scalar(),
            "notifications": s.query(func.count(Notification.id)).scalar(),
        }

    counts_pass_1 = get_counts(db)
    print("\n[ROW COUNTS AFTER PASS 1]")
    for table, count in counts_pass_1.items():
        print(f"  {table:25}: {count}")

    # 3. Run seed.py #2 (Idempotency Check)
    print("\n[STEP 3] Running seed_database() - Pass 2 (Idempotency Check)...")
    seed_database(db=db)
    counts_pass_2 = get_counts(db)

    print("\n[ROW COUNTS AFTER PASS 2]")
    for table, count in counts_pass_2.items():
        print(f"  {table:25}: {count}")

    idempotency_failed = False
    for table in counts_pass_1:
        if counts_pass_1[table] != counts_pass_2[table]:
            print(f"  [FAIL] Count mismatch in {table}: Pass 1 had {counts_pass_1[table]}, Pass 2 had {counts_pass_2[table]}")
            idempotency_failed = True

    if idempotency_failed:
        raise RuntimeError("Idempotency verification failed! Duplicate records were detected.")
    print("  --> IDEMPOTENCY CONFIRMED: 0 duplicate records created on second execution!")

    # 4. Verify 5 Primary Demo Accounts Authentication
    print("\n[STEP 4] Verifying Authentication for 5 Primary Demo Accounts...")
    primary_accounts = [
        ("Admin", "pillu.212006@gmail.com", "Neha@6328", UserRole.ADMIN),
        ("Doctor", "kmeghana27@gmail.com", "Megha@612", UserRole.DOCTOR),
        ("Patient", "tanmai88@gmail.com", "tanmai88", UserRole.PATIENT),
        ("Lab Tech", "vinaysimha27@gmail.com", "Vinay@736", UserRole.LAB_TECHNICIAN),
        ("Pharmacy Staff", "tirupujitha03@gmail.com", "tiru@333", UserRole.PHARMACY_STAFF),
    ]

    # Override get_db dependency for API client
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    auth_tokens = {}
    for role_label, email, password, expected_role in primary_accounts:
        user_record = db.query(User).filter(User.email == email).first()
        assert user_record is not None, f"User {email} not found in DB!"
        assert verify_password(password, user_record.hashed_password), f"Password hash mismatch for {email}!"
        assert user_record.role == expected_role, f"Role mismatch for {email}: expected {expected_role}, got {user_record.role}"

        # Test through actual FastAPI login endpoint
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        if resp.status_code != 200:
            print(f"  [FAIL] Login failed for {email}: {resp.status_code} {resp.text}")
            raise RuntimeError(f"Login failed for {email}")
        data = resp.json()
        token = data.get("access_token")
        assert token, f"No access token in response for {email}"
        role_returned = data.get("role")
        assert role_returned == expected_role.value, f"Expected role {expected_role.value}, got {role_returned}"
        auth_tokens[role_label] = token
        print(f"  [OK] {role_label:15} ({email}) authenticated successfully! Role: {role_returned}")

    # 5. Verify Doctor Directory
    print("\n[STEP 5] Verifying Doctor Directory & Admin Verification Workflow...")
    # Public Directory (Approved Doctors)
    dir_resp = client.get("/api/v1/doctors/directory")
    assert dir_resp.status_code == 200, f"Doctor directory failed: {dir_resp.text}"
    approved_docs = dir_resp.json()
    approved_names = [d.get("user", {}).get("full_name") for d in approved_docs]
    print(f"  Approved Doctors in Directory: {approved_names}")

    assert "Ayan" in approved_names, "Dr. Ayan missing from approved doctor directory!"
    assert "Ananya Sharma" in approved_names, "Dr. Ananya Sharma missing from approved doctor directory!"

    # Verify Dr. Naresh Trehan is NOT in public directory (since he is PENDING)
    assert "Naresh Trehan" not in approved_names, "Dr. Naresh Trehan should NOT be in approved directory while PENDING!"
    print("  [OK] Dr. Naresh Trehan correctly excluded from public approved directory.")

    # Admin Pending Doctors List
    admin_token = auth_tokens["Admin"]
    pending_resp = client.get(
        "/api/v1/admin/pending-doctors",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert pending_resp.status_code == 200, f"Admin pending doctors failed: {pending_resp.text}"
    pending_docs = pending_resp.json()
    pending_names = [d.get("user", {}).get("full_name") for d in pending_docs]
    print(f"  Pending Doctors in Admin Review: {pending_names}")
    assert "Naresh Trehan" in pending_names, "Dr. Naresh Trehan missing from Admin pending list!"
    print("  [OK] Dr. Naresh Trehan verified PENDING for Admin credential review workflow.")

    # 6. Verify Doctor Details and Availability Schedules
    print("\n[STEP 6] Verifying Doctor Profiles & Availability Schedules...")
    doc_ayan = db.query(DoctorProfile).join(User).filter(User.email == "dr.ayan@careai.com").first()
    assert doc_ayan is not None
    assert doc_ayan.specialization == "Cardiology"
    assert doc_ayan.experience_years == 5
    assert doc_ayan.consultation_fee == Decimal("500.00")
    assert doc_ayan.approval_status == DoctorApprovalStatus.APPROVED
    ayan_days = sorted([a.day_of_week for a in doc_ayan.availabilities if a.is_active])
    assert ayan_days == [0, 2, 4, 6], f"Expected Mon/Wed/Fri/Sun [0, 2, 4, 6], got {ayan_days}"
    print(f"  [OK] Dr. Ayan verified: Cardiology, 5 yrs exp, Rs. {doc_ayan.consultation_fee}, Available days: {ayan_days} (Mon, Wed, Fri, Sun)")

    doc_trehan = db.query(DoctorProfile).join(User).filter(User.email == "dr.trehan@careai.com").first()
    assert doc_trehan is not None
    assert doc_trehan.specialization == "Cardiovascular and Cardiothoracic Surgery"
    assert doc_trehan.experience_years == 20
    assert doc_trehan.consultation_fee == Decimal("1500.00")
    assert doc_trehan.approval_status == DoctorApprovalStatus.PENDING
    trehan_days = sorted([a.day_of_week for a in doc_trehan.availabilities if a.is_active])
    assert trehan_days == [3], f"Expected Thursday [3], got {trehan_days}"
    print(f"  [OK] Dr. Naresh Trehan verified: Cardiovascular Surgery, 20 yrs exp, Rs. {doc_trehan.consultation_fee}, Available days: {trehan_days} (Thu), Status: PENDING")

    doc_ananya = db.query(DoctorProfile).join(User).filter(User.email == "dr.ananya@careai.com").first()
    assert doc_ananya is not None
    assert doc_ananya.specialization == "Gynecology"
    assert doc_ananya.experience_years == 10
    assert doc_ananya.consultation_fee == Decimal("1000.00")
    assert doc_ananya.approval_status == DoctorApprovalStatus.APPROVED
    ananya_days = sorted([a.day_of_week for a in doc_ananya.availabilities if a.is_active])
    assert ananya_days == [0, 4, 6], f"Expected Mon/Fri/Sun [0, 4, 6], got {ananya_days}"
    print(f"  [OK] Dr. Ananya Sharma verified: Gynecology, 10 yrs exp, Rs. {doc_ananya.consultation_fee}, Available days: {ananya_days} (Mon, Fri, Sun)")

    # 7. Verify PostgreSQL-compatible JSON field validity
    print("\n[STEP 7] Verifying PostgreSQL-Compatible JSON Structure...")
    audit_events = db.query(LabAuditEvent).all()
    assert len(audit_events) >= 3, "Expected at least 3 LabAuditEvents"
    for event in audit_events:
        assert isinstance(event.details, dict), f"LabAuditEvent.details must be a dict! Got: {type(event.details)}: {event.details}"
        assert "message" in event.details, f"LabAuditEvent.details must contain 'message' key! Got: {event.details}"
    print(f"  [OK] All {len(audit_events)} LabAuditEvent.details records are valid JSON dictionaries.")

    # Check PatientProfile JSON fields
    pat_profs = db.query(PatientProfile).all()
    for prof in pat_profs:
        assert isinstance(prof.allergies, list), f"PatientProfile.allergies must be list! Got: {type(prof.allergies)}"
        assert isinstance(prof.chronic_conditions, list), f"PatientProfile.chronic_conditions must be list! Got: {type(prof.chronic_conditions)}"
        assert isinstance(prof.current_medications, list), f"PatientProfile.current_medications must be list! Got: {type(prof.current_medications)}"
    print(f"  [OK] All {len(pat_profs)} PatientProfile JSON fields verified as valid JSON lists.")

    # Check Lab API endpoint returns formatted audit details
    order1 = db.query(LabOrder).filter(LabOrder.priority == LabOrderPriority.STAT).first()
    assert order1 is not None
    lab_tech_token = auth_tokens["Lab Tech"]
    order_resp = client.get(f"/api/v1/lab/orders/{order1.id}", headers={"Authorization": f"Bearer {lab_tech_token}"})
    assert order_resp.status_code == 200, f"Lab order detail fetch failed: {order_resp.text}"
    order_data = order_resp.json()
    assert len(order_data.get("audit_events", [])) > 0, "Expected audit events in lab order response"
    event_details_str = order_data["audit_events"][0].get("details")
    assert isinstance(event_details_str, str), f"Expected audit_event details to be string in API response! Got {type(event_details_str)}: {event_details_str}"
    print(f"  [OK] API endpoint /api/v1/lab/orders/{order1.id} returned string-formatted audit event: '{event_details_str}'")

    db.close()
    app.dependency_overrides.clear()
    engine.dispose()
    try:
        if os.path.exists(test_db_filename):
            os.remove(test_db_filename)
    except Exception:
        pass

    print("\n=================================================================")
    print("ALL VERIFICATION CHECKS PASSED WITH 100% COMPLIANCE!")
    print("=================================================================")


if __name__ == "__main__":
    run_full_verification()
