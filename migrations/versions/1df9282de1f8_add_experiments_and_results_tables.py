"""add_experiments_and_results_tables

Revision ID: 1df9282de1f8
Revises: 3a66cc9bf18a
Create Date: 2025-11-16 11:12:05.091253

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1df9282de1f8'
down_revision: Union[str, None] = '3a66cc9bf18a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create experiments and experiment_results tables for A/B testing framework."""

    # Create experiments table
    op.create_table(
        'experiments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('control_strategy', sa.Text(), nullable=False),
        sa.Column('test_strategy', sa.Text(), nullable=False),
        sa.Column('sample_size', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('winner', sa.Text(), nullable=True),
        sa.CheckConstraint("status IN ('pending', 'active', 'completed', 'cancelled')", name='valid_experiment_status'),
        sa.CheckConstraint('sample_size > 0', name='positive_sample_size'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on status for fast active experiment queries
    op.create_index('idx_experiments_status', 'experiments', ['status'])

    # Create experiment_results table
    op.create_table(
        'experiment_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('strategy_assigned', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=False),
        sa.Column('cost_usd', sa.Float(), nullable=False),
        sa.Column('quality_score', sa.Integer(), nullable=True),
        sa.Column('provider', sa.Text(), nullable=False),
        sa.Column('model', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for fast aggregation queries
    op.create_index('idx_experiment_results_experiment_id', 'experiment_results', ['experiment_id'])
    op.create_index('idx_experiment_results_strategy', 'experiment_results', ['strategy_assigned'])
    op.create_index('idx_experiment_results_user_id', 'experiment_results', ['user_id'])


def downgrade() -> None:
    """Drop experiments and experiment_results tables."""

    # Drop indexes first
    op.drop_index('idx_experiment_results_user_id', table_name='experiment_results')
    op.drop_index('idx_experiment_results_strategy', table_name='experiment_results')
    op.drop_index('idx_experiment_results_experiment_id', table_name='experiment_results')

    # Drop tables (results first due to FK constraint)
    op.drop_table('experiment_results')

    op.drop_index('idx_experiments_status', table_name='experiments')
    op.drop_table('experiments')
