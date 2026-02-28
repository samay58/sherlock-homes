from alembic import op
import sqlalchemy as sa

revision = "2eaa91ec76da"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("email", sa.String(length=255), nullable=False, unique=True),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
        )

    if "criteria" not in tables:
        op.create_table(
            "criteria",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False, server_default=sa.text("'My Criteria'")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("price_min", sa.Float(), nullable=True),
            sa.Column("price_max", sa.Float(), nullable=True),
            sa.Column("beds_min", sa.Integer(), nullable=True),
            sa.Column("baths_min", sa.Float(), nullable=True),
            sa.Column("sqft_min", sa.Integer(), nullable=True),
            sa.Column("require_natural_light", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("require_high_ceilings", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("require_outdoor_space", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )

    if "property_listings" not in tables:
        op.create_table(
            "property_listings",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("address", sa.String(length=255), nullable=False),
            sa.Column("price", sa.Float(), nullable=False),
            sa.Column("beds", sa.Integer(), nullable=True),
            sa.Column("baths", sa.Float(), nullable=True),
            sa.Column("sqft", sa.Integer(), nullable=True),
            sa.Column("property_type", sa.String(length=50), nullable=True),
            sa.Column("url", sa.String(length=500), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), server_default=sa.text("'active'")),
            sa.Column("days_on_market", sa.Integer(), nullable=True),
            sa.Column("last_updated", sa.DateTime(), nullable=True),
        )


def downgrade():
    op.execute("DROP TABLE IF EXISTS property_listings")
    op.execute("DROP TABLE IF EXISTS criteria")
    op.execute("DROP TABLE IF EXISTS users")
