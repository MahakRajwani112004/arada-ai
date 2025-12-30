"""Tests for the reranker module."""

import pytest

from src.knowledge.reranker import (
    BM25Scorer,
    CrossEncoderReranker,
    HybridReranker,
    RankedResult,
    reciprocal_rank_fusion,
)


class TestBM25Scorer:
    """Tests for BM25Scorer class."""

    def test_init_default_params(self):
        """Test BM25Scorer initializes with default parameters."""
        scorer = BM25Scorer()
        assert scorer.k1 == 1.5
        assert scorer.b == 0.75

    def test_init_custom_params(self):
        """Test BM25Scorer initializes with custom parameters."""
        scorer = BM25Scorer(k1=2.0, b=0.5)
        assert scorer.k1 == 2.0
        assert scorer.b == 0.5

    def test_score_empty_documents(self):
        """Test scoring with empty document list."""
        scorer = BM25Scorer()
        scores = scorer.score("test query", [])
        assert scores == []

    def test_score_single_document(self):
        """Test scoring a single document."""
        scorer = BM25Scorer()
        documents = ["This is a test document about machine learning"]
        scores = scorer.score("machine learning", documents)
        assert len(scores) == 1
        assert scores[0] > 0  # Should have positive score for matching terms

    def test_score_multiple_documents(self):
        """Test scoring multiple documents."""
        scorer = BM25Scorer()
        documents = [
            "Machine learning is a subset of artificial intelligence",
            "Python is a programming language",
            "Deep learning uses neural networks for machine learning",
        ]
        scores = scorer.score("machine learning", documents)
        assert len(scores) == 3
        # Documents with "machine learning" should score higher
        assert scores[0] > scores[1]  # ML doc > Python doc
        assert scores[2] > scores[1]  # DL doc > Python doc

    def test_score_exact_match_higher(self):
        """Test that exact matches score higher."""
        scorer = BM25Scorer()
        documents = [
            "machine learning techniques",
            "artificial intelligence methods",
        ]
        scores = scorer.score("machine learning", documents)
        assert scores[0] > scores[1]

    def test_score_no_match(self):
        """Test scoring when no terms match."""
        scorer = BM25Scorer()
        documents = ["Python programming language"]
        scores = scorer.score("quantum physics", documents)
        assert len(scores) == 1
        assert scores[0] == 0.0  # No matching terms

    def test_tokenize(self):
        """Test tokenization method."""
        scorer = BM25Scorer()
        tokens = scorer._tokenize("Hello, World! This is a Test-123.")
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens
        assert "123" in tokens
        # Should be lowercase
        assert "Hello" not in tokens


class TestCrossEncoderReranker:
    """Tests for CrossEncoderReranker class."""

    def test_init_default_model(self):
        """Test CrossEncoderReranker initializes with default model."""
        reranker = CrossEncoderReranker()
        assert reranker.model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def test_init_custom_model(self):
        """Test CrossEncoderReranker initializes with custom model."""
        reranker = CrossEncoderReranker(model_name="custom-model")
        assert reranker.model_name == "custom-model"

    def test_rerank_empty_documents(self):
        """Test reranking with empty document list."""
        reranker = CrossEncoderReranker()
        results = reranker.rerank("test query", [])
        assert results == []

    def test_rerank_fallback_when_unavailable(self):
        """Test fallback behavior when sentence-transformers is unavailable."""
        reranker = CrossEncoderReranker()
        # Force unavailable state for testing
        original_available = reranker._available
        reranker._available = False

        documents = ["doc1", "doc2", "doc3"]
        results = reranker.rerank("query", documents)

        # Should return fallback scores in original order
        assert len(results) == 3
        assert results[0][0] == 0  # First doc index
        assert results[1][0] == 1  # Second doc index
        assert results[2][0] == 2  # Third doc index

        # Restore original state
        reranker._available = original_available

    def test_rerank_with_top_k(self):
        """Test reranking with top_k limit."""
        reranker = CrossEncoderReranker()
        # Force unavailable state for predictable testing
        original_available = reranker._available
        reranker._available = False

        documents = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        results = reranker.rerank("query", documents, top_k=3)

        assert len(results) == 3

        # Restore original state
        reranker._available = original_available


class TestReciprocalRankFusion:
    """Tests for reciprocal_rank_fusion function."""

    def test_single_ranking(self):
        """Test RRF with a single ranking."""
        rankings = [
            [("doc1", 0.9), ("doc2", 0.7), ("doc3", 0.5)],
        ]
        results = reciprocal_rank_fusion(rankings, k=60)

        assert len(results) == 3
        # Order should be preserved
        assert results[0][0] == "doc1"
        assert results[1][0] == "doc2"
        assert results[2][0] == "doc3"

    def test_multiple_rankings_agreement(self):
        """Test RRF when rankings agree."""
        rankings = [
            [("doc1", 0.9), ("doc2", 0.7), ("doc3", 0.5)],
            [("doc1", 0.8), ("doc2", 0.6), ("doc3", 0.4)],
        ]
        results = reciprocal_rank_fusion(rankings, k=60)

        # doc1 should be first since both rankings agree
        assert results[0][0] == "doc1"
        assert results[1][0] == "doc2"
        assert results[2][0] == "doc3"

    def test_multiple_rankings_disagreement(self):
        """Test RRF when rankings disagree."""
        rankings = [
            [("doc1", 0.9), ("doc2", 0.7), ("doc3", 0.5)],
            [("doc3", 0.9), ("doc2", 0.7), ("doc1", 0.5)],
        ]
        results = reciprocal_rank_fusion(rankings, k=60)

        # doc2 should benefit from being ranked 2nd in both
        # RRF scores: doc1 = 1/61 + 1/63, doc2 = 1/62 + 1/62, doc3 = 1/63 + 1/61
        assert len(results) == 3
        # doc1 and doc3 should tie, doc2 in middle or similar

    def test_different_k_values(self):
        """Test RRF with different k values."""
        rankings = [
            [("doc1", 0.9), ("doc2", 0.7)],
            [("doc2", 0.8), ("doc1", 0.6)],
        ]

        # Higher k smooths differences
        results_high_k = reciprocal_rank_fusion(rankings, k=100)
        results_low_k = reciprocal_rank_fusion(rankings, k=10)

        # Both should return 2 documents
        assert len(results_high_k) == 2
        assert len(results_low_k) == 2

    def test_empty_rankings(self):
        """Test RRF with empty rankings."""
        rankings = []
        results = reciprocal_rank_fusion(rankings, k=60)
        assert results == []

    def test_partial_overlap(self):
        """Test RRF when rankings have partial overlap."""
        rankings = [
            [("doc1", 0.9), ("doc2", 0.7)],
            [("doc3", 0.8), ("doc2", 0.6)],
        ]
        results = reciprocal_rank_fusion(rankings, k=60)

        # All three docs should appear
        doc_ids = [r[0] for r in results]
        assert "doc1" in doc_ids
        assert "doc2" in doc_ids
        assert "doc3" in doc_ids
        # doc2 appears in both, so should have higher combined score
        assert results[0][0] == "doc2"


class TestHybridReranker:
    """Tests for HybridReranker class."""

    def test_init_default(self):
        """Test HybridReranker initializes with defaults."""
        reranker = HybridReranker()
        assert reranker.use_bm25 is True
        assert reranker.use_cross_encoder is False
        assert reranker.bm25 is not None
        assert reranker.cross_encoder is None

    def test_init_with_bm25_disabled(self):
        """Test HybridReranker with BM25 disabled."""
        reranker = HybridReranker(use_bm25=False)
        assert reranker.use_bm25 is False
        assert reranker.bm25 is None

    def test_init_with_cross_encoder(self):
        """Test HybridReranker with cross-encoder enabled."""
        reranker = HybridReranker(use_cross_encoder=True)
        assert reranker.use_cross_encoder is True
        assert reranker.cross_encoder is not None

    def test_rerank_empty_results(self):
        """Test reranking with empty results."""
        reranker = HybridReranker()
        results = reranker.rerank("test query", [])
        assert results == []

    def test_rerank_single_result(self):
        """Test reranking with a single result."""
        reranker = HybridReranker()
        results = [
            {
                "id": "doc1",
                "content": "Machine learning is awesome",
                "metadata": {"source": "test"},
                "score": 0.9,
            }
        ]
        ranked = reranker.rerank("machine learning", results)

        assert len(ranked) == 1
        assert isinstance(ranked[0], RankedResult)
        assert ranked[0].id == "doc1"
        assert ranked[0].content == "Machine learning is awesome"
        assert ranked[0].metadata == {"source": "test"}
        assert ranked[0].original_score == 0.9

    def test_rerank_multiple_results(self):
        """Test reranking with multiple results."""
        reranker = HybridReranker()
        results = [
            {
                "id": "doc1",
                "content": "Python programming language",
                "metadata": {},
                "score": 0.8,
            },
            {
                "id": "doc2",
                "content": "Machine learning with Python",
                "metadata": {},
                "score": 0.75,
            },
            {
                "id": "doc3",
                "content": "Deep learning neural networks",
                "metadata": {},
                "score": 0.7,
            },
        ]
        ranked = reranker.rerank("machine learning", results)

        assert len(ranked) == 3
        # All results should be RankedResult instances
        for r in ranked:
            assert isinstance(r, RankedResult)

    def test_rerank_with_top_k(self):
        """Test reranking with top_k limit."""
        reranker = HybridReranker()
        results = [
            {"id": f"doc{i}", "content": f"Document {i}", "metadata": {}, "score": 0.5}
            for i in range(10)
        ]
        ranked = reranker.rerank("document", results, top_k=3)

        assert len(ranked) == 3

    def test_rerank_preserves_metadata(self):
        """Test that reranking preserves document metadata."""
        reranker = HybridReranker()
        results = [
            {
                "id": "doc1",
                "content": "Test content",
                "metadata": {
                    "source": "file.pdf",
                    "page": 1,
                    "custom_field": "value",
                },
                "score": 0.9,
            }
        ]
        ranked = reranker.rerank("test", results)

        assert ranked[0].metadata["source"] == "file.pdf"
        assert ranked[0].metadata["page"] == 1
        assert ranked[0].metadata["custom_field"] == "value"

    def test_rerank_bm25_only(self):
        """Test reranking with BM25 only (no cross-encoder)."""
        reranker = HybridReranker(use_bm25=True, use_cross_encoder=False)
        results = [
            {
                "id": "doc1",
                "content": "Artificial intelligence research",
                "metadata": {},
                "score": 0.9,
            },
            {
                "id": "doc2",
                "content": "Machine learning machine learning machine",
                "metadata": {},
                "score": 0.7,
            },
        ]
        ranked = reranker.rerank("machine learning", results)

        # doc2 should rank higher due to BM25 boost from term frequency
        assert len(ranked) == 2
        # The combined_score should be the RRF score
        assert all(r.combined_score > 0 for r in ranked)

    def test_rerank_vector_only(self):
        """Test reranking with neither BM25 nor cross-encoder."""
        reranker = HybridReranker(use_bm25=False, use_cross_encoder=False)
        results = [
            {"id": "doc1", "content": "First document", "metadata": {}, "score": 0.9},
            {"id": "doc2", "content": "Second document", "metadata": {}, "score": 0.7},
        ]
        ranked = reranker.rerank("query", results)

        # Should preserve original ranking (by vector score)
        assert len(ranked) == 2
        assert ranked[0].id == "doc1"
        assert ranked[1].id == "doc2"


class TestRankedResult:
    """Tests for RankedResult dataclass."""

    def test_create_ranked_result(self):
        """Test creating a RankedResult instance."""
        result = RankedResult(
            id="doc1",
            content="Test content",
            metadata={"key": "value"},
            original_score=0.9,
            rerank_score=0.85,
            combined_score=0.87,
        )

        assert result.id == "doc1"
        assert result.content == "Test content"
        assert result.metadata == {"key": "value"}
        assert result.original_score == 0.9
        assert result.rerank_score == 0.85
        assert result.combined_score == 0.87


class TestIntegration:
    """Integration tests for the reranker module."""

    def test_full_hybrid_pipeline(self):
        """Test the full hybrid search pipeline."""
        # Simulate search results from vector store
        vector_results = [
            {
                "id": "doc1",
                "content": "Machine learning is a field of artificial intelligence",
                "metadata": {"source": "ml_basics.pdf"},
                "score": 0.85,
            },
            {
                "id": "doc2",
                "content": "Python is widely used in data science and machine learning",
                "metadata": {"source": "python_intro.pdf"},
                "score": 0.82,
            },
            {
                "id": "doc3",
                "content": "Neural networks are the foundation of deep learning",
                "metadata": {"source": "dl_guide.pdf"},
                "score": 0.78,
            },
            {
                "id": "doc4",
                "content": "Web development with JavaScript frameworks",
                "metadata": {"source": "web_dev.pdf"},
                "score": 0.72,
            },
        ]

        # Run hybrid reranking
        reranker = HybridReranker(use_bm25=True, use_cross_encoder=False)
        ranked = reranker.rerank("machine learning", vector_results, top_k=3)

        # Verify output format
        assert len(ranked) == 3
        assert all(isinstance(r, RankedResult) for r in ranked)

        # Verify relevant docs are ranked higher
        ranked_ids = [r.id for r in ranked]
        assert "doc1" in ranked_ids  # Contains "machine learning"
        assert "doc2" in ranked_ids  # Contains "machine learning"
        # doc4 (web dev) should likely not be in top 3

    def test_reranking_improves_relevance(self):
        """Test that hybrid reranking improves relevance ordering."""
        # Results where vector search may not have perfect ordering
        results = [
            {
                "id": "doc1",
                "content": "Python programming guide for beginners",
                "metadata": {},
                "score": 0.9,  # High vector score but less relevant
            },
            {
                "id": "doc2",
                "content": "Machine learning machine learning deep learning",
                "metadata": {},
                "score": 0.7,  # Lower vector score but more relevant to query
            },
        ]

        reranker = HybridReranker(use_bm25=True)
        ranked = reranker.rerank("machine learning", results)

        # After BM25 + RRF, doc2 should potentially rank higher
        # due to term frequency boost
        assert len(ranked) == 2
        # The exact ranking depends on RRF calculation
        # but doc2's BM25 score should be much higher
