"""API schemas for knowledge base management."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


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


# ==================== Search Schemas ====================


class SearchKnowledgeBaseRequest(BaseModel):
    """Request to search a knowledge base."""

    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)
    similarity_threshold: float = Field(0.1, ge=0.0, le=1.0)


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
