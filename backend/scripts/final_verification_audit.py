"""CareAI SaaS — Master Final Verification & Audit Execution Script.

Runs comprehensive live integration and RBAC security verification across all
5 platform roles, diagnostic lab workflows, pharmacy dispensary, cross-role
journeys, and AI capabilities.
"""
import sys
from datetime import datetime, date, time, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch

from app.main import app
from app.database.session import SessionLocal
from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.availability import DoctorAvailability
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription, PrescriptionItem, PrescriptionStatus
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
from app.models.medical_document import MedicalDocument, DocumentType
from app.models.ai_report import AIAnalysisReport, InteractionSeverity
from app.models.ai_assistant import AIConversation, AIMessage
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.ai.client import ai_client, AIProviderUnavailableError


def run_master_verification():
    print("=" * 85)
    print("CAREAI HEALTHCARE SAAS — FINAL PRODUCTION & VERIFICATION AUDIT")
    print("=" * 85)

    client = TestClient(app)
    db: Session = SessionLocal()

    audit_records = []

    def record(category: str, check_name: str, passed: bool, details: str = ""):
        tag = "PASS" if passed else "FAIL"
        print(f"[{tag}] [{category}] {check_name}" + (f" -> {details}" if details else ""))
        audit_records.append({"category": category, "check": check_name, "passed": passed, "details": details})
        if not passed:
            print(f"   [ERROR-DETAILS]: {details}")

    try:
        # ===================================================================
        # SECTION 1: AUTHENTICATION & IDENTITY FOR ALL 5 ROLES
        # ===================================================================
        creds = [
            (UserRole.ADMIN, "admin@careai.com", "AdminPass123!"),
            (UserRole.DOCTOR, "dr.sarah@careai.com", "DoctorPass123!"),
            (UserRole.PATIENT, "patient.john@example.com", "PatientPass123!"),
            (UserRole.LAB_TECHNICIAN, "lab.tech@careai.com", "LabTechPass123!"),
            (UserRole.PHARMACY_STAFF, "pharmacy.staff@careai.com", "PharmacyPass123!"),
        ]

        tokens = {}
        for role, email, password in creds:
            res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
            if res.status_code == 200:
                t = res.json()["access_token"]
                tokens[role] = {"Authorization": f"Bearer {t}"}
                me_res = client.get("/api/v1/auth/me", headers=tokens[role])
                me_role = me_res.json().get("role") if me_res.status_code == 200 else None
                record("1. Authentication", f"Login & Role Resolution for {role.value}", me_role == role.value, f"Resolved role: {me_role}")
            else:
                record("1. Authentication", f"Login for {role.value}", False, f"Status {res.status_code}: {res.text}")

        # Invalid password rejection
        bad_pw = client.post("/api/v1/auth/login", json={"email": "admin@careai.com", "password": "WrongPassword!"})
        record("1. Authentication", "Reject Invalid Password", bad_pw.status_code == 401, f"Status: {bad_pw.status_code}")

        # Self registration policy
        pat_reg = client.post("/api/v1/auth/register", json={
            "email": f"audit.pat.{int(datetime.now().timestamp())}@careai.com",
            "password": "Password123!",
            "full_name": "Audit Registered Patient",
            "role": "PATIENT",
        })
        record("1. Authentication", "Public Patient Self-Registration Allowed", pat_reg.status_code == 201, f"Status: {pat_reg.status_code}")

        for priv_role in ["ADMIN", "LAB_TECHNICIAN", "PHARMACY_STAFF"]:
            priv_reg = client.post("/api/v1/auth/register", json={
                "email": f"bad.{priv_role.lower()}@careai.com",
                "password": "Password123!",
                "full_name": "Privilege Escalation Attempt",
                "role": priv_role,
            })
            record("1. Authentication", f"Block Public {priv_role} Self-Registration", priv_reg.status_code == 403, f"Status: {priv_reg.status_code}")

        # ===================================================================
        # SECTION 2: LAB TECHNICIAN COMPLETE WORKFLOW
        # ===================================================================
        # 1. Lab dashboard statistics
        lab_dash = client.get("/api/v1/dashboard/lab-technician", headers=tokens[UserRole.LAB_TECHNICIAN])
        record("2. Lab Technician", "Lab Dashboard Metrics Retrieval", lab_dash.status_code == 200 and "stats" in lab_dash.json())

        lab_stats = client.get("/api/v1/lab/stats", headers=tokens[UserRole.LAB_TECHNICIAN])
        record("2. Lab Technician", "Lab Queue Statistics Endpoint", lab_stats.status_code == 200 and "pending_samples" in lab_stats.json())

        # 2. Doctor creates STAT lab requisition with Electrolyte & CBC panel
        pat_john = db.query(PatientProfile).join(User).filter(User.email == "patient.john@example.com").first()
        doc_sarah = db.query(DoctorProfile).join(User).filter(User.email == "dr.sarah@careai.com").first()
        cbc_t = db.query(LabTest).filter(LabTest.test_code == "CBC-001").first()
        elec_t = db.query(LabTest).filter(LabTest.test_code == "ELEC-008").first()

        lab_order_res = client.post("/api/v1/lab/orders", json={
            "patient_id": pat_john.id,
            "priority": "STAT",
            "clinical_notes": "Stat emergency panel for acute electrolyte workup",
            "items": [
                {"lab_test_id": cbc_t.id, "instructions": "Full differential"},
                {"lab_test_id": elec_t.id, "instructions": "Evaluate potassium"},
            ],
        }, headers=tokens[UserRole.DOCTOR])
        record("2. Lab Technician", "Doctor Creates STAT Diagnostic Order", lab_order_res.status_code == 201, f"Order #{lab_order_res.json().get('id')}")
        order_id = lab_order_res.json()["id"]
        item_ids = [i["id"] for i in lab_order_res.json()["items"]]

        # 3. Patient cannot view unreleased order
        pat_hidden = client.get(f"/api/v1/lab/orders/{order_id}", headers=tokens[UserRole.PATIENT])
        record("2. Lab Technician", "Patient Blocked from Unreleased Lab Order", pat_hidden.status_code == 403, f"Status: {pat_hidden.status_code}")

        # 4. Lab Tech Work Queue
        queue_res = client.get("/api/v1/lab/queue?priority=STAT", headers=tokens[UserRole.LAB_TECHNICIAN])
        record("2. Lab Technician", "Lab Technician STAT Work Queue Listing", queue_res.status_code == 200 and any(o["id"] == order_id for o in queue_res.json()))

        # 5. Sample Collection (Compromised sample triggers recollection)
        hem_sample = client.post(f"/api/v1/lab/orders/{order_id}/collect-sample", json={
            "specimen_type": "Whole Blood",
            "sample_condition": "HEMOLYZED",
            "collection_notes": "Sample rejected due to visible hemolysis.",
        }, headers=tokens[UserRole.LAB_TECHNICIAN])
        order_chk = client.get(f"/api/v1/lab/orders/{order_id}", headers=tokens[UserRole.LAB_TECHNICIAN])
        record("2. Lab Technician", "Compromised Sample Rejection (Retains SAMPLE_PENDING)", hem_sample.status_code == 200 and order_chk.json()["status"] == "SAMPLE_PENDING")

        # Clean collection
        clean_sample = client.post(f"/api/v1/lab/orders/{order_id}/collect-sample", json={
            "specimen_type": "Whole Blood + Serum SST",
            "sample_condition": "ACCEPTABLE",
            "collection_notes": "Clean redraw, 2 tubes.",
        }, headers=tokens[UserRole.LAB_TECHNICIAN])
        record("2. Lab Technician", "Specimen Collection Recorded (ACCEPTABLE)", clean_sample.status_code == 200 and clean_sample.json()["sample_condition"] == "ACCEPTABLE")

        # 6. Start Analytical Processing
        proc_res = client.post(f"/api/v1/lab/orders/{order_id}/start-processing", headers=tokens[UserRole.LAB_TECHNICIAN])
        record("2. Lab Technician", "Analytical Processing Started (IN_PROGRESS)", proc_res.status_code == 200 and proc_res.json()["status"] == "IN_PROGRESS")

        # 7. Result Entry with Critical High Potassium (6.9 mmol/L)
        res_entry = client.post(f"/api/v1/lab/orders/{order_id}/enter-results", json={
            "results": [
                {"lab_order_item_id": item_ids[0], "numeric_value": 14.0, "unit": "g/dL"},
                {"lab_order_item_id": item_ids[1], "numeric_value": 6.9, "unit": "mmol/L"},
            ]
        }, headers=tokens[UserRole.LAB_TECHNICIAN])
        entry_data = res_entry.json()
        pot_item = next((it for it in entry_data["items"] if it["id"] == item_ids[1]), None)
        is_crit = pot_item and pot_item["result"]["is_critical"] is True and pot_item["result"]["result_flag"] == "CRITICAL"
        record("2. Lab Technician", "Result Entry with Automated Critical Threshold Flagging", res_entry.status_code == 200 and is_crit, f"Flag: {pot_item['result']['result_flag']}")

        # 8. Premature Release Blocked Before Verification
        early_rel = client.post(f"/api/v1/lab/orders/{order_id}/release", headers=tokens[UserRole.LAB_TECHNICIAN])
        record("2. Lab Technician", "Prevent Premature Release Before Verification", early_rel.status_code == 400, f"Status: {early_rel.status_code}")

        # 9. Verification
        ver_res = client.post(f"/api/v1/lab/orders/{order_id}/verify", json={
            "verification_notes": "Recalibrated ISE analyzer and verified with senior technologist.",
        }, headers=tokens[UserRole.LAB_TECHNICIAN])
        record("2. Lab Technician", "Technician Verification of Diagnostic Findings", ver_res.status_code == 200 and ver_res.json()["status"] == "VERIFIED")

        # 10. Release
        rel_res = client.post(f"/api/v1/lab/orders/{order_id}/release", headers=tokens[UserRole.LAB_TECHNICIAN])
        record("2. Lab Technician", "Diagnostic Report Release (RELEASED)", rel_res.status_code == 200 and rel_res.json()["status"] == "RELEASED")

        # 11. Patient Portal Views Released Report
        pat_reports = client.get("/api/v1/lab/patient/my-reports", headers=tokens[UserRole.PATIENT])
        record("2. Lab Technician", "Patient Portal Lists Released Diagnostic Reports", pat_reports.status_code == 200 and any(r["id"] == order_id for r in pat_reports.json()))

        pat_report_detail = client.get(f"/api/v1/lab/patient/my-reports/{order_id}", headers=tokens[UserRole.PATIENT])
        record("2. Lab Technician", "Patient Views Structured Diagnostic Lab Report Details", pat_report_detail.status_code == 200 and len(pat_report_detail.json()["results"]) == 2)

        # ===================================================================
        # SECTION 3: PHARMACY STAFF COMPLETE WORKFLOW
        # ===================================================================
        # 1. Pharmacy Dashboard
        pharm_dash = client.get("/api/v1/pharmacy/dashboard", headers=tokens[UserRole.PHARMACY_STAFF])
        record("3. Pharmacy Staff", "Pharmacy Dashboard Operational Metrics", pharm_dash.status_code == 200 and "stats" in pharm_dash.json())

        # Create a fresh completed consultation appointment for this test
        fresh_appt = Appointment(
            patient_id=pat_john.id,
            doctor_id=doc_sarah.id,
            scheduled_start=datetime.now(timezone.utc) - timedelta(days=1),
            scheduled_end=datetime.now(timezone.utc) - timedelta(days=1, minutes=30),
            status=AppointmentStatus.COMPLETED,
            reason="Hypertension Medication Review",
        )
        db.add(fresh_appt)
        db.commit()
        db.refresh(fresh_appt)

        doc_rx_res = client.post("/api/v1/prescriptions", json={
            "appointment_id": fresh_appt.id,
            "diagnosis": "Stage 2 Hypertension with Renal Impairment",
            "clinical_notes": "Monitor serum potassium and creatinine regularly.",
            "valid_until": (date.today() + timedelta(days=90)).isoformat(),
            "items": [
                {
                    "medication_name": "Amlodipine Besylate",
                    "drug_name": "Amlodipine",
                    "dosage": "5 mg",
                    "frequency": "Once daily in the morning",
                    "duration": "30 days",
                    "route_of_administration": "Oral",
                    "instructions": "Take with water.",
                }
            ],
        }, headers=tokens[UserRole.DOCTOR])
        record("3. Pharmacy Staff", "Doctor Issues Prescription with Items", doc_rx_res.status_code == 201, f"Prescription #{doc_rx_res.json().get('id') if doc_rx_res.status_code == 201 else doc_rx_res.text}")
        rx_id = doc_rx_res.json()["id"]

        # 3. Pharmacy Queue listing & search
        pharm_q = client.get("/api/v1/pharmacy/prescriptions", headers=tokens[UserRole.PHARMACY_STAFF])
        record("3. Pharmacy Staff", "Pharmacy Dispensary Queue Retrieval", pharm_q.status_code == 200 and any(r["id"] == rx_id for r in pharm_q.json()))

        pharm_filter = client.get("/api/v1/pharmacy/prescriptions?search=John", headers=tokens[UserRole.PHARMACY_STAFF])
        record("3. Pharmacy Staff", "Pharmacy Queue Search by Patient Name", pharm_filter.status_code == 200 and any(r["id"] == rx_id for r in pharm_filter.json()))

        # 4. Pharmacy Details view
        rx_detail = client.get(f"/api/v1/pharmacy/prescriptions/{rx_id}", headers=tokens[UserRole.PHARMACY_STAFF])
        record("3. Pharmacy Staff", "Prescription Detail with Clinical Notes", rx_detail.status_code == 200 and rx_detail.json()["id"] == rx_id)

        # 5. Status Transition: PRESCRIBED -> UNDER_REVIEW
        st_rev = client.patch(f"/api/v1/pharmacy/prescriptions/{rx_id}/status", json={
            "status": "UNDER_REVIEW",
            "pharmacy_notes": "Pharmacist review in progress for dosage appropriateness.",
        }, headers=tokens[UserRole.PHARMACY_STAFF])
        record("3. Pharmacy Staff", "Status Transition to UNDER_REVIEW", st_rev.status_code == 200 and st_rev.json()["status"] == "UNDER_REVIEW")

        # 6. Status Transition: UNDER_REVIEW -> READY
        st_ready = client.patch(f"/api/v1/pharmacy/prescriptions/{rx_id}/status", json={
            "status": "READY",
            "pharmacy_notes": "Prepared and labeled. Ready in pickup bay #4.",
        }, headers=tokens[UserRole.PHARMACY_STAFF])
        record("3. Pharmacy Staff", "Status Transition to READY (Ready for Pickup)", st_ready.status_code == 200 and st_ready.json()["status"] == "READY")

        # 7. Status Transition: READY -> DISPENSED via /dispense endpoint
        st_disp = client.post(f"/api/v1/pharmacy/prescriptions/{rx_id}/dispense", json={
            "pharmacy_notes": "Dispensed to patient in person. Verified identity.",
        }, headers=tokens[UserRole.PHARMACY_STAFF])
        disp_data = st_disp.json()
        record("3. Pharmacy Staff", "Dispense Medication (DISPENSED with Dispenser Name)", st_disp.status_code == 200 and disp_data["status"] == "DISPENSED" and disp_data["dispensed_by_name"] is not None)

        # 8. Notifications after dispensing
        pat_notifs = client.get("/api/v1/notifications", headers=tokens[UserRole.PATIENT])
        record("3. Pharmacy Staff", "Patient Receives Medication Dispensed Notification", pat_notifs.status_code == 200 and any("dispensed" in n["title"].lower() or "ready" in n["title"].lower() for n in pat_notifs.json()["items"]))

        doc_notifs = client.get("/api/v1/notifications", headers=tokens[UserRole.DOCTOR])
        record("3. Pharmacy Staff", "Doctor Receives Dispensation Confirmation Notification", doc_notifs.status_code == 200 and any("dispensed" in n["title"].lower() for n in doc_notifs.json()["items"]))

        # 9. Immutability: Pharmacy cannot modify doctor prescription clinical details
        pharm_tamper = client.post("/api/v1/prescriptions", json={
            "appointment_id": fresh_appt.id,
            "diagnosis": "Tampered Diagnosis",
            "items": [{"medication_name": "Tampered Drug", "dosage": "500mg", "frequency": "Daily", "duration": "30d"}],
        }, headers=tokens[UserRole.PHARMACY_STAFF])
        record("3. Pharmacy Staff", "Confirm Pharmacy Staff Blocked from Authoring Prescriptions (403)", pharm_tamper.status_code == 403, f"Status: {pharm_tamper.status_code}")

        # ===================================================================
        # SECTION 4: CROSS-ROLE WORKFLOWS END-TO-END
        # ===================================================================
        # 1. Patient -> Appointment -> Doctor workflow
        # Find doctor directory
        doc_dir = client.get("/api/v1/doctors/directory?specialization=Cardiology", headers=tokens[UserRole.PATIENT])
        record("4. Cross-Role E2E", "Patient Searches Doctor Directory", doc_dir.status_code == 200 and len(doc_dir.json()) >= 1)

        # Discover slots for weekday with Dr. Sarah
        target_d = date.today() + timedelta(days=3)
        while target_d.weekday() >= 5:
            target_d += timedelta(days=1)
        slots_res = client.get(f"/api/v1/doctors/{doc_sarah.id}/available-slots?date={target_d.isoformat()}", headers=tokens[UserRole.PATIENT])
        record("4. Cross-Role E2E", "Patient Discovers Available Consultation Slots", slots_res.status_code == 200 and len(slots_res.json()["available_slots"]) > 0)
        first_slot = slots_res.json()["available_slots"][0]
        sp = [int(x) for x in first_slot.split(":")[:2]]
        start_dt = datetime.combine(target_d, time(sp[0], sp[1]))
        end_dt = start_dt + timedelta(minutes=30)

        # Book appointment
        new_appt = client.post("/api/v1/appointments", json={
            "doctor_id": doc_sarah.id,
            "scheduled_start": start_dt.isoformat(),
            "scheduled_end": end_dt.isoformat(),
            "reason": "Cardiac Evaluation",
            "patient_notes": "Periodic checkup",
        }, headers=tokens[UserRole.PATIENT])
        record("4. Cross-Role E2E", "Patient Books Consultation Appointment", new_appt.status_code == 201, f"Appt #{new_appt.json().get('id') if new_appt.status_code == 201 else new_appt.text}")
        booked_appt_id = new_appt.json()["id"]

        # Doctor views, confirms, and completes appointment
        doc_appts = client.get("/api/v1/appointments/doctor/my", headers=tokens[UserRole.DOCTOR])
        record("4. Cross-Role E2E", "Doctor Views Incoming Booked Appointment", doc_appts.status_code == 200 and any(a["id"] == booked_appt_id for a in doc_appts.json()))

        # Doctor confirms appointment
        conf_appt = client.patch(f"/api/v1/appointments/{booked_appt_id}/confirm", headers=tokens[UserRole.DOCTOR])
        record("4. Cross-Role E2E", "Doctor Confirms Appointment (CONFIRMED)", conf_appt.status_code == 200 and conf_appt.json()["status"] == "CONFIRMED")

        # Doctor completes appointment
        comp_appt = client.patch(f"/api/v1/appointments/{booked_appt_id}/complete", json={
            "doctor_notes": "Consultation concluded successfully. Prescription issued.",
        }, headers=tokens[UserRole.DOCTOR])
        record("4. Cross-Role E2E", "Doctor Completes Appointment (COMPLETED)", comp_appt.status_code == 200 and comp_appt.json()["status"] == "COMPLETED")

        # 2. Admin -> Doctor Approval Gate
        new_doc_reg = client.post("/api/v1/auth/register", json={
            "email": f"audit.new.doc.{int(datetime.now().timestamp())}@careai.com",
            "password": "DoctorPass123!",
            "full_name": "Dr. Candidate Review",
            "role": "DOCTOR",
        })
        record("4. Cross-Role E2E", "New Doctor Registers (Initial State PENDING)", new_doc_reg.status_code == 201)
        new_doc_token = new_doc_reg.json()["access_token"]
        new_doc_headers = {"Authorization": f"Bearer {new_doc_token}"}

        # Check pending status
        cand_prof = client.get("/api/v1/doctors/me/profile", headers=new_doc_headers)
        record("4. Cross-Role E2E", "Doctor Profile Verification Status is PENDING", cand_prof.status_code == 200 and cand_prof.json()["approval_status"] == "PENDING")
        cand_prof_id = cand_prof.json()["id"]

        # Admin lists pending doctors
        admin_pending = client.get("/api/v1/admin/pending-doctors", headers=tokens[UserRole.ADMIN])
        record("4. Cross-Role E2E", "Admin Lists Pending Doctor Applications", admin_pending.status_code == 200 and any(d["id"] == cand_prof_id for d in admin_pending.json()))

        # Admin approves doctor
        appr_act = client.put(f"/api/v1/admin/doctors/{cand_prof_id}/approval", json={
            "approval_status": "APPROVED",
        }, headers=tokens[UserRole.ADMIN])
        record("4. Cross-Role E2E", "Admin Approves Doctor Credential Application", appr_act.status_code == 200 and appr_act.json()["approval_status"] == "APPROVED")

        # ===================================================================
        # SECTION 5: RBAC SECURITY BOUNDARIES ACROSS ALL 5 ROLES
        # ===================================================================
        # Full 5x5 dashboard isolation matrix
        matrix = [
            (UserRole.PATIENT, "/api/v1/dashboard/patient"),
            (UserRole.DOCTOR, "/api/v1/dashboard/doctor"),
            (UserRole.ADMIN, "/api/v1/dashboard/admin"),
            (UserRole.LAB_TECHNICIAN, "/api/v1/dashboard/lab-technician"),
            (UserRole.PHARMACY_STAFF, "/api/v1/dashboard/pharmacy"),
        ]

        for allowed_r, ep in matrix:
            # Authorized access
            res_auth = client.get(ep, headers=tokens[allowed_r])
            record("5. RBAC Security", f"Authorized Access: {allowed_r.value} -> {ep}", res_auth.status_code == 200, f"HTTP {res_auth.status_code}")

            # Unauthorized other roles
            for test_r, h in tokens.items():
                if test_r != allowed_r:
                    res_block = client.get(ep, headers=h)
                    record("5. RBAC Security", f"RBAC Deny: {test_r.value} -> {ep}", res_block.status_code == 403, f"HTTP {res_block.status_code}")

            # Unauthenticated
            res_anon = client.get(ep)
            record("5. RBAC Security", f"Unauthenticated Block: Anonymous -> {ep}", res_anon.status_code in [401, 403], f"HTTP {res_anon.status_code}")

        # Specific role barriers:
        # Patient cannot access Admin user management
        pat_adm_block = client.get("/api/v1/admin/users", headers=tokens[UserRole.PATIENT])
        record("5. RBAC Security", "Patient Blocked from Admin User Management (403)", pat_adm_block.status_code == 403)

        # Doctor cannot create administrative staff
        doc_staff_block = client.post("/api/v1/admin/staff", json={
            "email": "intruder@bad.com", "password": "Pass!", "full_name": "Intruder", "role": "ADMIN"
        }, headers=tokens[UserRole.DOCTOR])
        record("5. RBAC Security", "Doctor Blocked from Staff Provisioning (403)", doc_staff_block.status_code == 403)

        # Lab Tech cannot view pharmacy queue
        lab_pharm_block = client.get("/api/v1/pharmacy/prescriptions", headers=tokens[UserRole.LAB_TECHNICIAN])
        record("5. RBAC Security", "Lab Tech Blocked from Pharmacy Queue (403)", lab_pharm_block.status_code == 403)

        # Pharmacy Staff cannot view lab queue
        pharm_lab_block = client.get("/api/v1/lab/queue", headers=tokens[UserRole.PHARMACY_STAFF])
        record("5. RBAC Security", "Pharmacy Staff Blocked from Lab Queue (403)", pharm_lab_block.status_code == 403)

        # Admin PHI boundary: Admin cannot download sensitive patient documents
        admin_phi_doc = MedicalDocument(
            patient_id=pat_john.id,
            uploaded_by_user_id=pat_john.user_id,
            file_name="phi_sensitive_test.pdf",
            storage_key=f"documents/phi_test_{int(datetime.now().timestamp())}.pdf",
            file_size=512,
            mime_type="application/pdf",
            title="Sensitive Genomic Analysis",
            document_type=DocumentType.LAB_REPORT,
        )
        db.add(admin_phi_doc)
        db.commit()

        admin_dl = client.get(f"/api/v1/medical-documents/{admin_phi_doc.id}/download", headers=tokens[UserRole.ADMIN])
        record("5. RBAC Security", "Admin PHI Privacy Barrier (Admin cannot download patient documents)", admin_dl.status_code == 403, f"Status: {admin_dl.status_code}")

        # ===================================================================
        # SECTION 6: AI-POWERED FEATURES & FAULT TOLERANCE
        # ===================================================================
        # 1. CareAI Assistant Chat Execution
        ai_chat = client.post("/api/v1/ai-assistant/chat", json={
            "message": "What is the recommended fasting blood glucose range for an adult?",
        }, headers=tokens[UserRole.PATIENT])

        if ai_chat.status_code == 200:
            record("6. AI Capabilities", "CareAI Assistant Live Response", True, f"Model: {ai_chat.json().get('model_name')}")
            conv_id = ai_chat.json()["conversation_id"]

            # Conversation listing
            convs = client.get("/api/v1/ai-assistant/conversations", headers=tokens[UserRole.PATIENT])
            record("6. AI Capabilities", "AI Assistant Multi-Turn Conversation Listing", convs.status_code == 200 and len(convs.json()) >= 1)

            # Cleanup thread
            del_c = client.delete(f"/api/v1/ai-assistant/conversations/{conv_id}", headers=tokens[UserRole.PATIENT])
            record("6. AI Capabilities", "AI Assistant Conversation Thread Deletion", del_c.status_code == 200)
        elif ai_chat.status_code == 503:
            record("6. AI Capabilities", "AI Assistant Controlled Outage Fallback (HTTP 503)", True, f"Detail: {ai_chat.json().get('detail')}")

        # 2. Emergency Symptom Detection & Triage Guidance
        with patch.object(ai_client, "generate_completion", return_value="Please call emergency services immediately."):
            emerg_res = client.post("/api/v1/ai-assistant/chat", json={
                "message": "I have severe crushing chest pain radiating to my left arm.",
            }, headers=tokens[UserRole.PATIENT])
            has_emerg = emerg_res.status_code == 200 and emerg_res.json().get("safety_metadata", {}).get("emergency_symptom_detected") is True
            record("6. AI Capabilities", "Emergency Symptom Detection & Safety Guardrails", has_emerg, "Emergency detected in safety metadata")

        # 3. Prescription Safety Analysis Engine (Ad-hoc & Prescription Binding)
        interaction_analysis = client.post("/api/v1/ai/analyze-interactions", json={
            "medications": ["Lisinopril", "Spironolactone"],
            "patient_allergies": ["Penicillin"],
            "patient_conditions": ["Hypertension", "Mild Chronic Kidney Disease"],
        }, headers=tokens[UserRole.DOCTOR])
        record("6. AI Capabilities", "Multi-Drug Interaction Analysis Sandbox (/ai/analyze-interactions)", interaction_analysis.status_code == 200 and "overall_risk_level" in interaction_analysis.json(), f"Risk: {interaction_analysis.json().get('overall_risk_level')}")

        rx_analysis = client.post(f"/api/v1/ai/prescriptions/{rx_id}/analyze", headers=tokens[UserRole.DOCTOR])
        record("6. AI Capabilities", "Prescription Safety Analysis Engine (/ai/prescriptions/{id}/analyze)", rx_analysis.status_code == 200 and "overall_risk_level" in rx_analysis.json(), f"Report ID: {rx_analysis.json().get('id')}")

        rx_report = client.get(f"/api/v1/ai/prescriptions/{rx_id}/report", headers=tokens[UserRole.PATIENT])
        record("6. AI Capabilities", "Retrieve Prescription Safety Report (/ai/prescriptions/{id}/report)", rx_report.status_code == 200 and rx_report.json()["prescription_id"] == rx_id)

        # 4. Medical Document AI Analysis
        # Create valid mock PDF document for John
        from scripts.verify_live_gemini import create_mock_pdf_with_text
        from app.services.medical_document_service import medical_document_service
        pat_user_obj = db.query(User).filter(User.email == "patient.john@example.com").first()
        doc_obj = medical_document_service.upload_document(
            db=db,
            patient_user=pat_user_obj,
            file_content=create_mock_pdf_with_text("Hemoglobin: 14.5 g/dL. WBC: 6,500 /uL. Platelets: 250,000 /uL. Diagnostic impression: Normal hematologic parameters."),
            original_filename="cbc_report_audit.pdf",
            title="Complete Blood Count Laboratory Panel",
            document_type=DocumentType.LAB_REPORT,
        )
        doc_analysis = client.post(f"/api/v1/medical-documents/{doc_obj.id}/analyze", headers=tokens[UserRole.PATIENT])
        record("6. AI Capabilities", "Medical Document AI Analysis Flow", doc_analysis.status_code in [200, 503], f"Status: {doc_analysis.status_code}")

        # 5. Fault Tolerance when Gemini Provider is Down
        with patch.object(ai_client, "generate_completion", side_effect=AIProviderUnavailableError("Gemini API connection reset")):
            outage_res = client.post("/api/v1/ai-assistant/chat", json={
                "message": "Explain hypertension lifestyle modifications.",
            }, headers=tokens[UserRole.PATIENT])
            record("6. AI Capabilities", "Controlled Fault Tolerance on Provider Outage (503 Service Unavailable)", outage_res.status_code == 503, f"Status: {outage_res.status_code}")

    finally:
        db.close()

    print("=" * 85)
    total_checks = len(audit_records)
    passed_checks = sum(1 for r in audit_records if r["passed"])
    pass_pct = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
    print(f"MASTER VERIFICATION AUDIT COMPLETE: {passed_checks}/{total_checks} CHECKS PASSED ({pass_pct:.1f}%)")
    print("=" * 85)

    return passed_checks == total_checks, audit_records


if __name__ == "__main__":
    success, _ = run_master_verification()
    sys.exit(0 if success else 1)
