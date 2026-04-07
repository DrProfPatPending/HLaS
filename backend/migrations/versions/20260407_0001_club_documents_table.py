"""
Add club_documents table for club document storage

Revision ID: 20260407_0001
Revises: 20260405_0002
Create Date: 2026-04-07
"""

from alembic import op
import sqlalchemy as sa

revision = '20260407_0001'
down_revision = '20260405_0002'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'club_documents',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('club_id', sa.BigInteger(), sa.ForeignKey('clubs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('file_name', sa.String(length=512), nullable=False, server_default=''),
        sa.Column('file_ext', sa.String(length=16), nullable=False, server_default=''),
        sa.Column('mime_type', sa.String(length=128), nullable=False, server_default='application/octet-stream'),
        sa.Column('file_size', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('file_data', sa.LargeBinary(), nullable=False),
        sa.Column('uploaded_by_user_id', sa.BigInteger(), sa.ForeignKey('app_users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_club_documents_club_created', 'club_documents', ['club_id', 'created_at'])
    op.create_index('ix_club_documents_uploaded_by', 'club_documents', ['uploaded_by_user_id'])


def downgrade():
    op.drop_index('ix_club_documents_uploaded_by', table_name='club_documents')
    op.drop_index('ix_club_documents_club_created', table_name='club_documents')
    op.drop_table('club_documents')
