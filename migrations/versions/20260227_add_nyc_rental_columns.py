"""Add NYC rental feature columns to property_listings.

Columns were present in the SQLAlchemy model but missing from Alembic
migrations (worked locally via SQLite create_all but not on PostgreSQL).

Revision ID: nyc_rental_cols_001
Revises: 9f7a2b3c4d5e
Create Date: 2026-02-27
"""
from alembic import op
import sqlalchemy as sa

revision = "nyc_rental_cols_001"
down_revision = "9f7a2b3c4d5e"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("property_listings")}

    with op.batch_alter_table("property_listings") as batch:
        if "is_pet_friendly" not in columns:
            batch.add_column(sa.Column("is_pet_friendly", sa.Boolean(), server_default="false"))
        if "is_no_pets" not in columns:
            batch.add_column(sa.Column("is_no_pets", sa.Boolean(), server_default="false"))
        if "has_gym_keywords" not in columns:
            batch.add_column(sa.Column("has_gym_keywords", sa.Boolean(), server_default="false"))
        if "has_doorman_keywords" not in columns:
            batch.add_column(sa.Column("has_doorman_keywords", sa.Boolean(), server_default="false"))
        if "has_building_quality_keywords" not in columns:
            batch.add_column(sa.Column("has_building_quality_keywords", sa.Boolean(), server_default="false"))


def downgrade():
    with op.batch_alter_table("property_listings") as batch:
        batch.drop_column("has_building_quality_keywords")
        batch.drop_column("has_doorman_keywords")
        batch.drop_column("has_gym_keywords")
        batch.drop_column("is_no_pets")
        batch.drop_column("is_pet_friendly")
