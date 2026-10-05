"""Role-Aware Medical RAG (Retrieval-Augmented Generation) Subsystem."""
from app.rag.embeddings import embedding_service, BaseEmbeddingService
from app.rag.text_splitter import medical_text_splitter, MedicalTextSplitter, TextChunk
from app.rag.document_loader import document_loader, DocumentLoader
from app.rag.vector_store import vector_store, VectorStore
from app.rag.retriever import role_aware_retriever, RoleAwareRetriever
from app.rag.context_builder import context_builder, ContextBuilder
from app.rag.rag_service import rag_service, RAGService, RAGResult

__all__ = [
    "embedding_service",
    "BaseEmbeddingService",
    "medical_text_splitter",
    "MedicalTextSplitter",
    "TextChunk",
    "document_loader",
    "DocumentLoader",
    "vector_store",
    "VectorStore",
    "role_aware_retriever",
    "RoleAwareRetriever",
    "context_builder",
    "ContextBuilder",
    "rag_service",
    "RAGService",
    "RAGResult",
]
