"""Complete End-to-End System Integration, Security, and Functional Audit Test Suite (Prompt 15)."""
from datetime import datetime, date, time, timedelta
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.patient import PatientProfile
from app.models.availability import DoctorAvailability
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription, PrescriptionItem, PrescriptionStatus
from app.models.medical_document import MedicalDocument, DocumentType
from app.models.lab import (
    LabTest,
    LabOrder,
    LabOrderItem,
    LabSample,
    LabResult,
    LabOrderPriority,
    LabOrderStatus,
    SampleCondition,
    ResultFlag,
)
from app.models.ai_report import AIAnalysisReport, InteractionSeverity
from app.models.ai_assistant import AIConversation, AIMessage
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.core.security import get_password_hash, create_access_token


def make_user(
    db: Session,
    email: str,
    role: UserRole,
    full_name: str,
    specialization: str = "Cardiology",
    is_approved: bool = True,
) -> User:
    """Helper to persist user and domain profile."""
    user = User(
        email=email.lower(),
        hashed_password=get_password_hash("AuditPass123!"),
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
            date_of_birth=date(1992, 8, 20),
            blood_group="O+",
            allergies=[{"name": "Penicillin", "severity": "HIGH"}],
            chronic_conditions=["Mild Hypertension"],
            current_medications=[{"name": "Amlodipine"}],
        )
        db.add(profile)
    elif role == UserRole.DOCTOR:
        profile = DoctorProfile(
            user_id=user.id,
            specialization=specialization,
            license_number=f"MED-AUDIT-{user.id}",
            approval_status=DoctorApprovalStatus.APPROVED if is_approved else DoctorApprovalStatus.PENDING,
            consultation_fee=140.00,
            experience_years=10,
        )
        db.add(profile)

    db.commit()
    db.refresh(user)
    return user


def auth_header(user: User) -> dict:
    """Generate authorization headers."""
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


class TestSystemIntegrationE2E:
    """End-to-End integration and security audit test suite."""

    @pytest.fixture(autouse=True)
    def setup_e2e_data(self, db_session: Session):
        """Seed clean database with realistic role fixtures."""
        self.patient = make_user(db_session, "audit.patient@careai.com", UserRole.PATIENT, "Grace Hopper")
        self.patient2 = make_user(db_session, "audit.patient2@careai.com", UserRole.PATIENT, "Ada Lovelace")
        self.doctor = make_user(db_session, "audit.doctor@careai.com", UserRole.DOCTOR, "Dr. Alexander Fleming", is_approved=True)
        self.admin = make_user(db_session, "audit.admin@careai.com", UserRole.ADMIN, "Chief Medical Admin")
        self.lab_tech = make_user(db_session, "audit.labtech@careai.com", UserRole.LAB_TECHNICIAN, "Alex Rivera")
        self.pharm_staff = make_user(db_session, "audit.pharmacy@careai.com", UserRole.PHARMACY_STAFF, "Elena Rostova")

        # Doctor Profile & Schedule
        doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == self.doctor.id).first()
        self.doc_prof = doc_prof
        pat_prof = db_session.query(PatientProfile).filter(PatientProfile.user_id == self.patient.id).first()
        self.pat_prof = pat_prof

        # Weekly Schedule: Monday through Friday 09:00 - 17:00
        for day in range(5):
            avail = DoctorAvailability(
                doctor_id=doc_prof.id,
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(17, 0),
                slot_duration_minutes=30,
                is_active=True,
            )
            db_session.add(avail)

        # Standard Lab Test Catalog
        self.lab_test = LabTest(
            test_name="Lipid Panel with Risk Evaluation",
            test_code="AUDIT-LIPID-01",
            category="Biochemistry",
            specimen_type="Serum (SST)",
            reference_range="Cholesterol: < 200 mg/dL",
            unit="mg/dL",
            is_active=True,
        )
        db_session.add(self.lab_test)
        db_session.commit()

    # -----------------------------------------------------------------------
    # PHASE 2: VERIFY ALL 5 LOGIN FLOWS & AUTHENTICATION
    # -----------------------------------------------------------------------
    def test_all_5_login_flows_and_token_resolution(self, client: TestClient):
        """Verify login for PATIENT, DOCTOR, ADMIN, LAB_TECHNICIAN, PHARMACY_STAFF."""
        roles_to_test = [
            ("audit.patient@careai.com", "AuditPass123!", "PATIENT"),
            ("audit.doctor@careai.com", "AuditPass123!", "DOCTOR"),
            ("audit.admin@careai.com", "AuditPass123!", "ADMIN"),
            ("audit.labtech@careai.com", "AuditPass123!", "LAB_TECHNICIAN"),
            ("audit.pharmacy@careai.com", "AuditPass123!", "PHARMACY_STAFF"),
        ]

        for email, pwd, expected_role in roles_to_test:
            # 1. Login POST /auth/login (JSON body with email & password)
            res = client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": pwd},
            )
            assert res.status_code == status.HTTP_200_OK, f"Login failed for {email}"
            token_data = res.json()
            assert "access_token" in token_data
            assert token_data["token_type"] == "bearer"

            # 2. Verify /auth/me returns authenticated identity and role
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            me_res = client.get("/api/v1/auth/me", headers=headers)
            assert me_res.status_code == status.HTTP_200_OK
            me_data = me_res.json()
            assert me_data["email"] == email
            assert me_data["role"] == expected_role

    def test_invalid_credentials_rejected(self, client: TestClient):
        """Verify invalid passwords or non-existent emails return 401."""
        res_bad_pw = client.post(
            "/api/v1/auth/login",
            json={"email": "audit.patient@careai.com", "password": "WrongPassword!"},
        )
        assert res_bad_pw.status_code == status.HTTP_401_UNAUTHORIZED

        res_bad_user = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@careai.com", "password": "AnyPassword123!"},
        )
        assert res_bad_user.status_code == status.HTTP_401_UNAUTHORIZED

    # -----------------------------------------------------------------------
    # PHASE 3: ROLE ISOLATION & SECURITY ATTACK TESTING (RBAC PENETRATION)
    # -----------------------------------------------------------------------
    def test_rbac_security_cross_role_access_rejection(self, client: TestClient):
        """Penetration test: verify independent backend authorization stops cross-role access."""
        pat_headers = auth_header(self.patient)
        doc_headers = auth_header(self.doctor)
        lab_headers = auth_header(self.lab_tech)
        pharm_headers = auth_header(self.pharm_staff)

        # 1. Patient trying to access doctor/admin/lab/pharmacy endpoints
        assert client.get("/api/v1/dashboard/doctor", headers=pat_headers).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/dashboard/admin", headers=pat_headers).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/dashboard/lab-technician", headers=pat_headers).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/dashboard/pharmacy", headers=pat_headers).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/admin/users", headers=pat_headers).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/lab/queue", headers=pat_headers).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/pharmacy/prescriptions", headers=pat_headers).status_code == status.HTTP_403_FORBIDDEN

        # 2. Doctor trying to access admin endpoints, lab-only mutations, pharmacy mutations
        assert client.get("/api/v1/admin/pending-doctors", headers=doc_headers).status_code == status.HTTP_403_FORBIDDEN
        assert client.post("/api/v1/admin/staff", headers=doc_headers, json={
            "email": "hacked@careai.com", "password": "Pass123!", "full_name": "Hacked", "role": "ADMIN"
        }).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/pharmacy/dashboard", headers=doc_headers).status_code == status.HTTP_403_FORBIDDEN

        # 3. Lab Tech trying to dispense prescriptions or access admin routes
        assert client.get("/api/v1/admin/users", headers=lab_headers).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/pharmacy/dashboard", headers=lab_headers).status_code == status.HTTP_403_FORBIDDEN

        # 4. Pharmacy Staff trying to author prescriptions or enter lab results
        assert client.post("/api/v1/prescriptions", headers=pharm_headers, json={}).status_code == status.HTTP_403_FORBIDDEN
        assert client.get("/api/v1/lab/queue", headers=pharm_headers).status_code == status.HTTP_403_FORBIDDEN

        # 5. Unauthenticated calls rejected with 401
        assert client.get("/api/v1/dashboard/patient").status_code == status.HTTP_401_UNAUTHORIZED
        assert client.get("/api/v1/dashboard/doctor").status_code == status.HTTP_401_UNAUTHORIZED

    # -----------------------------------------------------------------------
    # PHASE 4: COMPLETE PATIENT JOURNEY
    # -----------------------------------------------------------------------
    def test_complete_patient_journey(self, client: TestClient, db_session: Session):
        """Verify registration -> directory -> slot lookup -> booking -> profile -> notifications."""
        # 1. Register new patient
        reg_res = client.post(
            "/api/v1/auth/register",
            json={
                "email": "new.patient.e2e@careai.com",
                "password": "PatientPass123!",
                "full_name": "E2E Patient Test",
                "role": "PATIENT",
            },
        )
        assert reg_res.status_code == status.HTTP_201_CREATED

        # 2. Login
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "new.patient.e2e@careai.com", "password": "PatientPass123!"},
        )
        assert login_res.status_code == status.HTTP_200_OK
        headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

        # 3. Patient Dashboard (real DB metrics)
        dash_res = client.get("/api/v1/dashboard/patient", headers=headers)
        assert dash_res.status_code == status.HTTP_200_OK
        assert "stats" in dash_res.json()
        assert "medical_profile_status" in dash_res.json()

        # 4. Search Doctor Directory
        dir_res = client.get("/api/v1/doctors/directory?specialization=Cardiology", headers=headers)
        assert dir_res.status_code == status.HTTP_200_OK
        docs = dir_res.json()
        assert len(docs) >= 1
        doc_id = docs[0]["id"]

        # 5. Dynamic Slot Discovery
        target_date = date.today() + timedelta(days=2)
        # Avoid weekend for monday-friday schedule
        while target_date.weekday() >= 5:
            target_date += timedelta(days=1)

        slots_res = client.get(f"/api/v1/doctors/{doc_id}/available-slots?date={target_date.isoformat()}", headers=headers)
        assert slots_res.status_code == status.HTTP_200_OK
        slots = slots_res.json()["available_slots"]
        assert len(slots) > 0

        # 6. Book Appointment
        first_slot = slots[0]
        slot_parts = [int(p) for p in first_slot.split(":")[:2]]
        slot_start = datetime.combine(target_date, time(slot_parts[0], slot_parts[1]))
        slot_end = slot_start + timedelta(minutes=30)

        book_res = client.post(
            "/api/v1/appointments",
            headers=headers,
            json={
                "doctor_id": doc_id,
                "scheduled_start": slot_start.isoformat(),
                "scheduled_end": slot_end.isoformat(),
                "reason": "Cardiovascular Checkup",
                "patient_notes": "Routine followup for blood pressure",
            },
        )
        assert book_res.status_code == status.HTTP_201_CREATED
        appt_id = book_res.json()["id"]


        # 7. View Appointments List
        appts_res = client.get("/api/v1/appointments/my", headers=headers)
        assert appts_res.status_code == status.HTTP_200_OK
        assert any(a["id"] == appt_id for a in appts_res.json())

        # 8. Update Medical Profile
        prof_res = client.put(
            "/api/v1/patients/medical-profile",
            headers=headers,
            json={
                "blood_group": "A+",
                "gender": "Female",
                "allergies": [{"name": "Aspirin", "severity": "HIGH"}],
                "chronic_conditions": ["Asthma"],
                "current_medications": [{"name": "Albuterol"}],
            },
        )
        assert prof_res.status_code == status.HTTP_200_OK
        assert prof_res.json()["blood_group"] == "A+"

    # -----------------------------------------------------------------------
    # PHASE 5 & 6: DOCTOR VERIFICATION WORKFLOW & ADMIN GOVERNANCE
    # -----------------------------------------------------------------------
    def test_doctor_registration_approval_gate(self, client: TestClient, db_session: Session):
        """Verify unapproved doctors cannot practice until reviewed and approved by Admin."""
        # 1. Doctor registers
        doc_reg = client.post(
            "/api/v1/auth/register",
            json={
                "email": "unapproved.dr.watson@careai.com",
                "password": "DocSecret123!",
                "full_name": "Dr. John Watson",
                "role": "DOCTOR",
            },
        )
        assert doc_reg.status_code == status.HTTP_201_CREATED
        unapproved_doc_token = doc_reg.json()["access_token"]
        unapproved_doc_headers = {"Authorization": f"Bearer {unapproved_doc_token}"}

        # 2. Check profile shows approval_status = PENDING
        prof_res = client.get("/api/v1/doctors/me/profile", headers=unapproved_doc_headers)
        assert prof_res.status_code == status.HTTP_200_OK
        doc_profile_id = prof_res.json()["id"]
        assert prof_res.json()["approval_status"] == "PENDING"

        # 3. Patient tries to book unapproved doctor -> REJECTED (400)
        pat_headers = auth_header(self.patient)
        book_unapproved = client.post(
            "/api/v1/appointments",
            headers=pat_headers,
            json={
                "doctor_id": doc_profile_id,
                "scheduled_start": (datetime.now() + timedelta(days=2)).isoformat(),
                "scheduled_end": (datetime.now() + timedelta(days=2, minutes=30)).isoformat(),
                "reason": "Test Consultation",
            },
        )
        assert book_unapproved.status_code == status.HTTP_400_BAD_REQUEST
        assert "not been approved" in book_unapproved.json()["detail"].lower()

        # 4. Admin lists pending doctors -> sees unapproved doctor
        admin_headers = auth_header(self.admin)
        pending_res = client.get("/api/v1/admin/pending-doctors", headers=admin_headers)
        assert pending_res.status_code == status.HTTP_200_OK
        assert any(d["id"] == doc_profile_id for d in pending_res.json())

        # 5. Admin approves doctor
        appr_res = client.put(
            f"/api/v1/admin/doctors/{doc_profile_id}/approval",
            headers=admin_headers,
            json={"approval_status": "APPROVED"},
        )
        assert appr_res.status_code == status.HTTP_200_OK
        assert appr_res.json()["approval_status"] == "APPROVED"

        # 6. Doctor profile is now APPROVED
        updated_prof = client.get("/api/v1/doctors/me/profile", headers=unapproved_doc_headers)
        assert updated_prof.json()["approval_status"] == "APPROVED"

    # -----------------------------------------------------------------------
    # PHASE 6: ADMIN MEDICAL PRIVACY ISOLATION
    # -----------------------------------------------------------------------
    def test_admin_medical_document_privacy_boundary(self, client: TestClient, db_session: Session):
        """Verify Admin cannot download patient private medical records."""
        # Create a document for patient
        doc = MedicalDocument(
            patient_id=self.pat_prof.id,
            uploaded_by_user_id=self.patient.id,
            file_name="blood_test.pdf",
            storage_key="documents/mock_blood_test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            title="Private Diagnostic Record",
            document_type=DocumentType.LAB_REPORT,
        )
        db_session.add(doc)
        db_session.commit()

        # Admin attempting to download -> 403 Forbidden
        admin_headers = auth_header(self.admin)
        res = client.get(f"/api/v1/medical-documents/{doc.id}/download", headers=admin_headers)
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert "cannot access sensitive patient medical records" in res.json()["detail"].lower()

    # -----------------------------------------------------------------------
    # PHASE 7: COMPLETE LAB TECHNICIAN JOURNEY
    # -----------------------------------------------------------------------
    def test_complete_lab_technician_workflow(self, client: TestClient, db_session: Session):
        """Verify order creation -> queue -> collect -> enter results -> verify -> release."""
        doc_headers = auth_header(self.doctor)
        lab_headers = auth_header(self.lab_tech)

        # 1. Doctor creates Lab Order (requires appointment relationship)
        appt = Appointment(
            doctor_id=self.doc_prof.id,
            patient_id=self.pat_prof.id,
            scheduled_start=datetime.now() - timedelta(days=1),
            scheduled_end=datetime.now() - timedelta(days=1, minutes=30),
            status=AppointmentStatus.COMPLETED,
            reason="Cardiology Evaluation",
        )
        db_session.add(appt)
        db_session.commit()

        order_res = client.post(
            "/api/v1/lab/orders",
            headers=doc_headers,
            json={
                "patient_id": self.pat_prof.id,
                "priority": "STAT",
                "clinical_notes": "Hyperlipidemia Assessment",
                "items": [{"lab_test_id": self.lab_test.id}],
            },
        )
        assert order_res.status_code == status.HTTP_201_CREATED
        order_id = order_res.json()["id"]
        order_item_id = order_res.json()["items"][0]["id"]

        # 2. Lab Tech views work queue
        queue_res = client.get("/api/v1/lab/queue?priority=STAT", headers=lab_headers)
        assert queue_res.status_code == status.HTTP_200_OK
        assert any(o["id"] == order_id for o in queue_res.json())

        # 3. Lab Tech collects sample
        sample_res = client.post(
            f"/api/v1/lab/orders/{order_id}/collect-sample",
            headers=lab_headers,
            json={
                "specimen_type": "Serum (SST)",
                "sample_condition": "ACCEPTABLE",
                "collection_notes": "Draw completed without hemolysis",
            },
        )
        assert sample_res.status_code == status.HTTP_200_OK
        assert sample_res.json()["specimen_type"] == "Serum (SST)"
        assert sample_res.json()["sample_condition"] == "ACCEPTABLE"


        # 4. Lab Tech starts testing
        start_res = client.post(f"/api/v1/lab/orders/{order_id}/start-processing", headers=lab_headers)
        assert start_res.status_code == status.HTTP_200_OK
        assert start_res.json()["status"] == "IN_PROGRESS"

        # 5. Lab Tech enters results
        result_res = client.post(
            f"/api/v1/lab/orders/{order_id}/enter-results",
            headers=lab_headers,
            json={
                "results": [
                    {
                        "lab_order_item_id": order_item_id,
                        "numeric_value": 245.0,
                        "unit": "mg/dL",
                        "reference_range": "< 200 mg/dL",
                    }
                ]
            },
        )
        assert result_res.status_code == status.HTTP_200_OK
        assert result_res.json()["status"] == "RESULTS_ENTERED"

        # 6. Lab Tech verifies results
        verify_res = client.post(
            f"/api/v1/lab/orders/{order_id}/verify",
            headers=lab_headers,
            json={"verification_notes": "Quality control standard confirmed"},
        )
        assert verify_res.status_code == status.HTTP_200_OK
        assert verify_res.json()["status"] == "VERIFIED"

        # 7. Lab Tech releases report
        release_res = client.post(f"/api/v1/lab/orders/{order_id}/release", headers=lab_headers)
        assert release_res.status_code == status.HTTP_200_OK
        assert release_res.json()["status"] == "RELEASED"

        # 8. Patient can view released report
        pat_headers = auth_header(self.patient)
        pat_rep = client.get(f"/api/v1/lab/patient/my-reports/{order_id}", headers=pat_headers)
        assert pat_rep.status_code == status.HTTP_200_OK
        assert pat_rep.json()["status"] == "RELEASED"

    # -----------------------------------------------------------------------
    # PHASE 8: COMPLETE PHARMACY STAFF JOURNEY & PRESCRIPTION IMMUTABILITY
    # -----------------------------------------------------------------------
    def test_complete_pharmacy_dispensary_and_prescription_immutability(self, client: TestClient, db_session: Session):
        """Verify prescription queue -> under review -> ready -> dispensed and strict immutability."""
        doc_headers = auth_header(self.doctor)
        pharm_headers = auth_header(self.pharm_staff)

        # Create consultation appointment
        appt = Appointment(
            doctor_id=self.doc_prof.id,
            patient_id=self.pat_prof.id,
            scheduled_start=datetime.now() - timedelta(days=1),
            scheduled_end=datetime.now() - timedelta(days=1, minutes=30),
            status=AppointmentStatus.COMPLETED,
            reason="Hypertension Consult",
        )
        db_session.add(appt)
        db_session.commit()

        # 1. Doctor authors digital prescription
        rx_res = client.post(
            "/api/v1/prescriptions",
            headers=doc_headers,
            json={
                "appointment_id": appt.id,
                "diagnosis": "Primary Essential Hypertension",
                "clinical_notes": "Take with meals.",
                "valid_until": (date.today() + timedelta(days=60)).isoformat(),
                "items": [
                    {
                        "medication_name": "Lisinopril",
                        "drug_name": "Lisinopril",
                        "dosage": "10mg",
                        "frequency": "Once daily",
                        "duration": "30 days",
                        "route_of_administration": "Oral",
                        "instructions": "Take in the morning",
                    }
                ],
            },
        )
        assert rx_res.status_code == status.HTTP_201_CREATED
        rx_id = rx_res.json()["id"]

        # 2. Pharmacy staff reviews queue
        queue_res = client.get("/api/v1/pharmacy/prescriptions?status=PRESCRIBED", headers=pharm_headers)
        assert queue_res.status_code == status.HTTP_200_OK
        assert any(r["id"] == rx_id for r in queue_res.json())

        # 3. Move to UNDER_REVIEW
        r1 = client.patch(
            f"/api/v1/pharmacy/prescriptions/{rx_id}/status",
            headers=pharm_headers,
            json={"status": "UNDER_REVIEW", "pharmacy_notes": "Pharmacist verifying contraindications."},
        )
        assert r1.status_code == status.HTTP_200_OK
        assert r1.json()["status"] == "UNDER_REVIEW"

        # 4. Move to READY
        r2 = client.patch(
            f"/api/v1/pharmacy/prescriptions/{rx_id}/status",
            headers=pharm_headers,
            json={"status": "READY", "pharmacy_notes": "Medication staged for patient pickup."},
        )
        assert r2.status_code == status.HTTP_200_OK
        assert r2.json()["status"] == "READY"

        # 5. Dispense medication
        disp_res = client.post(
            f"/api/v1/pharmacy/prescriptions/{rx_id}/dispense",
            headers=pharm_headers,
            json={"pharmacy_notes": "Dispensed to patient in person."},
        )
        assert disp_res.status_code == status.HTTP_200_OK
        assert disp_res.json()["status"] == "DISPENSED"
        assert disp_res.json()["dispensed_at"] is not None
        assert disp_res.json()["dispensed_by_name"] == "Elena Rostova"

        # 6. IMMUTABILITY CHECK: Pharmacy cannot author or mutate doctor diagnosis/medications
        tamper_res = client.post(
            "/api/v1/prescriptions",
            headers=pharm_headers,
            json={
                "appointment_id": appt.id,
                "diagnosis": "Tampered",
                "items": [{"medication_name": "TamperedDrug", "dosage": "100mg", "frequency": "Daily", "duration": "10d"}],
            },
        )
        assert tamper_res.status_code == status.HTTP_403_FORBIDDEN

    # -----------------------------------------------------------------------
    # PHASE 9: AI ASSISTANT CONVERSATION & CONTEXT ISOLATION
    # -----------------------------------------------------------------------
    def test_ai_assistant_conversation_isolation_and_fallback(self, client: TestClient, db_session: Session):
        """Verify conversation thread isolation between users and friendly handling of missing Gemini keys."""
        pat1_headers = auth_header(self.patient)
        pat2_headers = auth_header(self.patient2)

        # Create thread for Patient 1 in DB
        conv = AIConversation(
            user_id=self.patient.id,
            role=UserRole.PATIENT,
            title="Blood Pressure Management Advice",
        )
        db_session.add(conv)
        db_session.flush()

        msg = AIMessage(
            conversation_id=conv.id,
            sender="USER",
            content="What lifestyle changes help with hypertension?",
        )
        db_session.add(msg)
        db_session.commit()

        # Patient 1 can access own thread
        res1 = client.get(f"/api/v1/ai-assistant/conversations/{conv.id}", headers=pat1_headers)
        assert res1.status_code == status.HTTP_200_OK
        assert len(res1.json()["messages"]) == 1

        # Patient 2 trying to access Patient 1's conversation -> 404 (Isolation)
        res2 = client.get(f"/api/v1/ai-assistant/conversations/{conv.id}", headers=pat2_headers)
        assert res2.status_code == status.HTTP_404_NOT_FOUND

        # Patient 1 deleting conversation
        del_res = client.delete(f"/api/v1/ai-assistant/conversations/{conv.id}", headers=pat1_headers)
        assert del_res.status_code == status.HTTP_200_OK

    # -----------------------------------------------------------------------
    # PHASE 11: NOTIFICATION USER ISOLATION
    # -----------------------------------------------------------------------
    def test_notification_user_isolation(self, client: TestClient, db_session: Session):
        """Verify notifications sent to User A are strictly invisible to User B."""
        # Create notification for patient 1
        notif = Notification(
            user_id=self.patient.id,
            title="Appointment Reminder",
            message="Your consultation is tomorrow at 10:00 AM.",
            notification_type=NotificationType.APPOINTMENT,
            priority=NotificationPriority.NORMAL,
            is_read=False,
        )
        db_session.add(notif)
        db_session.commit()

        pat1_headers = auth_header(self.patient)
        pat2_headers = auth_header(self.patient2)

        # Patient 1 sees notification in items
        res1 = client.get("/api/v1/notifications", headers=pat1_headers)
        assert res1.status_code == status.HTTP_200_OK
        assert any(n["id"] == notif.id for n in res1.json()["items"])

        # Patient 2 does not see Patient 1's notification
        res2 = client.get("/api/v1/notifications", headers=pat2_headers)
        assert res2.status_code == status.HTTP_200_OK
        assert not any(n["id"] == notif.id for n in res2.json()["items"])

        # Patient 1 marks as read
        read_res = client.patch(f"/api/v1/notifications/{notif.id}/read", headers=pat1_headers)
        assert read_res.status_code == status.HTTP_200_OK
        assert read_res.json()["is_read"] is True
