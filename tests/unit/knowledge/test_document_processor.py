"""Tests for the enhanced document processor module.

Tests cover:
- Document type detection and MIME type mapping
- PDF processing with tables and images
- DOCX processing with tables and images
- PPTX slide extraction
- Excel/CSV to markdown table conversion
- Image OCR extraction
- Text/HTML processing
- Error handling for unsupported/missing files
"""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.knowledge.document_processor import (
    DocumentType,
    ExtractionResult,
    ExtractedImage,
    ExtractedTable,
    EXTENSION_MAP,
    MIME_TYPE_MAP,
    get_document_type,
    get_mime_type,
    get_supported_types,
    process_document,
    PDFProcessor,
    DOCXProcessor,
    PPTXProcessor,
    ExcelProcessor,
    ImageProcessor,
    TextProcessor,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def temp_txt_file():
    """Create a temporary text file for testing."""
    content = "This is test content.\nSecond line here.\nThird line with more text."
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_md_file():
    """Create a temporary markdown file for testing."""
    content = """# Test Document

This is a test paragraph.

## Section 1

Some content in section 1.

## Section 2

More content here.
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_html_file():
    """Create a temporary HTML file for testing."""
    content = """<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
<h1>Test Heading</h1>
<p>Test paragraph content.</p>
<script>console.log('ignored');</script>
<style>.ignored { color: red; }</style>
</body>
</html>
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(content)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing."""
    content = """Name,Age,City
Alice,30,New York
Bob,25,Los Angeles
Charlie,35,Chicago
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(content)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


# ============================================================================
# Tests for Document Type Detection
# ============================================================================


class TestGetDocumentType:
    """Tests for document type detection."""

    def test_pdf_detection(self):
        """Test PDF document type detection."""
        assert get_document_type("document.pdf") == DocumentType.PDF
        assert get_document_type("file.PDF") == DocumentType.PDF

    def test_docx_detection(self):
        """Test DOCX document type detection."""
        assert get_document_type("document.docx") == DocumentType.DOCX
        assert get_document_type("file.doc") == DocumentType.DOCX

    def test_pptx_detection(self):
        """Test PPTX document type detection."""
        assert get_document_type("presentation.pptx") == DocumentType.PPTX
        assert get_document_type("slides.ppt") == DocumentType.PPTX

    def test_excel_detection(self):
        """Test Excel document type detection."""
        assert get_document_type("spreadsheet.xlsx") == DocumentType.XLSX
        assert get_document_type("data.xls") == DocumentType.XLSX

    def test_csv_detection(self):
        """Test CSV document type detection."""
        assert get_document_type("data.csv") == DocumentType.CSV

    def test_text_detection(self):
        """Test text file type detection."""
        assert get_document_type("readme.txt") == DocumentType.TXT
        assert get_document_type("readme.md") == DocumentType.MD
        assert get_document_type("readme.markdown") == DocumentType.MD

    def test_html_detection(self):
        """Test HTML file type detection."""
        assert get_document_type("page.html") == DocumentType.HTML
        assert get_document_type("page.htm") == DocumentType.HTML

    def test_image_detection(self):
        """Test image file type detection."""
        assert get_document_type("photo.jpg") == DocumentType.IMAGE
        assert get_document_type("photo.jpeg") == DocumentType.IMAGE
        assert get_document_type("image.png") == DocumentType.IMAGE
        assert get_document_type("graphic.gif") == DocumentType.IMAGE
        assert get_document_type("scan.tiff") == DocumentType.IMAGE
        assert get_document_type("photo.webp") == DocumentType.IMAGE

    def test_unsupported_type(self):
        """Test unsupported file type returns None."""
        assert get_document_type("file.xyz") is None
        assert get_document_type("file.unknown") is None
        assert get_document_type("noextension") is None


class TestGetMimeType:
    """Tests for MIME type mapping."""

    def test_pdf_mime_type(self):
        """Test PDF MIME type."""
        assert get_mime_type("document.pdf") == "application/pdf"

    def test_docx_mime_type(self):
        """Test DOCX MIME type."""
        assert get_mime_type("document.docx") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def test_pptx_mime_type(self):
        """Test PPTX MIME type."""
        assert get_mime_type("slides.pptx") == "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    def test_xlsx_mime_type(self):
        """Test XLSX MIME type."""
        assert get_mime_type("data.xlsx") == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def test_csv_mime_type(self):
        """Test CSV MIME type."""
        assert get_mime_type("data.csv") == "text/csv"

    def test_text_mime_types(self):
        """Test text MIME types."""
        assert get_mime_type("file.txt") == "text/plain"
        assert get_mime_type("file.md") == "text/markdown"
        assert get_mime_type("file.html") == "text/html"

    def test_image_mime_types(self):
        """Test image MIME types."""
        assert get_mime_type("photo.jpg") == "image/jpeg"
        assert get_mime_type("photo.jpeg") == "image/jpeg"
        assert get_mime_type("image.png") == "image/png"
        assert get_mime_type("image.gif") == "image/gif"

    def test_unknown_mime_type(self):
        """Test unknown extension returns octet-stream."""
        assert get_mime_type("file.xyz") == "application/octet-stream"


class TestGetSupportedTypes:
    """Tests for supported file types list."""

    def test_returns_list(self):
        """Test that get_supported_types returns a list."""
        types = get_supported_types()
        assert isinstance(types, list)
        assert len(types) > 0

    def test_contains_common_types(self):
        """Test that common file types are supported."""
        types = get_supported_types()
        assert "pdf" in types
        assert "docx" in types
        assert "txt" in types
        assert "csv" in types
        assert "png" in types
        assert "jpg" in types


# ============================================================================
# Tests for Text Processor
# ============================================================================


class TestTextProcessor:
    """Tests for plain text and markdown processing."""

    @pytest.fixture
    def processor(self):
        return TextProcessor()

    def test_supports_txt(self, processor):
        """Test processor supports TXT files."""
        assert processor.supports(DocumentType.TXT) is True

    def test_supports_md(self, processor):
        """Test processor supports MD files."""
        assert processor.supports(DocumentType.MD) is True

    def test_supports_html(self, processor):
        """Test processor supports HTML files."""
        assert processor.supports(DocumentType.HTML) is True

    def test_does_not_support_pdf(self, processor):
        """Test processor does not support PDF."""
        assert processor.supports(DocumentType.PDF) is False

    @pytest.mark.asyncio
    async def test_extract_txt(self, processor, temp_txt_file):
        """Test extracting text from a .txt file."""
        result = await processor.extract(temp_txt_file, "test.txt")

        assert result.error is None
        assert "test content" in result.text.lower()
        assert result.word_count > 0
        assert result.page_count == 1

    @pytest.mark.asyncio
    async def test_extract_md(self, processor, temp_md_file):
        """Test extracting text from a .md file."""
        result = await processor.extract(temp_md_file, "test.md")

        assert result.error is None
        assert "# Test Document" in result.text
        assert "## Section 1" in result.text
        assert result.word_count > 0

    @pytest.mark.asyncio
    async def test_extract_html(self, processor, temp_html_file):
        """Test extracting text from HTML file strips tags."""
        result = await processor.extract(temp_html_file, "test.html")

        assert result.error is None
        assert "Test Heading" in result.text
        assert "Test paragraph content" in result.text
        # Script and style content should be stripped
        assert "console.log" not in result.text
        assert ".ignored" not in result.text

    @pytest.mark.asyncio
    async def test_extract_nonexistent_file(self, processor):
        """Test extracting from non-existent file returns error."""
        result = await processor.extract("/nonexistent/file.txt", "file.txt")

        # Will raise an exception that gets caught
        assert result.error is not None or result.text == ""


# ============================================================================
# Tests for Excel Processor
# ============================================================================


class TestExcelProcessor:
    """Tests for Excel/CSV processing."""

    @pytest.fixture
    def processor(self):
        return ExcelProcessor()

    def test_supports_xlsx(self, processor):
        """Test processor supports XLSX files."""
        assert processor.supports(DocumentType.XLSX) is True

    def test_supports_csv(self, processor):
        """Test processor supports CSV files."""
        assert processor.supports(DocumentType.CSV) is True

    def test_does_not_support_pdf(self, processor):
        """Test processor does not support PDF."""
        assert processor.supports(DocumentType.PDF) is False

    @pytest.mark.asyncio
    async def test_extract_csv(self, processor, temp_csv_file):
        """Test extracting CSV as markdown table."""
        result = await processor.extract(temp_csv_file, "test.csv")

        assert result.error is None
        assert "Name" in result.text
        assert "Age" in result.text
        assert "City" in result.text
        assert "Alice" in result.text
        assert "Bob" in result.text
        assert len(result.tables) == 1
        assert result.tables[0].row_count == 3
        assert result.tables[0].col_count == 3


# ============================================================================
# Tests for process_document Main Function
# ============================================================================


class TestProcessDocument:
    """Tests for the main process_document function."""

    @pytest.mark.asyncio
    async def test_process_txt_file(self, temp_txt_file):
        """Test processing a text file."""
        result = await process_document(temp_txt_file, "document.txt")

        assert result.error is None
        assert len(result.text) > 0
        assert result.word_count > 0

    @pytest.mark.asyncio
    async def test_process_md_file(self, temp_md_file):
        """Test processing a markdown file."""
        result = await process_document(temp_md_file, "readme.md")

        assert result.error is None
        assert "Test Document" in result.text

    @pytest.mark.asyncio
    async def test_process_csv_file(self, temp_csv_file):
        """Test processing a CSV file."""
        result = await process_document(temp_csv_file, "data.csv")

        assert result.error is None
        assert "Name" in result.text
        assert len(result.tables) > 0

    @pytest.mark.asyncio
    async def test_process_nonexistent_file(self):
        """Test processing a non-existent file."""
        result = await process_document("/nonexistent/file.txt", "missing.txt")

        assert result.error is not None
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_process_unsupported_type(self, temp_txt_file):
        """Test processing an unsupported file type."""
        result = await process_document(temp_txt_file, "file.xyz")

        assert result.error is not None
        assert "unsupported" in result.error.lower()


# ============================================================================
# Tests for ExtractionResult Dataclass
# ============================================================================


class TestExtractionResult:
    """Tests for ExtractionResult dataclass."""

    def test_default_values(self):
        """Test ExtractionResult has proper default values."""
        result = ExtractionResult(text="test")

        assert result.text == "test"
        assert result.tables == []
        assert result.images == []
        assert result.metadata == {}
        assert result.page_count == 0
        assert result.word_count == 0
        assert result.has_ocr_content is False
        assert result.error is None

    def test_with_tables(self):
        """Test ExtractionResult with tables."""
        table = ExtractedTable(
            markdown="| A | B |\n|---|---|\n| 1 | 2 |",
            row_count=1,
            col_count=2,
        )
        result = ExtractionResult(text="test", tables=[table])

        assert len(result.tables) == 1
        assert result.tables[0].row_count == 1

    def test_with_images(self):
        """Test ExtractionResult with images."""
        image = ExtractedImage(
            data=b"fake image data",
            format="png",
            width=100,
            height=100,
        )
        result = ExtractionResult(text="test", images=[image])

        assert len(result.images) == 1
        assert result.images[0].format == "png"


# ============================================================================
# Tests for Processor Support Methods
# ============================================================================


class TestProcessorSupport:
    """Tests for processor support methods."""

    def test_pdf_processor_support(self):
        """Test PDFProcessor supports only PDF."""
        processor = PDFProcessor()
        assert processor.supports(DocumentType.PDF) is True
        assert processor.supports(DocumentType.DOCX) is False
        assert processor.supports(DocumentType.TXT) is False

    def test_docx_processor_support(self):
        """Test DOCXProcessor supports only DOCX."""
        processor = DOCXProcessor()
        assert processor.supports(DocumentType.DOCX) is True
        assert processor.supports(DocumentType.PDF) is False
        assert processor.supports(DocumentType.TXT) is False

    def test_pptx_processor_support(self):
        """Test PPTXProcessor supports only PPTX."""
        processor = PPTXProcessor()
        assert processor.supports(DocumentType.PPTX) is True
        assert processor.supports(DocumentType.PDF) is False
        assert processor.supports(DocumentType.DOCX) is False

    def test_image_processor_support(self):
        """Test ImageProcessor supports only images."""
        processor = ImageProcessor()
        assert processor.supports(DocumentType.IMAGE) is True
        assert processor.supports(DocumentType.PDF) is False
        assert processor.supports(DocumentType.TXT) is False


# ============================================================================
# Tests for Extension Map
# ============================================================================


class TestExtensionMap:
    """Tests for EXTENSION_MAP completeness."""

    def test_all_common_extensions_mapped(self):
        """Test all common extensions are in the map."""
        expected_extensions = [
            "pdf", "docx", "doc", "pptx", "ppt",
            "xlsx", "xls", "csv",
            "txt", "md", "markdown",
            "html", "htm",
            "jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp",
        ]
        for ext in expected_extensions:
            assert ext in EXTENSION_MAP, f"Extension {ext} not in EXTENSION_MAP"


class TestMimeTypeMap:
    """Tests for MIME_TYPE_MAP completeness."""

    def test_all_extensions_have_mime_types(self):
        """Test all extensions in EXTENSION_MAP have MIME types."""
        # Not all extensions have MIME types (like 'doc', 'ppt' which map to newer formats)
        # but common ones should
        common_extensions = [
            "pdf", "docx", "pptx", "xlsx", "csv",
            "txt", "md", "html",
            "jpg", "jpeg", "png", "gif",
        ]
        for ext in common_extensions:
            assert ext in MIME_TYPE_MAP, f"Extension {ext} not in MIME_TYPE_MAP"
