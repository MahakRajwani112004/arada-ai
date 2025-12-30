"""Add workflow_schedules table for cron-based scheduled execution.

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2025-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create workflow_schedules table."""
    op.create_table(
        'workflow_schedules',
        sa.Column('id', sa.String(36), primary_key=True),

        # Reference to workflow
        sa.Column('workflow_id', sa.String(100), sa.ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False, index=True),

        # Owner
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),

        # Schedule configuration
        sa.Column('cron_expression', sa.String(100), nullable=False),
        sa.Column('timezone', sa.String(100), nullable=False, server_default='UTC'),
        sa.Column('enabled', sa.Boolean, nullable=False, server_default='true'),

        # Input for scheduled runs
        sa.Column('input_text', sa.Text, nullable=True),
        sa.Column('context_json', JSONB, nullable=False, server_default='{}'),

        # Temporal integration
        sa.Column('temporal_schedule_id', sa.String(255), nullable=True),

        # Tracking
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('run_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create index for finding enabled schedules by next run time
    op.create_index(
        'ix_workflow_schedules_next_run',
        'workflow_schedules',
        ['next_run_at', 'enabled'],
        postgresql_where=sa.text("enabled = true")
    )


def downgrade() -> None:
    """Drop workflow_schedules table."""
    op.drop_index('ix_workflow_schedules_next_run', table_name='workflow_schedules')
    op.drop_table('workflow_schedules')
