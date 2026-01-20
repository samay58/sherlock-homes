from alembic import op
import sqlalchemy as sa

revision = "20250507_add_photos_json"
down_revision = "20250507_make_price_nullable"
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("property_listings")}
    if "photos" not in columns:
        op.add_column("property_listings", sa.Column("photos", sa.JSON(), nullable=True))

def downgrade():
    op.drop_column("property_listings", "photos") 
