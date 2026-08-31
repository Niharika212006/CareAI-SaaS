"""Services registry."""
from app.services.auth_service import auth_service, AuthService
from app.services.user_service import user_service, UserService
from app.services.patient_service import patient_service, PatientService
from app.services.doctor_service import doctor_service, DoctorService
from app.services.appointment_service import appointment_service, AppointmentService
from app.services.prescription_service import prescription_service, PrescriptionService
from app.services.ai_service import ai_service, AIService

__all__ = [
    "auth_service",
    "AuthService",
    "user_service",
    "UserService",
    "patient_service",
    "PatientService",
    "doctor_service",
    "DoctorService",
    "appointment_service",
    "AppointmentService",
    "prescription_service",
    "PrescriptionService",
    "ai_service",
    "AIService",
]
