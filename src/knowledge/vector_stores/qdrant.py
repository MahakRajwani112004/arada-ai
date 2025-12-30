"""Qdrant Vector Store Client."""
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams


@dataclass
class SearchResult:
    """Result from vector similarity search."""

    id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class QdrantStore:
    """Qdrant vector store for RAG knowledge base."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ):
        """Initialize Qdrant client."""
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port or int(os.getenv("QDRANT_PORT", "6333"))
        self._client: Optional[AsyncQdrantClient] = None

    async def connect(self) -> None:
        """Connect to Qdrant server."""
        if self._client is None:
            self._client = AsyncQdrantClient(host=self.host, port=self.port)

    async def close(self) -> None:
        """Close connection."""
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> AsyncQdrantClient:
        """Get client, ensuring connected."""
        if self._client is None:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._client

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: Distance = Distance.COSINE,
    ) -> bool:
        """Create a collection if it doesn't exist."""
        collections = await self.client.get_collections()
        existing = [c.name for c in collections.collections]

        if collection_name in existing:
            return False

        await self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=distance),
        )
        return True

    async def upsert(
        self,
        collection_name: str,
        points: List[Dict[str, Any]],
    ) -> None:
        """
        Upsert points into collection.

        Each point should have:
        - id: str or int
        - vector: List[float]
        - payload: Dict with content and metadata
        """
        qdrant_points = [
            PointStruct(
                id=p["id"],
                vector=p["vector"],
                payload=p.get("payload", {}),
            )
            for p in points
        ]

        await self.client.upsert(
            collection_name=collection_name,
            points=qdrant_points,
        )

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
    ) -> List[SearchResult]:
        """Search for similar vectors."""
        # qdrant-client 1.7+ uses query_points instead of search
        response = await self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
        )

        return [
            SearchResult(
                id=str(r.id),
                content=r.payload.get("content", "") if r.payload else "",
                score=r.score,
                metadata={k: v for k, v in r.payload.items() if k != "content"} if r.payload else {},
            )
            for r in response.points
        ]

    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        await self.client.delete_collection(collection_name=collection_name)
        return True

    async def delete_by_document_id(
        self,
        collection_name: str,
        document_id: str,
    ) -> int:
        """Delete all points belonging to a specific document.

        Args:
            collection_name: The collection to delete from
            document_id: The document ID to match in payload

        Returns:
            Number of points deleted (approximate)
        """
        # Create filter for document_id in payload
        delete_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        )

        # Delete points matching the filter
        result = await self.client.delete(
            collection_name=collection_name,
            points_selector=delete_filter,
        )

        return result.operation_id if result else 0
