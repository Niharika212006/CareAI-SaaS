"""Seed script to populate CareAI Healthcare SaaS with rich demo data."""
import sys
from datetime import date, time, datetime, timedelta
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.availability import DoctorAvailability, DoctorUnavailableDate
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription, PrescriptionItem
from app.models.ai_report import AIAnalysisReport, InteractionSeverity
from app.core.security import get_password_hash


def seed_database():
    db: Session = SessionLocal()
    try:
        print("[+] Seeding CareAI Healthcare SaaS platform...")

        # 1. Platform Administrator
        admin = db.query(User).filter(User.email == "admin@careai.com").first()
        if not admin:
            admin = User(
                email="admin@careai.com",
                hashed_password=get_password_hash("AdminPass123!"),
                full_name="Chief Medical Admin",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
            )
            db.add(admin)
            db.flush()
            print("  [OK] Admin created: admin@careai.com / AdminPass123!")

        # 1b. Lab Technician
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

        # 1c. Pharmacy Staff
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

        # 2. Approved Doctors
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

        # 3. Verified Patients
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

        # 4. Sample Completed Consultation & Digital Prescription with AI Report
        sarah_prof = doc_profiles.get("dr.sarah@careai.com")
        john_prof = pat_profiles.get("patient.john@example.com")

        if sarah_prof and john_prof:
            existing_appt = db.query(Appointment).filter(
                Appointment.doctor_id == sarah_prof.id,
                Appointment.patient_id == john_prof.id,
            ).first()

            if not existing_appt:
                past_time = datetime.now() - timedelta(days=3)
                appt = Appointment(
                    doctor_id=sarah_prof.id,
                    patient_id=john_prof.id,
                    scheduled_start=past_time,
                    scheduled_end=past_time + timedelta(minutes=30),
                    status=AppointmentStatus.COMPLETED,
                    reason="Cardiovascular review & blood pressure follow-up",
                    patient_notes="Noticed slightly higher morning blood pressure readings.",
                    doctor_notes="Patient shows stable cardiac rhythm. Adjusted ACE-inhibitor therapy and reviewed lifestyle factors.",
                )
                db.add(appt)
                db.flush()

                # Digital Prescription
                prescription = Prescription(
                    appointment_id=appt.id,
                    doctor_id=sarah_prof.id,
                    patient_id=john_prof.id,
                    diagnosis="Essential Stage 1 Hypertension with lipid management",
                    clinical_notes="Maintain daily sodium intake under 2g. Follow up in 90 days.",
                    valid_until=date.today() + timedelta(days=90),
                )
                db.add(prescription)
                db.flush()

                # Prescription Items
                item1 = PrescriptionItem(
                    prescription_id=prescription.id,
                    medication_name="Lisinopril",
                    drug_name="Lisinopril",
                    dosage="20mg",
                    frequency="Once daily",
                    duration="90 days",
                    instructions="Take orally in the morning with water",
                )
                item2 = PrescriptionItem(
                    prescription_id=prescription.id,
                    medication_name="Hydrochlorothiazide",
                    drug_name="Hydrochlorothiazide",
                    dosage="12.5mg",
                    frequency="Once daily",
                    duration="90 days",
                    instructions="Take in the morning to prevent nocturia",
                )
                db.add(item1)
                db.add(item2)
                db.flush()

                # AI Analysis Report
                ai_report = AIAnalysisReport(
                    prescription_id=prescription.id,
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
                print("  [OK] Sample consultation, prescription & AI safety report created!")

        db.commit()
        print("\n[SUCCESS] CareAI demo data seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding database: {e}", file=sys.stderr)
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
