"""
Add club_logos table for storing club logo images as BLOBs

Revision ID: 20260325_0001
Revises: 20260318_0007_remove_legacy_columns
Create Date: 2026-03-25
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        "club_logos",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("club_short_name", sa.String(length=32), nullable=False, unique=True),
        sa.Column("image_data", sa.LargeBinary(), nullable=False),
        sa.Column("mime_type", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

def downgrade():
    op.drop_table("club_logos")
