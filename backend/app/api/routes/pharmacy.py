"""FastAPI API routes for Pharmacy Staff workspace, prescription queue, dispensing, and safety alerts."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, Body, status, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.prescription import Prescription, PrescriptionStatus
from app.models.ai_report import InteractionSeverity
from app.dependencies.auth import (
    get_current_active_user,
    require_role,
    get_current_pharmacy_staff_user,
    get_current_admin_user,
)

from app.schemas.pharmacy import (
    PharmacyPrescriptionSummary,
    PharmacyPrescriptionDetail,
    PrescriptionStatusUpdate,
    PrescriptionDispenseRequest,
    PharmacyStatsResponse,
)
from app.schemas.dashboard import PharmacyDashboardResponse
from app.schemas.prescription import PrescriptionRead
from app.schemas.ai import AISafetyReportResponse
from app.services.ai_service import ai_service
from app.services.pharmacy_service import pharmacy_service
from app.services.dashboard_service import dashboard_service


router = APIRouter(prefix="/pharmacy", tags=["Pharmacy Staff & Dispensary"])


@router.get("/dashboard", response_model=PharmacyDashboardResponse)
def get_pharmacy_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve real-time operational dashboard for authenticated pharmacy staff."""
    if current_user.role not in [UserRole.PHARMACY_STAFF, UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return dashboard_service.get_pharmacy_dashboard(db=db, pharmacy_user=current_user)


@router.get("/prescriptions", response_model=List[PharmacyPrescriptionSummary])
def get_pharmacy_prescriptions(
    status_filter: Optional[PrescriptionStatus] = Query(None, alias="status"),
    search: Optional[str] = Query(None, description="Search by patient name or diagnosis"),
    risk_level: Optional[InteractionSeverity] = Query(None, description="Filter by AI safety risk severity"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List clinical prescriptions in the pharmacy dispensary queue with filtering."""
    if current_user.role not in [UserRole.PHARMACY_STAFF, UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    items, _ = pharmacy_service.get_pharmacy_queue(
        db=db,
        status_filter=status_filter,
        search=search,
        risk_level=risk_level,
        skip=skip,
        limit=limit,
    )
    return items


@router.get("/prescriptions/{prescription_id}", response_model=PharmacyPrescriptionDetail)
def get_pharmacy_prescription_detail(
    prescription_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve full prescription details including medication instructions and AI safety report."""
    rx = pharmacy_service.get_prescription_detail(
        db=db,
        prescription_id=prescription_id,
        current_user=current_user,
    )

    dispensed_by_name = rx.dispensed_by.full_name if rx.dispensed_by else None
    latest_report = rx.ai_reports[0] if rx.ai_reports else None
    ai_report_read = ai_service._serialize_report(latest_report) if latest_report else None



    return PharmacyPrescriptionDetail(
        id=rx.id,
        appointment_id=rx.appointment_id,
        patient_id=rx.patient_id,
        patient=rx.patient,
        doctor_id=rx.doctor_id,
        doctor=rx.doctor,
        diagnosis=rx.diagnosis,
        clinical_notes=rx.clinical_notes,
        valid_until=rx.valid_until,
        status=rx.status,
        pharmacy_notes=rx.pharmacy_notes,
        dispensed_at=rx.dispensed_at,
        dispensed_by_user_id=rx.dispensed_by_user_id,
        dispensed_by_name=dispensed_by_name,
        created_at=rx.created_at,
        updated_at=rx.updated_at,
        items=rx.items,
        latest_ai_report=ai_report_read,
    )


@router.patch("/prescriptions/{prescription_id}/status", response_model=PrescriptionRead)
def update_prescription_status(
    prescription_id: int = Path(..., ge=1),
    payload: PrescriptionStatusUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update prescription dispensing status (Pharmacy Staff & Admin only).
    Emits notifications when ready for pickup or dispensed.
    """
    rx = pharmacy_service.update_prescription_status(
        db=db,
        prescription_id=prescription_id,
        current_user=current_user,
        new_status=payload.status,
        pharmacy_notes=payload.pharmacy_notes,
    )
    dispensed_name = rx.dispensed_by.full_name if rx.dispensed_by else None
    return PrescriptionRead(
        id=rx.id,
        appointment_id=rx.appointment_id,
        patient_id=rx.patient_id,
        doctor_id=rx.doctor_id,
        diagnosis=rx.diagnosis,
        clinical_summary=rx.diagnosis,
        clinical_notes=rx.clinical_notes,
        notes=rx.notes,
        valid_until=rx.valid_until,
        status=rx.status,
        pharmacy_notes=rx.pharmacy_notes,
        dispensed_at=rx.dispensed_at,
        dispensed_by_user_id=rx.dispensed_by_user_id,
        dispensed_by_name=dispensed_name,
        created_at=rx.created_at,
        updated_at=rx.updated_at,
        items=rx.items,
        patient=rx.patient,
        doctor=rx.doctor,
    )


@router.post("/prescriptions/{prescription_id}/dispense", response_model=PrescriptionRead)
def dispense_prescription(
    prescription_id: int = Path(..., ge=1),
    payload: Optional[PrescriptionDispenseRequest] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Mark prescription as dispensed to the patient with dispensing notes (Pharmacy Staff & Admin only).
    """
    notes = payload.pharmacy_notes if payload else None
    rx = pharmacy_service.update_prescription_status(
        db=db,
        prescription_id=prescription_id,
        current_user=current_user,
        new_status=PrescriptionStatus.DISPENSED,
        pharmacy_notes=notes,
    )
    dispensed_name = rx.dispensed_by.full_name if rx.dispensed_by else None
    return PrescriptionRead(
        id=rx.id,
        appointment_id=rx.appointment_id,
        patient_id=rx.patient_id,
        doctor_id=rx.doctor_id,
        diagnosis=rx.diagnosis,
        clinical_summary=rx.diagnosis,
        clinical_notes=rx.clinical_notes,
        notes=rx.notes,
        valid_until=rx.valid_until,
        status=rx.status,
        pharmacy_notes=rx.pharmacy_notes,
        dispensed_at=rx.dispensed_at,
        dispensed_by_user_id=rx.dispensed_by_user_id,
        dispensed_by_name=dispensed_name,
        created_at=rx.created_at,
        updated_at=rx.updated_at,
        items=rx.items,
        patient=rx.patient,
        doctor=rx.doctor,
    )
