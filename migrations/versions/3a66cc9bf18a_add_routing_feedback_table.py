"""add_routing_feedback_table

Revision ID: 3a66cc9bf18a
Revises: 003_feedback_tables
Create Date: 2025-11-16 09:40:19.623905

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a66cc9bf18a'
down_revision: Union[str, None] = '003_feedback_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create routing_feedback table and add request_id to routing_metrics."""

    # Step 1: Add request_id column to routing_metrics (if not exists)
    # This is needed for the FK from routing_feedback
    # Different syntax for SQLite vs PostgreSQL
    from alembic import context

    if context.get_bind().dialect.name == 'postgresql':
        op.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='routing_metrics' AND column_name='request_id'
                ) THEN
                    ALTER TABLE routing_metrics ADD COLUMN request_id TEXT UNIQUE;
                END IF;
            END $$;
        """)
    else:
        # SQLite: Try to add column, ignore if exists
        try:
            op.add_column('routing_metrics', sa.Column('request_id', sa.Text(), unique=True))
        except Exception:
            # Column already exists, continue
            pass

    # Step 2: Create routing_feedback table
    op.create_table(
        'routing_feedback',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('request_id', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('quality_score', sa.Integer(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('is_helpful', sa.Boolean(), nullable=True),
        sa.Column('prompt_pattern', sa.Text(), nullable=True),
        sa.Column('selected_provider', sa.Text(), nullable=True),
        sa.Column('selected_model', sa.Text(), nullable=True),
        sa.Column('complexity_score', sa.Float(), nullable=True),
        sa.Column('user_id', sa.Text(), nullable=True),
        sa.Column('session_id', sa.Text(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        # FK to routing_metrics
        sa.ForeignKeyConstraint(['request_id'], ['routing_metrics.request_id'])
    )

    # Step 3: Create indexes for performance
    op.create_index('idx_routing_feedback_pattern', 'routing_feedback', ['prompt_pattern'])
    op.create_index('idx_routing_feedback_provider', 'routing_feedback', ['selected_provider'])
    op.create_index('idx_routing_feedback_timestamp', 'routing_feedback', ['timestamp'])


def downgrade() -> None:
    """Drop routing_feedback table and remove request_id from routing_metrics."""
    # Drop indexes
    op.drop_index('idx_routing_feedback_timestamp', table_name='routing_feedback')
    op.drop_index('idx_routing_feedback_provider', table_name='routing_feedback')
    op.drop_index('idx_routing_feedback_pattern', table_name='routing_feedback')

    # Drop table
    op.drop_table('routing_feedback')

    # Note: We don't remove request_id from routing_metrics in downgrade
    # because it might be used by other parts of the system
