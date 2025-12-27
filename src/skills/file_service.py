"""File service for skills - handles upload, extraction, and storage.

Skills need file content for prompt injection, not vector search.
So we extract text and store a preview (first ~2000 chars) in the DB.
"""

import mimetypes
import os
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

from src.config.logging import get_logger
from src.skills.models import FileType, SkillFile
from src.storage.object_storage import get_storage

logger = get_logger(__name__)

# Maximum preview size for DB storage (chars)
MAX_PREVIEW_SIZE = 4000

# Supported file types for text extraction
SUPPORTED_EXTENSIONS = {
    # Documents
    "pdf": "application/pdf",
    "txt": "text/plain",
    "md": "text/markdown",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    # Code files (read as text)
    "py": "text/x-python",
    "js": "text/javascript",
    "ts": "text/typescript",
    "jsx": "text/javascript",
    "tsx": "text/typescript",
    "json": "application/json",
    "yaml": "text/yaml",
    "yml": "text/yaml",
    "xml": "application/xml",
    "html": "text/html",
    "css": "text/css",
    "sql": "text/x-sql",
    "sh": "text/x-shellscript",
    "bash": "text/x-shellscript",
    # Data files
    "csv": "text/csv",
    "tsv": "text/tab-separated-values",
    # Config files
    "env": "text/plain",
    "ini": "text/plain",
    "toml": "text/plain",
    "conf": "text/plain",
}


@dataclass
class FileUploadResult:
    """Result of a file upload operation."""

    success: bool
    skill_file: Optional[SkillFile] = None
    error: Optional[str] = None


def get_file_extension(filename: str) -> str:
    """Get lowercase file extension."""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def is_supported_file(filename: str) -> bool:
    """Check if file type is supported."""
    ext = get_file_extension(filename)
    return ext in SUPPORTED_EXTENSIONS


def get_mime_type(filename: str) -> str:
    """Get MIME type for a file."""
    ext = get_file_extension(filename)
    if ext in SUPPORTED_EXTENSIONS:
        return SUPPORTED_EXTENSIONS[ext]
    # Fallback to mimetypes library
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


async def extract_text(file_path: str, file_ext: str) -> str:
    """Extract text content from a file.

    Args:
        file_path: Path to the file
        file_ext: File extension (lowercase, no dot)

    Returns:
        Extracted text content
    """
    # Text-based files - read directly
    text_extensions = {
        "txt", "md", "py", "js", "ts", "jsx", "tsx", "json", "yaml", "yml",
        "xml", "html", "css", "sql", "sh", "bash", "csv", "tsv", "env",
        "ini", "toml", "conf"
    }

    if file_ext in text_extensions:
        return await _extract_text_file(file_path)
    elif file_ext == "pdf":
        return await _extract_pdf(file_path)
    elif file_ext == "docx":
        return await _extract_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")


async def _extract_text_file(file_path: str) -> str:
    """Extract text from plain text files."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


async def _extract_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        text_parts = []

        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"[Page {page_num + 1}]\n{page_text}")

        return "\n\n".join(text_parts)

    except ImportError:
        # Fallback to PyMuPDF
        try:
            import fitz

            doc = fitz.open(file_path)
            text_parts = []
            for page_num, page in enumerate(doc):
                text_parts.append(f"[Page {page_num + 1}]\n{page.get_text()}")
            doc.close()
            return "\n\n".join(text_parts)
        except ImportError:
            raise ImportError(
                "PDF support requires pypdf or pymupdf. "
                "Install with: pip install pypdf"
            )


async def _extract_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    try:
        from docx import Document

        doc = Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n\n".join(paragraphs)

    except ImportError:
        raise ImportError(
            "DOCX support requires python-docx. "
            "Install with: pip install python-docx"
        )


async def upload_skill_file(
    skill_id: str,
    filename: str,
    file_data: bytes,
    file_type: FileType = FileType.REFERENCE,
) -> FileUploadResult:
    """Upload a file for a skill.

    Args:
        skill_id: ID of the skill this file belongs to
        filename: Original filename
        file_data: File content as bytes
        file_type: Whether this is a REFERENCE or TEMPLATE file

    Returns:
        FileUploadResult with the created SkillFile or error
    """
    file_ext = get_file_extension(filename)

    # Validate file type
    if not is_supported_file(filename):
        return FileUploadResult(
            success=False,
            error=f"Unsupported file type: .{file_ext}. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS.keys()))}"
        )

    try:
        # Save to temp file for extraction
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name

        try:
            # Extract text content
            text_content = await extract_text(tmp_path, file_ext)

            # Create preview (first N chars)
            content_preview = text_content[:MAX_PREVIEW_SIZE]
            if len(text_content) > MAX_PREVIEW_SIZE:
                content_preview += "\n\n[... content truncated ...]"

        finally:
            # Clean up temp file
            os.unlink(tmp_path)

        # Generate unique file ID and storage key
        file_id = f"file_{uuid.uuid4().hex[:12]}"
        storage_key = f"skills/{skill_id}/{file_id}_{filename}"

        # Upload to MinIO
        storage = get_storage()
        mime_type = get_mime_type(filename)
        await storage.upload(storage_key, file_data, content_type=mime_type)

        # Create SkillFile object
        skill_file = SkillFile(
            id=file_id,
            name=filename,
            file_type=file_type,
            mime_type=mime_type,
            storage_url=storage_key,
            content_preview=content_preview,
            size_bytes=len(file_data),
            uploaded_at=datetime.utcnow(),
        )

        logger.info(
            "skill_file_uploaded",
            skill_id=skill_id,
            file_id=file_id,
            filename=filename,
            size_bytes=len(file_data),
            preview_length=len(content_preview),
        )

        return FileUploadResult(success=True, skill_file=skill_file)

    except Exception as e:
        logger.error(
            "skill_file_upload_failed",
            skill_id=skill_id,
            filename=filename,
            error=str(e),
        )
        return FileUploadResult(success=False, error=str(e))


async def delete_skill_file(storage_url: str) -> bool:
    """Delete a skill file from storage.

    Args:
        storage_url: The storage key/URL of the file

    Returns:
        True if deleted successfully
    """
    try:
        storage = get_storage()
        return await storage.delete(storage_url)
    except Exception as e:
        logger.error("skill_file_delete_failed", storage_url=storage_url, error=str(e))
        return False


async def get_file_download_url(storage_url: str, expires_seconds: int = 3600) -> str:
    """Get a presigned download URL for a skill file.

    Args:
        storage_url: The storage key/URL of the file
        expires_seconds: How long the URL should be valid

    Returns:
        Presigned URL for downloading the file
    """
    storage = get_storage()
    return await storage.get_url(storage_url, expires_seconds)


def get_supported_extensions() -> list[str]:
    """Get list of supported file extensions."""
    return sorted(SUPPORTED_EXTENSIONS.keys())
