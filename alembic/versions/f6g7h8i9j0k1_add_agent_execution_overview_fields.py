"""Add agent execution overview fields for MVP.

Adds minimal fields to support the Agent Overview tab:
- input_preview: First 200 chars of user input
- output_preview: First 500 chars of agent output
- total_tokens: Token count per execution
- total_cost_cents: Cost per execution
- parent_execution_id: For nested agent call tracing

Revision ID: f6g7h8i9j0k1
Revises: d4e5f6g7h8i9
Create Date: 2026-01-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6g7h8i9j0k1'
down_revision: Union[str, None] = 'd4e5f6g7h8i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add overview fields to agent_executions table."""
    # Input/output previews
    op.add_column(
        'agent_executions',
        sa.Column('input_preview', sa.String(200), nullable=True,
                  comment='First 200 chars of sanitized user input')
    )
    op.add_column(
        'agent_executions',
        sa.Column('output_preview', sa.String(500), nullable=True,
                  comment='First 500 chars of agent output')
    )

    # Token and cost tracking
    op.add_column(
        'agent_executions',
        sa.Column('total_tokens', sa.Integer, nullable=False, server_default='0',
                  comment='Total tokens used in this execution')
    )
    op.add_column(
        'agent_executions',
        sa.Column('total_cost_cents', sa.Integer, nullable=False, server_default='0',
                  comment='Total cost in cents for this execution')
    )

    # Parent execution for nested calls
    op.add_column(
        'agent_executions',
        sa.Column('parent_execution_id', sa.String(36), nullable=True,
                  comment='Parent execution ID for nested agent calls')
    )

    # Add index for parent_execution_id to support trace queries
    op.create_index(
        'ix_agent_executions_parent_execution_id',
        'agent_executions',
        ['parent_execution_id']
    )


def downgrade() -> None:
    """Remove overview fields from agent_executions table."""
    op.drop_index('ix_agent_executions_parent_execution_id', table_name='agent_executions')
    op.drop_column('agent_executions', 'parent_execution_id')
    op.drop_column('agent_executions', 'total_cost_cents')
    op.drop_column('agent_executions', 'total_tokens')
    op.drop_column('agent_executions', 'output_preview')
    op.drop_column('agent_executions', 'input_preview')
