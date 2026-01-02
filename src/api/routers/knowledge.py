"""API router for knowledge base management."""
import asyncio
import os
import re
import tempfile
from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.knowledge import (
    BatchUploadResponse,
    CreateKnowledgeBaseRequest,
    DocumentCategoryListResponse,
    DocumentTagListResponse,
    DocumentTagResponse,
    KnowledgeBaseListResponse,
    KnowledgeBaseResponse,
    KnowledgeDocumentListResponse,
    KnowledgeDocumentResponse,
    SearchKnowledgeBaseRequest,
    SearchKnowledgeBaseResponse,
    SearchResultItem,
    UpdateDocumentMetadataRequest,
    UpdateKnowledgeBaseRequest,
    UploadDocumentResponse,
)
from src.auth.dependencies import CurrentUser
from src.config.logging import get_logger
from src.knowledge.chunker import get_file_type, process_document
from src.knowledge.document_processor import get_mime_type, get_supported_types
from src.knowledge.knowledge_base import Document, KnowledgeBase
from src.models.knowledge_config import KnowledgeBaseConfig
from src.knowledge.vector_stores.qdrant import QdrantStore
from src.storage.database import get_session
from src.storage.knowledge_repository import KnowledgeRepository
from src.storage.object_storage import get_storage

logger = get_logger(__name__)

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB - increased to support larger documents


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks.

    Removes path separators, null bytes, and special characters.

    Args:
        filename: Original filename from user input

    Returns:
        Sanitized filename safe for storage paths
    """
    if not filename:
        return "unnamed_file"

    # Get base name (removes any path components like ../ or /)
    base = os.path.basename(filename)

    # Remove null bytes
    base = base.replace("\x00", "")

    # Replace path separators that might have survived
    base = base.replace("/", "_").replace("\\", "_")

    # Keep only safe characters (alphanumeric, underscore, hyphen, dot)
    base = re.sub(r"[^a-zA-Z0-9._-]", "_", base)

    # Collapse multiple underscores
    base = re.sub(r"_+", "_", base)

    # Remove leading dots (prevent hidden files)
    base = base.lstrip(".")

    # Ensure we have something left
    if not base:
        base = "unnamed_file"

    # Limit length
    if len(base) > 200:
        base = base[:200]

    return base


# Content type mapping for uploads
CONTENT_TYPES = {
    "pdf": "application/pdf",
    "txt": "text/plain",
    "md": "text/markdown",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def get_repository(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = None,
) -> KnowledgeRepository:
    """Get knowledge repository with database session, scoped to current user."""
    user_id = current_user.id if current_user else None
    return KnowledgeRepository(session, user_id=user_id)


def _kb_to_response(kb) -> KnowledgeBaseResponse:
    """Convert KB dataclass to response schema."""
    return KnowledgeBaseResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        collection_name=kb.collection_name,
        embedding_model=kb.embedding_model,
        document_count=kb.document_count,
        chunk_count=kb.chunk_count,
        status=kb.status,
        error_message=kb.error_message,
        created_by=kb.created_by,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


def _doc_to_response(doc) -> KnowledgeDocumentResponse:
    """Convert document dataclass to response schema."""
    return KnowledgeDocumentResponse(
        id=doc.id,
        knowledge_base_id=doc.knowledge_base_id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        chunk_count=doc.chunk_count,
        status=doc.status,
        error_message=doc.error_message,
        created_at=doc.created_at,
        indexed_at=doc.indexed_at,
        # Metadata fields
        tags=doc.tags or [],
        category=doc.category,
        author=doc.author,
        custom_metadata=doc.custom_metadata or {},
    )


# ==================== Knowledge Base Endpoints ====================


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    request: CreateKnowledgeBaseRequest,
    current_user: CurrentUser,
    repo: KnowledgeRepository = Depends(get_repository),
) -> KnowledgeBaseResponse:
    """Create a new knowledge base."""
    logger.info(
        "knowledge_base_create_started",
        name=request.name,
        user_id=current_user.id,
    )

    kb = await repo.create_knowledge_base(
        name=request.name,
        description=request.description,
        embedding_model=request.embedding_model,
    )

    logger.info(
        "knowledge_base_created",
        kb_id=kb.id,
        name=kb.name,
        user_id=current_user.id,
    )
    return _kb_to_response(kb)


@router.get("", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases(
    repo: KnowledgeRepository = Depends(get_repository),
) -> KnowledgeBaseListResponse:
    """List all knowledge bases."""
    kbs = await repo.list_knowledge_bases()

    return KnowledgeBaseListResponse(
        knowledge_bases=[_kb_to_response(kb) for kb in kbs],
        total=len(kbs),
    )


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: str,
    repo: KnowledgeRepository = Depends(get_repository),
) -> KnowledgeBaseResponse:
    """Get knowledge base by ID."""
    kb = await repo.get_knowledge_base(kb_id)

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {kb_id}",
        )

    return _kb_to_response(kb)


@router.patch("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: str,
    request: UpdateKnowledgeBaseRequest,
    current_user: CurrentUser,
    repo: KnowledgeRepository = Depends(get_repository),
) -> KnowledgeBaseResponse:
    """Update a knowledge base."""
    kb = await repo.update_knowledge_base(
        kb_id=kb_id,
        name=request.name,
        description=request.description,
    )

    if not kb:
        logger.warning(
            "knowledge_base_update_not_found",
            kb_id=kb_id,
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {kb_id}",
        )

    logger.info(
        "knowledge_base_updated",
        kb_id=kb_id,
        name=kb.name,
        user_id=current_user.id,
    )
    return _kb_to_response(kb)


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    kb_id: str,
    current_user: CurrentUser,
    repo: KnowledgeRepository = Depends(get_repository),
) -> None:
    """Delete a knowledge base and all its documents."""
    # Get KB to find collection name
    kb = await repo.get_knowledge_base(kb_id)
    if not kb:
        logger.warning(
            "knowledge_base_delete_not_found",
            kb_id=kb_id,
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {kb_id}",
        )

    # Delete from Qdrant
    try:
        kb_config = KnowledgeBaseConfig(
            collection_name=kb.collection_name,
            embedding_model=kb.embedding_model,
        )
        knowledge_base = KnowledgeBase(kb_config)
        await knowledge_base.initialize()
        await knowledge_base.delete()
        await knowledge_base.close()
    except Exception as e:
        logger.warning("failed_to_delete_qdrant_collection", error=str(e))

    # Get documents to delete from MinIO
    docs = await repo.list_documents(kb_id)
    storage = get_storage()

    for doc in docs:
        if doc.file_path:
            try:
                await storage.delete(doc.file_path)
            except Exception as e:
                logger.warning("failed_to_delete_minio_object", key=doc.file_path, error=str(e))

    # Delete from database
    deleted = await repo.delete_knowledge_base(kb_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {kb_id}",
        )

    logger.info(
        "knowledge_base_deleted",
        kb_id=kb_id,
        name=kb.name,
        user_id=current_user.id,
    )


# ==================== Document Endpoints ====================


@router.get("/{kb_id}/documents", response_model=KnowledgeDocumentListResponse)
async def list_documents(
    kb_id: str,
    status_filter: str | None = None,
    category: str | None = None,
    tags: str | None = None,  # Comma-separated list of tags
    repo: KnowledgeRepository = Depends(get_repository),
) -> KnowledgeDocumentListResponse:
    """List all documents in a knowledge base.

    Filter options:
    - status_filter: Filter by document status (pending, processing, indexed, error)
    - category: Filter by category
    - tags: Comma-separated list of tags to filter by (documents with ANY of these tags)
    """
    # Verify KB exists
    kb = await repo.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {kb_id}",
        )

    # Parse tags
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    docs = await repo.list_documents(
        knowledge_base_id=kb_id,
        status=status_filter,
        category=category,
        tags=tag_list,
    )

    return KnowledgeDocumentListResponse(
        documents=[_doc_to_response(doc) for doc in docs],
        total=len(docs),
    )


# ==================== Chunked Upload Endpoints ====================


@router.post("/{kb_id}/documents/upload/init")
async def init_chunked_upload(
    kb_id: str,
    current_user: CurrentUser,
    filename: str = Form(...),
    file_size: int = Form(...),
    content_type: str = Form(...),
    repo: KnowledgeRepository = Depends(get_repository),
):
    """Initialize a chunked upload session.

    Returns upload_id and chunk information for client to upload chunks.
    """
    from src.storage.upload_manager import get_upload_manager, CHUNK_SIZE

    # Verify KB exists
    kb = await repo.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {kb_id}",
        )

    # Validate file type
    file_type = get_file_type(filename)
    if not file_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported: {', '.join(sorted(get_supported_types()))}",
        )

    try:
        manager = get_upload_manager()
        session = await manager.init_upload(
            knowledge_base_id=kb_id,
            filename=filename,
            file_size=file_size,
            content_type=content_type,
        )

        logger.info(
            "chunked_upload_initialized",
            upload_id=session.upload_id,
            kb_id=kb_id,
            filename=filename,
            user_id=current_user.id,
        )

        return {
            "upload_id": session.upload_id,
            "filename": session.filename,
            "file_size": session.file_size,
            "chunk_size": session.chunk_size,
            "total_chunks": session.total_chunks,
            "status": session.status.value,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{kb_id}/documents/upload/{upload_id}/chunk/{chunk_num}")
async def upload_chunk(
    kb_id: str,
    upload_id: str,
    chunk_num: int,
    current_user: CurrentUser,
    chunk: UploadFile = File(...),
):
    """Upload a single chunk of a file.

    Chunks are 0-indexed. Upload all chunks then call /complete.
    """
    from src.storage.upload_manager import get_upload_manager

    manager = get_upload_manager()

    # Verify session exists and matches KB
    session = await manager.get_session(upload_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload session not found: {upload_id}",
        )

    if session.knowledge_base_id != kb_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload session does not belong to this knowledge base",
        )

    try:
        chunk_data = await chunk.read()
        session = await manager.upload_chunk(upload_id, chunk_num, chunk_data)

        return {
            "upload_id": session.upload_id,
            "chunk_num": chunk_num,
            "received_chunks": len(session.received_chunks),
            "total_chunks": session.total_chunks,
            "status": session.status.value,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{kb_id}/documents/upload/{upload_id}/complete")
async def complete_chunked_upload(
    kb_id: str,
    upload_id: str,
    current_user: CurrentUser,
    repo: KnowledgeRepository = Depends(get_repository),
):
    """Complete a chunked upload and trigger document indexing.

    Assembles all chunks and stores the file in MinIO.
    Returns the created document record.
    """
    from src.storage.upload_manager import get_upload_manager

    manager = get_upload_manager()

    # Verify session
    session = await manager.get_session(upload_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload session not found: {upload_id}",
        )

    if session.knowledge_base_id != kb_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload session does not belong to this knowledge base",
        )

    # Verify KB exists
    kb = await repo.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {kb_id}",
        )

    try:
        # Complete the upload (assembles chunks and uploads to MinIO)
        session = await manager.complete_upload(upload_id)

        # Get file type
        file_type = get_file_type(session.filename) or "unknown"

        # Create document record
        doc = await repo.create_document(
            knowledge_base_id=kb_id,
            filename=session.filename,
            file_type=file_type,
            file_size=session.file_size,
            file_path=session.storage_key,
            status="pending",
        )

        # Trigger indexing in background
        asyncio.create_task(_process_and_index_document(kb, doc, repo))

        logger.info(
            "chunked_upload_completed",
            upload_id=upload_id,
            doc_id=doc.id,
            kb_id=kb_id,
            user_id=current_user.id,
        )

        return {
            "document": {
                "id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "status": doc.status,
                "created_at": doc.created_at.isoformat(),
            },
            "upload": {
                "upload_id": session.upload_id,
                "status": session.status.value,
                "checksum": session.checksum,
            },
            "message": "Upload complete. Document is being indexed.",
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("chunked_upload_complete_failed", upload_id=upload_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete upload: {str(e)}",
        )


@router.get("/{kb_id}/documents/upload/{upload_id}/status")
async def get_upload_status(
    kb_id: str,
    upload_id: str,
    current_user: CurrentUser,
):
    """Get the status of a chunked upload session."""
    from src.storage.upload_manager import get_upload_manager

    manager = get_upload_manager()
    session = await manager.get_session(upload_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload session not found: {upload_id}",
        )

    if session.knowledge_base_id != kb_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload session does not belong to this knowledge base",
        )

    return {
        "upload_id": session.upload_id,
        "filename": session.filename,
        "file_size": session.file_size,
        "chunk_size": session.chunk_size,
        "total_chunks": session.total_chunks,
        "received_chunks": sorted(list(session.received_chunks)),
        "missing_chunks": sorted(list(set(range(session.total_chunks)) - session.received_chunks)),
        "status": session.status.value,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "completed_at": session.completed_at,
        "error_message": session.error_message,
    }


@router.delete("/{kb_id}/documents/upload/{upload_id}")
async def cancel_chunked_upload(
    kb_id: str,
    upload_id: str,
    current_user: CurrentUser,
):
    """Cancel a chunked upload and cleanup resources."""
    from src.storage.upload_manager import get_upload_manager

    manager = get_upload_manager()
    session = await manager.get_session(upload_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload session not found: {upload_id}",
        )

    if session.knowledge_base_id != kb_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload session does not belong to this knowledge base",
        )

    await manager.cancel_upload(upload_id)

    logger.info(
        "chunked_upload_cancelled",
        upload_id=upload_id,
        kb_id=kb_id,
        user_id=current_user.id,
    )

    return {"message": "Upload cancelled", "upload_id": upload_id}


# ==================== Standard Upload Endpoint ====================


@router.post("/{kb_id}/documents", response_model=UploadDocumentResponse)
async def upload_document(
    kb_id: str,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    repo: KnowledgeRepository = Depends(get_repository),
) -> UploadDocumentResponse:
    """Upload and index a document to a knowledge base."""
    logger.info(
        "document_upload_started",
        kb_id=kb_id,
        filename=file.filename,
        user_id=current_user.id,
    )

    # Verify KB exists
    kb = await repo.get_knowledge_base(kb_id)
    if not kb:
        logger.warning(
            "document_upload_kb_not_found",
            kb_id=kb_id,
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {kb_id}",
        )

    # Validate file type
    file_type = get_file_type(file.filename or "")
    if not file_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported: {', '.join(sorted(get_supported_types()))}",
        )

    # Read file content to check size
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB",
        )

    # Upload to MinIO
    storage = get_storage()
    file_id = uuid4().hex[:12]
    safe_filename = sanitize_filename(file.filename or "unknown")
    storage_key = f"{kb_id}/{file_id}_{safe_filename}"

    await storage.upload(
        key=storage_key,
        data=content,
        content_type=get_mime_type(file.filename or ""),
    )

    # Create document record (file_path now stores MinIO key)
    doc = await repo.create_document(
        knowledge_base_id=kb_id,
        filename=file.filename or "unknown",
        file_type=file_type,
        file_size=file_size,
        file_path=storage_key,
    )

    # Process document (extract text, chunk, embed)
    try:
        await _process_and_index_document(kb, doc, repo)
        doc = await repo.get_document(doc.id)
        logger.info(
            "document_upload_completed",
            doc_id=doc.id,
            kb_id=kb_id,
            filename=file.filename,
            status=doc.status,
            user_id=current_user.id,
        )
    except Exception as e:
        logger.error(
            "document_indexing_failed",
            doc_id=doc.id,
            kb_id=kb_id,
            error=str(e),
            user_id=current_user.id,
        )
        await repo.update_document(
            doc_id=doc.id,
            status="error",
            error_message=str(e),
        )
        doc = await repo.get_document(doc.id)

    return UploadDocumentResponse(
        document=_doc_to_response(doc),
        message=f"Document {'indexed successfully' if doc.status == 'indexed' else 'upload failed: ' + (doc.error_message or 'unknown error')}",
    )


@router.post("/{kb_id}/documents/batch", response_model=BatchUploadResponse)
async def upload_documents_batch(
    kb_id: str,
    current_user: CurrentUser,
    files: List[UploadFile] = File(...),
    repo: KnowledgeRepository = Depends(get_repository),
) -> BatchUploadResponse:
    """Upload multiple documents to a knowledge base."""
    # Verify KB exists
    kb = await repo.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {kb_id}",
        )

    documents = []
    errors = []
    success_count = 0
    error_count = 0

    for file in files:
        try:
            # Validate file type
            file_type = get_file_type(file.filename or "")
            if not file_type:
                errors.append(f"{file.filename}: Unsupported file type. Supported: {', '.join(sorted(get_supported_types()))}")
                error_count += 1
                continue

            # Read and validate size
            content = await file.read()
            file_size = len(content)

            if file_size > MAX_FILE_SIZE:
                errors.append(f"{file.filename}: File too large")
                error_count += 1
                continue

            # Upload to MinIO
            storage = get_storage()
            file_id = uuid4().hex[:12]
            safe_filename = sanitize_filename(file.filename or "unknown")
            storage_key = f"{kb_id}/{file_id}_{safe_filename}"

            await storage.upload(
                key=storage_key,
                data=content,
                content_type=get_mime_type(file.filename or ""),
            )

            # Create document record (file_path now stores MinIO key)
            doc = await repo.create_document(
                knowledge_base_id=kb_id,
                filename=file.filename or "unknown",
                file_type=file_type,
                file_size=file_size,
                file_path=storage_key,
            )

            # Process document
            try:
                await _process_and_index_document(kb, doc, repo)
                doc = await repo.get_document(doc.id)
                success_count += 1
            except Exception as e:
                logger.error("document_indexing_failed", doc_id=doc.id, error=str(e))
                await repo.update_document(
                    doc_id=doc.id,
                    status="error",
                    error_message=str(e),
                )
                doc = await repo.get_document(doc.id)
                errors.append(f"{file.filename}: {str(e)}")
                error_count += 1

            documents.append(_doc_to_response(doc))

        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
            error_count += 1

    return BatchUploadResponse(
        documents=documents,
        success_count=success_count,
        error_count=error_count,
        errors=errors,
    )


@router.delete("/{kb_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    kb_id: str,
    doc_id: str,
    current_user: CurrentUser,
    repo: KnowledgeRepository = Depends(get_repository),
) -> None:
    """Delete a document from a knowledge base."""
    doc = await repo.get_document(doc_id)

    if not doc or doc.knowledge_base_id != kb_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )

    # Get KB info to delete vectors
    kb = await repo.get_knowledge_base(kb_id)

    # Delete vectors from Qdrant
    if kb:
        try:
            kb_config = KnowledgeBaseConfig(
                collection_name=kb.collection_name,
                embedding_model=kb.embedding_model,
            )
            knowledge_base = KnowledgeBase(kb_config)
            await knowledge_base.initialize()
            await knowledge_base.delete_document_vectors(doc_id)
            await knowledge_base.close()
            logger.info("vectors_deleted", doc_id=doc_id, kb_id=kb_id)
        except Exception as e:
            logger.warning("failed_to_delete_vectors", doc_id=doc_id, error=str(e))

    # Delete from MinIO
    if doc.file_path:
        storage = get_storage()
        try:
            await storage.delete(doc.file_path)
        except Exception as e:
            logger.warning("failed_to_delete_minio_object", key=doc.file_path, error=str(e))

    # Delete from database
    await repo.delete_document(doc_id)
    logger.info("document_deleted", doc_id=doc_id, kb_id=kb_id)


# ==================== Document Metadata Endpoints ====================


@router.patch("/{kb_id}/documents/{doc_id}/metadata", response_model=KnowledgeDocumentResponse)
async def update_document_metadata(
    kb_id: str,
    doc_id: str,
    request: UpdateDocumentMetadataRequest,
    current_user: CurrentUser,
    repo: KnowledgeRepository = Depends(get_repository),
) -> KnowledgeDocumentResponse:
    """Update document metadata (tags, category, author, custom_metadata)."""
    # Verify document exists and belongs to KB
    doc = await repo.get_document(doc_id)
    if not doc or doc.knowledge_base_id != kb_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )

    # Update metadata
    updated_doc = await repo.update_document_metadata(
        doc_id=doc_id,
        tags=request.tags,
        category=request.category,
        author=request.author,
        custom_metadata=request.custom_metadata,
    )

    logger.info(
        "document_metadata_updated",
        doc_id=doc_id,
        kb_id=kb_id,
        user_id=current_user.id,
    )

    return _doc_to_response(updated_doc)


@router.get("/{kb_id}/tags", response_model=DocumentTagListResponse)
async def get_tags(
    kb_id: str,
    prefix: str | None = None,
    limit: int = 20,
    repo: KnowledgeRepository = Depends(get_repository),
) -> DocumentTagListResponse:
    """Get tags used in a knowledge base for autocomplete.

    Args:
        kb_id: Knowledge base ID
        prefix: Optional prefix to filter tags (for autocomplete)
        limit: Maximum number of tags to return (default 20)
    """
    # Verify KB exists
    kb = await repo.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {kb_id}",
        )

    tags = await repo.get_tags(
        knowledge_base_id=kb_id,
        prefix=prefix,
        limit=limit,
    )

    return DocumentTagListResponse(
        tags=[
            DocumentTagResponse(tag=t.tag, usage_count=t.usage_count)
            for t in tags
        ],
        total=len(tags),
    )


@router.get("/{kb_id}/categories", response_model=DocumentCategoryListResponse)
async def get_categories(
    kb_id: str,
    repo: KnowledgeRepository = Depends(get_repository),
) -> DocumentCategoryListResponse:
    """Get all categories used in a knowledge base."""
    # Verify KB exists
    kb = await repo.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {kb_id}",
        )

    categories = await repo.get_categories(kb_id)

    return DocumentCategoryListResponse(
        categories=categories,
        total=len(categories),
    )


# ==================== Document Preview Endpoints ====================


@router.get("/{kb_id}/documents/{doc_id}/download")
async def download_document(
    kb_id: str,
    doc_id: str,
    current_user: CurrentUser,
    repo: KnowledgeRepository = Depends(get_repository),
):
    """Download the original document file."""
    from fastapi.responses import Response

    doc = await repo.get_document(doc_id)

    if not doc or doc.knowledge_base_id != kb_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )

    if not doc.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not available",
        )

    try:
        storage = get_storage()
        file_content = await storage.download(doc.file_path)

        # Determine content type
        content_type = get_mime_type(doc.filename)

        return Response(
            content=file_content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'inline; filename="{doc.filename}"',
                "Cache-Control": "private, max-age=3600",
            },
        )
    except Exception as e:
        logger.error("document_download_failed", doc_id=doc_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download document: {str(e)}",
        )


@router.get("/{kb_id}/documents/{doc_id}/preview")
async def preview_document(
    kb_id: str,
    doc_id: str,
    current_user: CurrentUser,
    repo: KnowledgeRepository = Depends(get_repository),
):
    """Get document preview data including extracted text and metadata.

    Returns the extracted text content suitable for displaying in a preview.
    For binary formats like PDF, returns extracted text. For images, returns
    a presigned URL for direct viewing.
    """
    from src.knowledge.document_processor import get_document_type, DocumentType

    doc = await repo.get_document(doc_id)

    if not doc or doc.knowledge_base_id != kb_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )

    if not doc.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not available",
        )

    try:
        storage = get_storage()
        doc_type = get_document_type(doc.filename)

        # For images, return presigned URL for direct viewing
        if doc_type == DocumentType.IMAGE:
            presigned_url = await storage.get_url(doc.file_path, expires_seconds=3600)
            return {
                "type": "image",
                "url": presigned_url,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
            }

        # For text-based files, extract and return the text
        file_content = await storage.download(doc.file_path)

        # Get file extension
        ext = doc.filename.rsplit(".", 1)[-1].lower() if "." in doc.filename else ""

        # Create temp file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            tmp.write(file_content)
            temp_path = tmp.name

        try:
            from src.knowledge.document_processor import process_document as extract_document

            result = await extract_document(temp_path, doc.filename)

            return {
                "type": "text",
                "content": result.text,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "page_count": result.page_count,
                "word_count": result.word_count,
                "has_tables": len(result.tables) > 0,
                "has_images": len(result.images) > 0,
                "tables": [
                    {
                        "markdown": t.markdown,
                        "page_number": t.page_number,
                        "sheet_name": t.sheet_name,
                        "row_count": t.row_count,
                        "col_count": t.col_count,
                    }
                    for t in result.tables
                ],
                "metadata": result.metadata,
            }
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        logger.error("document_preview_failed", doc_id=doc_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}",
        )


# ==================== Search Endpoint ====================


@router.post("/{kb_id}/search", response_model=SearchKnowledgeBaseResponse)
async def search_knowledge_base(
    kb_id: str,
    request: SearchKnowledgeBaseRequest,
    current_user: CurrentUser,
    repo: KnowledgeRepository = Depends(get_repository),
) -> SearchKnowledgeBaseResponse:
    """Search a knowledge base."""
    logger.debug(
        "knowledge_base_search_started",
        kb_id=kb_id,
        query_length=len(request.query),
        top_k=request.top_k,
        user_id=current_user.id,
    )

    kb = await repo.get_knowledge_base(kb_id)

    if not kb:
        logger.warning(
            "knowledge_base_search_kb_not_found",
            kb_id=kb_id,
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {kb_id}",
        )

    try:
        from src.knowledge.knowledge_base import SearchMode

        kb_config = KnowledgeBaseConfig(
            collection_name=kb.collection_name,
            embedding_model=kb.embedding_model,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
        )
        knowledge_base = KnowledgeBase(kb_config)
        await knowledge_base.initialize()

        # Determine search mode
        search_mode = SearchMode(request.mode.value)
        if request.rerank and search_mode == SearchMode.HYBRID:
            search_mode = SearchMode.HYBRID_RERANK

        result = await knowledge_base.search(
            query=request.query,
            top_k=request.top_k,
            score_threshold=request.similarity_threshold,
            mode=search_mode,
        )

        await knowledge_base.close()

        logger.info(
            "knowledge_base_search_completed",
            kb_id=kb_id,
            results_count=len(result.documents),
            mode=search_mode.value,
            user_id=current_user.id,
        )

        return SearchKnowledgeBaseResponse(
            results=[
                SearchResultItem(
                    content=doc.content,
                    score=doc.score,
                    metadata=doc.metadata,
                )
                for doc in result.documents
            ],
            query=request.query,
            total_results=len(result.documents),
        )

    except Exception as e:
        logger.error(
            "knowledge_base_search_failed",
            kb_id=kb_id,
            error=str(e),
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


# ==================== Helper Functions ====================


async def _process_and_index_document(kb, doc, repo: KnowledgeRepository) -> None:
    """Process a document: extract text, chunk, embed, and index."""
    # Update status
    await repo.update_document(doc.id, status="processing")

    # Download from MinIO to temp file for processing
    storage = get_storage()
    file_content = await storage.download(doc.file_path)

    # Get file extension from filename
    ext = doc.filename.rsplit(".", 1)[-1].lower() if "." in doc.filename else ""

    # Create temp file with correct extension (needed for document parsers)
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(file_content)
        temp_path = tmp.name

    try:
        # Process document from temp file
        result = await process_document(
            file_path=temp_path,
            filename=doc.filename,
        )
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

    if result.error:
        raise Exception(result.error)

    if not result.chunks:
        raise Exception("No content extracted from document")

    # Initialize knowledge base
    kb_config = KnowledgeBaseConfig(
        collection_name=kb.collection_name,
        embedding_model=kb.embedding_model,
    )
    knowledge_base = KnowledgeBase(kb_config)
    await knowledge_base.initialize()

    try:
        # Convert chunks to documents
        documents = [
            Document(
                content=chunk.content,
                metadata={
                    **chunk.metadata,
                    "document_id": doc.id,
                    "knowledge_base_id": kb.id,
                },
            )
            for chunk in result.chunks
        ]

        # Add to vector store
        await knowledge_base.add_documents(documents)

        # Update document status
        await repo.update_document(
            doc_id=doc.id,
            status="indexed",
            chunk_count=len(result.chunks),
            indexed_at=datetime.now(timezone.utc),
        )

        # Update KB stats
        await repo.update_kb_stats(kb.id)

        logger.info(
            "document_indexed",
            doc_id=doc.id,
            kb_id=kb.id,
            chunks=len(result.chunks),
        )

    finally:
        await knowledge_base.close()
