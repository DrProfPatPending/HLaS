"""Merge heads 20260602_0001 and 20260613_0001

Revision ID: 20260613_0002
Revises: 20260602_0001, 20260613_0001
Create Date: 2026-06-13 17:40:00
"""

from typing import Sequence, Union


revision: str = "20260613_0002"
down_revision: Union[str, Sequence[str], None] = ("20260602_0001", "20260613_0001")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Merge migration: no-op on schema/data.
    pass


def downgrade() -> None:
    # Merge migration: no-op on schema/data.
    pass
