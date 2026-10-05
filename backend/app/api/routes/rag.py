"""Role-Aware Medical RAG API Endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import (
    get_current_active_user,
    require_role,
)
from app.models.user import User, UserRole
from app.models.knowledge import KnowledgeDocument
from app.models.medical_document import MedicalDocument
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile
from app.models.appointment import Appointment
from app.schemas.rag import (
    RAGDocumentCreate,
    RAGDocumentRead,
    RAGDocumentListResponse,
    RAGSearchRequest,
    RAGSearchResponse,
    RAGStatusResponse,
    RAGCitationsource,
)
from app.rag import rag_service, vector_store, role_aware_retriever

router = APIRouter(prefix="/rag", tags=["Role-Aware Medical RAG System"])


@router.get(
    "/status",
    response_model=RAGStatusResponse,
    summary="Get operational status and configuration of RAG subsystem",
)
def get_rag_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RAGStatusResponse:
    """Check whether RAG is enabled, the active embedding model, and indexed chunk counts."""
    status_data = rag_service.get_status(db)
    return RAGStatusResponse(**status_data)


@router.get(
    "/documents",
    response_model=RAGDocumentListResponse,
    summary="List medical knowledge documents authorized for the current user",
)
def list_authorized_knowledge_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    document_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RAGDocumentListResponse:
    """
    Retrieve knowledge documents accessible to the authenticated user based on role and patient scoping.
    """
    allowed_ids = role_aware_retriever.resolve_authorized_document_ids(db, current_user)
    if not allowed_ids:
        return RAGDocumentListResponse(items=[], total=0)

    query = db.query(KnowledgeDocument).filter(KnowledgeDocument.id.in_(allowed_ids))
    if document_type:
        query = query.filter(KnowledgeDocument.document_type == document_type)

    total = query.count()
    items = query.order_by(KnowledgeDocument.created_at.desc()).offset(skip).limit(limit).all()

    return RAGDocumentListResponse(
        items=[RAGDocumentRead.model_validate(it) for it in items],
        total=total,
    )


@router.post(
    "/documents",
    response_model=RAGDocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Index a new clinical guideline, hospital protocol, or reference document",
)
def create_and_index_document(
    payload: RAGDocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DOCTOR)),
) -> RAGDocumentRead:
    """
    Index a new clinical guideline, hospital protocol, or reference into the RAG vector store.
    Restricted to DOCTOR and ADMIN roles.
    """
    doc = rag_service.index_knowledge_document(
        db=db,
        document_name=payload.document_name,
        document_type=payload.document_type,
        content=payload.content,
        source=payload.source,
        uploaded_by_user_id=current_user.id,
        allowed_roles=payload.allowed_roles or ["ALL"],
        document_date=payload.document_date,
        doc_metadata=payload.doc_metadata,
    )
    return RAGDocumentRead.model_validate(doc)


@router.get(
    "/documents/{document_id}",
    response_model=RAGDocumentRead,
    summary="Retrieve details of an authorized knowledge document",
)
def get_knowledge_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RAGDocumentRead:
    """Retrieve metadata of a specific indexed knowledge document with RBAC authorization."""
    allowed_ids = role_aware_retriever.resolve_authorized_document_ids(db, current_user)
    if document_id not in allowed_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this medical knowledge document.",
        )

    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge document #{document_id} not found.",
        )
    return RAGDocumentRead.model_validate(doc)


@router.delete(
    "/documents/{document_id}",
    summary="Delete an indexed knowledge document and its vector chunks",
)
def delete_knowledge_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Delete a knowledge document. Permitted for Admins or the original uploader."""
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge document #{document_id} not found.",
        )

    if current_user.role != UserRole.ADMIN and doc.uploaded_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators or the original uploader can delete knowledge documents.",
        )

    vector_store.delete_document(db, document_id)
    return {
        "status": "success",
        "message": f"Knowledge document #{document_id} and its associated vector chunks were deleted successfully.",
    }


@router.post(
    "/index-medical-document/{medical_document_id}",
    response_model=RAGDocumentRead,
    summary="Index an existing patient medical document into the RAG vector store",
)
def index_existing_medical_document(
    medical_document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RAGDocumentRead:
    """
    Explicitly trigger or refresh RAG vector indexing for an uploaded patient health record.
    Requires patient ownership or authorized doctor clinical relationship.
    """
    med_doc = db.query(MedicalDocument).filter(MedicalDocument.id == medical_document_id).first()
    if not med_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medical document #{medical_document_id} not found.",
        )

    # Check authorization
    if current_user.role == UserRole.PATIENT:
        patient_profile = (
            db.query(PatientProfile)
            .filter(PatientProfile.user_id == current_user.id)
            .first()
        )
        if not patient_profile or med_doc.patient_id != patient_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only index your own personal medical records.",
            )
    elif current_user.role == UserRole.DOCTOR:
        doctor_profile = (
            db.query(DoctorProfile)
            .filter(DoctorProfile.user_id == current_user.id)
            .first()
        )
        if not doctor_profile:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Doctor profile required.")
        has_rel = (
            db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_profile.id,
                Appointment.patient_id == med_doc.patient_id,
            )
            .first()
        )
        if not has_rel:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Clinical authorization required to index records for this patient.",
            )
    elif current_user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrators cannot access or index patient clinical records under privacy regulations.",
        )

    doc = rag_service.index_medical_document(db, medical_document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract readable text from this document for indexing.",
        )
    return RAGDocumentRead.model_validate(doc)


@router.post(
    "/search",
    response_model=RAGSearchResponse,
    summary="Execute role-authorized semantic retrieval across the knowledge base",
)
def search_knowledge_base(
    request: RAGSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RAGSearchResponse:
    """
    Search indexed medical documents with strict RBAC enforcement.
    Never searches unauthorized documents.
    """
    rag_result = rag_service.retrieve(
        db=db,
        query=request.query,
        user=current_user,
        target_patient_id=request.patient_id,
        document_type=request.document_type,
        date_from=request.date_from,
        date_to=request.date_to,
        top_k=request.top_k or 5,
    )

    sources = [
        RAGCitationsource(
            document_id=s["document_id"],
            document_name=s["document_name"],
            document_type=s["document_type"],
            page=s.get("page"),
            source=s.get("source", "Knowledge Base"),
            similarity_score=s.get("similarity_score", 0.0),
        )
        for s in rag_result.sources
    ]

    return RAGSearchResponse(
        query=request.query,
        user_role=current_user.role.value,
        rag_used=rag_result.rag_used,
        sources=sources,
        context_text=rag_result.context_text,
    )
