"""Phase 2 foundation: add global users and member-user links

Revision ID: 20260318_0003
Revises: 20260318_0002
Create Date: 2026-03-18 22:20:00

This migration is intentionally non-breaking:
- Current auth continues to work from members/member_sessions.
- New tables are populated from members in a 1:1 shape for now.
- Later Phase 2 migrations can merge multiple member rows into one app_user.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = "20260318_0003"
down_revision: Union[str, Sequence[str], None] = "20260318_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("legacy_member_id", sa.BigInteger(), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("email", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("display_name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("password_hash", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["legacy_member_id"], ["members.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("legacy_member_id", name="uq_app_users_legacy_member_id"),
    )

    op.create_index("ix_app_users_username", "app_users", ["username"])
    op.create_index("ix_app_users_email", "app_users", ["email"])

    op.create_table(
        "member_user_links",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("member_id", sa.BigInteger(), nullable=False),
        sa.Column("club_id", sa.BigInteger(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["user_id"], ["app_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("member_id", name="uq_member_user_links_member_id"),
        sa.UniqueConstraint("user_id", "member_id", name="uq_member_user_links_user_member"),
    )

    op.create_index("ix_member_user_links_user_id", "member_user_links", ["user_id"])
    op.create_index("ix_member_user_links_club_id", "member_user_links", ["club_id"])

    conn = op.get_bind()

    conn.execute(
        text(
            """
            INSERT INTO app_users (legacy_member_id, username, email, display_name, password_hash, is_active)
            SELECT
                m.id,
                COALESCE(m.username, ''),
                COALESCE(m.email, ''),
                COALESCE(NULLIF(m.members_name, ''), NULLIF(m.username, ''), CONCAT('member-', m.id::text)),
                COALESCE(m.password, ''),
                TRUE
            FROM members m
            ON CONFLICT (legacy_member_id) DO NOTHING
            """
        )
    )

    conn.execute(
        text(
            """
            INSERT INTO member_user_links (user_id, member_id, club_id, is_primary)
            SELECT
                au.id,
                m.id,
                m.club_id,
                TRUE
            FROM members m
            JOIN app_users au ON au.legacy_member_id = m.id
            ON CONFLICT (member_id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_member_user_links_club_id", table_name="member_user_links")
    op.drop_index("ix_member_user_links_user_id", table_name="member_user_links")
    op.drop_table("member_user_links")

    op.drop_index("ix_app_users_email", table_name="app_users")
    op.drop_index("ix_app_users_username", table_name="app_users")
    op.drop_table("app_users")
