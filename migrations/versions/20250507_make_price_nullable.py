from alembic import op
import sqlalchemy as sa

revision = "20250507_make_price_nullable"
down_revision = "20250507_add_provider_columns"
branch_labels = None
depends_on = None


def upgrade():
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("property_listings") as batch:
            batch.alter_column("price", existing_type=sa.Float(), nullable=True)
    else:
        op.alter_column("property_listings", "price", existing_type=sa.Float(), nullable=True)


def downgrade():
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("property_listings") as batch:
            batch.alter_column("price", existing_type=sa.Float(), nullable=False)
    else:
        op.alter_column("property_listings", "price", existing_type=sa.Float(), nullable=False)
