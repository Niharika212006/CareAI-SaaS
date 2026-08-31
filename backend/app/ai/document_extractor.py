"""Document text extraction abstraction supporting PDFs and OCR fallbacks."""
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger("healthcare.ai.extractor")


class DocumentTextExtractor:
    """Encapsulated utility for extracting readable text from medical records and lab PDFs."""

    @staticmethod
    def extract_from_pdf(file_path: Path, max_pages: int = 20, max_chars: int = 20000) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract embedded text from a PDF file using pypdf.
        Returns: (extracted_text, error_message)
        """
        try:
            from pypdf import PdfReader
        except ImportError:
            logger.error("pypdf library not available.")
            return None, "PDF processing library is not installed on the server."

        if not file_path.exists() or not file_path.is_file():
            return None, "Document file not found on storage."

        try:
            reader = PdfReader(str(file_path))
            total_pages = len(reader.pages)
            if total_pages == 0:
                return None, "The PDF document contains no pages."

            extracted_chunks = []
            char_count = 0

            pages_to_process = min(total_pages, max_pages)
            for page_idx in range(pages_to_process):
                page = reader.pages[page_idx]
                text = page.extract_text() or ""
                clean_page_text = text.strip()
                if clean_page_text:
                    extracted_chunks.append(clean_page_text)
                    char_count += len(clean_page_text)
                    if char_count >= max_chars:
                        extracted_chunks.append("\n[... Remaining document text truncated for clinical analysis limit ...]")
                        break

            full_text = "\n\n".join(extracted_chunks).strip()

            if not full_text:
                return (
                    None,
                    "No readable text could be extracted from this PDF. It appears to be a scanned image or non-text document.",
                )

            return full_text, None

        except Exception as err:
            logger.warning(f"Failed to extract PDF text from {file_path.name}: {err}")
            return None, f"Could not read PDF text: {str(err)}"

    @staticmethod
    def extract_from_image(file_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """
        Graceful OCR fallback for image files (JPG, PNG).
        Reports clean unavailability when system OCR dependencies are not active.
        """
        if not file_path.exists() or not file_path.is_file():
            return None, "Image file not found on storage."

        # Structured, responsible fallback
        return (
            None,
            "Direct OCR extraction for standalone image files is not currently enabled. "
            "Please upload a text-based digital PDF report for AI analysis.",
        )

    @classmethod
    def extract_text(cls, file_path: Path, mime_type: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Dispatch extraction based on file extension and MIME type.
        Returns: (extracted_text, error_message)
        """
        ext = file_path.suffix.lower()

        if ext == ".pdf" or (mime_type and "pdf" in mime_type.lower()):
            return cls.extract_from_pdf(file_path)
        elif ext in [".jpg", ".jpeg", ".png"] or (mime_type and "image" in mime_type.lower()):
            return cls.extract_from_image(file_path)
        else:
            return None, f"Unsupported document format '{ext}' for text extraction."


document_extractor = DocumentTextExtractor()
