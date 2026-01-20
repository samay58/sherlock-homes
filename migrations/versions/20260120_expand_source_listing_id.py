"""Expand source_listing_id length for multi-source URLs.

Revision ID: listing_sources_002
Revises: listing_sources_001
Create Date: 2026-01-20
"""

from alembic import op
import sqlalchemy as sa


revision = "listing_sources_002"
down_revision = "listing_sources_001"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {col["name"] for col in inspector.get_columns("property_listings")}
    if "source_listing_id" in columns:
        with op.batch_alter_table("property_listings") as batch:
            batch.alter_column(
                "source_listing_id",
                existing_type=sa.String(length=128),
                type_=sa.String(length=512),
            )


def downgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {col["name"] for col in inspector.get_columns("property_listings")}
    if "source_listing_id" in columns:
        with op.batch_alter_table("property_listings") as batch:
            batch.alter_column(
                "source_listing_id",
                existing_type=sa.String(length=512),
                type_=sa.String(length=128),
            )
