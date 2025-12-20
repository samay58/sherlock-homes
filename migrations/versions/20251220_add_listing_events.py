"""Add listing snapshots and events for change tracking.

Revision ID: listing_events_001
Revises: visual_scoring_001
Create Date: 2025-12-20
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "listing_events_001"
down_revision = "visual_scoring_001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "listing_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("property_listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_hash", sa.String(length=64), nullable=False),
        sa.Column("snapshot_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_listing_snapshots_listing_id", "listing_snapshots", ["listing_id"])
    op.create_index("ix_listing_snapshots_snapshot_hash", "listing_snapshots", ["snapshot_hash"])
    op.create_index("ix_listing_snapshots_created_at", "listing_snapshots", ["created_at"])

    op.create_table(
        "listing_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("property_listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("old_value", sa.JSON(), nullable=True),
        sa.Column("new_value", sa.JSON(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_listing_events_listing_id", "listing_events", ["listing_id"])
    op.create_index("ix_listing_events_event_type", "listing_events", ["event_type"])
    op.create_index("ix_listing_events_created_at", "listing_events", ["created_at"])


def downgrade():
    op.drop_index("ix_listing_events_created_at", table_name="listing_events")
    op.drop_index("ix_listing_events_event_type", table_name="listing_events")
    op.drop_index("ix_listing_events_listing_id", table_name="listing_events")
    op.drop_table("listing_events")

    op.drop_index("ix_listing_snapshots_created_at", table_name="listing_snapshots")
    op.drop_index("ix_listing_snapshots_snapshot_hash", table_name="listing_snapshots")
    op.drop_index("ix_listing_snapshots_listing_id", table_name="listing_snapshots")
    op.drop_table("listing_snapshots")
