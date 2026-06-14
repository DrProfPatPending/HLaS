"""Add club_field_order table for per-club field-order configuration

Revision ID: 20260614_0001
Revises: 20260613_0001
Create Date: 2026-06-14 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text


revision: str = "20260614_0001"
down_revision: Union[str, Sequence[str], None] = "20260613_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "club_field_order",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("club_id", sa.BigInteger(), sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("club_id", name="uq_club_field_order_club_id"),
    )
    op.create_index("ix_club_field_order_club_id", "club_field_order", ["club_id"])

    conn = op.get_bind()
    conn.execute(
        text(
            """
            INSERT INTO club_field_order (club_id, config)
            SELECT c.id, COALESCE(a.value, '{}'::jsonb)
            FROM clubs c
            LEFT JOIN app_settings a
              ON a.scope = 'global' AND a.key = 'field_order'
            WHERE c.is_active = TRUE
            ON CONFLICT (club_id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_club_field_order_club_id", table_name="club_field_order")
    op.drop_table("club_field_order")
