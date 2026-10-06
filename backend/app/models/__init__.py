"""SQLAlchemy models registry."""
from app.models.base import TimeStampedModel
from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription, PrescriptionItem
from app.models.ai_report import AIAnalysisReport, InteractionSeverity
from app.models.availability import DoctorAvailability, DoctorUnavailableDate
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.models.medical_document import MedicalDocument, DocumentType
from app.models.document_analysis import MedicalDocumentAnalysis, AnalysisStatus
from app.models.ai_assistant import AIConversation, AIMessage
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

__all__ = [
    "TimeStampedModel",
    "User",
    "UserRole",
    "PatientProfile",
    "DoctorProfile",
    "DoctorApprovalStatus",
    "Appointment",
    "AppointmentStatus",
    "Prescription",
    "PrescriptionItem",
    "AIAnalysisReport",
    "InteractionSeverity",
    "DoctorAvailability",
    "DoctorUnavailableDate",
    "Notification",
    "NotificationType",
    "NotificationPriority",
    "MedicalDocument",
    "DocumentType",
    "MedicalDocumentAnalysis",
    "AnalysisStatus",
    "AIConversation",
    "AIMessage",
    "LabTest",
    "LabOrder",
    "LabOrderItem",
    "LabSample",
    "LabResult",
    "LabAuditEvent",
    "LabOrderPriority",
    "LabOrderStatus",
    "SampleCondition",
    "ResultFlag",
]
