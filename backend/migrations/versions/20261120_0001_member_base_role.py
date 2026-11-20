"""Explicit 'member' base role (CORE-35, #62)

Renames the base club role 'user' to 'member' and adds
member_role_assignments.source ('auto' rows are granted and revoked from
membership by db.postgres_backend.sync_member_roles; 'admin' rows were set in
the user/role screens and are left alone). Existing assignments become
'admin'. The member role rows themselves are created by the sync, which runs
at backend startup straight after this migration.

Revision ID: 20261120_0001
Revises: 20261118_0001
Create Date: 2026-11-20
"""

from alembic import op
import sqlalchemy as sa


revision = '20261120_0001'
down_revision = '20261118_0001'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE roles SET code = 'member', name = 'Member' "
        "WHERE code = 'user' AND NOT EXISTS (SELECT 1 FROM roles WHERE code = 'member')"
    ))
    conn.execute(sa.text(
        "INSERT INTO roles (code, name, scope_type, is_system) "
        "SELECT 'member', 'Member', 'club', TRUE "
        "WHERE NOT EXISTS (SELECT 1 FROM roles WHERE code = 'member')"
    ))
    conn.execute(sa.text(
        "ALTER TABLE member_role_assignments "
        "ADD COLUMN IF NOT EXISTS source VARCHAR(16) NOT NULL DEFAULT 'admin'"
    ))


def downgrade():
    conn = op.get_bind()
    # Remove the automatically managed member assignments, then restore the
    # old name. Admin-set member rows are kept and follow the rename.
    conn.execute(sa.text(
        "DELETE FROM member_role_assignments "
        "WHERE source = 'auto' AND role_id = (SELECT id FROM roles WHERE code = 'member')"
    ))
    op.drop_column('member_role_assignments', 'source')
    conn.execute(sa.text(
        "UPDATE roles SET code = 'user', name = 'User' "
        "WHERE code = 'member' AND NOT EXISTS (SELECT 1 FROM roles WHERE code = 'user')"
    ))
