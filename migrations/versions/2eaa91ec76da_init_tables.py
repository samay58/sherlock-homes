from alembic import op
import sqlalchemy as sa

revision = "2eaa91ec76da"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Idempotent base creation (handles partially created DBs)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            hashed_password VARCHAR(255) NOT NULL
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS criteria (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL DEFAULT 'My Criteria',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            price_min FLOAT,
            price_max FLOAT,
            beds_min INTEGER,
            baths_min FLOAT,
            sqft_min INTEGER,
            require_natural_light BOOLEAN NOT NULL DEFAULT FALSE,
            require_high_ceilings BOOLEAN NOT NULL DEFAULT FALSE,
            require_outdoor_space BOOLEAN NOT NULL DEFAULT FALSE
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS property_listings (
            id SERIAL PRIMARY KEY,
            address VARCHAR(255) NOT NULL,
            price FLOAT NOT NULL,
            beds INTEGER,
            baths FLOAT,
            sqft INTEGER,
            property_type VARCHAR(50),
            url VARCHAR(500) NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'active',
            days_on_market INTEGER,
            last_updated TIMESTAMP
        );
        """
    )


def downgrade():
    op.execute("DROP TABLE IF EXISTS property_listings")
    op.execute("DROP TABLE IF EXISTS criteria")
    op.execute("DROP TABLE IF EXISTS users")
