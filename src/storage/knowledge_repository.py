"""Knowledge Base Repository - stores and retrieves knowledge bases and documents."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models import DocumentTagModel, KnowledgeBaseModel, KnowledgeDocumentModel


@dataclass
class KnowledgeBase:
    """Knowledge base data object."""

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


@dataclass
class KnowledgeDocument:
    """Knowledge document data object."""

    id: str
    knowledge_base_id: str
    filename: str
    file_type: str
    file_size: int
    file_path: Optional[str]
    chunk_count: int
    status: str
    error_message: Optional[str]
    created_at: datetime
    indexed_at: Optional[datetime]
    # Metadata fields
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    author: Optional[str] = None
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentTag:
    """Document tag data object for autocomplete."""

    id: str
    knowledge_base_id: str
    tag: str
    usage_count: int
    created_at: datetime
    updated_at: datetime


class KnowledgeRepository:
    """PostgreSQL-backed knowledge base repository."""

    def __init__(self, session: AsyncSession, user_id: str | None = None):
        """Initialize with database session and optional user_id for filtering."""
        self.session = session
        self.user_id = user_id

    # ==================== Knowledge Base CRUD ====================

    async def create_knowledge_base(
        self,
        name: str,
        description: str = "",
        embedding_model: str = "text-embedding-3-small",
        created_by: Optional[str] = None,
    ) -> KnowledgeBase:
        """Create a new knowledge base."""
        kb_id = f"kb-{uuid4().hex[:12]}"
        collection_name = f"kb_{uuid4().hex[:16]}"  # Qdrant collection name

        model = KnowledgeBaseModel(
            id=kb_id,
            name=name,
            description=description,
            collection_name=collection_name,
            embedding_model=embedding_model,
            document_count=0,
            chunk_count=0,
            status="active",
            created_by=created_by,
        )
        # Set user_id if available
        if self.user_id:
            model.user_id = self.user_id

        self.session.add(model)
        await self.session.flush()

        return self._kb_to_dataclass(model)

    async def get_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBase]:
        """Get knowledge base by ID (scoped to user if user_id is set)."""
        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == kb_id)
        if self.user_id:
            stmt = stmt.where(KnowledgeBaseModel.user_id == self.user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._kb_to_dataclass(model)

    async def list_knowledge_bases(
        self,
        created_by: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[KnowledgeBase]:
        """List knowledge bases with optional filters (scoped to user if user_id is set)."""
        stmt = select(KnowledgeBaseModel)

        if created_by:
            stmt = stmt.where(KnowledgeBaseModel.created_by == created_by)
        if status:
            stmt = stmt.where(KnowledgeBaseModel.status == status)

        # Filter by user_id if set
        if self.user_id:
            stmt = stmt.where(KnowledgeBaseModel.user_id == self.user_id)

        stmt = stmt.order_by(KnowledgeBaseModel.created_at.desc())

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._kb_to_dataclass(m) for m in models]

    async def update_knowledge_base(
        self,
        kb_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[KnowledgeBase]:
        """Update knowledge base fields (scoped to user if user_id is set)."""
        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == kb_id)
        if self.user_id:
            stmt = stmt.where(KnowledgeBaseModel.user_id == self.user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        if name is not None:
            model.name = name
        if description is not None:
            model.description = description
        if status is not None:
            model.status = status
        if error_message is not None:
            model.error_message = error_message

        model.updated_at = datetime.now(timezone.utc)
        await self.session.flush()

        return self._kb_to_dataclass(model)

    async def delete_knowledge_base(self, kb_id: str) -> bool:
        """Delete knowledge base and all its documents (scoped to user if user_id is set)."""
        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == kb_id)
        if self.user_id:
            stmt = stmt.where(KnowledgeBaseModel.user_id == self.user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return False

        # Delete all documents first (cascade should handle this, but being explicit)
        stmt = select(KnowledgeDocumentModel).where(
            KnowledgeDocumentModel.knowledge_base_id == kb_id
        )
        result = await self.session.execute(stmt)
        docs = result.scalars().all()
        for doc in docs:
            await self.session.delete(doc)

        await self.session.delete(model)
        await self.session.flush()
        return True

    async def update_kb_stats(self, kb_id: str) -> None:
        """Update document and chunk counts for a knowledge base."""
        # Count documents
        doc_count_stmt = (
            select(func.count(KnowledgeDocumentModel.id))
            .where(KnowledgeDocumentModel.knowledge_base_id == kb_id)
            .where(KnowledgeDocumentModel.status == "indexed")
        )
        doc_result = await self.session.execute(doc_count_stmt)
        doc_count = doc_result.scalar() or 0

        # Sum chunks
        chunk_sum_stmt = (
            select(func.coalesce(func.sum(KnowledgeDocumentModel.chunk_count), 0))
            .where(KnowledgeDocumentModel.knowledge_base_id == kb_id)
            .where(KnowledgeDocumentModel.status == "indexed")
        )
        chunk_result = await self.session.execute(chunk_sum_stmt)
        chunk_count = chunk_result.scalar() or 0

        # Update KB
        model = await self.session.get(KnowledgeBaseModel, kb_id)
        if model:
            model.document_count = doc_count
            model.chunk_count = chunk_count
            model.updated_at = datetime.now(timezone.utc)
            await self.session.flush()

    # ==================== Document CRUD ====================

    async def create_document(
        self,
        knowledge_base_id: str,
        filename: str,
        file_type: str,
        file_size: int,
        file_path: Optional[str] = None,
    ) -> KnowledgeDocument:
        """Create a new document record."""
        doc_id = f"doc-{uuid4().hex[:12]}"

        model = KnowledgeDocumentModel(
            id=doc_id,
            knowledge_base_id=knowledge_base_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            chunk_count=0,
            status="pending",
        )

        self.session.add(model)
        await self.session.flush()

        return self._doc_to_dataclass(model)

    async def get_document(self, doc_id: str) -> Optional[KnowledgeDocument]:
        """Get document by ID."""
        model = await self.session.get(KnowledgeDocumentModel, doc_id)
        if model is None:
            return None
        return self._doc_to_dataclass(model)

    async def list_documents(
        self,
        knowledge_base_id: str,
        status: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[KnowledgeDocument]:
        """List documents in a knowledge base with optional filters."""
        stmt = select(KnowledgeDocumentModel).where(
            KnowledgeDocumentModel.knowledge_base_id == knowledge_base_id
        )

        if status:
            stmt = stmt.where(KnowledgeDocumentModel.status == status)
        if category:
            stmt = stmt.where(KnowledgeDocumentModel.category == category)
        if tags:
            # Filter documents that have any of the specified tags
            stmt = stmt.where(KnowledgeDocumentModel.tags.overlap(tags))

        stmt = stmt.order_by(KnowledgeDocumentModel.created_at.desc())

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._doc_to_dataclass(m) for m in models]

    async def update_document(
        self,
        doc_id: str,
        status: Optional[str] = None,
        chunk_count: Optional[int] = None,
        error_message: Optional[str] = None,
        indexed_at: Optional[datetime] = None,
    ) -> Optional[KnowledgeDocument]:
        """Update document fields."""
        model = await self.session.get(KnowledgeDocumentModel, doc_id)
        if model is None:
            return None

        if status is not None:
            model.status = status
        if chunk_count is not None:
            model.chunk_count = chunk_count
        if error_message is not None:
            model.error_message = error_message
        if indexed_at is not None:
            model.indexed_at = indexed_at

        await self.session.flush()

        return self._doc_to_dataclass(model)

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document."""
        model = await self.session.get(KnowledgeDocumentModel, doc_id)
        if model is None:
            return False

        kb_id = model.knowledge_base_id
        old_tags = model.tags or []

        await self.session.delete(model)
        await self.session.flush()

        # Update KB stats
        await self.update_kb_stats(kb_id)

        # Update tag counts
        for tag in old_tags:
            await self._decrement_tag_count(kb_id, tag)

        return True

    async def update_document_metadata(
        self,
        doc_id: str,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        author: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[KnowledgeDocument]:
        """Update document metadata fields."""
        model = await self.session.get(KnowledgeDocumentModel, doc_id)
        if model is None:
            return None

        kb_id = model.knowledge_base_id
        old_tags = set(model.tags or [])

        if tags is not None:
            new_tags = set(tags)
            # Update tag counts
            for tag in old_tags - new_tags:
                await self._decrement_tag_count(kb_id, tag)
            for tag in new_tags - old_tags:
                await self._increment_tag_count(kb_id, tag)
            model.tags = tags

        if category is not None:
            model.category = category if category else None
        if author is not None:
            model.author = author if author else None
        if custom_metadata is not None:
            model.custom_metadata = custom_metadata

        await self.session.flush()

        return self._doc_to_dataclass(model)

    # ==================== Tag Management ====================

    async def get_tags(
        self,
        knowledge_base_id: str,
        prefix: Optional[str] = None,
        limit: int = 20,
    ) -> List[DocumentTag]:
        """Get tags for a knowledge base (for autocomplete)."""
        stmt = select(DocumentTagModel).where(
            DocumentTagModel.knowledge_base_id == knowledge_base_id
        )

        if prefix:
            stmt = stmt.where(DocumentTagModel.tag.ilike(f"{prefix}%"))

        stmt = stmt.order_by(DocumentTagModel.usage_count.desc()).limit(limit)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._tag_to_dataclass(m) for m in models]

    async def get_categories(self, knowledge_base_id: str) -> List[str]:
        """Get unique categories used in a knowledge base."""
        stmt = (
            select(KnowledgeDocumentModel.category)
            .where(KnowledgeDocumentModel.knowledge_base_id == knowledge_base_id)
            .where(KnowledgeDocumentModel.category.isnot(None))
            .distinct()
            .order_by(KnowledgeDocumentModel.category)
        )

        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    async def _increment_tag_count(self, knowledge_base_id: str, tag: str) -> None:
        """Increment tag usage count or create new tag."""
        stmt = select(DocumentTagModel).where(
            DocumentTagModel.knowledge_base_id == knowledge_base_id,
            DocumentTagModel.tag == tag,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.usage_count += 1
            model.updated_at = datetime.now(timezone.utc)
        else:
            model = DocumentTagModel(
                id=f"tag-{uuid4().hex[:12]}",
                knowledge_base_id=knowledge_base_id,
                tag=tag,
                usage_count=1,
            )
            self.session.add(model)

        await self.session.flush()

    async def _decrement_tag_count(self, knowledge_base_id: str, tag: str) -> None:
        """Decrement tag usage count or delete if zero."""
        stmt = select(DocumentTagModel).where(
            DocumentTagModel.knowledge_base_id == knowledge_base_id,
            DocumentTagModel.tag == tag,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.usage_count -= 1
            if model.usage_count <= 0:
                await self.session.delete(model)
            else:
                model.updated_at = datetime.now(timezone.utc)
            await self.session.flush()

    # ==================== Helpers ====================

    def _kb_to_dataclass(self, model: KnowledgeBaseModel) -> KnowledgeBase:
        """Convert ORM model to dataclass."""
        return KnowledgeBase(
            id=model.id,
            name=model.name,
            description=model.description,
            collection_name=model.collection_name,
            embedding_model=model.embedding_model,
            document_count=model.document_count,
            chunk_count=model.chunk_count,
            status=model.status,
            error_message=model.error_message,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _doc_to_dataclass(self, model: KnowledgeDocumentModel) -> KnowledgeDocument:
        """Convert ORM model to dataclass."""
        return KnowledgeDocument(
            id=model.id,
            knowledge_base_id=model.knowledge_base_id,
            filename=model.filename,
            file_type=model.file_type,
            file_size=model.file_size,
            file_path=model.file_path,
            chunk_count=model.chunk_count,
            status=model.status,
            error_message=model.error_message,
            created_at=model.created_at,
            indexed_at=model.indexed_at,
            # Metadata fields
            tags=model.tags or [],
            category=model.category,
            author=model.author,
            custom_metadata=model.custom_metadata or {},
        )

    def _tag_to_dataclass(self, model: DocumentTagModel) -> DocumentTag:
        """Convert ORM model to dataclass."""
        return DocumentTag(
            id=model.id,
            knowledge_base_id=model.knowledge_base_id,
            tag=model.tag,
            usage_count=model.usage_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
