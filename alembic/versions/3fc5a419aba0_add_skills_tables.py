"""add_skills_tables

Revision ID: 3fc5a419aba0
Revises:
Create Date: 2025-12-26 16:49:26.271669

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3fc5a419aba0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create skills tables."""
    # Create skills table
    op.create_table(
        'skills',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('category', sa.String(50), nullable=False, index=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('definition_json', postgresql.JSONB(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft', index=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('marketplace_id', sa.String(100), nullable=True),
        sa.Column('rating_avg', sa.Integer(), nullable=True),
        sa.Column('rating_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('install_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create skill_versions table
    op.create_table(
        'skill_versions',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('skill_id', sa.String(100), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('definition_json', postgresql.JSONB(), nullable=False),
        sa.Column('changelog', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('skill_id', 'version', name='uq_skill_versions_skill_version'),
    )

    # Create skill_executions table
    op.create_table(
        'skill_executions',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('skill_id', sa.String(100), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('agent_id', sa.String(100), nullable=True, index=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('task_preview', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Drop skills tables."""
    op.drop_table('skill_executions')
    op.drop_table('skill_versions')
    op.drop_table('skills')
