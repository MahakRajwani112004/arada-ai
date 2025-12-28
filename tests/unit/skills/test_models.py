"""Tests for skills data models."""

import pytest
from datetime import datetime

from src.skills.models import (
    SkillCategory,
    FileType,
    SkillStatus,
    Terminology,
    ReasoningPattern,
    SkillExample,
    SkillFile,
)


class TestSkillCategory:
    """Tests for SkillCategory enum."""

    def test_domain_expertise_value(self):
        """Test DOMAIN_EXPERTISE value."""
        assert SkillCategory.DOMAIN_EXPERTISE.value == "domain_expertise"

    def test_document_generation_value(self):
        """Test DOCUMENT_GENERATION value."""
        assert SkillCategory.DOCUMENT_GENERATION.value == "document_generation"

    def test_all_categories_are_strings(self):
        """Test all category values are strings."""
        for category in SkillCategory:
            assert isinstance(category.value, str)

    def test_category_from_string(self):
        """Test creating category from string."""
        category = SkillCategory("domain_expertise")
        assert category == SkillCategory.DOMAIN_EXPERTISE

    def test_invalid_category_raises(self):
        """Test invalid category raises ValueError."""
        with pytest.raises(ValueError):
            SkillCategory("invalid_category")


class TestFileType:
    """Tests for FileType enum."""

    def test_reference_value(self):
        """Test REFERENCE value."""
        assert FileType.REFERENCE.value == "reference"

    def test_template_value(self):
        """Test TEMPLATE value."""
        assert FileType.TEMPLATE.value == "template"


class TestSkillStatus:
    """Tests for SkillStatus enum."""

    def test_draft_value(self):
        """Test DRAFT value."""
        assert SkillStatus.DRAFT.value == "draft"

    def test_published_value(self):
        """Test PUBLISHED value."""
        assert SkillStatus.PUBLISHED.value == "published"

    def test_archived_value(self):
        """Test ARCHIVED value."""
        assert SkillStatus.ARCHIVED.value == "archived"


class TestTerminology:
    """Tests for Terminology dataclass."""

    def test_create_terminology(self):
        """Test creating a Terminology instance."""
        term = Terminology(
            id="term-1",
            term="API",
            definition="Application Programming Interface",
            aliases=["api", "interface"],
        )

        assert term.id == "term-1"
        assert term.term == "API"
        assert term.definition == "Application Programming Interface"
        assert term.aliases == ["api", "interface"]

    def test_terminology_default_aliases(self):
        """Test that aliases defaults to empty list."""
        term = Terminology(
            id="term-1",
            term="Test",
            definition="A test term",
        )
        assert term.aliases == []

    def test_terminology_to_dict(self):
        """Test to_dict method."""
        term = Terminology(
            id="term-1",
            term="API",
            definition="Application Programming Interface",
            aliases=["api"],
        )

        result = term.to_dict()

        assert result == {
            "id": "term-1",
            "term": "API",
            "definition": "Application Programming Interface",
            "aliases": ["api"],
        }

    def test_terminology_from_dict(self):
        """Test from_dict method."""
        data = {
            "id": "term-1",
            "term": "REST",
            "definition": "Representational State Transfer",
            "aliases": ["rest", "restful"],
        }

        term = Terminology.from_dict(data)

        assert term.id == "term-1"
        assert term.term == "REST"
        assert term.definition == "Representational State Transfer"
        assert term.aliases == ["rest", "restful"]

    def test_terminology_from_dict_without_aliases(self):
        """Test from_dict without aliases key."""
        data = {
            "id": "term-1",
            "term": "Test",
            "definition": "Test definition",
        }

        term = Terminology.from_dict(data)
        assert term.aliases == []

    def test_terminology_roundtrip(self):
        """Test to_dict/from_dict roundtrip."""
        original = Terminology(
            id="term-123",
            term="GraphQL",
            definition="Query language for APIs",
            aliases=["graphql", "gql"],
        )

        dict_form = original.to_dict()
        restored = Terminology.from_dict(dict_form)

        assert restored.id == original.id
        assert restored.term == original.term
        assert restored.definition == original.definition
        assert restored.aliases == original.aliases


class TestReasoningPattern:
    """Tests for ReasoningPattern dataclass."""

    def test_create_reasoning_pattern(self):
        """Test creating a ReasoningPattern instance."""
        pattern = ReasoningPattern(
            id="pattern-1",
            name="Problem Analysis",
            steps=["Identify problem", "Analyze causes", "Propose solutions"],
            description="A systematic approach to problem solving",
        )

        assert pattern.id == "pattern-1"
        assert pattern.name == "Problem Analysis"
        assert len(pattern.steps) == 3
        assert pattern.description == "A systematic approach to problem solving"

    def test_reasoning_pattern_optional_description(self):
        """Test that description is optional."""
        pattern = ReasoningPattern(
            id="pattern-1",
            name="Quick Check",
            steps=["Check", "Verify"],
        )
        assert pattern.description is None

    def test_reasoning_pattern_to_dict(self):
        """Test to_dict method."""
        pattern = ReasoningPattern(
            id="pattern-1",
            name="Analysis",
            steps=["Step 1", "Step 2"],
            description="Test pattern",
        )

        result = pattern.to_dict()

        assert result == {
            "id": "pattern-1",
            "name": "Analysis",
            "steps": ["Step 1", "Step 2"],
            "description": "Test pattern",
        }

    def test_reasoning_pattern_from_dict(self):
        """Test from_dict method."""
        data = {
            "id": "pattern-1",
            "name": "Research",
            "steps": ["Gather", "Analyze", "Synthesize"],
            "description": "Research methodology",
        }

        pattern = ReasoningPattern.from_dict(data)

        assert pattern.id == "pattern-1"
        assert pattern.name == "Research"
        assert pattern.steps == ["Gather", "Analyze", "Synthesize"]
        assert pattern.description == "Research methodology"

    def test_reasoning_pattern_from_dict_without_description(self):
        """Test from_dict without description."""
        data = {
            "id": "pattern-1",
            "name": "Simple",
            "steps": ["Do it"],
        }

        pattern = ReasoningPattern.from_dict(data)
        assert pattern.description is None


class TestSkillExample:
    """Tests for SkillExample dataclass."""

    def test_create_skill_example(self):
        """Test creating a SkillExample instance."""
        example = SkillExample(
            id="ex-1",
            input="What is Python?",
            output="Python is a programming language.",
            context="Programming context",
        )

        assert example.id == "ex-1"
        assert example.input == "What is Python?"
        assert example.output == "Python is a programming language."
        assert example.context == "Programming context"

    def test_skill_example_optional_context(self):
        """Test that context is optional."""
        example = SkillExample(
            id="ex-1",
            input="Hello",
            output="Hi there!",
        )
        assert example.context is None

    def test_skill_example_to_dict(self):
        """Test to_dict method."""
        example = SkillExample(
            id="ex-1",
            input="Input text",
            output="Output text",
            context="Some context",
        )

        result = example.to_dict()

        assert result == {
            "id": "ex-1",
            "input": "Input text",
            "output": "Output text",
            "context": "Some context",
        }

    def test_skill_example_from_dict(self):
        """Test from_dict method."""
        data = {
            "id": "ex-1",
            "input": "Question?",
            "output": "Answer.",
            "context": "Context info",
        }

        example = SkillExample.from_dict(data)

        assert example.id == "ex-1"
        assert example.input == "Question?"
        assert example.output == "Answer."
        assert example.context == "Context info"

    def test_skill_example_from_dict_without_context(self):
        """Test from_dict without context."""
        data = {
            "id": "ex-1",
            "input": "Hi",
            "output": "Hello",
        }

        example = SkillExample.from_dict(data)
        assert example.context is None


class TestSkillFile:
    """Tests for SkillFile dataclass."""

    def test_create_skill_file(self):
        """Test creating a SkillFile instance."""
        now = datetime.utcnow()
        skill_file = SkillFile(
            id="file-1",
            name="document.pdf",
            file_type=FileType.REFERENCE,
            mime_type="application/pdf",
            storage_url="s3://bucket/file.pdf",
            content_preview="This is the preview content...",
            size_bytes=1024,
            uploaded_at=now,
        )

        assert skill_file.id == "file-1"
        assert skill_file.name == "document.pdf"
        assert skill_file.file_type == FileType.REFERENCE
        assert skill_file.mime_type == "application/pdf"
        assert skill_file.size_bytes == 1024
        assert skill_file.uploaded_at == now

    def test_skill_file_to_dict(self):
        """Test to_dict method."""
        now = datetime.utcnow()
        skill_file = SkillFile(
            id="file-1",
            name="template.docx",
            file_type=FileType.TEMPLATE,
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            storage_url="s3://bucket/template.docx",
            content_preview="Template content...",
            size_bytes=2048,
            uploaded_at=now,
        )

        result = skill_file.to_dict()

        assert result["id"] == "file-1"
        assert result["name"] == "template.docx"
        assert result["file_type"] == "template"
        assert result["size_bytes"] == 2048
        assert result["uploaded_at"] == now.isoformat()

    def test_skill_file_from_dict(self):
        """Test from_dict method."""
        now = datetime.utcnow()
        data = {
            "id": "file-1",
            "name": "reference.txt",
            "file_type": "reference",
            "mime_type": "text/plain",
            "storage_url": "s3://bucket/ref.txt",
            "content_preview": "Reference content",
            "size_bytes": 512,
            "uploaded_at": now.isoformat(),
        }

        skill_file = SkillFile.from_dict(data)

        assert skill_file.id == "file-1"
        assert skill_file.name == "reference.txt"
        assert skill_file.file_type == FileType.REFERENCE
        assert skill_file.size_bytes == 512
