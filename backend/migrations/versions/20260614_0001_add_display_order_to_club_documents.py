"""Add display_order to club_documents

Revision ID: 20260614_0001
Revises: 20260613_0002
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa


revision = '20260614_0001'
down_revision = '20260613_0002'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'club_documents',
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
    )
    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY club_id
                    ORDER BY created_at DESC, id DESC
                ) AS row_num
            FROM club_documents
        )
        UPDATE club_documents AS d
        SET display_order = ranked.row_num
        FROM ranked
        WHERE d.id = ranked.id
        """
    )
    op.create_index(
        'ix_club_documents_club_display_order',
        'club_documents',
        ['club_id', 'display_order', 'id'],
    )


def downgrade():
    op.drop_index('ix_club_documents_club_display_order', table_name='club_documents')
    op.drop_column('club_documents', 'display_order')
