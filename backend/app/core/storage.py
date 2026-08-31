"""Storage abstraction for local and future cloud medical document file management."""
import os
import re
import uuid
import mimetypes
from pathlib import Path
from typing import Tuple, Optional
from fastapi import HTTPException, status

# Default base directory for medical document uploads
BASE_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "medical_documents"

# Healthcare document security limits and constraints
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB maximum
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
}


class StorageService:
    """Encapsulated storage service managing secure file storage, sanitation, and retrieval."""

    def __init__(self, upload_dir: Path = BASE_UPLOAD_DIR):
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize user-provided filename to prevent directory traversal and injection attacks.
        Strips path components, relative segments (../), null bytes, and non-whitelisted characters.
        """
        if not filename:
            return "medical_document"

        # Extract only the base name (prevents ../ or \ traversal)
        clean_name = os.path.basename(filename).strip()
        # Remove null bytes and control chars
        clean_name = clean_name.replace("\x00", "").replace("\r", "").replace("\n", "")
        # Remove traversal sequences
        clean_name = re.sub(r"\.\.+[/\\:]*", "", clean_name)
        # Keep alphanumeric, dashes, underscores, and dots
        clean_name = re.sub(r"[^\w\.\-\_]", "_", clean_name)
        # Collapse multiple underscores/dots
        clean_name = re.sub(r"_+", "_", clean_name)
        clean_name = clean_name.strip("._ ")

        if not clean_name:
            return "medical_document"
        return clean_name[:200]  # Cap length

    def validate_file(self, file_content: bytes, original_filename: str, declared_mime_type: Optional[str] = None) -> Tuple[str, str]:
        """
        Validate file size, extension, and MIME type.
        Returns: (sanitized_filename, resolved_mime_type)
        """
        # Check empty file
        if not file_content or len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        # Check maximum file size
        if len(file_content) > MAX_FILE_SIZE_BYTES:
            max_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {max_mb:.0f} MB.",
            )

        sanitized_filename = self.sanitize_filename(original_filename)
        ext = Path(sanitized_filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{ext}' is not permitted. Allowed types: PDF, JPG, JPEG, PNG.",
            )

        # Determine MIME type
        guessed_mime, _ = mimetypes.guess_type(sanitized_filename)
        mime_type = declared_mime_type or guessed_mime or "application/octet-stream"
        mime_type_clean = mime_type.split(";")[0].strip().lower()

        if mime_type_clean not in ALLOWED_MIME_TYPES and guessed_mime not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"MIME type '{mime_type}' is not supported for medical documents.",
            )

        return sanitized_filename, (guessed_mime or mime_type_clean)

    def save_file(
        self,
        file_content: bytes,
        original_filename: str,
        declared_mime_type: Optional[str] = None,
    ) -> Tuple[str, str, int, str]:
        """
        Persist file content to disk with a generated unique storage key.
        Returns: (storage_key, sanitized_filename, file_size_bytes, mime_type)
        """
        sanitized_filename, mime_type = self.validate_file(
            file_content=file_content,
            original_filename=original_filename,
            declared_mime_type=declared_mime_type,
        )

        ext = Path(sanitized_filename).suffix.lower()
        unique_token = uuid.uuid4().hex
        storage_key = f"{unique_token}{ext}"

        target_path = (self.upload_dir / storage_key).resolve()

        # Prevent escaping upload root
        if not target_path.is_relative_to(self.upload_dir.resolve()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file storage destination path.",
            )

        try:
            with open(target_path, "wb") as f:
                f.write(file_content)
        except OSError as err:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to write file to storage: {str(err)}",
            )

        file_size = len(file_content)
        return storage_key, sanitized_filename, file_size, mime_type

    def get_file_path(self, storage_key: str) -> Optional[Path]:
        """Retrieve verified physical file path for download/streaming."""
        if not storage_key:
            return None

        # Sanitize storage key to avoid path traversal in keys
        clean_key = os.path.basename(storage_key)
        target_path = (self.upload_dir / clean_key).resolve()

        if not target_path.is_relative_to(self.upload_dir.resolve()):
            return None

        if target_path.exists() and target_path.is_file():
            return target_path

        return None

    def delete_file(self, storage_key: str) -> bool:
        """Safely delete stored file. Returns True if deleted or already absent."""
        if not storage_key:
            return True

        clean_key = os.path.basename(storage_key)
        target_path = (self.upload_dir / clean_key).resolve()

        if not target_path.is_relative_to(self.upload_dir.resolve()):
            return False

        try:
            if target_path.exists() and target_path.is_file():
                target_path.unlink()
            return True
        except OSError:
            return False


storage_service = StorageService()
