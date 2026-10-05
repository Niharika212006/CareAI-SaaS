"""Pydantic schemas for the Role-Aware Medical RAG subsystem."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class RAGDocumentCreate(BaseModel):
    """Payload to create and index a medical knowledge document or clinical protocol."""
    document_name: str = Field(..., min_length=2, max_length=255, description="Document title / protocol name")
    document_type: str = Field(default="CLINICAL_GUIDELINE", description="Document classification")
    content: str = Field(..., min_length=10, description="Full text or guidelines content to chunk and embed")
    source: Optional[str] = Field(default=None, description="Origin or publishing body")
    allowed_roles: Optional[List[str]] = Field(default=["ALL"], description="Roles authorized to retrieve this document")
    document_date: Optional[datetime] = Field(default=None, description="Effective / clinical record date")
    doc_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom metadata tags")


class RAGDocumentRead(BaseModel):
    """Schema representing an indexed medical knowledge document."""
    id: int
    document_name: str
    document_type: str
    source: Optional[str] = None
    patient_id: Optional[int] = None
    medical_document_id: Optional[int] = None
    uploaded_by_user_id: Optional[int] = None
    allowed_roles: Optional[List[str]] = None
    document_date: Optional[datetime] = None
    doc_metadata: Optional[Dict[str, Any]] = None
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RAGDocumentListResponse(BaseModel):
    """Paginated response of indexed knowledge documents."""
    items: List[RAGDocumentRead]
    total: int


class RAGSearchRequest(BaseModel):
    """Payload for role-authorized semantic retrieval."""
    query: str = Field(..., min_length=2, max_length=1000, description="Clinical inquiry or search query")
    patient_id: Optional[int] = Field(default=None, description="Target patient ID if querying patient records")
    document_type: Optional[str] = Field(default=None, description="Filter by document type")
    date_from: Optional[datetime] = Field(default=None, description="Filter documents from this date")
    date_to: Optional[datetime] = Field(default=None, description="Filter documents up to this date")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Maximum number of relevant chunks to retrieve")


class RAGCitationsource(BaseModel):
    """Source reference metadata for retrieved knowledge."""
    document_id: int
    document_name: str
    document_type: str
    page: Optional[int] = None
    source: str
    similarity_score: float


class RAGSearchResponse(BaseModel):
    """Structured response from semantic search."""
    query: str
    user_role: str
    rag_used: bool
    sources: List[RAGCitationsource]
    context_text: str


class RAGStatusResponse(BaseModel):
    """Status and configuration parameters of the RAG subsystem."""
    rag_enabled: bool
    embedding_model: str
    embedding_dimension: int
    vector_backend: str
    total_documents_indexed: int
    total_chunks_indexed: int
    top_k_default: int
    chunk_size: int
    chunk_overlap: int
