"""API schemas for knowledge base management."""
from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SearchModeEnum(str, Enum):
    """Search mode for knowledge base queries."""
    VECTOR = "vector"  # Pure semantic search
    BM25 = "bm25"  # Pure lexical search (with vector pre-filter)
    HYBRID = "hybrid"  # Combined vector + BM25 with RRF
    HYBRID_RERANK = "hybrid_rerank"  # Hybrid + cross-encoder re-ranking


# ==================== Knowledge Base Schemas ====================


class CreateKnowledgeBaseRequest(BaseModel):
    """Request to create a new knowledge base."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=1000)
    embedding_model: str = Field("text-embedding-3-small", max_length=100)


class UpdateKnowledgeBaseRequest(BaseModel):
    """Request to update a knowledge base."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class KnowledgeBaseResponse(BaseModel):
    """Response containing knowledge base details."""

    id: str
    name: str
    description: str
    collection_name: str
    embedding_model: str
    document_count: int
    chunk_count: int
    status: str
    error_message: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseListResponse(BaseModel):
    """Response containing list of knowledge bases."""

    knowledge_bases: List[KnowledgeBaseResponse]
    total: int


# ==================== Document Schemas ====================


class KnowledgeDocumentResponse(BaseModel):
    """Response containing document details."""

    id: str
    knowledge_base_id: str
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str
    error_message: Optional[str]
    created_at: datetime
    indexed_at: Optional[datetime]
    # Metadata fields
    tags: List[str] = []
    category: Optional[str] = None
    author: Optional[str] = None
    custom_metadata: dict = {}


class KnowledgeDocumentListResponse(BaseModel):
    """Response containing list of documents."""

    documents: List[KnowledgeDocumentResponse]
    total: int


class UploadDocumentResponse(BaseModel):
    """Response after uploading a document."""

    document: KnowledgeDocumentResponse
    message: str


class BatchUploadResponse(BaseModel):
    """Response after uploading multiple documents."""

    documents: List[KnowledgeDocumentResponse]
    success_count: int
    error_count: int
    errors: List[str]


# ==================== Metadata Schemas ====================


class UpdateDocumentMetadataRequest(BaseModel):
    """Request to update document metadata."""

    tags: Optional[List[str]] = Field(None, max_length=20)
    category: Optional[str] = Field(None, max_length=100)
    author: Optional[str] = Field(None, max_length=200)
    custom_metadata: Optional[dict] = None


class DocumentTagResponse(BaseModel):
    """A tag used in the knowledge base."""

    tag: str
    usage_count: int


class DocumentTagListResponse(BaseModel):
    """Response containing list of tags for autocomplete."""

    tags: List[DocumentTagResponse]
    total: int


class DocumentCategoryListResponse(BaseModel):
    """Response containing list of categories."""

    categories: List[str]
    total: int


# ==================== Search Schemas ====================


class SearchKnowledgeBaseRequest(BaseModel):
    """Request to search a knowledge base."""

    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)
    similarity_threshold: float = Field(0.1, ge=0.0, le=1.0)
    mode: SearchModeEnum = Field(
        SearchModeEnum.VECTOR,
        description="Search mode: vector (semantic), bm25 (lexical), hybrid, or hybrid_rerank"
    )
    rerank: bool = Field(
        False,
        description="Enable cross-encoder re-ranking (applies to hybrid mode)"
    )


class SearchResultItem(BaseModel):
    """A single search result."""

    content: str
    score: float
    metadata: dict


class SearchKnowledgeBaseResponse(BaseModel):
    """Response from knowledge base search."""

    results: List[SearchResultItem]
    query: str
    total_results: int
