"""API routes registry."""
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.patients import router as patients_router
from app.api.routes.doctors import router as doctors_router
from app.api.routes.admin import router as admin_router
from app.api.routes.appointments import router as appointments_router
from app.api.routes.prescriptions import router as prescriptions_router
from app.api.routes.ai import router as ai_router

__all__ = [
    "auth_router",
    "users_router",
    "patients_router",
    "doctors_router",
    "admin_router",
    "appointments_router",
    "prescriptions_router",
    "ai_router",
]
