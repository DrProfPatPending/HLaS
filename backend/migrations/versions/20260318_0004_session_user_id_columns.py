"""Phase 2b: add user_id to session token tables

Revision ID: 20260318_0004
Revises: 20260318_0003
Create Date: 2026-03-18 22:45:00
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = "20260318_0004"
down_revision: Union[str, Sequence[str], None] = "20260318_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS member_sessions (
                token_hash VARCHAR(64) PRIMARY KEY,
                member_id INTEGER NOT NULL,
                club_short_name VARCHAR(64) NOT NULL,
                username VARCHAR(255),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                expires_at TIMESTAMPTZ NOT NULL,
                last_seen_at TIMESTAMPTZ,
                revoked_at TIMESTAMPTZ
            )
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS member_refresh_sessions (
                refresh_token_hash VARCHAR(64) PRIMARY KEY,
                member_id INTEGER NOT NULL,
                club_short_name VARCHAR(64) NOT NULL,
                username VARCHAR(255),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                expires_at TIMESTAMPTZ NOT NULL,
                last_seen_at TIMESTAMPTZ,
                revoked_at TIMESTAMPTZ
            )
            """
        )
    )

    conn.execute(text("ALTER TABLE member_sessions ADD COLUMN IF NOT EXISTS user_id BIGINT"))
    conn.execute(text("ALTER TABLE member_refresh_sessions ADD COLUMN IF NOT EXISTS user_id BIGINT"))

    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_member_sessions_user_id ON member_sessions (user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_member_refresh_sessions_user_id ON member_refresh_sessions (user_id)"))


def downgrade() -> None:
    op.drop_index("ix_member_refresh_sessions_user_id", table_name="member_refresh_sessions")
    op.drop_index("ix_member_sessions_user_id", table_name="member_sessions")

    op.drop_column("member_refresh_sessions", "user_id")
    op.drop_column("member_sessions", "user_id")
