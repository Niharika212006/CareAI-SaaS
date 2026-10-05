"""SQLAlchemy data models for Role-Aware Medical RAG Knowledge Documents and Chunks."""
import enum
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database.base import Base
from app.models.base import TimeStampedModel


class KnowledgeDocumentType(str, enum.Enum):
    """Classification of medical knowledge and document records."""
    CLINICAL_GUIDELINE = "CLINICAL_GUIDELINE"
    CLINICAL_PROTOCOL = "CLINICAL_PROTOCOL"
    HOSPITAL_PROCEDURE = "HOSPITAL_PROCEDURE"
    DRUG_INFORMATION = "DRUG_INFORMATION"
    DISEASE_REFERENCE = "DISEASE_REFERENCE"
    LAB_REFERENCE = "LAB_REFERENCE"
    MEDICAL_REPORT = "MEDICAL_REPORT"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    PATIENT_RECORD = "PATIENT_RECORD"
    OTHER = "OTHER"


class KnowledgeDocument(Base, TimeStampedModel):
    """
    Parent medical knowledge entity representing an approved reference guideline,
    clinical protocol, drug monograph, or patient-specific health document.
    """
    __tablename__ = "knowledge_documents"

    document_name = Column(String(255), nullable=False, index=True)
    document_type = Column(String(100), default=KnowledgeDocumentType.OTHER.value, nullable=False, index=True)
    source = Column(String(255), nullable=True)

    # Scoping & Multi-Tenancy / RBAC
    patient_id = Column(
        Integer,
        ForeignKey("patient_profiles.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    medical_document_id = Column(
        Integer,
        ForeignKey("medical_documents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    uploaded_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Role-Based Access Control list of allowed roles (e.g., ["DOCTOR", "PATIENT"] or ["ALL"])
    allowed_roles = Column(JSON, nullable=True)

    # Temporal RAG: Document effective/published or clinical record date
    document_date = Column(DateTime, nullable=True, index=True)

    # General metadata (version, author, specialty, tags, etc.)
    doc_metadata = Column(JSON, nullable=True)
    chunk_count = Column(Integer, default=0, nullable=False)

    # Relationships
    chunks = relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="KnowledgeChunk.chunk_index.asc()",
    )
    patient = relationship("PatientProfile", backref="knowledge_documents")
    uploaded_by = relationship("User", backref="uploaded_knowledge_documents")
    medical_document = relationship("MedicalDocument", backref="knowledge_documents")

    def __repr__(self) -> str:
        return f"<KnowledgeDocument(id={self.id}, name='{self.document_name}', type='{self.document_type}')>"


class KnowledgeChunk(Base):
    """
    Semantically chunked and embedded passage extracted from a parent KnowledgeDocument.
    Preserves exact page numbering and clinical metadata for verified citations.
    """
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(
        Integer,
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)

    # PDF page number or section number for exact grounded source citations
    page_number = Column(Integer, nullable=True, index=True)

    # 384-dimensional dense vector embedding (compatible with BAAI/bge-small-en-v1.5)
    # Native Vector type on PostgreSQL (pgvector); stores list in SQLite
    embedding = Column(Vector(384), nullable=True)

    # Bounded denormalized metadata for fast pre-filtering before semantic retrieval
    chunk_metadata = Column(JSON, nullable=True)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    document = relationship("KnowledgeDocument", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<KnowledgeChunk(id={self.id}, doc_id={self.document_id}, index={self.chunk_index}, page={self.page_number})>"
