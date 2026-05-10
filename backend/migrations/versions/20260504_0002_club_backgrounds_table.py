"""
Add club_backgrounds table for storing club background images as BLOBs

Revision ID: 20260504_0002
Revises: 20260504_0001
Create Date: 2026-05-04
"""

revision = '20260504_0002'
down_revision = '20260504_0001'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "club_backgrounds",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("club_short_name", sa.String(length=32), nullable=False, unique=True),
        sa.Column("image_data", sa.LargeBinary(), nullable=False),
        sa.Column("mime_type", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_club_backgrounds_club_short_name", "club_backgrounds", ["club_short_name"], unique=True)


def downgrade():
    op.drop_table("club_backgrounds")
