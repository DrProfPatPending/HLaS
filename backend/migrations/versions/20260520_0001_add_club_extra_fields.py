"""
Add whatsapp_groups, social_media, and officers columns to clubs

Revision ID: 20260520_0001
Revises: 20260512_0001
Create Date: 2026-05-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260520_0001'
down_revision = '20260512_0001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'clubs',
        sa.Column(
            'whatsapp_groups',
            sa.Text(),
            nullable=False,
            server_default='',
        ),
    )
    op.add_column(
        'clubs',
        sa.Column(
            'social_media',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        'clubs',
        sa.Column(
            'officers',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade():
    op.drop_column('clubs', 'officers')
    op.drop_column('clubs', 'social_media')
    op.drop_column('clubs', 'whatsapp_groups')
