"""add_listing_feedback

Revision ID: 63d4be8ee48e
Revises: listing_sources_002
Create Date: 2026-01-19 21:54:06.205776

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '63d4be8ee48e'
down_revision = 'listing_sources_002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create listing_feedback table
    op.create_table(
        'listing_feedback',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('listing_id', sa.Integer(), sa.ForeignKey('property_listings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('feedback_type', sa.String(20), nullable=False),  # 'like', 'dislike', 'neutral'
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('listing_id', 'user_id', name='uq_listing_user_feedback'),
    )
    op.create_index('ix_listing_feedback_listing_id', 'listing_feedback', ['listing_id'])
    op.create_index('ix_listing_feedback_user_id', 'listing_feedback', ['user_id'])
    op.create_index('ix_listing_feedback_created_at', 'listing_feedback', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_listing_feedback_created_at', table_name='listing_feedback')
    op.drop_index('ix_listing_feedback_user_id', table_name='listing_feedback')
    op.drop_index('ix_listing_feedback_listing_id', table_name='listing_feedback')
    op.drop_table('listing_feedback')
