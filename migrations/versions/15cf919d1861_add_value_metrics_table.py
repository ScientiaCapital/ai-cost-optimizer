"""add value_metrics table

Revision ID: 15cf919d1861
Revises: 42c04c717aed
Create Date: 2025-10-30 17:21:38.812643

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15cf919d1861'
down_revision: Union[str, None] = '42c04c717aed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create value_metrics table for tracking cost savings and value delivered
    op.create_table(
        'value_metrics',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('query_type', sa.String()),
        sa.Column('complexity', sa.String()),
        sa.Column('selected_provider', sa.String()),
        sa.Column('selected_model', sa.String()),
        sa.Column('selected_cost', sa.Float()),
        sa.Column('baseline_provider', sa.String(), server_default='openai'),
        sa.Column('baseline_model', sa.String(), server_default='gpt-4'),
        sa.Column('baseline_cost', sa.Float()),
        sa.Column('savings', sa.Float())  # baseline_cost - selected_cost
    )

    # Create index for efficient querying by user and time
    op.create_index('ix_value_metrics_user_timestamp', 'value_metrics', ['user_id', 'timestamp'])


def downgrade() -> None:
    # Drop index first
    op.drop_index('ix_value_metrics_user_timestamp', table_name='value_metrics')

    # Drop table
    op.drop_table('value_metrics')
