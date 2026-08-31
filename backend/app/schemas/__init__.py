"""Pydantic schemas registry."""
from app.schemas.common import MessageResponse, BaseResponse, PaginatedResponse
from app.schemas.token import Token, TokenPayload
from app.schemas.user import UserBase, UserCreate, UserLogin, UserUpdate, UserRead
from app.schemas.patient import PatientProfileBase, PatientProfileCreate, PatientProfileUpdate, PatientProfileRead
from app.schemas.doctor import (
    DoctorProfileBase,
    DoctorProfileCreate,
    DoctorProfileUpdate,
    DoctorApprovalUpdate,
    DoctorProfileRead,
)
from app.schemas.appointment import (
    AppointmentBase,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentCancelRequest,
    AppointmentRejectRequest,
    AppointmentCompleteRequest,
    AppointmentRead,
)
from app.schemas.prescription import (
    PrescriptionItemBase,
    PrescriptionItemCreate,
    PrescriptionItemRead,
    PrescriptionBase,
    PrescriptionCreate,
    PrescriptionRead,
)
from app.schemas.ai import (
    InteractionItem,
    AIInteractionCheckRequest,
    AISafetyReportResponse,
)

__all__ = [
    "MessageResponse",
    "BaseResponse",
    "PaginatedResponse",
    "Token",
    "TokenPayload",
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserRead",
    "PatientProfileBase",
    "PatientProfileCreate",
    "PatientProfileUpdate",
    "PatientProfileRead",
    "DoctorProfileBase",
    "DoctorProfileCreate",
    "DoctorProfileUpdate",
    "DoctorApprovalUpdate",
    "DoctorProfileRead",
    "AppointmentBase",
    "AppointmentCreate",
    "AppointmentUpdate",
    "AppointmentCancelRequest",
    "AppointmentRejectRequest",
    "AppointmentCompleteRequest",
    "AppointmentRead",
    "PrescriptionItemBase",
    "PrescriptionItemCreate",
    "PrescriptionItemRead",
    "PrescriptionBase",
    "PrescriptionCreate",
    "PrescriptionRead",
    "InteractionItem",
    "AIInteractionCheckRequest",
    "AISafetyReportResponse",
]
