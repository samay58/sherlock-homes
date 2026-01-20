"""Add matching quality fields to criteria.

Revision ID: matching_quality_001
Revises: listing_events_001
Create Date: 2025-12-20
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "matching_quality_001"
down_revision = "listing_events_001"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {col["name"] for col in inspector.get_columns("criteria")}
    if "price_soft_max" not in columns:
        op.add_column("criteria", sa.Column("price_soft_max", sa.Float(), nullable=True))
    if "neighborhood_mode" not in columns:
        op.add_column("criteria", sa.Column("neighborhood_mode", sa.String(length=20), nullable=True))
    if "recency_mode" not in columns:
        op.add_column("criteria", sa.Column("recency_mode", sa.String(length=20), nullable=True))


def downgrade():
    op.drop_column("criteria", "recency_mode")
    op.drop_column("criteria", "neighborhood_mode")
    op.drop_column("criteria", "price_soft_max")
