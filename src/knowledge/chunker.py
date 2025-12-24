"""Document chunker for knowledge base ingestion.

Handles reading various file types and splitting them into chunks
suitable for embedding and vector storage.
"""
import os
import re
from dataclasses import dataclass
from typing import List, Optional

from src.config.logging import get_logger

logger = get_logger(__name__)

# Supported file types
SUPPORTED_TYPES = {"pdf", "txt", "md", "docx"}

# Default chunking settings
DEFAULT_CHUNK_SIZE = 500  # tokens (approx 4 chars per token)
DEFAULT_CHUNK_OVERLAP = 50


@dataclass
class TextChunk:
    """A chunk of text from a document."""

    content: str
    index: int
    metadata: dict


@dataclass
class ChunkingResult:
    """Result of chunking a document."""

    chunks: List[TextChunk]
    total_chars: int
    file_type: str
    error: Optional[str] = None


def get_file_type(filename: str) -> Optional[str]:
    """Extract and validate file type from filename."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext if ext in SUPPORTED_TYPES else None


async def extract_text_from_file(file_path: str, file_type: str) -> str:
    """Extract text content from a file.

    Args:
        file_path: Path to the file
        file_type: Type of file (pdf, txt, md, docx)

    Returns:
        Extracted text content
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_type == "txt" or file_type == "md":
        return await _extract_text_file(file_path)
    elif file_type == "pdf":
        return await _extract_pdf(file_path)
    elif file_type == "docx":
        return await _extract_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


async def _extract_text_file(file_path: str) -> str:
    """Extract text from .txt or .md file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


async def _extract_pdf(file_path: str) -> str:
    """Extract text from PDF file using pypdf."""
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
        logger.warning("pypdf not installed, trying alternative PDF extraction")
        # Fallback: try pymupdf
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)
            text_parts = []
            for page_num, page in enumerate(doc):
                text_parts.append(f"[Page {page_num + 1}]\n{page.get_text()}")
            doc.close()
            return "\n\n".join(text_parts)
        except ImportError:
            raise ImportError(
                "Neither pypdf nor pymupdf is installed. "
                "Install with: pip install pypdf or pip install pymupdf"
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
            "python-docx is not installed. Install with: pip install python-docx"
        )


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    source_filename: Optional[str] = None,
) -> List[TextChunk]:
    """Split text into overlapping chunks.

    Uses a simple character-based approach with sentence boundary awareness.

    Args:
        text: The text to chunk
        chunk_size: Target size per chunk in tokens (approx 4 chars = 1 token)
        chunk_overlap: Number of tokens to overlap between chunks
        source_filename: Original filename for metadata

    Returns:
        List of TextChunk objects
    """
    if not text.strip():
        return []

    # Convert token counts to approximate character counts
    char_chunk_size = chunk_size * 4
    char_overlap = chunk_overlap * 4

    # Clean up text
    text = _clean_text(text)

    # Split into sentences for better chunking
    sentences = _split_into_sentences(text)

    chunks = []
    current_chunk = []
    current_length = 0
    chunk_index = 0

    for sentence in sentences:
        sentence_length = len(sentence)

        # If single sentence is too long, split it
        if sentence_length > char_chunk_size:
            # First, save current chunk if any
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(
                    TextChunk(
                        content=chunk_text,
                        index=chunk_index,
                        metadata={
                            "source": source_filename,
                            "chunk_index": chunk_index,
                            "char_count": len(chunk_text),
                        },
                    )
                )
                chunk_index += 1
                current_chunk = []
                current_length = 0

            # Split long sentence into smaller pieces
            for sub_chunk in _split_long_text(sentence, char_chunk_size, char_overlap):
                chunks.append(
                    TextChunk(
                        content=sub_chunk,
                        index=chunk_index,
                        metadata={
                            "source": source_filename,
                            "chunk_index": chunk_index,
                            "char_count": len(sub_chunk),
                        },
                    )
                )
                chunk_index += 1
            continue

        # Check if adding this sentence would exceed chunk size
        if current_length + sentence_length > char_chunk_size and current_chunk:
            # Save current chunk
            chunk_text = " ".join(current_chunk)
            chunks.append(
                TextChunk(
                    content=chunk_text,
                    index=chunk_index,
                    metadata={
                        "source": source_filename,
                        "chunk_index": chunk_index,
                        "char_count": len(chunk_text),
                    },
                )
            )
            chunk_index += 1

            # Start new chunk with overlap from previous
            if char_overlap > 0 and current_chunk:
                # Keep last few sentences for overlap
                overlap_text = ""
                overlap_sentences = []
                for s in reversed(current_chunk):
                    if len(overlap_text) + len(s) < char_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_text = " ".join(overlap_sentences)
                    else:
                        break
                current_chunk = overlap_sentences
                current_length = len(overlap_text)
            else:
                current_chunk = []
                current_length = 0

        current_chunk.append(sentence)
        current_length += sentence_length

    # Don't forget the last chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append(
            TextChunk(
                content=chunk_text,
                index=chunk_index,
                metadata={
                    "source": source_filename,
                    "chunk_index": chunk_index,
                    "char_count": len(chunk_text),
                },
            )
        )

    logger.info(
        "text_chunked",
        filename=source_filename,
        total_chunks=len(chunks),
        total_chars=len(text),
    )

    return chunks


def _clean_text(text: str) -> str:
    """Clean up text for chunking."""
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    # Simple sentence splitting on common terminators
    # Handles periods, question marks, exclamation marks
    # Preserves abbreviations like Mr., Dr., etc.
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [s.strip() for s in sentences if s.strip()]


def _split_long_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Split a long text that exceeds chunk size."""
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        # Try to break at a space
        if end < text_len:
            space_pos = text.rfind(" ", start, end)
            if space_pos > start:
                end = space_pos

        chunks.append(text[start:end].strip())

        # Move start with overlap
        start = end - overlap if end < text_len else text_len

    return chunks


async def process_document(
    file_path: str,
    filename: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> ChunkingResult:
    """Process a document: extract text and chunk it.

    Args:
        file_path: Path to the file
        filename: Original filename
        chunk_size: Target chunk size in tokens
        chunk_overlap: Overlap between chunks in tokens

    Returns:
        ChunkingResult with chunks and metadata
    """
    file_type = get_file_type(filename)

    if not file_type:
        return ChunkingResult(
            chunks=[],
            total_chars=0,
            file_type="unknown",
            error=f"Unsupported file type. Supported: {', '.join(SUPPORTED_TYPES)}",
        )

    try:
        # Extract text
        text = await extract_text_from_file(file_path, file_type)

        if not text.strip():
            return ChunkingResult(
                chunks=[],
                total_chars=0,
                file_type=file_type,
                error="No text content found in file",
            )

        # Chunk the text
        chunks = chunk_text(
            text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            source_filename=filename,
        )

        return ChunkingResult(
            chunks=chunks,
            total_chars=len(text),
            file_type=file_type,
        )

    except Exception as e:
        logger.error("document_processing_failed", filename=filename, error=str(e))
        return ChunkingResult(
            chunks=[],
            total_chars=0,
            file_type=file_type,
            error=str(e),
        )
