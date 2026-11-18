"""Add comments to catch_returns

Revision ID: 20261118_0001
Revises: 20260730_0001
Create Date: 2026-11-18
"""

from alembic import op
import sqlalchemy as sa


revision = '20261118_0001'
down_revision = '20260730_0001'
branch_labels = None
depends_on = None


def upgrade():
	op.add_column(
		'catch_returns',
		sa.Column('comments', sa.Text(), nullable=False, server_default=''),
	)


def downgrade():
	op.drop_column('catch_returns', 'comments')
