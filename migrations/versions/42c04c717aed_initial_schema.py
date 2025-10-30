"""initial schema

Revision ID: 42c04c717aed
Revises: 
Create Date: 2025-10-30 17:20:40.932580

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42c04c717aed'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create requests table - logs all requests including cache hits
    op.create_table(
        'requests',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.Text(), nullable=False),
        sa.Column('prompt_preview', sa.Text(), nullable=False),
        sa.Column('complexity', sa.Text(), nullable=False),
        sa.Column('provider', sa.Text(), nullable=False),
        sa.Column('model', sa.Text(), nullable=False),
        sa.Column('tokens_in', sa.Integer(), nullable=False),
        sa.Column('tokens_out', sa.Integer(), nullable=False),
        sa.Column('cost', sa.Float(), nullable=False)
    )

    # Create response_cache table - stores unique prompts and their responses
    op.create_table(
        'response_cache',
        sa.Column('cache_key', sa.Text(), primary_key=True),
        sa.Column('prompt_normalized', sa.Text(), nullable=False),
        sa.Column('max_tokens', sa.Integer(), nullable=False),
        sa.Column('response', sa.Text(), nullable=False),
        sa.Column('provider', sa.Text(), nullable=False),
        sa.Column('model', sa.Text(), nullable=False),
        sa.Column('complexity', sa.Text(), nullable=False),
        sa.Column('tokens_in', sa.Integer(), nullable=False),
        sa.Column('tokens_out', sa.Integer(), nullable=False),
        sa.Column('cost', sa.Float(), nullable=False),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.Column('last_accessed', sa.Text(), nullable=False),
        sa.Column('hit_count', sa.Integer(), server_default='0'),
        sa.Column('upvotes', sa.Integer(), server_default='0'),
        sa.Column('downvotes', sa.Integer(), server_default='0'),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('invalidated', sa.Integer(), server_default='0'),
        sa.Column('invalidation_reason', sa.Text(), nullable=True)
    )

    # Create response_feedback table - stores user ratings for cached responses
    op.create_table(
        'response_feedback',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('cache_key', sa.Text(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['cache_key'], ['response_cache.cache_key'])
    )

    # Create indexes for faster lookups
    op.create_index('idx_cache_prompt', 'response_cache', ['prompt_normalized'])
    op.create_index('idx_cache_created', 'response_cache', ['created_at'])
    op.create_index('idx_feedback_cache_key', 'response_feedback', ['cache_key'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_feedback_cache_key', table_name='response_feedback')
    op.drop_index('idx_cache_created', table_name='response_cache')
    op.drop_index('idx_cache_prompt', table_name='response_cache')

    # Drop tables in reverse order
    op.drop_table('response_feedback')
    op.drop_table('response_cache')
    op.drop_table('requests')
