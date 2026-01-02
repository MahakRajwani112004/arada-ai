"""Tests for the embeddings module.

Tests cover:
- BaseEmbedding abstract class contract
- OpenAIEmbedding implementation with mocked API calls
- Embedding dimension handling for different models
- Single and batch embedding generation
- Error handling for missing API keys
- Factory function for embedding client creation
"""

from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.knowledge.embeddings import (
    BaseEmbedding,
    OpenAIEmbedding,
    get_embedding_client,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_settings():
    """Create mock settings with OpenAI API key."""
    settings = MagicMock()
    settings.openai_api_key = "test-api-key-12345"
    return settings


@pytest.fixture
def mock_settings_no_key():
    """Create mock settings without OpenAI API key."""
    settings = MagicMock()
    settings.openai_api_key = ""
    return settings


@pytest.fixture
def mock_embedding_response():
    """Create a mock embedding response from OpenAI."""
    mock_response = MagicMock()
    mock_embedding = MagicMock()
    mock_embedding.embedding = [0.1] * 1536  # Standard embedding dimension
    mock_response.data = [mock_embedding]
    return mock_response


@pytest.fixture
def mock_batch_embedding_response():
    """Create a mock batch embedding response from OpenAI."""
    mock_response = MagicMock()
    embeddings = []
    for i in range(3):
        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.1 + i * 0.1] * 1536
        embeddings.append(mock_embedding)
    mock_response.data = embeddings
    return mock_response


@pytest.fixture
def mock_openai_client(mock_embedding_response):
    """Create a mock OpenAI async client."""
    mock_client = AsyncMock()
    mock_client.embeddings = AsyncMock()
    mock_client.embeddings.create = AsyncMock(return_value=mock_embedding_response)
    return mock_client


@pytest.fixture
def sample_texts():
    """Sample texts for embedding tests."""
    return [
        "This is the first text for embedding.",
        "Another piece of text to embed.",
        "The third and final text sample.",
    ]


# ============================================================================
# Tests for BaseEmbedding Abstract Class
# ============================================================================


class TestBaseEmbedding:
    """Tests for BaseEmbedding abstract class."""

    def test_base_embedding_cannot_be_instantiated(self):
        """Test that BaseEmbedding cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            BaseEmbedding()
        assert "abstract" in str(exc_info.value).lower() or "instantiate" in str(exc_info.value).lower()

    def test_base_embedding_defines_embed_method(self):
        """Test that BaseEmbedding defines embed abstract method."""
        assert hasattr(BaseEmbedding, "embed")

    def test_base_embedding_defines_embed_batch_method(self):
        """Test that BaseEmbedding defines embed_batch abstract method."""
        assert hasattr(BaseEmbedding, "embed_batch")

    def test_base_embedding_defines_dimension_property(self):
        """Test that BaseEmbedding defines dimension abstract property."""
        assert hasattr(BaseEmbedding, "dimension")


class ConcreteEmbedding(BaseEmbedding):
    """Concrete implementation of BaseEmbedding for testing."""

    def __init__(self, dim: int = 768):
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed(self, text: str) -> List[float]:
        return [0.0] * self._dim

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [[0.0] * self._dim for _ in texts]


class TestConcreteEmbeddingImplementation:
    """Tests for a concrete BaseEmbedding implementation."""

    def test_concrete_embedding_can_be_instantiated(self):
        """Test that concrete implementation can be instantiated."""
        embedding = ConcreteEmbedding(dim=512)
        assert embedding is not None

    def test_concrete_embedding_dimension(self):
        """Test that dimension property works correctly."""
        embedding = ConcreteEmbedding(dim=512)
        assert embedding.dimension == 512

    @pytest.mark.asyncio
    async def test_concrete_embedding_embed(self):
        """Test that embed method works correctly."""
        embedding = ConcreteEmbedding(dim=768)
        result = await embedding.embed("Test text")
        assert len(result) == 768
        assert all(isinstance(x, float) for x in result)

    @pytest.mark.asyncio
    async def test_concrete_embedding_embed_batch(self):
        """Test that embed_batch method works correctly."""
        embedding = ConcreteEmbedding(dim=768)
        texts = ["Text 1", "Text 2", "Text 3"]
        result = await embedding.embed_batch(texts)
        assert len(result) == 3
        for emb in result:
            assert len(emb) == 768


# ============================================================================
# Tests for OpenAIEmbedding
# ============================================================================


class TestOpenAIEmbedding:
    """Tests for OpenAIEmbedding implementation."""

    def test_openai_embedding_init_with_valid_key(self, mock_settings):
        """Test initialization with valid API key."""
        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI") as mock_openai:
                embedding = OpenAIEmbedding()
                assert embedding.model == "text-embedding-3-small"
                mock_openai.assert_called_once_with(api_key="test-api-key-12345")

    def test_openai_embedding_init_with_custom_model(self, mock_settings):
        """Test initialization with custom model."""
        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI"):
                embedding = OpenAIEmbedding(model="text-embedding-3-large")
                assert embedding.model == "text-embedding-3-large"

    def test_openai_embedding_init_without_api_key(self, mock_settings_no_key):
        """Test initialization fails without API key."""
        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings_no_key):
            with pytest.raises(ValueError) as exc_info:
                OpenAIEmbedding()
            assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_openai_embedding_dimension_small_model(self, mock_settings):
        """Test dimension for text-embedding-3-small model."""
        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI"):
                embedding = OpenAIEmbedding(model="text-embedding-3-small")
                assert embedding.dimension == 1536

    def test_openai_embedding_dimension_large_model(self, mock_settings):
        """Test dimension for text-embedding-3-large model."""
        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI"):
                embedding = OpenAIEmbedding(model="text-embedding-3-large")
                assert embedding.dimension == 3072

    def test_openai_embedding_dimension_ada_model(self, mock_settings):
        """Test dimension for text-embedding-ada-002 model."""
        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI"):
                embedding = OpenAIEmbedding(model="text-embedding-ada-002")
                assert embedding.dimension == 1536

    def test_openai_embedding_dimension_unknown_model(self, mock_settings):
        """Test dimension fallback for unknown model."""
        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI"):
                embedding = OpenAIEmbedding(model="some-unknown-model")
                # Should fall back to default 1536
                assert embedding.dimension == 1536

    @pytest.mark.asyncio
    async def test_openai_embedding_embed(self, mock_settings, mock_embedding_response):
        """Test single text embedding generation."""
        mock_client = AsyncMock()
        mock_client.embeddings = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_embedding_response)

        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI", return_value=mock_client):
                embedding = OpenAIEmbedding()
                result = await embedding.embed("Test text")

                assert isinstance(result, list)
                assert len(result) == 1536
                mock_client.embeddings.create.assert_called_once_with(
                    input="Test text",
                    model="text-embedding-3-small",
                )

    @pytest.mark.asyncio
    async def test_openai_embedding_embed_batch(
        self, mock_settings, mock_batch_embedding_response, sample_texts
    ):
        """Test batch text embedding generation."""
        mock_client = AsyncMock()
        mock_client.embeddings = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_batch_embedding_response)

        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI", return_value=mock_client):
                embedding = OpenAIEmbedding()
                result = await embedding.embed_batch(sample_texts)

                assert isinstance(result, list)
                assert len(result) == 3
                for emb in result:
                    assert len(emb) == 1536
                mock_client.embeddings.create.assert_called_once_with(
                    input=sample_texts,
                    model="text-embedding-3-small",
                )

    @pytest.mark.asyncio
    async def test_openai_embedding_embed_empty_text(self, mock_settings, mock_embedding_response):
        """Test embedding generation for empty text."""
        mock_client = AsyncMock()
        mock_client.embeddings = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_embedding_response)

        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI", return_value=mock_client):
                embedding = OpenAIEmbedding()
                # Empty text should still be passed to the API
                result = await embedding.embed("")
                assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_openai_embedding_embed_batch_empty_list(self, mock_settings):
        """Test batch embedding generation for empty list."""
        mock_client = AsyncMock()
        mock_client.embeddings = AsyncMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)

        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI", return_value=mock_client):
                embedding = OpenAIEmbedding()
                result = await embedding.embed_batch([])
                assert result == []

    @pytest.mark.asyncio
    async def test_openai_embedding_uses_custom_model(self, mock_settings, mock_embedding_response):
        """Test that custom model is used in API call."""
        mock_client = AsyncMock()
        mock_client.embeddings = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_embedding_response)

        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI", return_value=mock_client):
                embedding = OpenAIEmbedding(model="text-embedding-3-large")
                await embedding.embed("Test")

                mock_client.embeddings.create.assert_called_once_with(
                    input="Test",
                    model="text-embedding-3-large",
                )


# ============================================================================
# Tests for OpenAIEmbedding.DIMENSIONS
# ============================================================================


class TestOpenAIEmbeddingDimensions:
    """Tests for OpenAIEmbedding dimension mapping."""

    def test_dimensions_contains_small_model(self):
        """Test that DIMENSIONS contains text-embedding-3-small."""
        assert "text-embedding-3-small" in OpenAIEmbedding.DIMENSIONS
        assert OpenAIEmbedding.DIMENSIONS["text-embedding-3-small"] == 1536

    def test_dimensions_contains_large_model(self):
        """Test that DIMENSIONS contains text-embedding-3-large."""
        assert "text-embedding-3-large" in OpenAIEmbedding.DIMENSIONS
        assert OpenAIEmbedding.DIMENSIONS["text-embedding-3-large"] == 3072

    def test_dimensions_contains_ada_model(self):
        """Test that DIMENSIONS contains text-embedding-ada-002."""
        assert "text-embedding-ada-002" in OpenAIEmbedding.DIMENSIONS
        assert OpenAIEmbedding.DIMENSIONS["text-embedding-ada-002"] == 1536

    def test_dimensions_has_three_models(self):
        """Test that DIMENSIONS has exactly three models."""
        assert len(OpenAIEmbedding.DIMENSIONS) == 3


# ============================================================================
# Tests for get_embedding_client Factory
# ============================================================================


class TestGetEmbeddingClient:
    """Tests for the get_embedding_client factory function."""

    def test_get_embedding_client_default_model(self, mock_settings):
        """Test factory returns client with default model."""
        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI"):
                client = get_embedding_client()
                assert isinstance(client, OpenAIEmbedding)
                assert client.model == "text-embedding-3-small"

    def test_get_embedding_client_custom_model(self, mock_settings):
        """Test factory returns client with custom model."""
        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI"):
                client = get_embedding_client(model="text-embedding-3-large")
                assert isinstance(client, OpenAIEmbedding)
                assert client.model == "text-embedding-3-large"

    def test_get_embedding_client_returns_base_embedding(self, mock_settings):
        """Test that factory returns instance of BaseEmbedding."""
        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI"):
                client = get_embedding_client()
                assert isinstance(client, BaseEmbedding)

    def test_get_embedding_client_without_api_key(self, mock_settings_no_key):
        """Test factory raises error without API key."""
        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings_no_key):
            with pytest.raises(ValueError) as exc_info:
                get_embedding_client()
            assert "OPENAI_API_KEY" in str(exc_info.value)


# ============================================================================
# Tests for Error Handling
# ============================================================================


class TestEmbeddingErrorHandling:
    """Tests for error handling in embedding operations."""

    @pytest.mark.asyncio
    async def test_embed_api_error(self, mock_settings):
        """Test handling of API errors during embedding."""
        mock_client = AsyncMock()
        mock_client.embeddings = AsyncMock()
        mock_client.embeddings.create = AsyncMock(side_effect=Exception("API Error"))

        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI", return_value=mock_client):
                embedding = OpenAIEmbedding()
                with pytest.raises(Exception) as exc_info:
                    await embedding.embed("Test text")
                assert "API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_embed_batch_api_error(self, mock_settings, sample_texts):
        """Test handling of API errors during batch embedding."""
        mock_client = AsyncMock()
        mock_client.embeddings = AsyncMock()
        mock_client.embeddings.create = AsyncMock(side_effect=Exception("Rate limit exceeded"))

        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI", return_value=mock_client):
                embedding = OpenAIEmbedding()
                with pytest.raises(Exception) as exc_info:
                    await embedding.embed_batch(sample_texts)
                assert "Rate limit exceeded" in str(exc_info.value)


# ============================================================================
# Tests for Embedding Vector Properties
# ============================================================================


class TestEmbeddingVectorProperties:
    """Tests for embedding vector characteristics."""

    @pytest.mark.asyncio
    async def test_embedding_returns_floats(self, mock_settings, mock_embedding_response):
        """Test that embedding returns list of floats."""
        mock_client = AsyncMock()
        mock_client.embeddings = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_embedding_response)

        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI", return_value=mock_client):
                embedding = OpenAIEmbedding()
                result = await embedding.embed("Test")
                assert all(isinstance(x, float) for x in result)

    @pytest.mark.asyncio
    async def test_batch_embedding_returns_list_of_lists(
        self, mock_settings, mock_batch_embedding_response, sample_texts
    ):
        """Test that batch embedding returns list of lists of floats."""
        mock_client = AsyncMock()
        mock_client.embeddings = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_batch_embedding_response)

        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI", return_value=mock_client):
                embedding = OpenAIEmbedding()
                result = await embedding.embed_batch(sample_texts)
                assert isinstance(result, list)
                for emb in result:
                    assert isinstance(emb, list)
                    assert all(isinstance(x, float) for x in emb)

    @pytest.mark.asyncio
    async def test_embedding_dimension_matches_model(self, mock_settings):
        """Test that embedding dimension matches model specification."""
        # Create mock response with correct dimension for large model
        mock_response = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.1] * 3072  # Large model dimension
        mock_response.data = [mock_embedding]

        mock_client = AsyncMock()
        mock_client.embeddings = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)

        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI", return_value=mock_client):
                embedding = OpenAIEmbedding(model="text-embedding-3-large")
                result = await embedding.embed("Test")
                assert len(result) == embedding.dimension


# ============================================================================
# Integration-like Tests (with mocked API)
# ============================================================================


class TestEmbeddingIntegration:
    """Integration-like tests with mocked API calls."""

    @pytest.mark.asyncio
    async def test_embed_and_check_dimension(self, mock_settings, mock_embedding_response):
        """Test embedding workflow: create client, embed text, verify dimension."""
        mock_client = AsyncMock()
        mock_client.embeddings = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_embedding_response)

        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI", return_value=mock_client):
                # Get client via factory
                client = get_embedding_client()

                # Verify it's the right type
                assert isinstance(client, BaseEmbedding)

                # Check dimension
                assert client.dimension == 1536

                # Generate embedding
                embedding = await client.embed("Test text for embedding")

                # Verify embedding
                assert len(embedding) == client.dimension

    @pytest.mark.asyncio
    async def test_batch_embed_multiple_texts(
        self, mock_settings, mock_batch_embedding_response, sample_texts
    ):
        """Test batch embedding workflow for multiple texts."""
        mock_client = AsyncMock()
        mock_client.embeddings = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_batch_embedding_response)

        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI", return_value=mock_client):
                client = get_embedding_client()

                # Generate batch embeddings
                embeddings = await client.embed_batch(sample_texts)

                # Verify we got correct number of embeddings
                assert len(embeddings) == len(sample_texts)

                # Verify each embedding has correct dimension
                for emb in embeddings:
                    assert len(emb) == client.dimension

    @pytest.mark.asyncio
    async def test_embedding_consistency(self, mock_settings):
        """Test that same text returns same embedding structure."""
        # Create consistent mock response
        mock_response = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.5] * 1536
        mock_response.data = [mock_embedding]

        mock_client = AsyncMock()
        mock_client.embeddings = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)

        with patch("src.knowledge.embeddings.get_settings", return_value=mock_settings):
            with patch("src.knowledge.embeddings.AsyncOpenAI", return_value=mock_client):
                client = get_embedding_client()

                # Call twice with same text
                result1 = await client.embed("Same text")
                result2 = await client.embed("Same text")

                # Should have same structure
                assert len(result1) == len(result2)
                assert type(result1) == type(result2)
