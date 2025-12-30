"""Re-ranker module for improving search relevance.

Provides:
- Cross-encoder re-ranking using sentence-transformers
- BM25 scoring for lexical matching
- Reciprocal Rank Fusion (RRF) for combining multiple rankings

Note: Cross-encoder models are optional dependencies.
Falls back to simple scoring if not available.
"""

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from src.config.logging import get_logger

logger = get_logger(__name__)

# Try to import sentence-transformers for cross-encoder
try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    logger.warning("sentence-transformers not installed. Cross-encoder re-ranking disabled.")


@dataclass
class RankedResult:
    """A search result with ranking score."""
    id: str
    content: str
    metadata: dict
    original_score: float
    rerank_score: float
    combined_score: float


class BM25Scorer:
    """BM25 scoring for lexical matching.

    Implements the BM25 algorithm for scoring document relevance
    based on term frequency.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """Initialize BM25 scorer.

        Args:
            k1: Term frequency saturation parameter (default 1.5)
            b: Document length normalization (default 0.75)
        """
        self.k1 = k1
        self.b = b

    def score(
        self,
        query: str,
        documents: List[str],
        avg_doc_length: Optional[float] = None,
    ) -> List[float]:
        """Score documents using BM25.

        Args:
            query: Search query
            documents: List of document texts
            avg_doc_length: Average document length (computed if not provided)

        Returns:
            List of BM25 scores
        """
        if not documents:
            return []

        # Tokenize
        query_terms = self._tokenize(query)
        doc_tokens = [self._tokenize(doc) for doc in documents]

        # Compute average document length
        if avg_doc_length is None:
            avg_doc_length = sum(len(tokens) for tokens in doc_tokens) / len(doc_tokens)

        # Compute document frequencies
        n_docs = len(documents)
        doc_freqs = {}
        for tokens in doc_tokens:
            unique_terms = set(tokens)
            for term in unique_terms:
                doc_freqs[term] = doc_freqs.get(term, 0) + 1

        # Score each document
        scores = []
        for tokens in doc_tokens:
            score = 0.0
            doc_len = len(tokens)
            term_freqs = {}
            for term in tokens:
                term_freqs[term] = term_freqs.get(term, 0) + 1

            for term in query_terms:
                if term not in term_freqs:
                    continue

                tf = term_freqs[term]
                df = doc_freqs.get(term, 0)

                # IDF
                idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1)

                # BM25 score
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / avg_doc_length))
                score += idf * (numerator / denominator)

            scores.append(score)

        return scores

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        # Convert to lowercase and split on non-alphanumeric
        import re
        return re.findall(r'\b\w+\b', text.lower())


class CrossEncoderReranker:
    """Cross-encoder re-ranker using sentence-transformers.

    Uses a cross-encoder model to compute more accurate relevance scores
    by jointly encoding query and document pairs.
    """

    # Default model - good balance of speed and accuracy
    DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self, model_name: Optional[str] = None):
        """Initialize cross-encoder reranker.

        Args:
            model_name: HuggingFace model name (default: ms-marco-MiniLM-L-6-v2)
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self._model: Optional["CrossEncoder"] = None
        self._available = CROSS_ENCODER_AVAILABLE

    @property
    def available(self) -> bool:
        """Check if cross-encoder is available."""
        return self._available

    def _get_model(self) -> "CrossEncoder":
        """Lazy load the model."""
        if not self._available:
            raise RuntimeError("sentence-transformers not installed")

        if self._model is None:
            logger.info("loading_cross_encoder", model=self.model_name)
            self._model = CrossEncoder(self.model_name)
            logger.info("cross_encoder_loaded", model=self.model_name)

        return self._model

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None,
    ) -> List[Tuple[int, float]]:
        """Re-rank documents using cross-encoder.

        Args:
            query: Search query
            documents: List of document texts
            top_k: Return only top-k results (default: all)

        Returns:
            List of (document_index, score) tuples, sorted by score descending
        """
        if not documents:
            return []

        if not self._available:
            # Fallback: return original order with placeholder scores
            return [(i, 1.0 - i * 0.01) for i in range(len(documents))]

        model = self._get_model()

        # Create query-document pairs
        pairs = [[query, doc] for doc in documents]

        # Get scores
        scores = model.predict(pairs)

        # Create (index, score) pairs and sort
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        if top_k:
            indexed_scores = indexed_scores[:top_k]

        return indexed_scores


def reciprocal_rank_fusion(
    rankings: List[List[Tuple[str, float]]],
    k: int = 60,
) -> List[Tuple[str, float]]:
    """Combine multiple rankings using Reciprocal Rank Fusion.

    RRF is a robust method for combining rankings from different sources
    (e.g., vector search and BM25) without requiring score normalization.

    Formula: RRF(d) = sum(1 / (k + rank_i(d)))

    Args:
        rankings: List of rankings, each containing (id, score) tuples
        k: RRF constant (default 60)

    Returns:
        Combined ranking as (id, rrf_score) tuples
    """
    # Compute RRF scores
    rrf_scores = {}

    for ranking in rankings:
        for rank, (doc_id, _) in enumerate(ranking, start=1):
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0.0
            rrf_scores[doc_id] += 1.0 / (k + rank)

    # Sort by RRF score
    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    return sorted_results


class HybridReranker:
    """Combines vector search with BM25 and optional cross-encoder re-ranking.

    Workflow:
    1. Get vector search results
    2. Score with BM25 (optional)
    3. Combine using RRF
    4. Re-rank with cross-encoder (optional)
    """

    def __init__(
        self,
        use_bm25: bool = True,
        use_cross_encoder: bool = False,
        cross_encoder_model: Optional[str] = None,
    ):
        """Initialize hybrid reranker.

        Args:
            use_bm25: Enable BM25 scoring for hybrid search
            use_cross_encoder: Enable cross-encoder re-ranking
            cross_encoder_model: Custom cross-encoder model name
        """
        self.use_bm25 = use_bm25
        self.use_cross_encoder = use_cross_encoder
        self.bm25 = BM25Scorer() if use_bm25 else None
        self.cross_encoder = (
            CrossEncoderReranker(cross_encoder_model)
            if use_cross_encoder
            else None
        )

    def rerank(
        self,
        query: str,
        results: List[dict],
        top_k: Optional[int] = None,
    ) -> List[RankedResult]:
        """Re-rank search results.

        Args:
            query: Search query
            results: List of search results with 'id', 'content', 'metadata', 'score'
            top_k: Return only top-k results

        Returns:
            List of RankedResult with combined scores
        """
        if not results:
            return []

        ids = [r["id"] for r in results]
        contents = [r["content"] for r in results]
        scores = [r["score"] for r in results]

        # Start with vector search ranking
        vector_ranking = list(zip(ids, scores))
        vector_ranking.sort(key=lambda x: x[1], reverse=True)

        rankings = [vector_ranking]

        # Add BM25 ranking
        if self.use_bm25 and self.bm25:
            bm25_scores = self.bm25.score(query, contents)
            bm25_ranking = list(zip(ids, bm25_scores))
            bm25_ranking.sort(key=lambda x: x[1], reverse=True)
            rankings.append(bm25_ranking)

        # Combine with RRF
        combined = reciprocal_rank_fusion(rankings)

        # Build result mapping
        result_map = {r["id"]: r for r in results}

        # Create ranked results
        ranked = []
        for doc_id, rrf_score in combined:
            r = result_map[doc_id]
            ranked.append(RankedResult(
                id=doc_id,
                content=r["content"],
                metadata=r.get("metadata", {}),
                original_score=r["score"],
                rerank_score=rrf_score,
                combined_score=rrf_score,
            ))

        # Apply cross-encoder re-ranking
        if self.use_cross_encoder and self.cross_encoder and self.cross_encoder.available:
            reranked_contents = [r.content for r in ranked]
            ce_results = self.cross_encoder.rerank(query, reranked_contents, top_k)

            # Reorder based on cross-encoder scores
            reranked = []
            for idx, ce_score in ce_results:
                r = ranked[idx]
                r.rerank_score = ce_score
                r.combined_score = ce_score  # Cross-encoder takes precedence
                reranked.append(r)
            ranked = reranked

        # Apply top_k
        if top_k:
            ranked = ranked[:top_k]

        return ranked


# Global reranker instance
_hybrid_reranker: Optional[HybridReranker] = None


def get_hybrid_reranker(
    use_bm25: bool = True,
    use_cross_encoder: bool = False,
) -> HybridReranker:
    """Get or create hybrid reranker singleton."""
    global _hybrid_reranker
    if _hybrid_reranker is None:
        _hybrid_reranker = HybridReranker(
            use_bm25=use_bm25,
            use_cross_encoder=use_cross_encoder,
        )
    return _hybrid_reranker
