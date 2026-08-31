"""Central API Router aggregating all modular route controllers."""
from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.patients import router as patients_router
from app.api.routes.doctors import router as doctors_router
from app.api.routes.admin import router as admin_router
from app.api.routes.appointments import router as appointments_router
from app.api.routes.prescriptions import router as prescriptions_router
from app.api.routes.ai import router as ai_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.medical_documents import router as medical_documents_router, doctor_router as doctor_documents_router
from app.api.routes.document_analyses import router as document_analyses_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(patients_router)
api_router.include_router(doctors_router)
api_router.include_router(admin_router)
api_router.include_router(appointments_router)
api_router.include_router(prescriptions_router)
api_router.include_router(ai_router)
api_router.include_router(dashboard_router)
api_router.include_router(notifications_router)
api_router.include_router(medical_documents_router)
api_router.include_router(doctor_documents_router)
api_router.include_router(document_analyses_router)
