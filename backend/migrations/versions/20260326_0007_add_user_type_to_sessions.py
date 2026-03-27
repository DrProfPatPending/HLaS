"""
Revision ID: 20260326_0007_add_user_type_to_sessions
Revises: 20260318_0004_session_user_id_columns
Create Date: 2026-03-26
"""

revision = '20260326_0007_add_user_type_sess'
down_revision = '20260318_0004'
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE member_sessions ADD COLUMN IF NOT EXISTS user_type VARCHAR(16) DEFAULT 'member'"))
    conn.execute(text("ALTER TABLE member_refresh_sessions ADD COLUMN IF NOT EXISTS user_type VARCHAR(16) DEFAULT 'member'"))

def downgrade() -> None:
    op.drop_column("member_sessions", "user_type")
    op.drop_column("member_refresh_sessions", "user_type")
