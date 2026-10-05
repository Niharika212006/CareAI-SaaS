"""Document loader and text normalizer supporting PDFs, text files, and MedicalDocuments."""
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from app.core.storage import storage_service
from app.models.medical_document import MedicalDocument

logger = logging.getLogger("healthcare.rag.loader")


class DocumentLoader:
    """Extracts, cleans, and normalizes text from medical records, guidelines, and PDF files."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Clean and normalize raw extracted document text."""
        if not text:
            return ""
        # Remove null bytes and non-printable control characters (except tabs and newlines)
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        # Normalize carriage returns and excessive whitespace
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
        # Collapse 3+ newlines into 2
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        # Replace multiple spaces with single space within lines
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cleaned.split("\n")]
        return "\n".join(lines).strip()

    @classmethod
    def load_pdf(cls, file_path: Path, max_pages: int = 50) -> List[Dict[str, Any]]:
        """
        Extract page-aware text from a PDF document using pypdf.
        Returns a list of dicts: [{"page_number": 1, "text": "..."}]
        """
        if not file_path.exists() or not file_path.is_file():
            logger.warning(f"PDF file does not exist: {file_path}")
            return []

        try:
            from pypdf import PdfReader
            reader = PdfReader(str(file_path))
            total_pages = len(reader.pages)
            if total_pages == 0:
                logger.warning(f"PDF contains 0 pages: {file_path}")
                return []

            pages_to_process = min(total_pages, max_pages)
            extracted_pages: List[Dict[str, Any]] = []

            for page_idx in range(pages_to_process):
                page = reader.pages[page_idx]
                raw_text = page.extract_text() or ""
                cleaned = cls.normalize_text(raw_text)
                if cleaned:
                    extracted_pages.append({
                        "page_number": page_idx + 1,  # 1-indexed for clinical citation
                        "text": cleaned,
                    })

            return extracted_pages

        except Exception as exc:
            logger.error(f"Error extracting PDF pages from {file_path}: {exc}")
            return []

    @classmethod
    def load_text(cls, text_content: str, page_number: int = 1) -> List[Dict[str, Any]]:
        """Wrap raw text or markdown into page-compatible structure."""
        cleaned = cls.normalize_text(text_content)
        if not cleaned:
            return []
        return [{"page_number": page_number, "text": cleaned}]

    @classmethod
    def load_medical_document(cls, medical_doc: MedicalDocument) -> List[Dict[str, Any]]:
        """Extract page-aware text from an existing MedicalDocument stored on disk."""
        file_path = storage_service.get_file_path(medical_doc.storage_key)
        if not file_path or not file_path.exists():
            logger.warning(f"MedicalDocument #{medical_doc.id} storage file not found.")
            # Fallback: check if description or title has meaningful text
            summary_text = f"Title: {medical_doc.title}\nType: {medical_doc.document_type.value}\nDescription: {medical_doc.description or ''}"
            return cls.load_text(summary_text)

        mime = (medical_doc.mime_type or "").lower()
        suffix = file_path.suffix.lower()

        if "pdf" in mime or suffix == ".pdf":
            pages = cls.load_pdf(file_path)
            if pages:
                return pages

        # Fallback to text reading if possible
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            cleaned = cls.normalize_text(content)
            if cleaned:
                return [{"page_number": 1, "text": cleaned}]
        except Exception:
            pass

        # If binary or image without OCR, index its clinical metadata header
        metadata_text = (
            f"Medical Document Record #{medical_doc.id}\n"
            f"Title: {medical_doc.title}\n"
            f"Category: {medical_doc.document_type.value}\n"
            f"Description: {medical_doc.description or 'No clinical description provided.'}\n"
            f"File: {medical_doc.file_name}"
        )
        return [{"page_number": 1, "text": metadata_text}]


document_loader = DocumentLoader()
