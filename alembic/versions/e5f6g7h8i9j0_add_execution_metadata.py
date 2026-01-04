"""Add execution_metadata JSONB column to agent_executions.

Revision ID: e5f6g7h8i9j0
Revises: f6g7h8i9j0k1
Create Date: 2026-01-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'e5f6g7h8i9j0'
down_revision: Union[str, None] = 'f6g7h8i9j0k1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add execution_metadata column."""
    op.add_column(
        'agent_executions',
        sa.Column(
            'execution_metadata',
            JSONB,
            nullable=True,
            comment='Full execution metadata including tool_calls, agent_results, etc.'
        )
    )


def downgrade() -> None:
    """Remove execution_metadata column."""
    op.drop_column('agent_executions', 'execution_metadata')
