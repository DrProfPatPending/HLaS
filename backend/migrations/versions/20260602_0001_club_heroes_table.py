"""
Add club_heroes table for storing club hero images as BLOBs

Revision ID: 20260602_0001
Revises: 20260520_0001
Create Date: 2026-06-02
"""

revision = '20260602_0001'
down_revision = '20260520_0001'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "club_heroes" not in inspector.get_table_names():
        op.create_table(
            "club_heroes",
            sa.Column("id", sa.BigInteger(), primary_key=True),
            sa.Column("club_short_name", sa.String(length=32), nullable=False, unique=True),
            sa.Column("image_data", sa.LargeBinary(), nullable=False),
            sa.Column("mime_type", sa.String(length=64), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )

    index_names = {idx.get("name") for idx in inspector.get_indexes("club_heroes")}
    if "ix_club_heroes_club_short_name" not in index_names:
        op.create_index("ix_club_heroes_club_short_name", "club_heroes", ["club_short_name"], unique=True)


def downgrade():
    op.drop_table("club_heroes")
