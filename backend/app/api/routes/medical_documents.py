"""Medical Documents and Health Records API Endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import (
    get_current_active_user,
    get_current_patient_user,
    get_current_doctor_user,
)
from app.models.user import User
from app.models.medical_document import DocumentType
from app.schemas.medical_document import (
    MedicalDocumentRead,
    MedicalDocumentUpdate,
    MedicalDocumentListResponse,
)
from app.services.medical_document_service import medical_document_service

router = APIRouter(prefix="/medical-documents", tags=["Medical Documents & Health Records"])
doctor_router = APIRouter(prefix="/doctors", tags=["Doctor Patient Clinical Records"])


@router.post(
    "",
    response_model=MedicalDocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload patient medical document",
)
async def upload_medical_document(
    file: UploadFile = File(..., description="Document file (PDF, JPG, JPEG, PNG, max 10MB)"),
    title: str = Form(..., description="Document title/label"),
    document_type: DocumentType = Form(DocumentType.OTHER, description="Healthcare document classification"),
    description: Optional[str] = Form(None, description="Optional notes/description"),
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
) -> MedicalDocumentRead:
    """Upload a new medical document for the authenticated patient."""
    file_bytes = await file.read()
    doc = medical_document_service.upload_document(
        db=db,
        patient_user=current_user,
        file_content=file_bytes,
        original_filename=file.filename or "medical_document",
        title=title,
        document_type=document_type,
        description=description,
        declared_mime_type=file.content_type,
    )
    return MedicalDocumentRead.model_validate(doc)


@router.get(
    "",
    response_model=MedicalDocumentListResponse,
    summary="List authenticated patient's medical documents",
)
def get_my_medical_documents(
    document_type: Optional[DocumentType] = Query(None, description="Filter by document type"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Page limit"),
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
) -> MedicalDocumentListResponse:
    """Retrieve paginated medical documents owned by current patient."""
    items, total = medical_document_service.get_patient_documents(
        db=db,
        patient_user=current_user,
        document_type=document_type,
        skip=skip,
        limit=limit,
    )
    return MedicalDocumentListResponse(
        items=[MedicalDocumentRead.model_validate(item) for item in items],
        total=total,
    )


@router.get(
    "/{document_id}",
    response_model=MedicalDocumentRead,
    summary="Get medical document metadata",
)
def get_medical_document_metadata(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> MedicalDocumentRead:
    """Retrieve metadata of a medical document (requires patient ownership or clinical doctor authorization)."""
    doc = medical_document_service.get_document_metadata_authorized(
        db=db,
        document_id=document_id,
        current_user=current_user,
    )
    return MedicalDocumentRead.model_validate(doc)


@router.get(
    "/{document_id}/download",
    summary="Securely download/view medical document file",
)
def download_medical_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve physical document file with verified patient ownership or clinical doctor authorization."""
    doc, file_path = medical_document_service.get_document_file_for_download(
        db=db,
        document_id=document_id,
        current_user=current_user,
    )
    return FileResponse(
        path=str(file_path),
        media_type=doc.mime_type,
        filename=doc.file_name,
    )


@router.patch(
    "/{document_id}",
    response_model=MedicalDocumentRead,
    summary="Update medical document metadata",
)
def update_medical_document(
    document_id: int,
    update_in: MedicalDocumentUpdate,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
) -> MedicalDocumentRead:
    """Update title, description, or category of an owned document."""
    doc = medical_document_service.update_document_metadata(
        db=db,
        document_id=document_id,
        patient_user=current_user,
        update_in=update_in,
    )
    return MedicalDocumentRead.model_validate(doc)


@router.delete(
    "/{document_id}",
    summary="Delete medical document",
)
def delete_medical_document(
    document_id: int,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
) -> dict:
    """Delete medical document metadata and stored file from disk."""
    medical_document_service.delete_document(
        db=db,
        document_id=document_id,
        patient_user=current_user,
    )
    return {"message": "Medical document deleted successfully."}


# ---------------------------------------------------------------------------
# Doctor Access Routes
# ---------------------------------------------------------------------------

@doctor_router.get(
    "/patients/{patient_id}/medical-documents",
    response_model=MedicalDocumentListResponse,
    summary="Doctor access to patient medical documents",
)
def get_patient_documents_for_doctor(
    patient_id: int,
    document_type: Optional[DocumentType] = Query(None, description="Filter by document type"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    current_user: User = Depends(get_current_doctor_user),
    db: Session = Depends(get_db),
) -> MedicalDocumentListResponse:
    """Retrieve patient documents for a doctor with a verified appointment relationship."""
    items, total = medical_document_service.get_patient_documents_for_doctor(
        db=db,
        patient_id=patient_id,
        doctor_user=current_user,
        document_type=document_type,
        skip=skip,
        limit=limit,
    )
    return MedicalDocumentListResponse(
        items=[MedicalDocumentRead.model_validate(item) for item in items],
        total=total,
    )
