"""Remove legacy identity columns: member_role_assignments.member_id and app_users.legacy_member_id

These columns were used in Phase 1 (member-centric identity). Phase 2 is now fully in place:
- member_role_assignments keyed on user_id (NOT NULL, user-scoped unique indexes)
- member_user_links is the canonical member↔user mapping

Revision ID: 20260318_0007
Revises: 20260318_0006
Create Date: 2026-03-18 00:07:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260318_0007"
down_revision = "20260318_0006"
branch_labels = None
depends_on = None


def upgrade():
    # -----------------------------------------------------------------------
    # 1. Drop member_id from member_role_assignments
    # -----------------------------------------------------------------------
    # Drop the FK constraint first (auto-named by PG as <table>_<col>_fkey).
    op.execute(
        "ALTER TABLE member_role_assignments "
        "DROP CONSTRAINT IF EXISTS member_role_assignments_member_id_fkey"
    )
    # Drop the plain btree index on member_id (used for query perf).
    op.execute("DROP INDEX IF EXISTS ix_mra_member_id")
    # Drop the column itself.
    op.drop_column("member_role_assignments", "member_id")

    # -----------------------------------------------------------------------
    # 2. Drop legacy_member_id from app_users
    # -----------------------------------------------------------------------
    op.execute(
        "ALTER TABLE app_users "
        "DROP CONSTRAINT IF EXISTS uq_app_users_legacy_member_id"
    )
    op.execute(
        "ALTER TABLE app_users "
        "DROP CONSTRAINT IF EXISTS app_users_legacy_member_id_fkey"
    )
    op.drop_column("app_users", "legacy_member_id")


def downgrade():
    # Re-add columns as nullable (no data is restored).
    op.add_column(
        "app_users",
        sa.Column(
            "legacy_member_id",
            sa.BigInteger(),
            sa.ForeignKey("members.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_unique_constraint(
        "uq_app_users_legacy_member_id",
        "app_users",
        ["legacy_member_id"],
    )

    op.add_column(
        "member_role_assignments",
        sa.Column(
            "member_id",
            sa.BigInteger(),
            sa.ForeignKey("members.id", ondelete="CASCADE"),
            nullable=True,   # nullable on downgrade; NOT NULL cannot be restored without data
        ),
    )
    op.create_index(
        "ix_mra_member_id",
        "member_role_assignments",
        ["member_id"],
    )
