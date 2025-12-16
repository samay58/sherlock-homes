"""Add visual scoring columns for photo analysis

Revision ID: visual_scoring_001
Revises: sherlock_intel_001
Create Date: 2025-12-05

Adds visual quality scoring from Claude Vision photo analysis:
- visual_quality_score: Overall visual appeal (0-100)
- visual_assessment: JSON with dimension scores and signals
- photos_hash: SHA256 hash for cache invalidation
- visual_analyzed_at: Timestamp of last analysis
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'visual_scoring_001'
down_revision = 'sherlock_intel_001'
branch_labels = None
depends_on = None


def upgrade():
    # Add visual scoring columns
    op.add_column(
        'property_listings',
        sa.Column('visual_quality_score', sa.Integer(), nullable=True)
    )
    op.add_column(
        'property_listings',
        sa.Column('visual_assessment', sa.JSON(), nullable=True)
    )
    op.add_column(
        'property_listings',
        sa.Column('photos_hash', sa.String(64), nullable=True)
    )
    op.add_column(
        'property_listings',
        sa.Column('visual_analyzed_at', sa.DateTime(), nullable=True)
    )


def downgrade():
    op.drop_column('property_listings', 'visual_analyzed_at')
    op.drop_column('property_listings', 'photos_hash')
    op.drop_column('property_listings', 'visual_assessment')
    op.drop_column('property_listings', 'visual_quality_score')
