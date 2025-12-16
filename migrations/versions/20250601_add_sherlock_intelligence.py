"""Add Sherlock Homes intelligence columns

Revision ID: sherlock_intel_001
Revises: add_nlp_columns
Create Date: 2025-06-01

Adds cached intelligence scores for the Sherlock Homes Deduction Engine:
- tranquility_score: Geospatial noise analysis (0-100)
- tranquility_factors: JSON with distance to busy streets, freeways, etc.
- light_potential_score: NLP-based light analysis (0-100)
- light_potential_signals: JSON with keywords and factors that contributed
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'sherlock_intel_001'
down_revision = 'add_nlp_columns'
branch_labels = None
depends_on = None


def upgrade():
    # Add Sherlock Homes intelligence columns
    op.add_column(
        'property_listings',
        sa.Column('tranquility_score', sa.Integer(), nullable=True)
    )
    op.add_column(
        'property_listings',
        sa.Column('tranquility_factors', sa.JSON(), nullable=True)
    )
    op.add_column(
        'property_listings',
        sa.Column('light_potential_score', sa.Integer(), nullable=True)
    )
    op.add_column(
        'property_listings',
        sa.Column('light_potential_signals', sa.JSON(), nullable=True)
    )


def downgrade():
    op.drop_column('property_listings', 'light_potential_signals')
    op.drop_column('property_listings', 'light_potential_score')
    op.drop_column('property_listings', 'tranquility_factors')
    op.drop_column('property_listings', 'tranquility_score')
