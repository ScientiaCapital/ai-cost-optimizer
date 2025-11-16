"""Add feedback tables for learning pipeline

Revision ID: 003_feedback_tables
Revises: 15cf919d1861
Create Date: 2025-11-08
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '003_feedback_tables'
down_revision = '15cf919d1861'
branch_labels = None
depends_on = None


def upgrade():
    """Create feedback and model performance tables."""

    # response_feedback table already exists from initial migration
    # Add new columns to existing table if needed
    # Note: The initial migration created response_feedback with different structure
    # This migration adds the model_performance_history table only

    # Create model_performance_history table
    op.create_table(
        'model_performance_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('pattern', sa.Text(), nullable=False),
        sa.Column('provider', sa.Text(), nullable=False),
        sa.Column('model', sa.Text(), nullable=False),

        # Computed metrics
        sa.Column('avg_quality_score', sa.Float(), nullable=True),
        sa.Column('correctness_rate', sa.Float(), nullable=True),
        sa.Column('sample_count', sa.Integer(), nullable=True),
        sa.Column('confidence_level', sa.Text(), nullable=True),

        # Cost tracking
        sa.Column('avg_cost', sa.Float(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=True),

        # Metadata
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('retraining_run_id', sa.Text(), nullable=True),

        sa.UniqueConstraint('pattern', 'provider', 'model', 'retraining_run_id',
                          name='uq_model_performance')
    )


def downgrade():
    """Drop feedback tables."""
    op.drop_table('model_performance_history')
    # response_feedback table is managed by initial migration, don't drop it here
