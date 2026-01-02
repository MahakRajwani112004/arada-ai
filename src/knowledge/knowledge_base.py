"""Knowledge Base - combines embedding and vector search.

Supports multiple search modes:
- vector: Pure semantic search using embeddings
- bm25: Pure lexical search using BM25
- hybrid: Combines vector and BM25 with RRF
- hybrid_rerank: Hybrid search with cross-encoder re-ranking
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.models.knowledge_config import KnowledgeBaseConfig

from .embeddings import BaseEmbedding, get_embedding_client
from .reranker import HybridReranker, RankedResult
from .vector_stores.qdrant import QdrantStore, SearchResult


class SearchMode(str, Enum):
    """Search mode for knowledge base queries."""
    VECTOR = "vector"  # Pure semantic search
    BM25 = "bm25"  # Pure lexical search
    HYBRID = "hybrid"  # Combined vector + BM25 with RRF
    HYBRID_RERANK = "hybrid_rerank"  # Hybrid + cross-encoder re-ranking


@dataclass
class Document:
    """Document for knowledge base."""

    content: str
    metadata: Dict[str, Any]
    id: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid4())


@dataclass
class RetrievalResult:
    """Result from knowledge base retrieval."""

    documents: List[SearchResult]
    query: str
    collection: str


class KnowledgeBase:
    """
    Knowledge base combining embeddings and vector search.

    Usage:
        kb = KnowledgeBase(config)
        await kb.initialize()

        # Add documents
        await kb.add_documents([Document(content="...", metadata={...})])

        # Search
        results = await kb.search("query text")
    """

    def __init__(self, config: KnowledgeBaseConfig):
        """Initialize knowledge base."""
        self.config = config
        self.collection_name = config.collection_name
        self._vector_store = QdrantStore()
        self._embedding: Optional[BaseEmbedding] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize connections and create collection if needed."""
        if self._initialized:
            return

        # Connect to vector store
        await self._vector_store.connect()

        # Get embedding client
        self._embedding = get_embedding_client(self.config.embedding_model)

        # Create collection if it doesn't exist
        await self._vector_store.create_collection(
            collection_name=self.collection_name,
            vector_size=self._embedding.dimension,
        )

        self._initialized = True

    async def close(self) -> None:
        """Close connections."""
        await self._vector_store.close()
        self._initialized = False

    @property
    def embedding(self) -> BaseEmbedding:
        """Get embedding client."""
        if self._embedding is None:
            raise RuntimeError("Not initialized. Call initialize() first.")
        return self._embedding

    async def add_documents(self, documents: List[Document]) -> int:
        """Add documents to the knowledge base."""
        if not self._initialized:
            await self.initialize()

        # Generate embeddings
        texts = [doc.content for doc in documents]
        embeddings = await self.embedding.embed_batch(texts)

        # Prepare points for vector store
        points = [
            {
                "id": doc.id,
                "vector": embedding,
                "payload": {
                    "content": doc.content,
                    **doc.metadata,
                },
            }
            for doc, embedding in zip(documents, embeddings)
        ]

        # Upsert to vector store
        await self._vector_store.upsert(self.collection_name, points)
        return len(documents)

    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        mode: SearchMode = SearchMode.VECTOR,
    ) -> RetrievalResult:
        """Search for relevant documents.

        Args:
            query: Search query text
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            mode: Search mode (vector, bm25, hybrid, hybrid_rerank)

        Returns:
            RetrievalResult with matching documents
        """
        if not self._initialized:
            await self.initialize()

        effective_top_k = top_k or self.config.top_k
        effective_threshold = score_threshold or self.config.similarity_threshold

        if mode == SearchMode.VECTOR:
            # Pure vector search
            return await self._vector_search(query, effective_top_k, effective_threshold)

        elif mode == SearchMode.BM25:
            # Pure BM25 search (still uses vector store, but re-ranks with BM25)
            return await self._hybrid_search(
                query, effective_top_k, effective_threshold,
                use_bm25=True, use_cross_encoder=False
            )

        elif mode == SearchMode.HYBRID:
            # Hybrid search (vector + BM25 with RRF)
            return await self._hybrid_search(
                query, effective_top_k, effective_threshold,
                use_bm25=True, use_cross_encoder=False
            )

        elif mode == SearchMode.HYBRID_RERANK:
            # Hybrid search with cross-encoder re-ranking
            return await self._hybrid_search(
                query, effective_top_k, effective_threshold,
                use_bm25=True, use_cross_encoder=True
            )

        else:
            # Default to vector search
            return await self._vector_search(query, effective_top_k, effective_threshold)

    async def _vector_search(
        self,
        query: str,
        top_k: int,
        score_threshold: float,
    ) -> RetrievalResult:
        """Perform pure vector search."""
        # Generate query embedding
        query_vector = await self.embedding.embed(query)

        # Search
        results = await self._vector_store.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            top_k=top_k,
            score_threshold=score_threshold,
        )

        return RetrievalResult(
            documents=results,
            query=query,
            collection=self.collection_name,
        )

    async def _hybrid_search(
        self,
        query: str,
        top_k: int,
        score_threshold: float,
        use_bm25: bool = True,
        use_cross_encoder: bool = False,
    ) -> RetrievalResult:
        """Perform hybrid search with optional re-ranking.

        1. Get initial results from vector search (fetch more for re-ranking)
        2. Apply BM25 scoring and RRF fusion
        3. Optionally re-rank with cross-encoder
        """
        # Fetch more results for re-ranking
        fetch_k = min(top_k * 3, 100)

        # Get vector search results
        query_vector = await self.embedding.embed(query)
        initial_results = await self._vector_store.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            top_k=fetch_k,
            score_threshold=score_threshold * 0.7,  # Lower threshold for candidates
        )

        if not initial_results:
            return RetrievalResult(
                documents=[],
                query=query,
                collection=self.collection_name,
            )

        # Convert to format for reranker
        results_for_rerank = [
            {
                "id": r.id,
                "content": r.content,
                "metadata": r.metadata,
                "score": r.score,
            }
            for r in initial_results
        ]

        # Apply hybrid re-ranking
        reranker = HybridReranker(
            use_bm25=use_bm25,
            use_cross_encoder=use_cross_encoder,
        )
        reranked = reranker.rerank(query, results_for_rerank, top_k=top_k)

        # Convert back to SearchResult
        final_results = [
            SearchResult(
                id=r.id,
                content=r.content,
                metadata=r.metadata,
                score=r.combined_score,
            )
            for r in reranked
        ]

        return RetrievalResult(
            documents=final_results,
            query=query,
            collection=self.collection_name,
        )

    async def delete(self) -> bool:
        """Delete the knowledge base collection."""
        return await self._vector_store.delete_collection(self.collection_name)

    async def delete_document_vectors(self, document_id: str) -> int:
        """Delete all vectors associated with a specific document.

        Args:
            document_id: The document ID whose vectors should be deleted

        Returns:
            Operation ID (0 if failed)
        """
        if not self._initialized:
            await self.initialize()

        return await self._vector_store.delete_by_document_id(
            collection_name=self.collection_name,
            document_id=document_id,
        )
