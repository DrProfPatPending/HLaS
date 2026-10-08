"""Add content_scope to club_documents

Revision ID: 20260730_0001
Revises: 20260615_0001
Create Date: 2026-07-30
"""

from alembic import op
import sqlalchemy as sa


revision = '20260730_0001'
down_revision = '20260615_0001'
branch_labels = None
depends_on = None


def upgrade():
	op.add_column(
		'club_documents',
		sa.Column('content_scope', sa.String(length=32), nullable=False, server_default='home'),
	)
	op.execute("UPDATE club_documents SET content_scope = 'home' WHERE content_scope IS NULL OR content_scope = ''")
	op.create_index(
		'ix_club_documents_club_scope_display_order',
		'club_documents',
		['club_id', 'content_scope', 'display_order', 'id'],
	)


def downgrade():
	op.drop_index('ix_club_documents_club_scope_display_order', table_name='club_documents')
	op.drop_column('club_documents', 'content_scope')
