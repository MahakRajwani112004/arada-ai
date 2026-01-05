"""Add agent_conversations and agent_messages tables for persistent chat history.

Revision ID: g7h8i9j0k1l2
Revises: e5f6g7h8i9j0
Create Date: 2026-01-04 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'g7h8i9j0k1l2'
down_revision: Union[str, None] = 'e5f6g7h8i9j0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create agent_conversations and agent_messages tables."""

    # Create agent_conversations table
    op.create_table(
        'agent_conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column(
            'agent_id',
            sa.String(100),
            sa.ForeignKey('agents.id', ondelete='CASCADE'),
            nullable=False,
            index=True
        ),
        sa.Column(
            'user_id',
            sa.String(36),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            index=True
        ),
        # Session metadata
        sa.Column('title', sa.String(255), nullable=False, server_default='New Conversation'),
        sa.Column('is_auto_title', sa.Boolean, nullable=False, server_default='true'),
        # Stats (denormalized for performance)
        sa.Column('message_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_message_preview', sa.String(100), nullable=True),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        # Status
        sa.Column('is_archived', sa.Boolean, nullable=False, server_default='false'),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create indexes for common queries
    op.create_index(
        'ix_agent_conversations_user_updated',
        'agent_conversations',
        ['user_id', 'updated_at'],
        unique=False
    )
    op.create_index(
        'ix_agent_conversations_agent_user',
        'agent_conversations',
        ['agent_id', 'user_id', 'updated_at'],
        unique=False
    )

    # Create agent_messages table
    op.create_table(
        'agent_messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column(
            'conversation_id',
            sa.String(36),
            sa.ForeignKey('agent_conversations.id', ondelete='CASCADE'),
            nullable=False,
            index=True
        ),
        # Message content
        sa.Column('role', sa.String(20), nullable=False),  # 'user', 'assistant', 'system'
        sa.Column('content', sa.Text, nullable=False),
        # Execution traceability
        sa.Column('workflow_id', sa.String(255), nullable=True),
        sa.Column('execution_id', sa.String(100), nullable=True),
        # Metadata (token usage, tool calls, etc.)
        sa.Column('metadata_json', JSONB, nullable=False, server_default='{}'),
        # Timestamp
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create index for loading messages in order
    op.create_index(
        'ix_agent_messages_conversation_created',
        'agent_messages',
        ['conversation_id', 'created_at'],
        unique=False
    )


def downgrade() -> None:
    """Drop agent_conversations and agent_messages tables."""
    op.drop_index('ix_agent_messages_conversation_created', table_name='agent_messages')
    op.drop_table('agent_messages')
    op.drop_index('ix_agent_conversations_agent_user', table_name='agent_conversations')
    op.drop_index('ix_agent_conversations_user_updated', table_name='agent_conversations')
    op.drop_table('agent_conversations')
