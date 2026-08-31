"""Seed script to populate CareAI Healthcare SaaS with rich, connected demo data across all 5 roles."""
import os
import sys
from datetime import date, time, datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.availability import DoctorAvailability, DoctorUnavailableDate
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription, PrescriptionItem, PrescriptionStatus
from app.models.ai_report import AIAnalysisReport, InteractionSeverity
from app.models.medical_document import MedicalDocument, DocumentType
from app.models.notification import Notification, NotificationType, NotificationPriority
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
from app.core.security import get_password_hash
from app.core.storage import storage_service


def seed_database():
    db: Session = SessionLocal()
    try:
        print("[+] Seeding CareAI Healthcare SaaS platform with rich demo data...")

        # -------------------------------------------------------------
        # 1. Platform Administrator
        # -------------------------------------------------------------
        admin = db.query(User).filter(User.email == "pillu.212006@gmail.com").first()
        if not admin:
            # Check legacy admin and update or create
            legacy_admin = db.query(User).filter(User.email == "admin@careai.com").first()
            if legacy_admin:
                legacy_admin.email = "pillu.212006@gmail.com"
                legacy_admin.hashed_password = get_password_hash("Neha@6328")
                admin = legacy_admin
                db.flush()
                print("  [OK] Admin updated: pillu.212006@gmail.com / Neha@6328")
            else:
                admin = User(
                    email="pillu.212006@gmail.com",
                    hashed_password=get_password_hash("Neha@6328"),
                    full_name="Chief Medical Admin",
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_verified=True,
                )
                db.add(admin)
                db.flush()
                print("  [OK] Admin created: pillu.212006@gmail.com / Neha@6328")
        else:
            admin.hashed_password = get_password_hash("Neha@6328")
            db.flush()
            print("  [OK] Admin password refreshed: pillu.212006@gmail.com / Neha@6328")

        # -------------------------------------------------------------
        # 1b. Lab Technician
        # -------------------------------------------------------------
        lab_tech = db.query(User).filter(User.email == "lab.tech@careai.com").first()
        if not lab_tech:
            lab_tech = User(
                email="lab.tech@careai.com",
                hashed_password=get_password_hash("LabTechPass123!"),
                full_name="Alex Rivera (Lead Lab Specialist)",
                role=UserRole.LAB_TECHNICIAN,
                is_active=True,
                is_verified=True,
            )
            db.add(lab_tech)
            db.flush()
            print("  [OK] Lab Technician created: lab.tech@careai.com / LabTechPass123!")

        # -------------------------------------------------------------
        # 1c. Pharmacy Staff
        # -------------------------------------------------------------
        pharmacy_staff = db.query(User).filter(User.email == "pharmacy.staff@careai.com").first()
        if not pharmacy_staff:
            pharmacy_staff = User(
                email="pharmacy.staff@careai.com",
                hashed_password=get_password_hash("PharmacyPass123!"),
                full_name="Elena Rostova (Chief Clinical Pharmacist)",
                role=UserRole.PHARMACY_STAFF,
                is_active=True,
                is_verified=True,
            )
            db.add(pharmacy_staff)
            db.flush()
            print("  [OK] Pharmacy Staff created: pharmacy.staff@careai.com / PharmacyPass123!")

        # -------------------------------------------------------------
        # 2. Approved Doctors
        # -------------------------------------------------------------
        doctors_data = [
            {
                "email": "dr.sarah@careai.com",
                "name": "Sarah Jenkins",
                "specialization": "Cardiology",
                "license": "MED-CARDIO-8890",
                "experience": 12,
                "bio": "Board-certified cardiologist specializing in preventive cardiology, coronary artery disease, and hypertension management.",
                "hospital": "Metro Heart & Vascular Institute",
                "fee": 150.00,
                "schedules": [
                    {"day": 0, "start": time(9, 0), "end": time(13, 0), "duration": 30},
                    {"day": 1, "start": time(9, 0), "end": time(13, 0), "duration": 30},
                    {"day": 3, "start": time(14, 0), "end": time(18, 0), "duration": 30},
                ],
            },
            {
                "email": "dr.marcus@careai.com",
                "name": "Marcus Vance",
                "specialization": "Neurology",
                "license": "MED-NEURO-5521",
                "experience": 9,
                "bio": "Clinical neurologist focused on migraine management, stroke prevention, and neuro-rehabilitation therapies.",
                "hospital": "University Neuro Clinic",
                "fee": 175.00,
                "schedules": [
                    {"day": 2, "start": time(10, 0), "end": time(16, 0), "duration": 30},
                    {"day": 4, "start": time(10, 0), "end": time(16, 0), "duration": 30},
                ],
            },
            {
                "email": "dr.emily@careai.com",
                "name": "Emily Chen",
                "specialization": "Pediatrics",
                "license": "MED-PED-3319",
                "experience": 8,
                "bio": "Dedicated pediatrician committed to child wellness, developmental milestones, and pediatric immunology.",
                "hospital": "Children's Health Alliance",
                "fee": 120.00,
                "schedules": [
                    {"day": 0, "start": time(9, 0), "end": time(14, 0), "duration": 20},
                    {"day": 2, "start": time(9, 0), "end": time(14, 0), "duration": 20},
                    {"day": 4, "start": time(9, 0), "end": time(14, 0), "duration": 20},
                ],
            },
        ]

        doc_profiles = {}
        for d in doctors_data:
            user = db.query(User).filter(User.email == d["email"]).first()
            if not user:
                user = User(
                    email=d["email"],
                    hashed_password=get_password_hash("DoctorPass123!"),
                    full_name=d["name"],
                    role=UserRole.DOCTOR,
                    is_active=True,
                    is_verified=True,
                )
                db.add(user)
                db.flush()

                prof = DoctorProfile(
                    user_id=user.id,
                    specialization=d["specialization"],
                    license_number=d["license"],
                    experience_years=d["experience"],
                    bio=d["bio"],
                    hospital_affiliation=d["hospital"],
                    consultation_fee=d["fee"],
                    approval_status=DoctorApprovalStatus.APPROVED,
                )
                db.add(prof)
                db.flush()
                doc_profiles[d["email"]] = prof

                # Add weekly schedules
                for s in d["schedules"]:
                    avail = DoctorAvailability(
                        doctor_id=prof.id,
                        day_of_week=s["day"],
                        start_time=s["start"],
                        end_time=s["end"],
                        slot_duration_minutes=s["duration"],
                        is_active=True,
                    )
                    db.add(avail)

                print(f"  [OK] Doctor created: {d['email']} / DoctorPass123! ({d['specialization']})")
            else:
                prof = db.query(DoctorProfile).filter(DoctorProfile.user_id == user.id).first()
                doc_profiles[d["email"]] = prof

        # -------------------------------------------------------------
        # 2b. Pending Doctor Awaiting Admin Verification (For Live Demo)
        # -------------------------------------------------------------
        pending_doc_user = db.query(User).filter(User.email == "dr.watson@careai.com").first()
        if not pending_doc_user:
            pending_doc_user = User(
                email="dr.watson@careai.com",
                hashed_password=get_password_hash("DoctorPass123!"),
                full_name="John Watson, MD",
                role=UserRole.DOCTOR,
                is_active=True,
                is_verified=True,
            )
            db.add(pending_doc_user)
            db.flush()

            watson_prof = DoctorProfile(
                user_id=pending_doc_user.id,
                specialization="Pulmonology",
                license_number="MED-PULM-7712",
                experience_years=14,
                bio="Consultant pulmonologist specializing in chronic obstructive pulmonary disease, asthma phenotyping, and interventional bronchoscopy.",
                hospital_affiliation="Royal Chest & Respiratory Hospital",
                consultation_fee=160.00,
                approval_status=DoctorApprovalStatus.PENDING,
            )
            db.add(watson_prof)
            db.flush()
            print("  [OK] Pending Doctor Application created: dr.watson@careai.com / DoctorPass123! (Pending Admin Approval)")

        # -------------------------------------------------------------
        # 3. Verified Patients
        # -------------------------------------------------------------
        patients_data = [
            {
                "email": "patient.john@example.com",
                "name": "Johnathan Doe",
                "dob": date(1988, 5, 14),
                "gender": "Male",
                "blood": "O+",
                "allergies": [
                    {"name": "Penicillin", "type": "MEDICATION", "severity": "CRITICAL", "reaction": "Anaphylaxis & severe hives"},
                    {"name": "Peanuts", "type": "FOOD", "severity": "HIGH", "reaction": "Throat swelling"},
                ],
                "chronic": ["Essential Hypertension", "Mild Hyperlipidemia"],
                "medications": [
                    {"name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily in the morning", "instructions": "Take with water"},
                    {"name": "Atorvastatin", "dosage": "20mg", "frequency": "Once daily at bedtime", "instructions": "Avoid grapefruit"},
                ],
                "smoking": "NEVER",
                "alcohol": "OCCASIONAL",
                "emergency_name": "Mary Doe",
                "emergency_phone": "+1 (555) 234-5678",
                "emergency_rel": "Spouse",
            },
            {
                "email": "patient.emma@example.com",
                "name": "Emma Watson",
                "dob": date(1992, 9, 21),
                "gender": "Female",
                "blood": "A+",
                "allergies": [
                    {"name": "Aspirin", "type": "MEDICATION", "severity": "HIGH", "reaction": "Bronchospasm & Wheezing"},
                    {"name": "NSAIDs", "type": "MEDICATION", "severity": "HIGH", "reaction": "Facial swelling"},
                ],
                "chronic": ["Bronchial Asthma"],
                "medications": [
                    {"name": "Albuterol Inhaler", "dosage": "90mcg", "frequency": "As needed", "instructions": "Inhale 2 puffs for shortness of breath"},
                ],
                "smoking": "NEVER",
                "alcohol": "NON_DRINKER",
                "emergency_name": "David Watson",
                "emergency_phone": "+1 (555) 876-5432",
                "emergency_rel": "Father",
            },
        ]

        pat_profiles = {}
        for p in patients_data:
            user = db.query(User).filter(User.email == p["email"]).first()
            if not user:
                user = User(
                    email=p["email"],
                    hashed_password=get_password_hash("PatientPass123!"),
                    full_name=p["name"],
                    role=UserRole.PATIENT,
                    is_active=True,
                    is_verified=True,
                )
                db.add(user)
                db.flush()

                prof = PatientProfile(
                    user_id=user.id,
                    date_of_birth=p["dob"],
                    gender=p["gender"],
                    blood_group=p["blood"],
                    allergies=p["allergies"],
                    chronic_conditions=p["chronic"],
                    past_conditions=["Seasonal Bronchitis (2022)"],
                    surgeries=["Appendectomy (2015)"],
                    current_medications=p["medications"],
                    smoking_status=p["smoking"],
                    alcohol_consumption=p["alcohol"],
                    emergency_contact_name=p["emergency_name"],
                    emergency_contact_phone=p["emergency_phone"],
                    emergency_contact_relationship=p["emergency_rel"],
                )
                db.add(prof)
                db.flush()
                pat_profiles[p["email"]] = prof
                print(f"  [OK] Patient created: {p['email']} / PatientPass123!")
            else:
                prof = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
                pat_profiles[p["email"]] = prof

        # -------------------------------------------------------------
        # 4. Standardized Lab Test Catalog (8 tests)
        # -------------------------------------------------------------
        catalog_tests = [
            {
                "name": "Complete Blood Count (CBC) with Differential",
                "code": "CBC-001",
                "category": "Hematology",
                "specimen": "Whole Blood (EDTA)",
                "ref_range": "WBC: 4.5-11.0, HGB: 12.0-17.5, PLT: 150-450",
                "unit": "Mixed",
                "prep": "No special fasting required.",
                "tat": "2-4 hours",
                "description": "Measures red cells, white blood cells, hemoglobin, hematocrit, and platelet counts.",
            },
            {
                "name": "Comprehensive Metabolic Panel (CMP-14)",
                "code": "CMP-002",
                "category": "Biochemistry",
                "specimen": "Serum (SST)",
                "ref_range": "Glucose: 70-99, Na: 135-145, K: 3.5-5.0",
                "unit": "mg/dL / mmol/L",
                "prep": "Fasting 8-12 hours required prior to collection.",
                "tat": "4-6 hours",
                "description": "Evaluates kidney function, liver function, blood sugar, and electrolyte levels.",
            },
            {
                "name": "Lipid Panel with Total Cholesterol / HDL / LDL",
                "code": "LIPID-003",
                "category": "Biochemistry",
                "specimen": "Serum (SST)",
                "ref_range": "Total Chol: < 200, HDL: > 40, LDL: < 100",
                "unit": "mg/dL",
                "prep": "Fasting 9-12 hours required.",
                "tat": "4 hours",
                "description": "Assesses cardiovascular risk by measuring blood lipid fractions.",
            },
            {
                "name": "Thyroid Stimulating Hormone (TSH)",
                "code": "TSH-004",
                "category": "Hormonal Tests",
                "specimen": "Serum",
                "ref_range": "0.40 - 4.50",
                "unit": "uIU/mL",
                "prep": "Take morning blood draw before daily thyroid medications if applicable.",
                "tat": "6-12 hours",
                "description": "Screens for thyroid gland disorders including hypothyroidism and hyperthyroidism.",
            },
            {
                "name": "Hemoglobin A1c (Glycated Hemoglobin)",
                "code": "HBA1C-005",
                "category": "Biochemistry",
                "specimen": "Whole Blood (EDTA)",
                "ref_range": "< 5.7 (Normal), 5.7-6.4 (Prediabetes), >= 6.5 (Diabetes)",
                "unit": "%",
                "prep": "No fasting required.",
                "tat": "3 hours",
                "description": "Measures average blood glucose concentration over the prior 2-3 months.",
            },
            {
                "name": "Routine Urinalysis with Microscopic Examination",
                "code": "URINE-006",
                "category": "Microbiology",
                "specimen": "Clean Catch Midstream Urine",
                "ref_range": "Protein: Negative, Glucose: Negative, Nitrite: Negative",
                "unit": "Qualitative",
                "prep": "Collect clean catch midstream sample using sterile collection kit.",
                "tat": "1-2 hours",
                "description": "Screening test for renal pathology, urinary tract infection, and metabolic disorders.",
            },
            {
                "name": "High-Sensitivity Cardiac Troponin I",
                "code": "TROP-007",
                "category": "Biochemistry",
                "specimen": "Plasma (Lithium Heparin)",
                "ref_range": "< 0.04",
                "unit": "ng/mL",
                "prep": "Immediate STAT draw for acute cardiac evaluation.",
                "tat": "30-60 minutes",
                "description": "Biomarker for myocardial necrosis and acute coronary syndrome.",
            },
            {
                "name": "Serum Electrolytes Panel (Na, K, Cl, CO2)",
                "code": "ELEC-008",
                "category": "Biochemistry",
                "specimen": "Serum",
                "ref_range": "Na: 135-145, K: 3.5-5.0, Cl: 96-106, CO2: 23-29",
                "unit": "mmol/L",
                "prep": "Standard draw without hemolysis.",
                "tat": "2 hours",
                "description": "Measures body fluid balance and acid-base equilibrium.",
            },
        ]

        lab_tests_map = {}
        for item in catalog_tests:
            existing_t = db.query(LabTest).filter(LabTest.test_code == item["code"]).first()
            if not existing_t:
                existing_t = LabTest(
                    test_name=item["name"],
                    test_code=item["code"],
                    category=item["category"],
                    specimen_type=item["specimen"],
                    reference_range=item["ref_range"],
                    unit=item["unit"],
                    preparation_instructions=item["prep"],
                    estimated_turnaround_time=item["tat"],
                    description=item["description"],
                    is_active=True,
                )
                db.add(existing_t)
                db.flush()
            lab_tests_map[item["code"]] = existing_t
        db.flush()
        print("  [OK] Lab Test Catalog populated (8 standardized tests).")

        # -------------------------------------------------------------
        # 5. Completed Consultations & Prescriptions in Distinct Stages
        # -------------------------------------------------------------
        sarah_prof = doc_profiles.get("dr.sarah@careai.com")
        marcus_prof = doc_profiles.get("dr.marcus@careai.com")
        emily_prof = doc_profiles.get("dr.emily@careai.com")
        john_prof = pat_profiles.get("patient.john@example.com")
        emma_prof = pat_profiles.get("patient.emma@example.com")

        if sarah_prof and john_prof:
            # Appointment 1: Past Completed Consultation
            appt1 = db.query(Appointment).filter(
                Appointment.doctor_id == sarah_prof.id,
                Appointment.patient_id == john_prof.id,
                Appointment.reason.ilike("%Cardiovascular%"),
            ).first()

            if not appt1:
                past_time = datetime.now(timezone.utc) - timedelta(days=4)
                appt1 = Appointment(
                    doctor_id=sarah_prof.id,
                    patient_id=john_prof.id,
                    scheduled_start=past_time,
                    scheduled_end=past_time + timedelta(minutes=30),
                    status=AppointmentStatus.COMPLETED,
                    reason="Cardiovascular review & blood pressure follow-up",
                    patient_notes="Noticed slightly higher morning blood pressure readings.",
                    doctor_notes="Patient shows stable cardiac rhythm. Adjusted ACE-inhibitor therapy and reviewed lifestyle factors.",
                )
                db.add(appt1)
                db.flush()

            # Prescription 1: PRESCRIBED (Pending Pharmacy Review)
            rx1 = db.query(Prescription).filter(
                Prescription.patient_id == john_prof.id,
                Prescription.diagnosis.ilike("%Hypertension%"),
            ).first()

            if not rx1:
                rx1 = Prescription(
                    appointment_id=appt1.id,
                    doctor_id=sarah_prof.id,
                    patient_id=john_prof.id,
                    diagnosis="Essential Stage 1 Hypertension with lipid management",
                    clinical_notes="Maintain daily sodium intake under 2g. Follow up in 90 days.",
                    valid_until=date.today() + timedelta(days=90),
                    status=PrescriptionStatus.PRESCRIBED,
                )
                db.add(rx1)
                db.flush()

                db.add(PrescriptionItem(
                    prescription_id=rx1.id,
                    medication_name="Lisinopril",
                    drug_name="Lisinopril",
                    dosage="20mg",
                    frequency="Once daily",
                    duration="90 days",
                    instructions="Take orally in the morning with water",
                ))
                db.add(PrescriptionItem(
                    prescription_id=rx1.id,
                    medication_name="Hydrochlorothiazide",
                    drug_name="Hydrochlorothiazide",
                    dosage="12.5mg",
                    frequency="Once daily",
                    duration="90 days",
                    instructions="Take in the morning to prevent nocturia",
                ))
                db.flush()

                # AI Analysis Report
                ai_report = AIAnalysisReport(
                    prescription_id=rx1.id,
                    patient_id=john_prof.id,
                    analyzed_by_user_id=sarah_prof.user_id,
                    overall_risk_level=InteractionSeverity.LOW,
                    total_findings=1,
                    clinical_summary="Prescription verified safe. Mild synergistic hypotensive mechanism expected between Lisinopril and Hydrochlorothiazide.",
                    summary="Prescription verified safe. Mild synergistic hypotensive mechanism expected between Lisinopril and Hydrochlorothiazide.",
                    ai_recommendations="Monitor routine electrolytes and renal function.",
                    findings=[
                        {
                            "type": "DRUG_DRUG",
                            "severity": "LOW",
                            "title": "Therapeutic Combination: ACE Inhibitor + Thiazide Diuretic",
                            "description": "Lisinopril combined with Hydrochlorothiazide provides synergistic blood pressure control.",
                            "recommendation": "Monitor routine electrolytes and renal function.",
                        }
                    ],
                    drug_drug_interactions=[
                        {
                            "drug1": "Lisinopril",
                            "drug2": "Hydrochlorothiazide",
                            "severity": "LOW",
                            "description": "Synergistic antihypertensive effect.",
                        }
                    ],
                    analysis_status="COMPLETED",
                )
                db.add(ai_report)
                print("  [OK] Prescription #1 created (PRESCRIBED stage with AI Report).")

        if emily_prof and john_prof:
            # Appointment 2: Prior General Wellness Consultation
            appt2 = db.query(Appointment).filter(
                Appointment.doctor_id == emily_prof.id,
                Appointment.patient_id == john_prof.id,
            ).first()

            if not appt2:
                past_time2 = datetime.now(timezone.utc) - timedelta(days=12)
                appt2 = Appointment(
                    doctor_id=emily_prof.id,
                    patient_id=john_prof.id,
                    scheduled_start=past_time2,
                    scheduled_end=past_time2 + timedelta(minutes=30),
                    status=AppointmentStatus.COMPLETED,
                    reason="Annual preventive lipid screening and dietary consultation",
                    patient_notes="Follow-up on cholesterol numbers.",
                    doctor_notes="Lipid profile indicates mild hypercholesterolemia. Statin therapy indicated.",
                )
                db.add(appt2)
                db.flush()

            # Prescription 2: UNDER_REVIEW (In Pharmacy Dispensary)
            rx2 = db.query(Prescription).filter(
                Prescription.patient_id == john_prof.id,
                Prescription.status == PrescriptionStatus.UNDER_REVIEW,
            ).first()

            if not rx2:
                rx2 = Prescription(
                    appointment_id=appt2.id if appt2 else None,
                    doctor_id=emily_prof.id,
                    patient_id=john_prof.id,
                    diagnosis="Hypercholesterolemia Management",
                    clinical_notes="Lipid management therapy renewal.",
                    valid_until=date.today() + timedelta(days=60),
                    status=PrescriptionStatus.UNDER_REVIEW,
                    pharmacy_notes="Pharmacist verifying patient profile and contraindication risks.",
                )
                db.add(rx2)
                db.flush()

                db.add(PrescriptionItem(
                    prescription_id=rx2.id,
                    medication_name="Atorvastatin",
                    drug_name="Atorvastatin",
                    dosage="20mg",
                    frequency="Once daily at night",
                    duration="60 days",
                    instructions="Take with water at bedtime. Avoid grapefruit juice.",
                ))
                db.flush()
                print("  [OK] Prescription #2 created (UNDER_REVIEW stage).")

        if marcus_prof and emma_prof:
            # Appointment 3: Upcoming Confirmed Appointment
            future_time = datetime.now(timezone.utc) + timedelta(days=2, hours=3)
            appt3 = db.query(Appointment).filter(
                Appointment.doctor_id == marcus_prof.id,
                Appointment.patient_id == emma_prof.id,
                Appointment.status == AppointmentStatus.CONFIRMED,
            ).first()

            if not appt3:
                appt3 = Appointment(
                    doctor_id=marcus_prof.id,
                    patient_id=emma_prof.id,
                    scheduled_start=future_time,
                    scheduled_end=future_time + timedelta(minutes=30),
                    status=AppointmentStatus.CONFIRMED,
                    reason="Migraine aura assessment and neuro-prophylaxis consult",
                    patient_notes="Experiencing occasional visual aura before headaches.",
                )
                db.add(appt3)
                db.flush()

            # Appointment 4: Past Pulmonology / Asthma Consultation
            appt4 = db.query(Appointment).filter(
                Appointment.doctor_id == marcus_prof.id,
                Appointment.patient_id == emma_prof.id,
                Appointment.status == AppointmentStatus.COMPLETED,
            ).first()

            if not appt4:
                past_time4 = datetime.now(timezone.utc) - timedelta(days=8)
                appt4 = Appointment(
                    doctor_id=marcus_prof.id,
                    patient_id=emma_prof.id,
                    scheduled_start=past_time4,
                    scheduled_end=past_time4 + timedelta(minutes=30),
                    status=AppointmentStatus.COMPLETED,
                    reason="Asthma symptom control check and inhaler refill",
                    doctor_notes="Lungs clear bilaterally. Inhaler replacement authorized.",
                )
                db.add(appt4)
                db.flush()

            # Prescription 3: READY for Pickup
            rx3 = db.query(Prescription).filter(
                Prescription.patient_id == emma_prof.id,
                Prescription.status == PrescriptionStatus.READY,
            ).first()

            if not rx3:
                rx3 = Prescription(
                    appointment_id=appt4.id if appt4 else None,
                    doctor_id=marcus_prof.id,
                    patient_id=emma_prof.id,
                    diagnosis="Bronchial Asthma Symptom Control",
                    clinical_notes="Inhaler rescue therapy replacement.",
                    valid_until=date.today() + timedelta(days=120),
                    status=PrescriptionStatus.READY,
                    pharmacy_notes="Packaged in dispensary bin B-12. Ready for patient pickup.",
                )
                db.add(rx3)
                db.flush()

                db.add(PrescriptionItem(
                    prescription_id=rx3.id,
                    medication_name="Albuterol Sulfate Inhalation Aerosol",
                    drug_name="Albuterol",
                    dosage="90mcg/actuation",
                    frequency="As needed (PRN)",
                    duration="30 days",
                    instructions="Inhale 2 puffs every 4-6 hours as needed for bronchospasm.",
                ))
                db.flush()
                print("  [OK] Prescription #3 created (READY for pickup stage).")

        if sarah_prof and emma_prof:
            # Appointment 5: Prior Infection Consultation
            appt5 = db.query(Appointment).filter(
                Appointment.doctor_id == sarah_prof.id,
                Appointment.patient_id == emma_prof.id,
            ).first()

            if not appt5:
                past_time5 = datetime.now(timezone.utc) - timedelta(days=20)
                appt5 = Appointment(
                    doctor_id=sarah_prof.id,
                    patient_id=emma_prof.id,
                    scheduled_start=past_time5,
                    scheduled_end=past_time5 + timedelta(minutes=30),
                    status=AppointmentStatus.COMPLETED,
                    reason="Acute bacterial bronchitis evaluation",
                    doctor_notes="Prescribed 5-day macrolide therapy given NSAID sensitivity.",
                )
                db.add(appt5)
                db.flush()

            # Prescription 4: DISPENSED
            rx4 = db.query(Prescription).filter(
                Prescription.patient_id == emma_prof.id,
                Prescription.status == PrescriptionStatus.DISPENSED,
            ).first()

            if not rx4:
                rx4 = Prescription(
                    appointment_id=appt5.id if appt5 else None,
                    doctor_id=sarah_prof.id,
                    patient_id=emma_prof.id,
                    diagnosis="Upper Respiratory Bacterial Infection (Resolved)",
                    clinical_notes="Complete full 5-day antibiotic course.",
                    valid_until=date.today() + timedelta(days=14),
                    status=PrescriptionStatus.DISPENSED,
                    pharmacy_notes="Dispensed by Pharmacist Elena Rostova. Verified no penicillin/aspirin allergy conflicts.",
                    dispensed_by_user_id=pharmacy_staff.id if pharmacy_staff else None,
                    dispensed_at=datetime.now(timezone.utc) - timedelta(days=2),
                )
                db.add(rx4)
                db.flush()

                db.add(PrescriptionItem(
                    prescription_id=rx4.id,
                    medication_name="Azithromycin Dihydrate",
                    drug_name="Azithromycin",
                    dosage="250mg",
                    frequency="Once daily",
                    duration="5 days",
                    instructions="Take 500mg day 1, then 250mg daily for 4 days.",
                ))
                db.flush()
                print("  [OK] Prescription #4 created (DISPENSED stage).")

        # -------------------------------------------------------------
        # 6. Sample Medical Documents (With Physical Files for Download)
        # -------------------------------------------------------------
        if john_prof:
            doc1 = db.query(MedicalDocument).filter(
                MedicalDocument.patient_id == john_prof.id,
                MedicalDocument.title.ilike("%Diagnostic Report%"),
            ).first()

            if not doc1:
                sample_pdf_bytes = (
                    b"%PDF-1.4\n1 0 obj\n<< /Title (Diagnostic Report) /Author (Metro Heart Institute) >>\n"
                    b"stream\nCareAI Diagnostic Laboratory Report - Patient: Johnathan Doe\n"
                    b"Test: Complete Blood Count & Lipid Profile\n"
                    b"Results: Normal cardiac parameters.\nendstream\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
                )
                storage_key, sanitized_filename, file_size, mime_type = storage_service.save_file(
                    file_content=sample_pdf_bytes,
                    original_filename="Cardio_Diagnostic_Report_2026.pdf",
                    declared_mime_type="application/pdf",
                )

                doc1 = MedicalDocument(
                    patient_id=john_prof.id,
                    uploaded_by_user_id=john_prof.user_id,
                    title="Cardiac Diagnostic & Lipid Panel Report",
                    document_type=DocumentType.LAB_REPORT,
                    description="Official diagnostic findings from annual cardiovascular screening.",
                    storage_key=storage_key,
                    original_filename=sanitized_filename,
                    file_size=file_size,
                    mime_type=mime_type,
                    ai_summary="Diagnostic panel confirms healthy cardiac rhythm and baseline lipids. Recommend routine dietary maintenance.",
                    ai_analysis_status="COMPLETED",
                )
                db.add(doc1)
                db.flush()
                print("  [OK] Patient medical document created with physical file in storage.")

        # -------------------------------------------------------------
        # 7. Active Diagnostic Lab Orders in Multiple Stages
        # -------------------------------------------------------------
        if sarah_prof and john_prof and lab_tests_map.get("CBC-001") and lab_tests_map.get("TROP-007"):
            # Lab Order 1: STAT Order in SAMPLE_PENDING
            order1 = db.query(LabOrder).filter(
                LabOrder.patient_id == john_prof.id,
                LabOrder.priority == LabOrderPriority.STAT,
            ).first()

            if not order1:
                order1 = LabOrder(
                    patient_id=john_prof.id,
                    doctor_id=sarah_prof.id,
                    clinical_notes="STAT cardiac evaluation: Patient reported mild exertional tightness. Rule out acute event.",
                    priority=LabOrderPriority.STAT,
                    status=LabOrderStatus.SAMPLE_PENDING,
                    ordered_at=datetime.now(timezone.utc) - timedelta(hours=1),
                )
                db.add(order1)
                db.flush()

                item_cbc = LabOrderItem(
                    lab_order_id=order1.id,
                    lab_test_id=lab_tests_map["CBC-001"].id,
                    instructions="STAT whole blood collection in EDTA tube.",
                )
                item_trop = LabOrderItem(
                    lab_order_id=order1.id,
                    lab_test_id=lab_tests_map["TROP-007"].id,
                    instructions="STAT troponin draw, prioritize rapid centrifugation.",
                )
                db.add(item_cbc)
                db.add(item_trop)
                db.flush()

                db.add(LabAuditEvent(
                    lab_order_id=order1.id,
                    action="ORDER_CREATED",
                    performed_by_user_id=sarah_prof.user_id,
                    details="STAT Lab Order placed by Dr. Sarah Jenkins",
                ))
                print("  [OK] Lab Order #1 created (STAT priority, SAMPLE_PENDING stage).")

        if marcus_prof and emma_prof and lab_tests_map.get("LIPID-003"):
            # Lab Order 2: Routine Order in IN_PROGRESS (Sample Collected)
            order2 = db.query(LabOrder).filter(
                LabOrder.patient_id == emma_prof.id,
                LabOrder.status == LabOrderStatus.IN_PROGRESS,
            ).first()

            if not order2:
                order2 = LabOrder(
                    patient_id=emma_prof.id,
                    doctor_id=marcus_prof.id,
                    clinical_notes="Routine metabolic and lipid panel screening.",
                    priority=LabOrderPriority.ROUTINE,
                    status=LabOrderStatus.IN_PROGRESS,
                    ordered_at=datetime.now(timezone.utc) - timedelta(hours=3),
                )
                db.add(order2)
                db.flush()

                item_lipid = LabOrderItem(
                    lab_order_id=order2.id,
                    lab_test_id=lab_tests_map["LIPID-003"].id,
                    instructions="Fasting specimen collected.",
                )
                db.add(item_lipid)
                db.flush()

                # Add sample collection
                db.add(LabSample(
                    lab_order_id=order2.id,
                    technician_id=lab_tech.id if lab_tech else 1,
                    specimen_type="Serum (SST)",
                    sample_condition=SampleCondition.ACCEPTABLE,
                    collection_notes="Specimen drawn without hemolysis. Placed in biochemistry centrifuge.",
                ))

                db.add(LabAuditEvent(
                    lab_order_id=order2.id,
                    action="SAMPLE_COLLECTED",
                    performed_by_user_id=lab_tech.id if lab_tech else 1,
                    details="Specimen collected and verified by Lab Tech Alex Rivera",
                ))
                print("  [OK] Lab Order #2 created (ROUTINE priority, IN_PROGRESS stage).")

        if sarah_prof and john_prof and lab_tests_map.get("CMP-002"):
            # Lab Order 3: Completed and RELEASED to Patient Portal
            order3 = db.query(LabOrder).filter(
                LabOrder.patient_id == john_prof.id,
                LabOrder.status == LabOrderStatus.RELEASED,
            ).first()

            if not order3:
                order3 = LabOrder(
                    patient_id=john_prof.id,
                    doctor_id=sarah_prof.id,
                    clinical_notes="Pre-medication comprehensive metabolic check.",
                    priority=LabOrderPriority.ROUTINE,
                    status=LabOrderStatus.RELEASED,
                    ordered_at=datetime.now(timezone.utc) - timedelta(days=2),
                )
                db.add(order3)
                db.flush()

                item_cmp = LabOrderItem(
                    lab_order_id=order3.id,
                    lab_test_id=lab_tests_map["CMP-002"].id,
                    instructions="Standard metabolic analysis.",
                )
                db.add(item_cmp)
                db.flush()

                db.add(LabSample(
                    lab_order_id=order3.id,
                    technician_id=lab_tech.id if lab_tech else 1,
                    specimen_type="Serum (SST)",
                    sample_condition=SampleCondition.ACCEPTABLE,
                    collection_notes="Specimen drawn correctly.",
                ))
                db.flush()

                # Verified Result
                result_cmp = LabResult(
                    lab_order_item_id=item_cmp.id,
                    test_name="Comprehensive Metabolic Panel (CMP-14)",
                    numeric_value=92.0,
                    text_value="Glucose 92 mg/dL, Na 140 mmol/L, K 4.2 mmol/L (All Normal)",
                    unit="mg/dL",
                    reference_range="Glucose: 70-99 mg/dL",
                    result_flag=ResultFlag.NORMAL,
                    entered_by_user_id=lab_tech.id if lab_tech else 1,
                    verified_by_user_id=lab_tech.id if lab_tech else 1,
                    verified_at=datetime.now(timezone.utc) - timedelta(days=1),
                    verification_notes="Results verified normal against reference interval.",
                    is_critical=False,
                )
                db.add(result_cmp)
                db.flush()

                db.add(LabAuditEvent(
                    lab_order_id=order3.id,
                    action="RESULTS_RELEASED",
                    performed_by_user_id=lab_tech.id if lab_tech else 1,
                    details="Diagnostic results verified and released to patient health record.",
                ))
                print("  [OK] Lab Order #3 created (RELEASED to patient portal stage).")

        # -------------------------------------------------------------
        # 8. In-App Notifications for All Roles
        # -------------------------------------------------------------
        demo_notifications = [
            # Patient John Doe
            {
                "user_email": "patient.john@example.com",
                "title": "Prescription Ready for Pickup",
                "message": "Your prescription for Lisinopril 20mg has been reviewed and is ready for pickup at the CareAI dispensary.",
                "type": NotificationType.PRESCRIPTION,
                "priority": NotificationPriority.NORMAL,
            },
            {
                "user_email": "patient.john@example.com",
                "title": "Diagnostic Lab Results Released",
                "message": "Your Comprehensive Metabolic Panel results are now available in your patient portal.",
                "type": NotificationType.SYSTEM,
                "priority": NotificationPriority.NORMAL,
            },
            # Doctor Sarah Jenkins
            {
                "user_email": "dr.sarah@careai.com",
                "title": "STAT Lab Requisition Received",
                "message": "STAT Lab Order #1 for Patient Johnathan Doe has been placed in the diagnostic queue.",
                "type": NotificationType.SYSTEM,
                "priority": NotificationPriority.HIGH,
            },
            # Admin
            {
                "user_email": "pillu.212006@gmail.com",
                "title": "Doctor Application Pending Review",
                "message": "Dr. John Watson (Pulmonology) has submitted medical credentials awaiting verification.",
                "type": NotificationType.DOCTOR_APPROVAL,
                "priority": NotificationPriority.HIGH,
            },
            # Lab Tech Alex Rivera
            {
                "user_email": "lab.tech@careai.com",
                "title": "New STAT Diagnostic Order in Queue",
                "message": "STAT specimen collection pending for Johnathan Doe (Troponin I + CBC).",
                "type": NotificationType.SYSTEM,
                "priority": NotificationPriority.HIGH,
            },
            # Pharmacy Staff Elena Rostova
            {
                "user_email": "pharmacy.staff@careai.com",
                "title": "New Digital Prescription Issued",
                "message": "New prescription for Lisinopril 20mg + Hydrochlorothiazide 12.5mg received in the fulfillment queue.",
                "type": NotificationType.PRESCRIPTION,
                "priority": NotificationPriority.NORMAL,
            },
        ]

        for notif_data in demo_notifications:
            target_user = db.query(User).filter(User.email == notif_data["user_email"]).first()
            if target_user:
                existing_n = db.query(Notification).filter(
                    Notification.user_id == target_user.id,
                    Notification.title == notif_data["title"],
                ).first()
                if not existing_n:
                    db.add(Notification(
                        user_id=target_user.id,
                        title=notif_data["title"],
                        message=notif_data["message"],
                        notification_type=notif_data["type"],
                        priority=notif_data["priority"],
                        is_read=False,
                    ))
        db.flush()
        print("  [OK] In-app notifications seeded across all 5 roles.")


        db.commit()
        print("\n[SUCCESS] CareAI demo data seeded successfully with 100% role fidelity!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding database: {e}", file=sys.stderr)
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
