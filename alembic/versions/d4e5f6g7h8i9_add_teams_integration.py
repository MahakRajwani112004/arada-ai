"""Add Teams integration tables.

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-01-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6g7h8i9'
down_revision: Union[str, None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Teams integration tables."""

    # Teams configuration table
    op.create_table(
        'teams_configurations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),

        # Bot credentials
        sa.Column('app_id', sa.String(100), nullable=False),
        sa.Column('app_password_ref', sa.String(500), nullable=False),  # Vault reference
        sa.Column('tenant_id', sa.String(100), nullable=True),

        # Default agent
        sa.Column('default_agent_id', sa.String(100), sa.ForeignKey('agents.id', ondelete='SET NULL'), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Teams conversations table
    op.create_table(
        'teams_conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('config_id', sa.String(36), sa.ForeignKey('teams_configurations.id', ondelete='CASCADE'), nullable=False, index=True),

        # Teams identifiers
        sa.Column('conversation_id', sa.String(500), nullable=False, index=True),
        sa.Column('channel_id', sa.String(500), nullable=True),
        sa.Column('team_id', sa.String(500), nullable=True),
        sa.Column('service_url', sa.String(500), nullable=False),

        # Conversation type
        sa.Column('conversation_type', sa.String(50), nullable=False, server_default='personal'),

        # Full conversation reference (Bot Framework format)
        sa.Column('reference_json', JSONB, nullable=False),

        # Agent mapping
        sa.Column('agent_id', sa.String(100), sa.ForeignKey('agents.id', ondelete='SET NULL'), nullable=True),

        # Last activity
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Teams messages table
    op.create_table(
        'teams_messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('teams_conversations.id', ondelete='CASCADE'), nullable=False, index=True),

        # Teams message identifier
        sa.Column('teams_message_id', sa.String(500), nullable=True),

        # Sender info
        sa.Column('sender_id', sa.String(500), nullable=False),
        sa.Column('sender_name', sa.String(200), nullable=True),
        sa.Column('is_from_bot', sa.Boolean, nullable=False, server_default='false'),

        # Content
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('content_type', sa.String(50), nullable=False, server_default='text'),

        # Workflow execution
        sa.Column('workflow_id', sa.String(255), nullable=True),

        # Metadata
        sa.Column('metadata_json', JSONB, nullable=False, server_default='{}'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create unique constraint for conversation_id per config
    op.create_index(
        'ix_teams_conversations_config_conv',
        'teams_conversations',
        ['config_id', 'conversation_id'],
        unique=True
    )


def downgrade() -> None:
    """Drop Teams integration tables."""
    op.drop_index('ix_teams_conversations_config_conv', table_name='teams_conversations')
    op.drop_table('teams_messages')
    op.drop_table('teams_conversations')
    op.drop_table('teams_configurations')
