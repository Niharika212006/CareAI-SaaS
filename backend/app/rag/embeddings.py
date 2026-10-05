"""Modular embedding generation service isolated from foundation LLM inference.

Provides dedicated text embedding capabilities using BAAI/bge-small-en-v1.5
via FastEmbed ONNX Runtime with a robust deterministic fallback.
"""
import abc
import hashlib
import logging
import math
import re
from typing import List, Optional

from app.core.config import settings

logger = logging.getLogger("healthcare.rag.embeddings")

DEFAULT_EMBEDDING_DIM = 384


class BaseEmbeddingService(abc.ABC):
    """Abstract base class for RAG text embedding services."""

    @property
    @abc.abstractmethod
    def dimension(self) -> int:
        """Return the vector dimensionality of embeddings."""
        pass

    @abc.abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generate a single normalized dense vector embedding for a user query."""
        pass

    @abc.abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate normalized dense vector embeddings for a batch of text chunks."""
        pass


class DeterministicSemanticEmbeddingService(BaseEmbeddingService):
    """
    Deterministic semantic hash embedding service producing 384-dimensional unit vectors.
    Acts as a high-reliability fallback when external weights or ONNX runtimes are unavailable.
    """

    def __init__(self, dimension: int = DEFAULT_EMBEDDING_DIM) -> None:
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    def _embed_single(self, text: str) -> List[float]:
        clean_text = (text or "").lower().strip()
        if not clean_text:
            return [0.0] * self._dim

        vec = [0.0] * self._dim
        words = re.findall(r"\w+", clean_text)
        if not words:
            words = [clean_text]

        for idx, word in enumerate(words):
            # Generate deterministic hashes across 4 buckets per token
            h1 = int(hashlib.md5(word.encode("utf-8")).hexdigest()[:8], 16)
            h2 = int(hashlib.sha256(word.encode("utf-8")).hexdigest()[:8], 16)
            pos1 = h1 % self._dim
            pos2 = (h1 + h2) % self._dim
            pos3 = (h2 + idx) % self._dim

            weight = 1.0 + (1.0 / (idx + 1))
            vec[pos1] += weight
            vec[pos2] += weight * 0.7
            vec[pos3] += weight * 0.5

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 1e-9:
            vec = [round(x / norm, 6) for x in vec]
        return vec

    def embed_query(self, text: str) -> List[float]:
        return self._embed_single(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_single(t) for t in texts]


class FastEmbedEmbeddingService(BaseEmbeddingService):
    """
    Production embedding service powered by FastEmbed ONNX Runtime.
    Defaults to BAAI/bge-small-en-v1.5 with 384 dimensions.
    """

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or settings.EMBEDDING_MODEL or "BAAI/bge-small-en-v1.5"
        self._model = None
        self._fallback = DeterministicSemanticEmbeddingService(DEFAULT_EMBEDDING_DIM)
        self._initialized = False

    @property
    def dimension(self) -> int:
        return DEFAULT_EMBEDDING_DIM

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return

        try:
            from fastembed import TextEmbedding
            logger.info(f"Initializing FastEmbed model: {self.model_name}")
            self._model = TextEmbedding(model_name=self.model_name)
            self._initialized = True
            logger.info("FastEmbed model initialized successfully.")
        except Exception as exc:
            logger.warning(
                f"FastEmbed initialization failed ({exc}). Using deterministic semantic fallback."
            )
            self._model = None
            self._initialized = True

    def embed_query(self, text: str) -> List[float]:
        self._ensure_initialized()
        clean = (text or "").strip()
        if not clean:
            return [0.0] * self.dimension

        if self._model is not None:
            try:
                embeddings_gen = self._model.embed([clean])
                for emb in embeddings_gen:
                    return [float(x) for x in emb]
            except Exception as exc:
                logger.warning(f"FastEmbed inference error ({exc}); using fallback.")

        return self._fallback.embed_query(clean)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        self._ensure_initialized()
        if not texts:
            return []

        clean_texts = [t if t and t.strip() else " " for t in texts]

        if self._model is not None:
            try:
                embeddings_gen = self._model.embed(clean_texts)
                return [[float(x) for x in emb] for emb in embeddings_gen]
            except Exception as exc:
                logger.warning(f"FastEmbed batch inference error ({exc}); using fallback.")

        return self._fallback.embed_documents(clean_texts)


# Singleton instance
embedding_service: BaseEmbeddingService = FastEmbedEmbeddingService()
