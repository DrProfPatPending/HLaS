"""Add RBAC tables: roles, member_role_assignments, security_audit_log

Revision ID: 20260318_0001
Revises: 20260317_0002
Create Date: 2026-03-18 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260318_0001"
down_revision: Union[str, Sequence[str], None] = "20260317_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # roles — catalog of role definitions (5 built-in system roles)
    # ------------------------------------------------------------------
    op.create_table(
        "roles",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        # 'global' roles apply across all clubs; 'club' roles are scoped to one
        sa.Column("scope_type", sa.String(length=16), nullable=False, server_default="club"),
        # True for the five hard-coded roles seeded next migration
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("code", name="uq_roles_code"),
    )

    # ------------------------------------------------------------------
    # member_role_assignments — links a member to a role, optionally
    # scoped to a specific club (club_id = NULL means global scope).
    # ------------------------------------------------------------------
    op.create_table(
        "member_role_assignments",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("member_id", sa.BigInteger(), nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        sa.Column("club_id", sa.BigInteger(), nullable=True),
        sa.Column("granted_by_member_id", sa.BigInteger(), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        # NULL = active assignment. Set to revoke without destroying history.
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by_member_id"], ["members.id"], ondelete="SET NULL"),
    )

    # Partial unique indexes handle NULLable club_id correctly: two NULL club_id
    # values are not equal under a standard UNIQUE constraint in PostgreSQL, so
    # we use separate partial indexes for club-scoped and global assignments.
    op.create_index(
        "uq_mra_member_role_club_active",
        "member_role_assignments",
        ["member_id", "role_id", "club_id"],
        unique=True,
        postgresql_where=sa.text("club_id IS NOT NULL AND revoked_at IS NULL"),
    )
    op.create_index(
        "uq_mra_member_role_global_active",
        "member_role_assignments",
        ["member_id", "role_id"],
        unique=True,
        postgresql_where=sa.text("club_id IS NULL AND revoked_at IS NULL"),
    )
    op.create_index("ix_mra_member_id", "member_role_assignments", ["member_id"])
    op.create_index("ix_mra_club_role", "member_role_assignments", ["club_id", "role_id"])

    # ------------------------------------------------------------------
    # security_audit_log — immutable ledger of security-relevant events
    # ------------------------------------------------------------------
    op.create_table(
        "security_audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        # NULL for system-generated actions (migrations, bootstrap)
        sa.Column("actor_member_id", sa.BigInteger(), nullable=True),
        # e.g. 'role.grant', 'role.revoke', 'member.delete', 'club.create'
        sa.Column("action", sa.String(length=64), nullable=False),
        # 'member', 'club', 'role_assignment', 'setting'
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=True),
        # NULL for app-level events
        sa.Column("club_id", sa.BigInteger(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["actor_member_id"], ["members.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_sal_actor_member_id", "security_audit_log", ["actor_member_id"])
    # Descending composite index — created via raw SQL because Alembic's
    # create_index helper does not support per-column DESC expressions.
    op.execute(
        "CREATE INDEX ix_sal_action_created_at "
        "ON security_audit_log (action, created_at DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_sal_action_created_at")
    op.drop_index("ix_sal_actor_member_id", table_name="security_audit_log")
    op.drop_table("security_audit_log")

    op.drop_index("ix_mra_club_role", table_name="member_role_assignments")
    op.drop_index("ix_mra_member_id", table_name="member_role_assignments")
    op.drop_index("uq_mra_member_role_global_active", table_name="member_role_assignments")
    op.drop_index("uq_mra_member_role_club_active", table_name="member_role_assignments")
    op.drop_table("member_role_assignments")

    op.drop_table("roles")
