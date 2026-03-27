"""
Alembic merge migration to resolve multiple heads after Option 3 migration.

Revision ID: 20260327_0001_merge_heads
Revises: 20260326_0001, 20260326_0007_add_user_type_to_sessions
Create Date: 2026-03-27
"""

revision = '20260327_0001_merge_heads'
down_revision = ('20260326_0001', '20260326_0007_add_user_type_to_sess')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
