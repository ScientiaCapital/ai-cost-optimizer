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

    # Create response_feedback table
    op.create_table(
        'response_feedback',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('request_id', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),

        # User ratings
        sa.Column('quality_score', sa.Integer(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('is_helpful', sa.Boolean(), nullable=True),

        # Context for learning
        sa.Column('prompt_pattern', sa.Text(), nullable=True),
        sa.Column('selected_provider', sa.Text(), nullable=True),
        sa.Column('selected_model', sa.Text(), nullable=True),
        sa.Column('complexity_score', sa.Float(), nullable=True),

        # Metadata
        sa.Column('user_id', sa.Text(), nullable=True),
        sa.Column('session_id', sa.Text(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
    )

    # Create indexes
    op.create_index('idx_feedback_pattern', 'response_feedback', ['prompt_pattern'])
    op.create_index('idx_feedback_model', 'response_feedback', ['selected_model'])
    op.create_index('idx_feedback_timestamp', 'response_feedback', ['timestamp'])

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
    op.drop_index('idx_feedback_timestamp', 'response_feedback')
    op.drop_index('idx_feedback_model', 'response_feedback')
    op.drop_index('idx_feedback_pattern', 'response_feedback')
    op.drop_table('response_feedback')
