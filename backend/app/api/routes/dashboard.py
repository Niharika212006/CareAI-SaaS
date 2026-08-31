"""Role-Based Real-Time Dashboard & Analytics Endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    PatientDashboardResponse,
    DoctorDashboardResponse,
    AdminDashboardResponse,
)
from app.services.dashboard_service import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboards & Analytics"])


@router.get(
    "/patient",
    response_model=PatientDashboardResponse,
    summary="Get real-time patient health dashboard metrics",
)
def get_patient_dashboard(
    current_user: User = Depends(require_role(UserRole.PATIENT)),
    db: Session = Depends(get_db),
) -> PatientDashboardResponse:
    """Retrieve personal appointment overview, nearest upcoming consultation, prescriptions, and health profile status."""
    return dashboard_service.get_patient_dashboard(db=db, patient_user=current_user)


@router.get(
    "/doctor",
    response_model=DoctorDashboardResponse,
    summary="Get real-time doctor clinical operational dashboard",
)
def get_doctor_dashboard(
    current_user: User = Depends(require_role(UserRole.DOCTOR)),
    db: Session = Depends(get_db),
) -> DoctorDashboardResponse:
    """Retrieve today's schedule, pending confirmation requests, availability rules, and treated patient metrics."""
    return dashboard_service.get_doctor_dashboard(db=db, doctor_user=current_user)


@router.get(
    "/admin",
    response_model=AdminDashboardResponse,
    summary="Get system-wide platform statistics and oversight metrics",
)
def get_admin_dashboard(
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> AdminDashboardResponse:
    """Retrieve platform-level user registrations, doctor credential approvals, consultation volumes, and AI safety analytics."""
    return dashboard_service.get_admin_dashboard(db=db)
