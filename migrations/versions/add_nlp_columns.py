"""Add NLP keyword columns to property_listings

Revision ID: add_nlp_columns
Revises: add_scout_system
Create Date: 2025-09-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_nlp_columns'
down_revision = 'add_scout_system'
branch_labels = None
depends_on = None


def upgrade():
    # Add NLP keyword columns that are missing
    with op.batch_alter_table('property_listings') as batch:
        # Essential Attributes
        batch.add_column(sa.Column('has_natural_light_keywords', sa.Boolean(), nullable=False, server_default='false'))
        batch.add_column(sa.Column('has_high_ceiling_keywords', sa.Boolean(), nullable=False, server_default='false'))
        batch.add_column(sa.Column('has_outdoor_space_keywords', sa.Boolean(), nullable=False, server_default='false'))
        # Skip has_parking_keywords - already exists
        # Skip has_view_keywords - already exists
        # Skip has_updated_systems_keywords - already exists
        # Skip has_home_office_keywords - already exists
        # Skip has_storage_keywords - already exists
        # Skip has_open_floor_plan_keywords - already exists
        # Skip has_architectural_details_keywords - already exists
        # Skip has_luxury_keywords - already exists
        # Skip has_designer_keywords - already exists
        # Skip has_tech_ready_keywords - already exists
        # Skip is_price_reduced - already exists
        # Skip price_reduction_amount - already exists
        # Skip price_reduction_date - already exists
        # Skip is_back_on_market - already exists
        # Skip has_busy_street_keywords - already exists
        # Skip has_foundation_issues_keywords - already exists
        # Skip has_hoa_issues_keywords - already exists
        # Skip is_north_facing_only - already exists
        # Skip is_basement_unit - already exists


def downgrade():
    with op.batch_alter_table('property_listings') as batch:
        batch.drop_column('has_outdoor_space_keywords')
        batch.drop_column('has_high_ceiling_keywords')
        batch.drop_column('has_natural_light_keywords')