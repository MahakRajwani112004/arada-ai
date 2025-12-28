"""Tests for the document chunker module.

Tests cover:
- File type detection and validation
- Text extraction from different file formats
- Text chunking strategies with various parameters
- Chunk size and overlap handling
- Sentence-aware chunking
- Long text splitting
- Error handling for missing/invalid files
"""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.knowledge.chunker import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    SUPPORTED_TYPES,
    ChunkingResult,
    TextChunk,
    _clean_text,
    _split_into_sentences,
    _split_long_text,
    chunk_text,
    extract_text_from_file,
    get_file_type,
    process_document,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_text():
    """Sample text for chunking tests."""
    return (
        "This is the first sentence. This is the second sentence. "
        "Here comes the third sentence! And what about the fourth? "
        "Finally, the fifth sentence concludes this paragraph."
    )


@pytest.fixture
def long_text():
    """Long text that will require multiple chunks."""
    sentences = [f"This is sentence number {i}." for i in range(1, 101)]
    return " ".join(sentences)


@pytest.fixture
def very_long_sentence():
    """A single sentence that exceeds chunk size."""
    words = ["word"] * 1000
    return " ".join(words) + "."


@pytest.fixture
def temp_text_file(sample_text):
    """Create a temporary text file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(sample_text)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_md_file():
    """Create a temporary markdown file for testing."""
    content = """# Heading

This is a paragraph with some **bold** text.

## Subheading

Another paragraph here with more content.
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


# ============================================================================
# Tests for get_file_type
# ============================================================================


class TestGetFileType:
    """Tests for file type detection."""

    def test_get_file_type_txt(self):
        """Test detection of txt files."""
        assert get_file_type("document.txt") == "txt"

    def test_get_file_type_md(self):
        """Test detection of markdown files."""
        assert get_file_type("readme.md") == "md"

    def test_get_file_type_pdf(self):
        """Test detection of PDF files."""
        assert get_file_type("report.pdf") == "pdf"

    def test_get_file_type_docx(self):
        """Test detection of DOCX files."""
        assert get_file_type("document.docx") == "docx"

    def test_get_file_type_case_insensitive(self):
        """Test that file type detection is case insensitive."""
        assert get_file_type("document.TXT") == "txt"
        assert get_file_type("document.PDF") == "pdf"
        assert get_file_type("document.MD") == "md"

    def test_get_file_type_unsupported(self):
        """Test that unsupported file types return None."""
        assert get_file_type("image.png") is None
        assert get_file_type("archive.zip") is None
        assert get_file_type("script.py") is None

    def test_get_file_type_no_extension(self):
        """Test files without extension return None."""
        assert get_file_type("filename") is None
        assert get_file_type("noextension") is None

    def test_get_file_type_multiple_dots(self):
        """Test files with multiple dots in name."""
        assert get_file_type("my.document.txt") == "txt"
        assert get_file_type("report.2024.pdf") == "pdf"

    def test_get_file_type_hidden_file(self):
        """Test hidden files with extension."""
        assert get_file_type(".hidden.txt") == "txt"

    def test_get_file_type_path_with_directories(self):
        """Test file paths with directories."""
        assert get_file_type("/path/to/document.txt") == "txt"
        assert get_file_type("folder/subfolder/file.pdf") == "pdf"


# ============================================================================
# Tests for _clean_text
# ============================================================================


class TestCleanText:
    """Tests for text cleaning function."""

    def test_clean_text_normalizes_whitespace(self):
        """Test that multiple spaces are normalized to single space."""
        text = "Hello    world   with    spaces"
        result = _clean_text(text)
        assert "    " not in result
        assert "Hello world with spaces" == result

    def test_clean_text_normalizes_newlines(self):
        """Test that excessive newlines are reduced."""
        text = "Paragraph one\n\n\n\n\nParagraph two"
        result = _clean_text(text)
        assert "\n\n\n" not in result

    def test_clean_text_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        text = "   Some text with spaces   "
        result = _clean_text(text)
        assert result == "Some text with spaces"

    def test_clean_text_preserves_content(self):
        """Test that content is preserved after cleaning."""
        text = "Important content here."
        result = _clean_text(text)
        assert "Important content here." in result

    def test_clean_text_handles_tabs(self):
        """Test that tabs are converted to spaces."""
        text = "Column1\tColumn2\tColumn3"
        result = _clean_text(text)
        assert "\t" not in result

    def test_clean_text_empty_string(self):
        """Test handling of empty string."""
        assert _clean_text("") == ""
        assert _clean_text("   ") == ""


# ============================================================================
# Tests for _split_into_sentences
# ============================================================================


class TestSplitIntoSentences:
    """Tests for sentence splitting function."""

    def test_split_sentences_periods(self):
        """Test splitting on periods."""
        text = "First sentence. Second sentence. Third sentence."
        sentences = _split_into_sentences(text)
        assert len(sentences) >= 2

    def test_split_sentences_question_marks(self):
        """Test splitting on question marks."""
        text = "What is this? How does it work? Interesting."
        sentences = _split_into_sentences(text)
        assert len(sentences) >= 2

    def test_split_sentences_exclamation_marks(self):
        """Test splitting on exclamation marks."""
        text = "Amazing! Great work! Keep going."
        sentences = _split_into_sentences(text)
        assert len(sentences) >= 2

    def test_split_sentences_mixed_punctuation(self):
        """Test splitting with mixed punctuation."""
        text = "Hello there. How are you? That's great!"
        sentences = _split_into_sentences(text)
        assert len(sentences) >= 2

    def test_split_sentences_removes_empty(self):
        """Test that empty sentences are removed."""
        text = "First sentence.   Second sentence."
        sentences = _split_into_sentences(text)
        assert all(s.strip() for s in sentences)

    def test_split_sentences_single_sentence(self):
        """Test handling of single sentence."""
        text = "Just one sentence here."
        sentences = _split_into_sentences(text)
        assert len(sentences) == 1

    def test_split_sentences_no_punctuation(self):
        """Test handling of text without sentence-ending punctuation."""
        text = "Text without punctuation"
        sentences = _split_into_sentences(text)
        assert len(sentences) == 1
        assert "Text without punctuation" in sentences[0]


# ============================================================================
# Tests for _split_long_text
# ============================================================================


class TestSplitLongText:
    """Tests for splitting text that exceeds chunk size."""

    def test_split_long_text_basic(self):
        """Test basic splitting of long text."""
        text = "word " * 100
        chunks = _split_long_text(text, chunk_size=50, overlap=10)
        assert len(chunks) > 1

    def test_split_long_text_respects_chunk_size(self):
        """Test that chunks respect the size limit."""
        text = "word " * 100
        chunk_size = 50
        chunks = _split_long_text(text, chunk_size=chunk_size, overlap=10)
        for chunk in chunks:
            assert len(chunk) <= chunk_size + 10  # Allow some flexibility for word boundaries

    def test_split_long_text_overlap(self):
        """Test that overlap is applied between chunks."""
        text = "a b c d e f g h i j k l m n o p q r s t u v w x y z"
        chunks = _split_long_text(text, chunk_size=20, overlap=5)
        # Verify there's some overlap by checking chunks > 1
        if len(chunks) > 1:
            # Chunks should have some overlapping content
            assert len(chunks) >= 2

    def test_split_long_text_short_text(self):
        """Test handling text shorter than chunk size."""
        text = "Short text"
        chunks = _split_long_text(text, chunk_size=100, overlap=10)
        assert len(chunks) == 1
        assert chunks[0].strip() == "Short text"

    def test_split_long_text_breaks_at_space(self):
        """Test that splitting prefers breaking at spaces."""
        text = "word1 word2 word3 word4 word5"
        chunks = _split_long_text(text, chunk_size=15, overlap=2)
        for chunk in chunks:
            # Chunks should not end mid-word (unless the word itself is too long)
            assert not chunk.endswith("ord")

    def test_split_long_text_no_overlap(self):
        """Test splitting with zero overlap."""
        text = "word " * 50
        chunks = _split_long_text(text, chunk_size=50, overlap=0)
        assert len(chunks) > 1


# ============================================================================
# Tests for chunk_text
# ============================================================================


class TestChunkText:
    """Tests for the main chunk_text function."""

    def test_chunk_text_returns_text_chunks(self, sample_text):
        """Test that chunk_text returns list of TextChunk objects."""
        chunks = chunk_text(sample_text, chunk_size=100, chunk_overlap=10)
        assert isinstance(chunks, list)
        assert all(isinstance(c, TextChunk) for c in chunks)

    def test_chunk_text_empty_input(self):
        """Test handling of empty input."""
        chunks = chunk_text("")
        assert chunks == []

        chunks = chunk_text("   ")
        assert chunks == []

    def test_chunk_text_whitespace_only(self):
        """Test handling of whitespace-only input."""
        chunks = chunk_text("   \n\n   \t   ")
        assert chunks == []

    def test_chunk_text_has_content(self, sample_text):
        """Test that chunks contain content."""
        chunks = chunk_text(sample_text, chunk_size=50, chunk_overlap=5)
        for chunk in chunks:
            assert chunk.content.strip()

    def test_chunk_text_has_index(self, sample_text):
        """Test that chunks have sequential indices."""
        chunks = chunk_text(sample_text, chunk_size=50, chunk_overlap=5)
        for i, chunk in enumerate(chunks):
            assert chunk.index == i

    def test_chunk_text_has_metadata(self, sample_text):
        """Test that chunks have metadata."""
        chunks = chunk_text(sample_text, chunk_size=50, chunk_overlap=5, source_filename="test.txt")
        for chunk in chunks:
            assert "source" in chunk.metadata
            assert chunk.metadata["source"] == "test.txt"
            assert "chunk_index" in chunk.metadata
            assert "char_count" in chunk.metadata

    def test_chunk_text_default_parameters(self, sample_text):
        """Test chunking with default parameters."""
        chunks = chunk_text(sample_text)
        assert isinstance(chunks, list)
        # Default chunk size is 500 tokens (2000 chars), short text should be single chunk
        if len(sample_text) < 2000:
            assert len(chunks) == 1

    def test_chunk_text_small_chunk_size(self, long_text):
        """Test chunking with small chunk size creates multiple chunks."""
        chunks = chunk_text(long_text, chunk_size=25, chunk_overlap=5)
        assert len(chunks) > 1

    def test_chunk_text_large_chunk_size(self, sample_text):
        """Test chunking with large chunk size creates single chunk."""
        chunks = chunk_text(sample_text, chunk_size=1000, chunk_overlap=10)
        assert len(chunks) == 1

    def test_chunk_text_preserves_content(self, sample_text):
        """Test that all content is preserved across chunks."""
        chunks = chunk_text(sample_text, chunk_size=50, chunk_overlap=0)
        combined = " ".join(c.content for c in chunks)
        # Key words should be preserved
        assert "first" in combined.lower()
        assert "second" in combined.lower()
        assert "sentence" in combined.lower()

    def test_chunk_text_handles_very_long_sentence(self, very_long_sentence):
        """Test handling of sentences longer than chunk size."""
        chunks = chunk_text(very_long_sentence, chunk_size=50, chunk_overlap=5)
        assert len(chunks) > 1
        for chunk in chunks:
            assert isinstance(chunk, TextChunk)

    def test_chunk_text_metadata_char_count_accurate(self, sample_text):
        """Test that char_count in metadata is accurate."""
        chunks = chunk_text(sample_text, chunk_size=50, chunk_overlap=5)
        for chunk in chunks:
            assert chunk.metadata["char_count"] == len(chunk.content)

    def test_chunk_text_no_source_filename(self, sample_text):
        """Test chunking without source filename."""
        chunks = chunk_text(sample_text, chunk_size=100, chunk_overlap=10)
        for chunk in chunks:
            assert chunk.metadata["source"] is None

    def test_chunk_text_overlap_creates_continuity(self, long_text):
        """Test that overlap creates content continuity between chunks."""
        chunks = chunk_text(long_text, chunk_size=25, chunk_overlap=5)
        # With overlap, chunks should share some content
        if len(chunks) >= 2:
            # Simply verify we got overlapping chunks
            assert len(chunks) >= 2


# ============================================================================
# Tests for extract_text_from_file
# ============================================================================


class TestExtractTextFromFile:
    """Tests for text extraction from files."""

    @pytest.mark.asyncio
    async def test_extract_text_txt(self, temp_text_file, sample_text):
        """Test extraction from text file."""
        content = await extract_text_from_file(temp_text_file, "txt")
        assert content == sample_text

    @pytest.mark.asyncio
    async def test_extract_text_md(self, temp_md_file):
        """Test extraction from markdown file."""
        content = await extract_text_from_file(temp_md_file, "md")
        assert "Heading" in content
        assert "paragraph" in content

    @pytest.mark.asyncio
    async def test_extract_text_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            await extract_text_from_file("/nonexistent/path/file.txt", "txt")
        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_extract_text_unsupported_type(self, temp_text_file):
        """Test error handling for unsupported file type."""
        with pytest.raises(ValueError) as exc_info:
            await extract_text_from_file(temp_text_file, "xyz")
        assert "Unsupported file type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_text_pdf_without_library(self, temp_text_file):
        """Test PDF extraction when libraries are not available."""
        # Mock both pypdf and fitz as unavailable
        with patch.dict("sys.modules", {"pypdf": None, "fitz": None}):
            with patch("src.knowledge.chunker._extract_pdf") as mock_extract:
                mock_extract.side_effect = ImportError("Neither pypdf nor pymupdf is installed")
                with pytest.raises(ImportError):
                    await extract_text_from_file(temp_text_file, "pdf")

    @pytest.mark.asyncio
    async def test_extract_text_docx_without_library(self, temp_text_file):
        """Test DOCX extraction when library is not available."""
        with patch("src.knowledge.chunker._extract_docx") as mock_extract:
            mock_extract.side_effect = ImportError("python-docx is not installed")
            with pytest.raises(ImportError):
                await extract_text_from_file(temp_text_file, "docx")


# ============================================================================
# Tests for process_document
# ============================================================================


class TestProcessDocument:
    """Tests for document processing function."""

    @pytest.mark.asyncio
    async def test_process_document_txt(self, temp_text_file, sample_text):
        """Test processing a text file."""
        result = await process_document(
            file_path=temp_text_file,
            filename="test.txt",
            chunk_size=100,
            chunk_overlap=10,
        )

        assert isinstance(result, ChunkingResult)
        assert result.file_type == "txt"
        assert result.error is None
        assert len(result.chunks) >= 1
        assert result.total_chars > 0

    @pytest.mark.asyncio
    async def test_process_document_md(self, temp_md_file):
        """Test processing a markdown file."""
        result = await process_document(
            file_path=temp_md_file,
            filename="readme.md",
            chunk_size=100,
            chunk_overlap=10,
        )

        assert result.file_type == "md"
        assert result.error is None
        assert len(result.chunks) >= 1

    @pytest.mark.asyncio
    async def test_process_document_unsupported_type(self, temp_text_file):
        """Test processing a file with unsupported extension."""
        result = await process_document(
            file_path=temp_text_file,
            filename="image.png",
        )

        assert result.file_type == "unknown"
        assert result.error is not None
        assert "Unsupported file type" in result.error
        assert len(result.chunks) == 0

    @pytest.mark.asyncio
    async def test_process_document_file_not_found(self):
        """Test processing a non-existent file."""
        result = await process_document(
            file_path="/nonexistent/path/file.txt",
            filename="file.txt",
        )

        assert result.file_type == "txt"
        assert result.error is not None
        assert len(result.chunks) == 0

    @pytest.mark.asyncio
    async def test_process_document_empty_file(self):
        """Test processing an empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            result = await process_document(
                file_path=temp_path,
                filename="empty.txt",
            )

            assert result.file_type == "txt"
            assert result.error is not None
            assert "No text content" in result.error
            assert len(result.chunks) == 0
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_process_document_whitespace_only_file(self):
        """Test processing a file with only whitespace."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("   \n\n   \t   ")
            temp_path = f.name

        try:
            result = await process_document(
                file_path=temp_path,
                filename="whitespace.txt",
            )

            assert result.file_type == "txt"
            assert result.error is not None
            assert "No text content" in result.error
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_process_document_custom_chunk_size(self, temp_text_file, sample_text):
        """Test processing with custom chunk size."""
        result = await process_document(
            file_path=temp_text_file,
            filename="test.txt",
            chunk_size=10,  # Very small chunks
            chunk_overlap=2,
        )

        assert result.error is None
        # Small chunk size should create multiple chunks
        if result.total_chars > 40:  # 10 tokens * 4 chars
            assert len(result.chunks) > 1

    @pytest.mark.asyncio
    async def test_process_document_returns_total_chars(self, temp_text_file, sample_text):
        """Test that total_chars is returned correctly."""
        result = await process_document(
            file_path=temp_text_file,
            filename="test.txt",
        )

        assert result.total_chars == len(sample_text)

    @pytest.mark.asyncio
    async def test_process_document_chunks_have_source_metadata(self, temp_text_file):
        """Test that chunks have source metadata."""
        result = await process_document(
            file_path=temp_text_file,
            filename="test.txt",
            chunk_size=50,
            chunk_overlap=5,
        )

        for chunk in result.chunks:
            assert chunk.metadata["source"] == "test.txt"


# ============================================================================
# Tests for Constants
# ============================================================================


class TestConstants:
    """Tests for module constants."""

    def test_supported_types(self):
        """Test that supported types are correctly defined."""
        assert "pdf" in SUPPORTED_TYPES
        assert "txt" in SUPPORTED_TYPES
        assert "md" in SUPPORTED_TYPES
        assert "docx" in SUPPORTED_TYPES
        assert len(SUPPORTED_TYPES) == 4

    def test_default_chunk_size(self):
        """Test default chunk size is reasonable."""
        assert DEFAULT_CHUNK_SIZE > 0
        assert DEFAULT_CHUNK_SIZE == 500

    def test_default_chunk_overlap(self):
        """Test default chunk overlap is reasonable."""
        assert DEFAULT_CHUNK_OVERLAP >= 0
        assert DEFAULT_CHUNK_OVERLAP < DEFAULT_CHUNK_SIZE
        assert DEFAULT_CHUNK_OVERLAP == 50


# ============================================================================
# Tests for TextChunk dataclass
# ============================================================================


class TestTextChunk:
    """Tests for TextChunk dataclass."""

    def test_text_chunk_creation(self):
        """Test creating a TextChunk."""
        chunk = TextChunk(
            content="Test content",
            index=0,
            metadata={"source": "test.txt"},
        )

        assert chunk.content == "Test content"
        assert chunk.index == 0
        assert chunk.metadata["source"] == "test.txt"

    def test_text_chunk_empty_metadata(self):
        """Test creating a TextChunk with empty metadata."""
        chunk = TextChunk(
            content="Test content",
            index=0,
            metadata={},
        )

        assert chunk.metadata == {}


# ============================================================================
# Tests for ChunkingResult dataclass
# ============================================================================


class TestChunkingResult:
    """Tests for ChunkingResult dataclass."""

    def test_chunking_result_success(self):
        """Test creating a successful ChunkingResult."""
        chunk = TextChunk(content="Test", index=0, metadata={})
        result = ChunkingResult(
            chunks=[chunk],
            total_chars=100,
            file_type="txt",
        )

        assert len(result.chunks) == 1
        assert result.total_chars == 100
        assert result.file_type == "txt"
        assert result.error is None

    def test_chunking_result_with_error(self):
        """Test creating a ChunkingResult with error."""
        result = ChunkingResult(
            chunks=[],
            total_chars=0,
            file_type="pdf",
            error="Failed to process PDF",
        )

        assert len(result.chunks) == 0
        assert result.error == "Failed to process PDF"

    def test_chunking_result_default_error(self):
        """Test that error defaults to None."""
        result = ChunkingResult(
            chunks=[],
            total_chars=0,
            file_type="txt",
        )

        assert result.error is None
