"""API endpoints for AI-Powered Medical Document Analysis."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import (
    get_current_active_user,
    get_current_patient_user,
)
from app.models.user import User
from app.schemas.document_analysis import DocumentAnalysisRead
from app.services.document_analysis_service import document_analysis_service

router = APIRouter(tags=["AI Document Analysis"])


@router.post(
    "/medical-documents/{document_id}/analyze",
    response_model=DocumentAnalysisRead,
    status_code=status.HTTP_200_OK,
    summary="Request responsible AI clinical analysis of an owned medical document",
)
def analyze_medical_document(
    document_id: int,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
) -> DocumentAnalysisRead:
    """Analyze text from an owned medical record, extract findings/lab markers, and save structured insight report."""
    analysis = document_analysis_service.analyze_document(
        db=db,
        document_id=document_id,
        current_user=current_user,
    )
    return DocumentAnalysisRead.model_validate(analysis)


@router.get(
    "/medical-documents/{document_id}/analysis",
    response_model=DocumentAnalysisRead,
    summary="Get latest AI analysis for a medical document",
)
def get_medical_document_analysis(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DocumentAnalysisRead:
    """Retrieve the latest structured AI analysis (requires owning patient or authorized consulting doctor)."""
    analysis = document_analysis_service.get_document_analysis(
        db=db,
        document_id=document_id,
        current_user=current_user,
    )
    return DocumentAnalysisRead.model_validate(analysis)


@router.get(
    "/document-analyses/{analysis_id}",
    response_model=DocumentAnalysisRead,
    summary="Get specific document analysis report by ID",
)
def get_analysis_by_id(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DocumentAnalysisRead:
    """Retrieve an analysis record by its primary ID after verifying parent document ownership or clinical authorization."""
    analysis = document_analysis_service.get_analysis_by_id(
        db=db,
        analysis_id=analysis_id,
        current_user=current_user,
    )
    return DocumentAnalysisRead.model_validate(analysis)
