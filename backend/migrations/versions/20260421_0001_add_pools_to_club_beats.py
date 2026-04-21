"""
Add pools JSON column to club_beats

Revision ID: 20260421_0001
Revises: 20260407_0001
Create Date: 2026-04-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260421_0001'
down_revision = '20260407_0001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'club_beats',
        sa.Column(
            'pools',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade():
    op.drop_column('club_beats', 'pools')
