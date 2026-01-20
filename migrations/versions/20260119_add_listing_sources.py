"""Add source tracking fields for multi-provider listings.

Revision ID: listing_sources_001
Revises: matching_quality_001
Create Date: 2026-01-19
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "listing_sources_001"
down_revision = "matching_quality_001"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {col["name"] for col in inspector.get_columns("property_listings")}
    uniques = {uc["name"] for uc in inspector.get_unique_constraints("property_listings")}
    with op.batch_alter_table("property_listings") as batch:
        if "source" not in columns:
            batch.add_column(sa.Column("source", sa.String(length=32), nullable=True))
        if "source_listing_id" not in columns:
            batch.add_column(sa.Column("source_listing_id", sa.String(length=128), nullable=True))
        if "sources_seen" not in columns:
            batch.add_column(sa.Column("sources_seen", sa.JSON(), nullable=True))
        if "last_seen_at" not in columns:
            batch.add_column(sa.Column("last_seen_at", sa.DateTime(), nullable=True))
        if "uq_property_listings_source_listing_id" not in uniques:
            batch.create_unique_constraint(
                "uq_property_listings_source_listing_id",
                ["source", "source_listing_id"],
            )


def downgrade():
    with op.batch_alter_table("property_listings") as batch:
        batch.drop_constraint("uq_property_listings_source_listing_id", type_="unique")
        batch.drop_column("last_seen_at")
        batch.drop_column("sources_seen")
        batch.drop_column("source_listing_id")
        batch.drop_column("source")
