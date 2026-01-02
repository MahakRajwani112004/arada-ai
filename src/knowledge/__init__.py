"""Knowledge base package.

Provides document processing, embedding, and vector search capabilities:
- Enhanced document processing (PDF, DOCX, PPTX, Excel, Images with OCR)
- Text chunking with overlap for RAG
- OpenAI embeddings
- Qdrant vector store integration
"""
from .chunker import (
    SUPPORTED_TYPES,
    ChunkingResult,
    TextChunk,
    chunk_text,
    get_file_type,
    process_document,
)
from .document_processor import (
    DocumentType,
    ExtractionResult,
    ExtractedImage,
    ExtractedTable,
    describe_images_with_llm,
    get_document_type,
    get_mime_type,
    get_supported_types,
    process_document as extract_document,
)
from .embeddings import BaseEmbedding, OpenAIEmbedding, get_embedding_client
from .knowledge_base import Document, KnowledgeBase, RetrievalResult, SearchMode
from .reranker import (
    BM25Scorer,
    CrossEncoderReranker,
    HybridReranker,
    RankedResult,
    reciprocal_rank_fusion,
)
from .vector_stores.qdrant import QdrantStore, SearchResult

__all__ = [
    # Knowledge Base
    "KnowledgeBase",
    "Document",
    "RetrievalResult",
    "SearchMode",
    # Vector Store
    "QdrantStore",
    "SearchResult",
    # Embeddings
    "BaseEmbedding",
    "OpenAIEmbedding",
    "get_embedding_client",
    # Re-ranking
    "BM25Scorer",
    "CrossEncoderReranker",
    "HybridReranker",
    "RankedResult",
    "reciprocal_rank_fusion",
    # Document Processing
    "DocumentType",
    "ExtractionResult",
    "ExtractedImage",
    "ExtractedTable",
    "get_document_type",
    "get_supported_types",
    "get_mime_type",
    "extract_document",
    "describe_images_with_llm",
    # Chunking
    "SUPPORTED_TYPES",
    "TextChunk",
    "ChunkingResult",
    "chunk_text",
    "get_file_type",
    "process_document",
]
