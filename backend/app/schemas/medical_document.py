"""Pydantic schemas for Medical Documents and Health Records."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.medical_document import DocumentType


class MedicalDocumentBase(BaseModel):
    """Shared document metadata attributes."""
    title: str = Field(..., min_length=1, max_length=255)
    document_type: DocumentType = DocumentType.OTHER
    description: Optional[str] = None


class MedicalDocumentCreate(MedicalDocumentBase):
    """Schema for document metadata submission upon upload."""
    pass


class MedicalDocumentUpdate(BaseModel):
    """Schema for updating document metadata."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    document_type: Optional[DocumentType] = None
    description: Optional[str] = None


class MedicalDocumentRead(MedicalDocumentBase):
    """Public read model for medical document metadata without exposing internal filesystem paths."""
    id: int
    patient_id: int
    uploaded_by_user_id: int
    file_name: str
    file_size: int
    mime_type: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MedicalDocumentListResponse(BaseModel):
    """Paginated list response of medical documents."""
    items: List[MedicalDocumentRead]
    total: int

    model_config = ConfigDict(from_attributes=True)
