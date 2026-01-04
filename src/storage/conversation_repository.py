"""Conversation Repository - stores and retrieves agent chat conversations."""
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models import (
    AgentConversationModel,
    AgentMessageModel,
    AgentModel,
)


@dataclass
class ConversationSummary:
    """Summary data for conversation list display."""

    id: str
    agent_id: str
    agent_name: str
    agent_type: str
    title: str
    message_count: int
    last_message_preview: Optional[str]
    last_message_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class MessageData:
    """Message data structure."""

    id: str
    role: str
    content: str
    workflow_id: Optional[str]
    execution_id: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime


@dataclass
class ConversationDetail:
    """Full conversation with messages."""

    id: str
    agent_id: str
    agent_name: str
    agent_type: str
    title: str
    is_auto_title: bool
    message_count: int
    messages: List[MessageData]
    created_at: datetime
    updated_at: datetime


class PostgresConversationRepository:
    """PostgreSQL-backed conversation repository."""

    def __init__(self, session: AsyncSession, user_id: str):
        """Initialize with database session and user_id for filtering."""
        self.session = session
        self.user_id = user_id

    async def list_all_conversations(
        self,
        limit: int = 50,
        offset: int = 0,
        include_archived: bool = False,
    ) -> Tuple[List[ConversationSummary], int]:
        """List all conversations for the user across all agents.

        Returns conversations sorted by updated_at descending (most recent first).
        """
        # Base query with join to agents for agent info
        stmt = (
            select(AgentConversationModel, AgentModel.name, AgentModel.agent_type)
            .join(AgentModel, AgentConversationModel.agent_id == AgentModel.id)
            .where(AgentConversationModel.user_id == self.user_id)
        )

        if not include_archived:
            stmt = stmt.where(AgentConversationModel.is_archived == False)

        # Count total
        count_stmt = (
            select(func.count())
            .select_from(AgentConversationModel)
            .where(AgentConversationModel.user_id == self.user_id)
        )
        if not include_archived:
            count_stmt = count_stmt.where(AgentConversationModel.is_archived == False)

        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Get paginated results
        stmt = (
            stmt.order_by(AgentConversationModel.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        conversations = [
            ConversationSummary(
                id=conv.id,
                agent_id=conv.agent_id,
                agent_name=agent_name,
                agent_type=agent_type,
                title=conv.title,
                message_count=conv.message_count,
                last_message_preview=conv.last_message_preview,
                last_message_at=conv.last_message_at,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
            for conv, agent_name, agent_type in rows
        ]

        return conversations, total

    async def list_agent_conversations(
        self,
        agent_id: str,
        limit: int = 50,
        offset: int = 0,
        include_archived: bool = False,
    ) -> Tuple[List[ConversationSummary], int]:
        """List conversations for a specific agent."""
        # Base query with join to agents for agent info
        stmt = (
            select(AgentConversationModel, AgentModel.name, AgentModel.agent_type)
            .join(AgentModel, AgentConversationModel.agent_id == AgentModel.id)
            .where(
                AgentConversationModel.user_id == self.user_id,
                AgentConversationModel.agent_id == agent_id,
            )
        )

        if not include_archived:
            stmt = stmt.where(AgentConversationModel.is_archived == False)

        # Count total
        count_stmt = (
            select(func.count())
            .select_from(AgentConversationModel)
            .where(
                AgentConversationModel.user_id == self.user_id,
                AgentConversationModel.agent_id == agent_id,
            )
        )
        if not include_archived:
            count_stmt = count_stmt.where(AgentConversationModel.is_archived == False)

        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Get paginated results
        stmt = (
            stmt.order_by(AgentConversationModel.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        conversations = [
            ConversationSummary(
                id=conv.id,
                agent_id=conv.agent_id,
                agent_name=agent_name,
                agent_type=agent_type,
                title=conv.title,
                message_count=conv.message_count,
                last_message_preview=conv.last_message_preview,
                last_message_at=conv.last_message_at,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
            for conv, agent_name, agent_type in rows
        ]

        return conversations, total

    async def create_conversation(
        self,
        agent_id: str,
        title: Optional[str] = None,
    ) -> str:
        """Create a new conversation. Returns conversation ID."""
        conversation_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        conversation = AgentConversationModel(
            id=conversation_id,
            agent_id=agent_id,
            user_id=self.user_id,
            title=title or "New Conversation",
            is_auto_title=title is None,
            message_count=0,
            created_at=now,
            updated_at=now,
        )

        self.session.add(conversation)
        await self.session.flush()

        return conversation_id

    async def get_conversation(
        self,
        conversation_id: str,
        message_limit: int = 100,
    ) -> Optional[ConversationDetail]:
        """Get conversation with messages."""
        # Get conversation with agent info
        stmt = (
            select(AgentConversationModel, AgentModel.name, AgentModel.agent_type)
            .join(AgentModel, AgentConversationModel.agent_id == AgentModel.id)
            .where(
                AgentConversationModel.id == conversation_id,
                AgentConversationModel.user_id == self.user_id,
            )
        )
        result = await self.session.execute(stmt)
        row = result.one_or_none()

        if row is None:
            return None

        conv, agent_name, agent_type = row

        # Get messages
        msg_stmt = (
            select(AgentMessageModel)
            .where(AgentMessageModel.conversation_id == conversation_id)
            .order_by(AgentMessageModel.created_at.asc())
            .limit(message_limit)
        )
        msg_result = await self.session.execute(msg_stmt)
        messages = msg_result.scalars().all()

        return ConversationDetail(
            id=conv.id,
            agent_id=conv.agent_id,
            agent_name=agent_name,
            agent_type=agent_type,
            title=conv.title,
            is_auto_title=conv.is_auto_title,
            message_count=conv.message_count,
            messages=[
                MessageData(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    workflow_id=msg.workflow_id,
                    execution_id=msg.execution_id,
                    metadata=msg.metadata_json or {},
                    created_at=msg.created_at,
                )
                for msg in messages
            ],
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )

    async def update_conversation(
        self,
        conversation_id: str,
        title: str,
    ) -> bool:
        """Update conversation title. Returns True if updated."""
        stmt = select(AgentConversationModel).where(
            AgentConversationModel.id == conversation_id,
            AgentConversationModel.user_id == self.user_id,
        )
        result = await self.session.execute(stmt)
        conv = result.scalar_one_or_none()

        if conv is None:
            return False

        conv.title = title
        conv.is_auto_title = False
        conv.updated_at = datetime.now(timezone.utc)
        await self.session.flush()

        return True

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation and all its messages. Returns True if deleted."""
        stmt = select(AgentConversationModel).where(
            AgentConversationModel.id == conversation_id,
            AgentConversationModel.user_id == self.user_id,
        )
        result = await self.session.execute(stmt)
        conv = result.scalar_one_or_none()

        if conv is None:
            return False

        await self.session.delete(conv)
        await self.session.flush()

        return True

    async def archive_conversation(self, conversation_id: str) -> bool:
        """Archive conversation (soft delete). Returns True if archived."""
        stmt = select(AgentConversationModel).where(
            AgentConversationModel.id == conversation_id,
            AgentConversationModel.user_id == self.user_id,
        )
        result = await self.session.execute(stmt)
        conv = result.scalar_one_or_none()

        if conv is None:
            return False

        conv.is_archived = True
        conv.updated_at = datetime.now(timezone.utc)
        await self.session.flush()

        return True

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        workflow_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Add message to conversation and update stats.

        Returns message ID if successful, None if conversation not found.
        """
        # Verify conversation exists and belongs to user
        stmt = select(AgentConversationModel).where(
            AgentConversationModel.id == conversation_id,
            AgentConversationModel.user_id == self.user_id,
        )
        result = await self.session.execute(stmt)
        conv = result.scalar_one_or_none()

        if conv is None:
            return None

        now = datetime.now(timezone.utc)
        message_id = str(uuid.uuid4())

        # Create message
        message = AgentMessageModel(
            id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            workflow_id=workflow_id,
            execution_id=execution_id,
            metadata_json=metadata or {},
            created_at=now,
        )
        self.session.add(message)

        # Update conversation stats
        conv.message_count += 1
        conv.last_message_preview = content[:100] if content else None
        conv.last_message_at = now
        conv.updated_at = now

        # Auto-generate title from first user message
        if conv.is_auto_title and role == "user" and conv.message_count == 1:
            conv.title = self._generate_title_from_content(content)

        await self.session.flush()

        return message_id

    def _generate_title_from_content(self, content: str) -> str:
        """Generate a title from message content."""
        # Take first 50 chars, clean up, add ellipsis if truncated
        title = content.strip()[:50]
        if len(content) > 50:
            # Try to break at word boundary
            last_space = title.rfind(" ")
            if last_space > 30:
                title = title[:last_space]
            title = title.rstrip() + "..."
        return title or "New Conversation"

    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MessageData]:
        """Get messages for a conversation (for pagination)."""
        # First verify access
        access_stmt = select(AgentConversationModel.id).where(
            AgentConversationModel.id == conversation_id,
            AgentConversationModel.user_id == self.user_id,
        )
        access_result = await self.session.execute(access_stmt)
        if access_result.scalar_one_or_none() is None:
            return []

        # Get messages
        stmt = (
            select(AgentMessageModel)
            .where(AgentMessageModel.conversation_id == conversation_id)
            .order_by(AgentMessageModel.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = result.scalars().all()

        return [
            MessageData(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                workflow_id=msg.workflow_id,
                execution_id=msg.execution_id,
                metadata=msg.metadata_json or {},
                created_at=msg.created_at,
            )
            for msg in messages
        ]

    async def conversation_exists(self, conversation_id: str) -> bool:
        """Check if conversation exists and belongs to user."""
        stmt = select(AgentConversationModel.id).where(
            AgentConversationModel.id == conversation_id,
            AgentConversationModel.user_id == self.user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
