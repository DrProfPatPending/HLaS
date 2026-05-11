"""
Add waypoints JSON column to club_beats

Revision ID: 20260511_0001
Revises: 20260504_0002
Create Date: 2026-05-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260511_0001'
down_revision = '20260504_0002'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'club_beats',
        sa.Column(
            'waypoints',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade():
    op.drop_column('club_beats', 'waypoints')
