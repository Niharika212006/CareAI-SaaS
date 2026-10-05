"""Database vector store supporting PostgreSQL pgvector with SQLite development fallback."""
import logging
import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.rag.embeddings import embedding_service
from app.rag.text_splitter import medical_text_splitter, TextChunk

logger = logging.getLogger("healthcare.rag.vector_store")


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two unit or arbitrary float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = 0.0
    norm1 = 0.0
    norm2 = 0.0
    for a, b in zip(v1, v2):
        dot += a * b
        norm1 += a * a
        norm2 += b * b
    if norm1 <= 1e-12 or norm2 <= 1e-12:
        return 0.0
    return max(-1.0, min(1.0, dot / (math.sqrt(norm1) * math.sqrt(norm2))))


class VectorStore:
    """Encapsulates vector persistence, pgvector native search, and SQLite fallback search."""

    @classmethod
    def save_document(
        cls,
        db: Session,
        document_name: str,
        document_type: str,
        pages: List[Dict[str, Any]],
        source: Optional[str] = None,
        patient_id: Optional[int] = None,
        medical_document_id: Optional[int] = None,
        uploaded_by_user_id: Optional[int] = None,
        allowed_roles: Optional[List[str]] = None,
        document_date: Optional[datetime] = None,
        doc_metadata: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeDocument:
        """
        Split document text, generate dense embeddings once, and persist chunks to database.
        """
        now = datetime.now(timezone.utc)
        doc = KnowledgeDocument(
            document_name=document_name.strip(),
            document_type=document_type.strip(),
            source=source,
            patient_id=patient_id,
            medical_document_id=medical_document_id,
            uploaded_by_user_id=uploaded_by_user_id,
            allowed_roles=allowed_roles or ["ALL"],
            document_date=document_date or now,
            doc_metadata=doc_metadata or {},
            chunk_count=0,
            created_at=now,
            updated_at=now,
        )
        db.add(doc)
        db.flush()

        base_meta = {
            "document_id": doc.id,
            "document_name": doc.document_name,
            "document_type": doc.document_type,
            "patient_id": doc.patient_id,
            "source": doc.source,
            "allowed_roles": doc.allowed_roles,
            "document_date": doc.document_date.isoformat() if doc.document_date else None,
        }

        # 1. Chunk document pages
        text_chunks: List[TextChunk] = medical_text_splitter.split_pages(pages, base_metadata=base_meta)
        if not text_chunks:
            # Fallback if pages were empty
            text_chunks = [
                TextChunk(
                    content=document_name,
                    chunk_index=0,
                    page_number=1,
                    metadata=base_meta,
                )
            ]

        # 2. Batch generate embeddings once
        chunk_texts = [tc.content for tc in text_chunks]
        embeddings = embedding_service.embed_documents(chunk_texts)

        # 3. Store chunks
        for idx, (tc, emb) in enumerate(zip(text_chunks, embeddings)):
            chunk = KnowledgeChunk(
                document_id=doc.id,
                chunk_index=idx,
                content=tc.content,
                page_number=tc.page_number,
                embedding=emb,
                chunk_metadata=tc.metadata,
                created_at=now,
            )
            db.add(chunk)

        doc.chunk_count = len(text_chunks)
        db.commit()
        db.refresh(doc)

        logger.info(
            f"RAG document ingestion completed. Document #{doc.id} ('{doc.document_name}') indexed {doc.chunk_count} chunks."
        )
        return doc

    @classmethod
    def similarity_search(
        cls,
        db: Session,
        query_embedding: List[float],
        allowed_document_ids: Optional[List[int]] = None,
        patient_id: Optional[int] = None,
        document_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        top_k: int = 5,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """
        Execute semantic similarity retrieval strictly scoped by pre-authorization criteria.
        Returns a list of (KnowledgeChunk, similarity_score) sorted descending by similarity.
        """
        if not query_embedding:
            return []

        # Build base filter
        filters = []
        if allowed_document_ids is not None:
            if not allowed_document_ids:
                # If explicit empty allowed list, authorization allows nothing
                return []
            filters.append(KnowledgeChunk.document_id.in_(allowed_document_ids))

        # Join with KnowledgeDocument to apply document-level filters if needed
        query = db.query(KnowledgeChunk).join(
            KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id
        )

        if patient_id is not None:
            filters.append(KnowledgeDocument.patient_id == patient_id)

        if document_type:
            filters.append(KnowledgeDocument.document_type == document_type)

        if date_from:
            filters.append(
                or_(
                    KnowledgeDocument.document_date >= date_from,
                    and_(KnowledgeDocument.document_date.is_(None), KnowledgeDocument.created_at >= date_from),
                )
            )

        if date_to:
            filters.append(
                or_(
                    KnowledgeDocument.document_date <= date_to,
                    and_(KnowledgeDocument.document_date.is_(None), KnowledgeDocument.created_at <= date_to),
                )
            )

        if filters:
            query = query.filter(and_(*filters))

        dialect_name = db.bind.dialect.name if db.bind else "sqlite"

        # Check if native pgvector similarity can be executed
        if dialect_name == "postgresql":
            try:
                # Use pgvector cosine distance operator (<=>)
                # Cosine distance = 1 - cosine similarity
                # Lowest distance = highest similarity
                chunks_with_dist = (
                    query.order_by(KnowledgeChunk.embedding.cosine_distance(query_embedding))
                    .limit(top_k)
                    .all()
                )
                results: List[Tuple[KnowledgeChunk, float]] = []
                for chunk in chunks_with_dist:
                    score = 0.85
                    if chunk.embedding is not None:
                        score = cosine_similarity(query_embedding, list(chunk.embedding))
                    results.append((chunk, round(score, 4)))
                return results
            except Exception as exc:
                logger.warning(f"PostgreSQL pgvector query error ({exc}); using in-memory similarity fallback.")

        # In-memory similarity calculation (SQLite / fallback)
        candidate_chunks = query.all()
        scored_chunks: List[Tuple[KnowledgeChunk, float]] = []

        for chunk in candidate_chunks:
            chunk_vec = chunk.embedding
            if chunk_vec is None:
                continue
            sim = cosine_similarity(query_embedding, list(chunk_vec))
            scored_chunks.append((chunk, round(sim, 4)))

        # Sort descending by similarity score
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]

    @classmethod
    def delete_document(cls, db: Session, document_id: int) -> bool:
        """Permanently delete a KnowledgeDocument and its cascaded chunks."""
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
        if not doc:
            return False
        db.delete(doc)
        db.commit()
        return True


vector_store = VectorStore()
