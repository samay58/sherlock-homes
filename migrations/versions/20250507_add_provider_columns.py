from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250507_add_provider_columns"
down_revision = "2eaa91ec76da"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("property_listings")}
    indexes = {idx["name"] for idx in inspector.get_indexes("property_listings")}
    add_listing_id = "listing_id" not in columns
    with op.batch_alter_table("property_listings") as batch:
        if add_listing_id:
            batch.add_column(sa.Column("listing_id", sa.String(length=64), nullable=True))
        if "lat" not in columns:
            batch.add_column(sa.Column("lat", sa.Float(), nullable=True))
        if "lon" not in columns:
            batch.add_column(sa.Column("lon", sa.Float(), nullable=True))
        if "year_built" not in columns:
            batch.add_column(sa.Column("year_built", sa.Integer(), nullable=True))
        if "listing_status" not in columns:
            batch.add_column(sa.Column("listing_status", sa.String(length=20), nullable=True))
        if "ix_property_listings_listing_id" not in indexes:
            batch.create_index("ix_property_listings_listing_id", ["listing_id"], unique=True)


def downgrade():
    with op.batch_alter_table("property_listings") as batch:
        batch.drop_index("ix_property_listings_listing_id")
        batch.drop_column("listing_status")
        batch.drop_column("year_built")
        batch.drop_column("lon")
        batch.drop_column("lat")
        batch.drop_column("listing_id") 
