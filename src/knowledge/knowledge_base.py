"""Knowledge Base - combines embedding and vector search."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.models.knowledge_config import KnowledgeBaseConfig

from .embeddings import BaseEmbedding, get_embedding_client
from .vector_stores.qdrant import QdrantStore, SearchResult


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
    ) -> RetrievalResult:
        """Search for relevant documents."""
        if not self._initialized:
            await self.initialize()

        # Generate query embedding
        query_vector = await self.embedding.embed(query)

        # Search
        results = await self._vector_store.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            top_k=top_k or self.config.top_k,
            score_threshold=score_threshold or self.config.similarity_threshold,
        )

        return RetrievalResult(
            documents=results,
            query=query,
            collection=self.collection_name,
        )

    async def delete(self) -> bool:
        """Delete the knowledge base collection."""
        return await self._vector_store.delete_collection(self.collection_name)
