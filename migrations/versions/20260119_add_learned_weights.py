"""Add learned_weights JSON column to users table.

Revision ID: 9f7a2b3c4d5e
Revises: 63d4be8ee48e
Create Date: 2026-01-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f7a2b3c4d5e'
down_revision = '63d4be8ee48e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add learned_weights column to users table
    # Structure: { "criterion_name": { "multiplier": float, "signal_count": int, "last_updated": str }, ... }
    op.add_column(
        'users',
        sa.Column('learned_weights', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('users', 'learned_weights')
