"""Enforce user-centric constraints on member_role_assignments.

Revision ID: 20260318_0006
Revises: 20260318_0005
Create Date: 2026-03-18 23:25:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260318_0006"
down_revision = "20260318_0005"
branch_labels = None
depends_on = None


def upgrade():
    # Ensure user_id is populated from member_user_links before enforcing constraints.
    op.execute(sa.text("""
        UPDATE member_role_assignments mra
        SET user_id = mul.user_id
        FROM member_user_links mul
        WHERE mul.member_id = mra.member_id
          AND mra.user_id IS NULL
    """))

    # Abort with a clear message if unresolved rows still exist.
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM member_role_assignments
                WHERE user_id IS NULL
            ) THEN
                RAISE EXCEPTION 'Cannot enforce NOT NULL on member_role_assignments.user_id: unresolved rows remain';
            END IF;
        END
        $$;
    """))

    # De-duplicate active rows at user scope before adding unique indexes.
    op.execute(sa.text("""
        WITH ranked AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY user_id, role_id, club_id
                    ORDER BY granted_at DESC, id DESC
                ) AS rn
            FROM member_role_assignments
            WHERE revoked_at IS NULL
              AND club_id IS NOT NULL
        )
        UPDATE member_role_assignments mra
        SET revoked_at = NOW()
        FROM ranked
        WHERE ranked.id = mra.id
          AND ranked.rn > 1
    """))

    op.execute(sa.text("""
        WITH ranked AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY user_id, role_id
                    ORDER BY granted_at DESC, id DESC
                ) AS rn
            FROM member_role_assignments
            WHERE revoked_at IS NULL
              AND club_id IS NULL
        )
        UPDATE member_role_assignments mra
        SET revoked_at = NOW()
        FROM ranked
        WHERE ranked.id = mra.id
          AND ranked.rn > 1
    """))

    # Replace old member-scoped unique indexes with user-scoped unique indexes.
    op.execute(sa.text("DROP INDEX IF EXISTS uq_mra_member_role_club_active"))
    op.execute(sa.text("DROP INDEX IF EXISTS uq_mra_member_role_global_active"))

    op.execute(sa.text("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_mra_user_role_club_active
        ON member_role_assignments (user_id, role_id, club_id)
        WHERE club_id IS NOT NULL AND revoked_at IS NULL
    """))
    op.execute(sa.text("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_mra_user_role_global_active
        ON member_role_assignments (user_id, role_id)
        WHERE club_id IS NULL AND revoked_at IS NULL
    """))

    op.execute(sa.text("""
        ALTER TABLE member_role_assignments
        ALTER COLUMN user_id SET NOT NULL
    """))


def downgrade():
    op.execute(sa.text("""
        ALTER TABLE member_role_assignments
        ALTER COLUMN user_id DROP NOT NULL
    """))

    op.execute(sa.text("DROP INDEX IF EXISTS uq_mra_user_role_global_active"))
    op.execute(sa.text("DROP INDEX IF EXISTS uq_mra_user_role_club_active"))

    op.execute(sa.text("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_mra_member_role_club_active
        ON member_role_assignments (member_id, role_id, club_id)
        WHERE club_id IS NOT NULL AND revoked_at IS NULL
    """))
    op.execute(sa.text("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_mra_member_role_global_active
        ON member_role_assignments (member_id, role_id)
        WHERE club_id IS NULL AND revoked_at IS NULL
    """))
