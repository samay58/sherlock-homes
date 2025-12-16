"""Add scout system and enhanced property matching

Revision ID: add_scout_system
Revises: 20250507_add_photos_json
Create Date: 2025-01-07

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_scout_system'
down_revision = '20250507_add_photos_json'
branch_labels = None
depends_on = None


def upgrade():
    # --- Criteria extensions ---
    with op.batch_alter_table('criteria') as batch:
        batch.add_column(sa.Column('beds_max', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('sqft_max', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('require_parking', sa.Boolean(), nullable=False, server_default='false'))
        batch.add_column(sa.Column('require_view', sa.Boolean(), nullable=False, server_default='false'))
        batch.add_column(sa.Column('require_updated_systems', sa.Boolean(), nullable=False, server_default='false'))
        batch.add_column(sa.Column('require_home_office', sa.Boolean(), nullable=False, server_default='false'))
        batch.add_column(sa.Column('require_storage', sa.Boolean(), nullable=False, server_default='false'))
        batch.add_column(sa.Column('min_walk_score', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('max_transit_distance', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('preferred_neighborhoods', sa.JSON(), nullable=True))
        batch.add_column(sa.Column('avoid_neighborhoods', sa.JSON(), nullable=True))
        batch.add_column(sa.Column('property_types', sa.JSON(), nullable=True))
        batch.add_column(sa.Column('parking_type', sa.String(50), nullable=True))
        batch.add_column(sa.Column('min_ceiling_height', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('architectural_styles', sa.JSON(), nullable=True))
        batch.add_column(sa.Column('include_price_reduced', sa.Boolean(), nullable=False, server_default='true'))
        batch.add_column(sa.Column('include_new_listings', sa.Boolean(), nullable=False, server_default='true'))
        batch.add_column(sa.Column('max_days_on_market', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('avoid_busy_streets', sa.Boolean(), nullable=False, server_default='true'))
        batch.add_column(sa.Column('avoid_north_facing_only', sa.Boolean(), nullable=False, server_default='true'))
        batch.add_column(sa.Column('avoid_basement_units', sa.Boolean(), nullable=False, server_default='true'))
        batch.add_column(sa.Column('excluded_streets', sa.JSON(), nullable=True))
        batch.add_column(sa.Column('scout_description', sa.Text(), nullable=True))
        batch.add_column(sa.Column('feature_weights', sa.JSON(), nullable=True))

    # --- Property listing columns ---
    with op.batch_alter_table('property_listings') as batch:
        batch.add_column(sa.Column('has_parking_keywords', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('has_view_keywords', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('has_updated_systems_keywords', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('has_home_office_keywords', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('has_storage_keywords', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('has_open_floor_plan_keywords', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('has_architectural_details_keywords', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('has_luxury_keywords', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('has_designer_keywords', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('has_tech_ready_keywords', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('is_price_reduced', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('price_reduction_amount', sa.Float(), nullable=True))
        batch.add_column(sa.Column('price_reduction_date', sa.DateTime(), nullable=True))
        batch.add_column(sa.Column('is_back_on_market', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('has_busy_street_keywords', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('has_foundation_issues_keywords', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('has_hoa_issues_keywords', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('is_north_facing_only', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('is_basement_unit', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('neighborhood', sa.String(100), nullable=True))
        batch.add_column(sa.Column('walk_score', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('transit_score', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('bike_score', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('parking_type', sa.String(50), nullable=True))
        batch.add_column(sa.Column('parking_spaces', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('has_ev_charging', sa.Boolean(), server_default='false'))
        batch.add_column(sa.Column('hoa_fee', sa.Float(), nullable=True))
        batch.add_column(sa.Column('hoa_includes', sa.JSON(), nullable=True))
        batch.add_column(sa.Column('lot_size', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('stories', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('architectural_style', sa.String(50), nullable=True))
        batch.add_column(sa.Column('listing_agent', sa.String(100), nullable=True))
        batch.add_column(sa.Column('listing_brokerage', sa.String(100), nullable=True))
        batch.add_column(sa.Column('match_score', sa.Float(), nullable=True))
        batch.add_column(sa.Column('feature_scores', sa.JSON(), nullable=True))

    # --- Scouts tables ---
    op.create_table(
        'scouts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('criteria_id', sa.Integer(), sa.ForeignKey('criteria.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('alert_frequency', sa.String(length=20), nullable=False, server_default='daily'),
        sa.Column('min_match_score', sa.Float(), nullable=False, server_default='60.0'),
        sa.Column('max_results_per_alert', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('search_keywords', sa.JSON(), nullable=True),
        sa.Column('search_neighborhoods', sa.JSON(), nullable=True),
        sa.Column('alert_email', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('alert_sms', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('alert_webhook', sa.String(length=500), nullable=True),
        sa.Column('last_run', sa.DateTime(), nullable=True),
        sa.Column('last_alert_sent', sa.DateTime(), nullable=True),
        sa.Column('total_matches_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_alerts_sent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('seen_listing_ids', sa.JSON(), nullable=True),
        sa.Column('positive_feedback_listings', sa.JSON(), nullable=True),
        sa.Column('negative_feedback_listings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index(op.f('ix_scouts_user_id'), 'scouts', ['user_id'], unique=False)

    op.create_table(
        'scout_runs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('scout_id', sa.Integer(), sa.ForeignKey('scouts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('started_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='running'),
        sa.Column('listings_evaluated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('matches_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('new_matches', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('alerts_sent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('matched_listings', sa.JSON(), nullable=True),
        sa.Column('top_score', sa.Float(), nullable=True),
        sa.Column('average_score', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
    )
    op.create_index(op.f('ix_scout_runs_scout_id'), 'scout_runs', ['scout_id'], unique=False)


def downgrade():
    # Drop scout tables
    op.drop_index(op.f('ix_scout_runs_scout_id'), table_name='scout_runs')
    op.drop_table('scout_runs')
    op.drop_index(op.f('ix_scouts_user_id'), table_name='scouts')
    op.drop_table('scouts')

    # Remove columns from property_listings
    with op.batch_alter_table('property_listings') as batch:
        batch.drop_column('feature_scores')
        batch.drop_column('match_score')
        batch.drop_column('listing_brokerage')
        batch.drop_column('listing_agent')
        batch.drop_column('architectural_style')
        batch.drop_column('stories')
        batch.drop_column('lot_size')
        batch.drop_column('hoa_includes')
        batch.drop_column('hoa_fee')
        batch.drop_column('has_ev_charging')
        batch.drop_column('parking_spaces')
        batch.drop_column('parking_type')
        batch.drop_column('bike_score')
        batch.drop_column('transit_score')
        batch.drop_column('neighborhood')
        batch.drop_column('is_basement_unit')
        batch.drop_column('is_north_facing_only')
        batch.drop_column('has_hoa_issues_keywords')
        batch.drop_column('has_foundation_issues_keywords')
        batch.drop_column('has_busy_street_keywords')
        batch.drop_column('is_back_on_market')
        batch.drop_column('price_reduction_date')
        batch.drop_column('price_reduction_amount')
        batch.drop_column('is_price_reduced')
        batch.drop_column('has_tech_ready_keywords')
        batch.drop_column('has_designer_keywords')
        batch.drop_column('has_luxury_keywords')
        batch.drop_column('has_architectural_details_keywords')
        batch.drop_column('has_open_floor_plan_keywords')
        batch.drop_column('has_storage_keywords')
        batch.drop_column('has_home_office_keywords')
        batch.drop_column('has_updated_systems_keywords')
        batch.drop_column('has_view_keywords')
        batch.drop_column('has_parking_keywords')

    # Remove columns from criteria
    with op.batch_alter_table('criteria') as batch:
        batch.drop_column('feature_weights')
        batch.drop_column('scout_description')
        batch.drop_column('excluded_streets')
        batch.drop_column('avoid_basement_units')
        batch.drop_column('avoid_north_facing_only')
        batch.drop_column('avoid_busy_streets')
        batch.drop_column('max_days_on_market')
        batch.drop_column('include_new_listings')
        batch.drop_column('include_price_reduced')
        batch.drop_column('architectural_styles')
        batch.drop_column('min_ceiling_height')
        batch.drop_column('parking_type')
        batch.drop_column('property_types')
        batch.drop_column('avoid_neighborhoods')
        batch.drop_column('preferred_neighborhoods')
        batch.drop_column('max_transit_distance')
        batch.drop_column('min_walk_score')
        batch.drop_column('require_storage')
        batch.drop_column('require_home_office')
        batch.drop_column('require_updated_systems')
        batch.drop_column('require_view')
        batch.drop_column('require_parking')
        batch.drop_column('sqft_max')
        batch.drop_column('beds_max')

