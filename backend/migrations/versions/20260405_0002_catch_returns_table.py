"""
Add catch_returns table for member catch-return entries

Revision ID: 20260405_0002
Revises: 20260405_0001
Create Date: 2026-04-05
"""

from alembic import op
import sqlalchemy as sa

revision = '20260405_0002'
down_revision = '20260405_0001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'catch_returns',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('club_id', sa.BigInteger(), sa.ForeignKey('clubs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('member_id', sa.BigInteger(), sa.ForeignKey('members.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_date', sa.Date(), nullable=False),
        sa.Column('beat_id', sa.String(length=64), nullable=False, server_default=''),
        sa.Column('small_trout', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('medium_trout', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('large_trout', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('small_grayling', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('medium_grayling', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('large_grayling', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('other_fish', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('flies_used', sa.Text(), nullable=False, server_default=''),
        sa.Column('weather_conditions', sa.Text(), nullable=False, server_default=''),
        sa.Column('predator_damage', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('small_trout >= 0', name='ck_catch_returns_small_trout_nonneg'),
        sa.CheckConstraint('medium_trout >= 0', name='ck_catch_returns_medium_trout_nonneg'),
        sa.CheckConstraint('large_trout >= 0', name='ck_catch_returns_large_trout_nonneg'),
        sa.CheckConstraint('small_grayling >= 0', name='ck_catch_returns_small_grayling_nonneg'),
        sa.CheckConstraint('medium_grayling >= 0', name='ck_catch_returns_medium_grayling_nonneg'),
        sa.CheckConstraint('large_grayling >= 0', name='ck_catch_returns_large_grayling_nonneg'),
        sa.CheckConstraint('other_fish >= 0', name='ck_catch_returns_other_fish_nonneg'),
    )
    op.create_index('ix_catch_returns_club_member_date', 'catch_returns', ['club_id', 'member_id', 'session_date'])


def downgrade():
    op.drop_index('ix_catch_returns_club_member_date', table_name='catch_returns')
    op.drop_table('catch_returns')
