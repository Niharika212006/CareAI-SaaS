"""AI clinical safety, drug interaction, and prescription risk analysis endpoints."""
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.schemas.ai import AIInteractionCheckRequest, AISafetyReportResponse
from app.services.ai_service import ai_service

router = APIRouter(prefix="/ai", tags=["AI Prescription Safety & Drug Interactions"])


@router.post(
    "/prescriptions/{prescription_id}/analyze",
    response_model=AISafetyReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Run comprehensive AI safety analysis on a digital prescription",
)
def analyze_prescription_safety(
    prescription_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AISafetyReportResponse:
    """
    Perform deterministic clinical safety audit on a digital prescription:
    - Drug-Drug Interaction Hazards
    - Dietary & Food Timing Advisories
    - Patient Allergy Contraindications
    - Duplicate Medications & Therapeutic Overlap
    Stores the generated report in the database and returns structured clinical findings.
    """
    return ai_service.analyze_prescription(
        db=db,
        prescription_id=prescription_id,
        current_user=current_user,
    )


@router.get(
    "/prescriptions/{prescription_id}/report",
    response_model=AISafetyReportResponse,
    summary="Retrieve latest AI safety analysis report for a prescription",
)
def get_prescription_safety_report(
    prescription_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AISafetyReportResponse:
    """Retrieve the most recent safety report generated for a specific prescription with RBAC verification."""
    return ai_service.get_latest_prescription_report(
        db=db,
        prescription_id=prescription_id,
        current_user=current_user,
    )


@router.get(
    "/reports/my",
    response_model=List[AISafetyReportResponse],
    summary="List historical safety analysis reports for the authenticated patient",
)
def get_my_safety_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role(UserRole.PATIENT, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> List[AISafetyReportResponse]:
    """Retrieve all safety reports generated for the authenticated patient's prescriptions."""
    return ai_service.get_patient_reports(
        db=db,
        patient_user=current_user,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/analyze-interactions",
    response_model=AISafetyReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Ad-hoc interaction analysis sandbox for custom medication payloads",
)
async def analyze_drug_interactions(
    request: AIInteractionCheckRequest,
    current_user: User = Depends(get_current_active_user),
) -> AISafetyReportResponse:
    """Run real-time multi-dimensional clinical interaction checks on a custom medication list."""
    return await ai_service.analyze_interactions(request)
