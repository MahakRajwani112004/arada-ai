"""Add workflow_approvals table for human-in-the-loop approval gates.

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create workflow_approvals table."""
    op.create_table(
        'workflow_approvals',
        sa.Column('id', sa.String(36), primary_key=True),

        # Workflow execution context
        sa.Column('workflow_id', sa.String(100), nullable=False, index=True),
        sa.Column('execution_id', sa.String(100), nullable=False, index=True),
        sa.Column('step_id', sa.String(100), nullable=False),
        sa.Column('temporal_workflow_id', sa.String(255), nullable=False),

        # Approval details
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('context', JSONB, nullable=False, server_default='{}'),

        # Who can approve
        sa.Column('approvers', ARRAY(sa.String), nullable=False, server_default='{}'),
        sa.Column('required_approvals', sa.Integer, nullable=False, server_default='1'),

        # Status: pending, approved, rejected, expired
        sa.Column('status', sa.String(20), nullable=False, server_default='pending', index=True),

        # Approval tracking
        sa.Column('approvals_received', JSONB, nullable=False, server_default='[]'),
        sa.Column('rejection_reason', sa.Text, nullable=True),

        # Timeout
        sa.Column('timeout_at', sa.DateTime(timezone=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),

        # User tracking
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('responded_by', sa.String(36), nullable=True),
    )

    # Create composite index for common query patterns
    op.create_index(
        'ix_workflow_approvals_pending_user',
        'workflow_approvals',
        ['status', 'created_by'],
        postgresql_where=sa.text("status = 'pending'")
    )


def downgrade() -> None:
    """Drop workflow_approvals table."""
    op.drop_index('ix_workflow_approvals_pending_user', table_name='workflow_approvals')
    op.drop_table('workflow_approvals')
