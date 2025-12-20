"""Knowledge base / RAG configuration."""
from typing import Optional

from pydantic import BaseModel, Field


class KnowledgeBaseConfig(BaseModel):
    """Knowledge base / RAG configuration."""

    enabled: bool = Field(
        default=True,
        description="Whether knowledge base is enabled",
    )
    collection_name: str = Field(
        ...,
        description="Vector DB collection name",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model to use",
    )
    embedding_provider: str = Field(
        default="openai",
        description="Embedding provider: openai, cohere, local",
    )
    top_k: int = Field(
        default=5,
        gt=0,
        le=50,
        description="Number of documents to retrieve",
    )
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score",
    )
    rerank: bool = Field(
        default=False,
        description="Whether to rerank results",
    )
    rerank_model: Optional[str] = Field(
        default=None,
        description="Reranking model if enabled",
    )
    chunk_overlap: int = Field(
        default=50,
        ge=0,
        description="Overlap between chunks",
    )
    include_metadata: bool = Field(
        default=True,
        description="Include metadata in retrieved docs",
    )
