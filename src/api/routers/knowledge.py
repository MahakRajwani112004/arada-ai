"""API router for knowledge base management."""
import os
import tempfile
from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.knowledge import (
    BatchUploadResponse,
    CreateKnowledgeBaseRequest,
    KnowledgeBaseListResponse,
    KnowledgeBaseResponse,
    KnowledgeDocumentListResponse,
    KnowledgeDocumentResponse,
    SearchKnowledgeBaseRequest,
    SearchKnowledgeBaseResponse,
    SearchResultItem,
    UpdateKnowledgeBaseRequest,
    UploadDocumentResponse,
)
from src.auth.dependencies import CurrentUser
from src.config.logging import get_logger
from src.knowledge.chunker import SUPPORTED_TYPES, get_file_type, process_document
from src.knowledge.knowledge_base import Document, KnowledgeBase
from src.models.knowledge_config import KnowledgeBaseConfig
from src.storage.database import get_session
from src.storage.knowledge_repository import KnowledgeRepository
from src.storage.object_storage import get_storage

logger = get_logger(__name__)

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

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
    repo: KnowledgeRepository = Depends(get_repository),
) -> KnowledgeDocumentListResponse:
    """List all documents in a knowledge base."""
    # Verify KB exists
    kb = await repo.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {kb_id}",
        )

    docs = await repo.list_documents(kb_id)

    return KnowledgeDocumentListResponse(
        documents=[_doc_to_response(doc) for doc in docs],
        total=len(docs),
    )


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
            detail=f"Unsupported file type. Supported: {', '.join(SUPPORTED_TYPES)}",
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
    storage_key = f"{kb_id}/{file_id}_{file.filename}"

    await storage.upload(
        key=storage_key,
        data=content,
        content_type=CONTENT_TYPES.get(file_type, "application/octet-stream"),
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
                errors.append(f"{file.filename}: Unsupported file type")
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
            storage_key = f"{kb_id}/{file_id}_{file.filename}"

            await storage.upload(
                key=storage_key,
                data=content,
                content_type=CONTENT_TYPES.get(file_type, "application/octet-stream"),
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
    repo: KnowledgeRepository = Depends(get_repository),
) -> None:
    """Delete a document from a knowledge base."""
    doc = await repo.get_document(doc_id)

    if not doc or doc.knowledge_base_id != kb_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )

    # Delete from MinIO
    if doc.file_path:
        storage = get_storage()
        try:
            await storage.delete(doc.file_path)
        except Exception as e:
            logger.warning("failed_to_delete_minio_object", key=doc.file_path, error=str(e))

    # TODO: Delete vectors from Qdrant (requires storing point IDs)

    # Delete from database
    await repo.delete_document(doc_id)
    logger.info("document_deleted", doc_id=doc_id, kb_id=kb_id)


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
        kb_config = KnowledgeBaseConfig(
            collection_name=kb.collection_name,
            embedding_model=kb.embedding_model,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
        )
        knowledge_base = KnowledgeBase(kb_config)
        await knowledge_base.initialize()

        result = await knowledge_base.search(
            query=request.query,
            top_k=request.top_k,
            score_threshold=request.similarity_threshold,
        )

        await knowledge_base.close()

        logger.info(
            "knowledge_base_search_completed",
            kb_id=kb_id,
            results_count=len(result.documents),
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
