"""add_document_metadata

Revision ID: a1b2c3d4e5f6
Revises: 3fc5a419aba0
Create Date: 2025-12-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '3fc5a419aba0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add metadata columns to knowledge_documents and create document_tags table."""
    # Add metadata columns to knowledge_documents
    op.add_column(
        'knowledge_documents',
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}')
    )
    op.add_column(
        'knowledge_documents',
        sa.Column('category', sa.String(100), nullable=True, index=True)
    )
    op.add_column(
        'knowledge_documents',
        sa.Column('author', sa.String(200), nullable=True)
    )
    op.add_column(
        'knowledge_documents',
        sa.Column('custom_metadata', postgresql.JSONB(), nullable=False, server_default='{}')
    )

    # Create index on category
    op.create_index(
        'ix_knowledge_documents_category',
        'knowledge_documents',
        ['category'],
        unique=False
    )

    # Create document_tags table for autocomplete
    op.create_table(
        'document_tags',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column(
            'knowledge_base_id',
            sa.String(100),
            sa.ForeignKey('knowledge_bases.id', ondelete='CASCADE'),
            nullable=False,
            index=True
        ),
        sa.Column('tag', sa.String(100), nullable=False, index=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now()
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now()
        ),
        # Ensure unique tag per knowledge base
        sa.UniqueConstraint('knowledge_base_id', 'tag', name='uq_document_tags_kb_tag'),
    )


def downgrade() -> None:
    """Remove metadata columns and document_tags table."""
    # Drop document_tags table
    op.drop_table('document_tags')

    # Drop index on category
    op.drop_index('ix_knowledge_documents_category', table_name='knowledge_documents')

    # Remove metadata columns from knowledge_documents
    op.drop_column('knowledge_documents', 'custom_metadata')
    op.drop_column('knowledge_documents', 'author')
    op.drop_column('knowledge_documents', 'category')
    op.drop_column('knowledge_documents', 'tags')
