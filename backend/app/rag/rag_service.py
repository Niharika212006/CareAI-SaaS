"""Central Orchestration Service for the Role-Aware Medical RAG System.

Maintains complete independence between retrieval and downstream LLM reasoning (Gemini / future MedGemma).
Ensures zero-downtime fallback when RAG retrieval is disabled or encounters runtime faults.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.models.user import User
from app.models.medical_document import MedicalDocument
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.rag.embeddings import embedding_service
from app.rag.document_loader import document_loader
from app.rag.vector_store import vector_store
from app.rag.retriever import role_aware_retriever
from app.rag.context_builder import context_builder

logger = logging.getLogger("healthcare.rag.service")


@dataclass
class RAGResult:
    """Standardized retrieval output decoupled from downstream LLM providers."""
    context_text: str = ""
    sources: List[Dict[str, Any]] = field(default_factory=list)
    retrieved_chunks: List[Any] = field(default_factory=list)
    rag_used: bool = False
    error: Optional[str] = None


class RAGService:
    """
    Coordinates document ingestion, role-scoped semantic search, and context assembly.
    """

    def is_enabled(self) -> bool:
        """Check if RAG capability is enabled via environment configuration."""
        return getattr(settings, "RAG_ENABLED", True)

    def retrieve(
        self,
        db: Session,
        query: str,
        user: User,
        target_patient_id: Optional[int] = None,
        document_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        top_k: Optional[int] = None,
    ) -> RAGResult:
        """
        Execute role-aware retrieval for user query:
        1. Check feature toggle.
        2. Perform role-bounded retrieval via RoleAwareRetriever.
        3. Build injection-defended context block.
        4. Extract structured source citations.
        5. Return clean RAGResult. In case of fault, logs and returns graceful fallback.
        """
        if not self.is_enabled():
            logger.info("RAG retrieval skipped: RAG_ENABLED is false.")
            return RAGResult(rag_used=False)

        clean_query = (query or "").strip()
        if not clean_query:
            return RAGResult(rag_used=False)

        effective_top_k = top_k or getattr(settings, "RAG_TOP_K", 5)

        try:
            chunks_with_scores = role_aware_retriever.retrieve(
                db=db,
                query=clean_query,
                user=user,
                target_patient_id=target_patient_id,
                document_type=document_type,
                date_from=date_from,
                date_to=date_to,
                top_k=effective_top_k,
            )

            if not chunks_with_scores:
                logger.info("RAG retrieval completed: No relevant chunks found for query within authorized scope.")
                return RAGResult(rag_used=False)

            context_text = context_builder.build_context_block(chunks_with_scores)
            sources = context_builder.extract_sources(chunks_with_scores)

            return RAGResult(
                context_text=context_text,
                sources=sources,
                retrieved_chunks=[chunk for chunk, _ in chunks_with_scores],
                rag_used=True,
            )

        except Exception as exc:
            logger.error(f"RAG retrieval failure ({exc}); triggering fallback to direct LLM.", exc_info=True)
            return RAGResult(rag_used=False, error="RAG retrieval temporarily unavailable.")

    def index_medical_document(self, db: Session, medical_document_id: int) -> Optional[KnowledgeDocument]:
        """
        Ingest an existing patient MedicalDocument into the RAG vector store.
        Scoped strictly to the owning patient.
        """
        med_doc = db.query(MedicalDocument).filter(MedicalDocument.id == medical_document_id).first()
        if not med_doc:
            logger.warning(f"Cannot index non-existent MedicalDocument #{medical_document_id}")
            return None

        # Check if already indexed
        existing = (
            db.query(KnowledgeDocument)
            .filter(KnowledgeDocument.medical_document_id == medical_document_id)
            .first()
        )
        if existing:
            # Delete old chunks and re-index
            vector_store.delete_document(db, existing.id)

        pages = document_loader.load_medical_document(med_doc)
        if not pages:
            logger.warning(f"No readable text extracted for MedicalDocument #{medical_document_id}")
            return None

        doc_title = med_doc.title or f"Medical Document #{med_doc.id}"
        doc = vector_store.save_document(
            db=db,
            document_name=doc_title,
            document_type=med_doc.document_type.value,
            pages=pages,
            source=f"CareAI Patient Document #{med_doc.id}",
            patient_id=med_doc.patient_id,
            medical_document_id=med_doc.id,
            uploaded_by_user_id=med_doc.uploaded_by_user_id,
            allowed_roles=["PATIENT", "DOCTOR"],
            document_date=med_doc.created_at,
            doc_metadata={
                "medical_document_id": med_doc.id,
                "file_name": med_doc.file_name,
                "mime_type": med_doc.mime_type,
            },
        )
        return doc

    def index_medical_document_safe(self, db: Session, medical_document_id: int) -> Optional[KnowledgeDocument]:
        """Safe wrapper for indexing medical documents; never raises exceptions to calling services."""
        try:
            return self.index_medical_document(db, medical_document_id)
        except Exception as exc:
            logger.error(f"Safe index failed for MedicalDocument #{medical_document_id}: {exc}")
            return None

    def index_knowledge_document(
        self,
        db: Session,
        document_name: str,
        document_type: str,
        content: str,
        source: Optional[str] = None,
        patient_id: Optional[int] = None,
        uploaded_by_user_id: Optional[int] = None,
        allowed_roles: Optional[List[str]] = None,
        document_date: Optional[datetime] = None,
        doc_metadata: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeDocument:
        """
        Index an authorized general clinical guideline, hospital protocol, or drug reference.
        """
        pages = document_loader.load_text(content)
        return vector_store.save_document(
            db=db,
            document_name=document_name,
            document_type=document_type,
            pages=pages,
            source=source or "CareAI Clinical Guidelines",
            patient_id=patient_id,
            medical_document_id=None,
            uploaded_by_user_id=uploaded_by_user_id,
            allowed_roles=allowed_roles or ["ALL"],
            document_date=document_date,
            doc_metadata=doc_metadata or {},
        )

    def get_status(self, db: Session) -> Dict[str, Any]:
        """Return operational telemetry of the RAG subsystem."""
        doc_count = db.query(func.count(KnowledgeDocument.id)).scalar() or 0
        chunk_count = db.query(func.count(KnowledgeChunk.id)).scalar() or 0
        dialect = db.bind.dialect.name if db.bind else "sqlite"
        return {
            "rag_enabled": self.is_enabled(),
            "embedding_model": settings.EMBEDDING_MODEL,
            "embedding_dimension": embedding_service.dimension,
            "vector_backend": "PostgreSQL + pgvector" if dialect == "postgresql" else "SQLite (Vector Fallback)",
            "total_documents_indexed": doc_count,
            "total_chunks_indexed": chunk_count,
            "top_k_default": settings.RAG_TOP_K,
            "chunk_size": settings.RAG_CHUNK_SIZE,
            "chunk_overlap": settings.RAG_CHUNK_OVERLAP,
        }


rag_service = RAGService()
