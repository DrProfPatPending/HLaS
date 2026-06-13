"""Add committee club role to RBAC catalog

Revision ID: 20260613_0001
Revises: 20260520_0001
Create Date: 2026-06-13 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = "20260613_0001"
down_revision: Union[str, Sequence[str], None] = "20260520_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text(
            """
            INSERT INTO roles (code, name, scope_type, is_system)
            VALUES ('committee', 'Committee', 'club', TRUE)
            ON CONFLICT (code) DO UPDATE
                SET name       = EXCLUDED.name,
                    scope_type = EXCLUDED.scope_type,
                    is_system  = EXCLUDED.is_system
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM roles WHERE code = 'committee'"))
