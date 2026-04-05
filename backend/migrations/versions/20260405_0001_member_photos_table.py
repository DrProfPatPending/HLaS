"""
Add member_photos table for storing member ID photos in PostgreSQL

Revision ID: 20260405_0001
Revises: 20260327_0001_merge_heads
Create Date: 2026-04-05
"""

from alembic import op
import sqlalchemy as sa

revision = '20260405_0001'
down_revision = '20260327_0001_merge_heads'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'member_photos',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('club_id', sa.BigInteger(), sa.ForeignKey('clubs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('member_id', sa.BigInteger(), sa.ForeignKey('members.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(length=512), nullable=False, server_default=''),
        sa.Column('mime_type', sa.String(length=64), nullable=False, server_default='image/jpeg'),
        sa.Column('image_data', sa.LargeBinary(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('member_id', name='uq_member_photos_member_id'),
    )
    op.create_index('ix_member_photos_club_id', 'member_photos', ['club_id'])
    op.create_index('ix_member_photos_club_filename', 'member_photos', ['club_id', 'filename'])


def downgrade():
    op.drop_index('ix_member_photos_club_filename', table_name='member_photos')
    op.drop_index('ix_member_photos_club_id', table_name='member_photos')
    op.drop_table('member_photos')
