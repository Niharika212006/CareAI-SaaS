"""Configurable, page-aware text splitting and chunking for medical documents."""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from app.core.config import settings


@dataclass
class TextChunk:
    """Represents a bounded slice of medical text with citation metadata."""
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MedicalTextSplitter:
    """
    Splits clinical and medical literature into semantic chunks.
    Respects paragraph and sentence boundaries to avoid splitting mid-formula or mid-sentence.
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        separators: Optional[List[str]] = None,
    ) -> None:
        self.chunk_size = chunk_size or getattr(settings, "RAG_CHUNK_SIZE", 800)
        self.chunk_overlap = chunk_overlap or getattr(settings, "RAG_CHUNK_OVERLAP", 100)
        self.separators = separators or ["\n\n", "\n", ". ", "; ", ", ", " "]

    def _split_into_segments(self, text: str, separator_idx: int = 0) -> List[str]:
        """Recursively split text using the hierarchy of natural separators."""
        if not text:
            return []

        if separator_idx >= len(self.separators):
            # Fallback to hard character slicing if no separator works
            return [
                text[i : i + self.chunk_size]
                for i in range(0, len(text), max(1, self.chunk_size - self.chunk_overlap))
            ]

        sep = self.separators[separator_idx]
        parts = text.split(sep)
        result = []
        current_chunk = []
        current_len = 0

        for part in parts:
            part_len = len(part) + len(sep)
            if current_len + part_len <= self.chunk_size:
                current_chunk.append(part)
                current_len += part_len
            else:
                if current_chunk:
                    joined = sep.join(current_chunk).strip()
                    if joined:
                        result.append(joined)
                    current_chunk = []
                    current_len = 0

                # If this single part exceeds chunk size, recurse with next separator
                if len(part) > self.chunk_size:
                    sub_chunks = self._split_into_segments(part, separator_idx + 1)
                    result.extend(sub_chunks)
                else:
                    current_chunk.append(part)
                    current_len = len(part)

        if current_chunk:
            joined = sep.join(current_chunk).strip()
            if joined:
                result.append(joined)

        return result

    def split_text(
        self,
        text: str,
        page_number: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[TextChunk]:
        """Split a continuous block of text into structured TextChunk instances."""
        clean = (text or "").strip()
        if not clean:
            return []

        meta = dict(metadata or {})
        raw_chunks = self._split_into_segments(clean)
        chunks: List[TextChunk] = []

        for idx, chunk_str in enumerate(raw_chunks):
            cleaned_chunk = chunk_str.strip()
            if cleaned_chunk:
                chunks.append(
                    TextChunk(
                        content=cleaned_chunk,
                        chunk_index=idx,
                        page_number=page_number,
                        metadata={**meta, "page_number": page_number, "chunk_index": idx},
                    )
                )

        return chunks

    def split_pages(
        self,
        pages: List[Dict[str, Any]],
        base_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[TextChunk]:
        """
        Split a sequence of extracted document pages while preserving page citations.
        pages format: [{'page_number': 1, 'text': '...'}, {'page_number': 2, 'text': '...'}]
        """
        all_chunks: List[TextChunk] = []
        global_index = 0
        base_meta = dict(base_metadata or {})

        for page in pages:
            p_num = page.get("page_number")
            p_text = page.get("text", "")
            page_chunks = self.split_text(p_text, page_number=p_num, metadata=base_meta)

            for chunk in page_chunks:
                chunk.chunk_index = global_index
                chunk.metadata["chunk_index"] = global_index
                all_chunks.append(chunk)
                global_index += 1

        return all_chunks


medical_text_splitter = MedicalTextSplitter()
