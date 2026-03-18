"""Add user_id column to member_role_assignments and backfill from member_user_links.

This links each role assignment to the central app_users record, enabling
user-centric role management that survives future identity merges.

Revision ID: 20260318_0005
Revises: 20260318_0004
"""
from alembic import op
import sqlalchemy as sa

revision = '20260318_0005'
down_revision = '20260318_0004'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.text("""
        ALTER TABLE member_role_assignments
        ADD COLUMN IF NOT EXISTS user_id BIGINT REFERENCES app_users(id) ON DELETE SET NULL
    """))
    op.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_mra_user_id
        ON member_role_assignments (user_id)
    """))
    op.execute(sa.text("""
        UPDATE member_role_assignments mra
        SET user_id = mul.user_id
        FROM member_user_links mul
        WHERE mul.member_id = mra.member_id
          AND mra.user_id IS NULL
    """))


def downgrade():
    op.execute(sa.text("DROP INDEX IF EXISTS ix_mra_user_id"))
    op.execute(sa.text(
        "ALTER TABLE member_role_assignments DROP COLUMN IF EXISTS user_id"
    ))
