"""
Add club_mini_sites table for configurable marketing pages

Revision ID: 20260504_0001
Revises: 20260421_0001
Create Date: 2026-05-04
"""

from alembic import op
import sqlalchemy as sa

revision = '20260504_0001'
down_revision = '20260421_0001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'club_mini_sites',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('club_id', sa.BigInteger(), sa.ForeignKey('clubs.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('title', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('tagline', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('hero_image_url', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('pages', sa.dialects.postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('social_links', sa.dialects.postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_club_mini_sites_club_id', 'club_mini_sites', ['club_id'])
    op.create_index('ix_club_mini_sites_enabled', 'club_mini_sites', ['enabled'])


def downgrade():
    op.drop_index('ix_club_mini_sites_enabled', table_name='club_mini_sites')
    op.drop_index('ix_club_mini_sites_club_id', table_name='club_mini_sites')
    op.drop_table('club_mini_sites')
