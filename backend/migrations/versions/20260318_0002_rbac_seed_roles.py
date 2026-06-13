"""Seed RBAC system roles and optional bootstrap app_owner assignment

Revision ID: 20260318_0002
Revises: 20260318_0001
Create Date: 2026-03-18 00:05:00

Bootstrap:
    Set env var HLAS_BOOTSTRAP_OWNER_USERNAME to the username (or email) of
    an existing member before running this migration to assign them as the
    first app_owner.

    If no env var is set the roles are still seeded but no assignment is
    created.  The app_owner can be assigned later via the role management API.
"""

from __future__ import annotations

import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = "20260318_0002"
down_revision: Union[str, Sequence[str], None] = "20260318_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# System role catalog — order matters for ROLE_HIERARCHY in security layer
# ---------------------------------------------------------------------------
SYSTEM_ROLES = [
    {
        "code": "user",
        "name": "User",
        "scope_type": "club",
        "is_system": True,
    },
    {
        "code": "committee",
        "name": "Committee",
        "scope_type": "club",
        "is_system": True,
    },
    {
        "code": "club_admin",
        "name": "Club Admin",
        "scope_type": "club",
        "is_system": True,
    },
    {
        "code": "club_manager",
        "name": "Club Manager",
        "scope_type": "club",
        "is_system": True,
    },
    {
        "code": "app_admin",
        "name": "App Admin",
        "scope_type": "global",
        "is_system": True,
    },
    {
        "code": "app_owner",
        "name": "App Owner",
        "scope_type": "global",
        "is_system": True,
    },
]


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 1. Seed system roles (idempotent)
    # ------------------------------------------------------------------
    for role in SYSTEM_ROLES:
        conn.execute(
            text(
                """
                INSERT INTO roles (code, name, scope_type, is_system)
                VALUES (:code, :name, :scope_type, :is_system)
                ON CONFLICT (code) DO UPDATE
                    SET name       = EXCLUDED.name,
                        scope_type = EXCLUDED.scope_type,
                        is_system  = EXCLUDED.is_system
                """
            ),
            role,
        )

    # ------------------------------------------------------------------
    # 2. Optional bootstrap: assign app_owner to a specific member
    # ------------------------------------------------------------------
    bootstrap_username = (
        os.getenv("HLAS_BOOTSTRAP_OWNER_USERNAME", "").strip()
        or os.getenv("HLAS_BOOTSTRAP_OWNER_EMAIL", "").strip()
    )

    if not bootstrap_username:
        print(
            "\nNOTICE: RBAC roles seeded. No HLAS_BOOTSTRAP_OWNER_USERNAME set — "
            "no app_owner assignment created. Assign one via the role management "
            "API or re-run with the env var set.\n"
        )
        return

    # Resolve the member by username or email
    member_row = conn.execute(
        text(
            """
            SELECT id, username, email, members_name
            FROM   members
            WHERE  username = :val OR email = :val
            LIMIT  1
            """
        ),
        {"val": bootstrap_username},
    ).fetchone()

    if member_row is None:
        print(
            f"\nWARNING: HLAS_BOOTSTRAP_OWNER_USERNAME='{bootstrap_username}' "
            "did not match any member (username or email). "
            "No app_owner assignment created.\n"
        )
        return

    member_id = member_row.id
    member_display = member_row.members_name or member_row.username or str(member_id)

    # Resolve app_owner role id
    role_row = conn.execute(
        text("SELECT id FROM roles WHERE code = 'app_owner'")
    ).fetchone()
    if role_row is None:
        raise RuntimeError("app_owner role not found — roles seed failed")

    role_id = role_row.id

    # Check if assignment already exists (idempotent)
    existing = conn.execute(
        text(
            """
            SELECT id FROM member_role_assignments
            WHERE  member_id = :member_id
              AND  role_id   = :role_id
              AND  club_id   IS NULL
              AND  revoked_at IS NULL
            """
        ),
        {"member_id": member_id, "role_id": role_id},
    ).fetchone()

    if existing:
        print(
            f"\nNOTICE: Member '{member_display}' already holds an active "
            "app_owner assignment — skipping.\n"
        )
        return

    # Create the global app_owner assignment (no club_id = global scope)
    conn.execute(
        text(
            """
            INSERT INTO member_role_assignments
                (member_id, role_id, club_id, granted_by_member_id)
            VALUES
                (:member_id, :role_id, NULL, NULL)
            """
        ),
        {"member_id": member_id, "role_id": role_id},
    )

    # Log the bootstrap in the audit log
    conn.execute(
        text(
            """
            INSERT INTO security_audit_log
                (actor_member_id, action, target_type, target_id, club_id, metadata)
            VALUES
                (NULL, 'role.grant', 'member', :member_id, NULL,
                 jsonb_build_object(
                     'role_code',      'app_owner',
                     'granted_to',     :member_display,
                     'bootstrap',      true
                 ))
            """
        ),
        {"member_id": member_id, "member_display": member_display},
    )

    print(
        f"\nSUCCESS: Member '{member_display}' (id={member_id}) assigned "
        "as app_owner.\n"
    )


def downgrade() -> None:
    conn = op.get_bind()
    # Remove all seeded system roles and any assignments created by this migration.
    # This cascades to member_role_assignments via FK ON DELETE CASCADE.
    conn.execute(text("DELETE FROM roles WHERE is_system = TRUE"))
    # Clear the bootstrap audit entry
    conn.execute(
        text(
            "DELETE FROM security_audit_log WHERE action = 'role.grant' "
            "AND metadata->>'bootstrap' = 'true'"
        )
    )
