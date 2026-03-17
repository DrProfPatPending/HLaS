"""Initial PostgreSQL baseline schema

Revision ID: 20260317_0001
Revises:
Create Date: 2026-03-17 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260317_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("scope", sa.String(length=32), nullable=False, server_default="global"),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("scope", "key", name="uq_app_settings_scope_key"),
    )

    op.create_table(
        "clubs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("short_name", sa.String(length=32), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("website_url", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("admin_email", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("logo_url", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("short_name", name="uq_clubs_short_name"),
    )

    op.create_table(
        "club_smtp_settings",
        sa.Column("club_id", sa.BigInteger(), nullable=False),
        sa.Column("host", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("port", sa.Integer(), nullable=False, server_default="587"),
        sa.Column("username", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("password", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("from_email", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("from_name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("use_ssl", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("use_tls", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("club_id"),
    )

    op.create_table(
        "club_beats",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("club_id", sa.BigInteger(), nullable=False),
        sa.Column("beat_name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("beat_id", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("river", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("position", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("beat_upstream", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("beat_downstream", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("beat_description", sa.Text(), nullable=False, server_default=""),
        sa.Column("detailed_description", sa.Text(), nullable=False, server_default=""),
        sa.Column("beat_upstream_latitude", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("beat_upstream_longitude", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("beat_downstream_latitude", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("beat_downstream_longitude", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("parking_locations", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("club_id", "beat_id", name="uq_club_beats_club_id_beat_id"),
    )

    op.create_table(
        "members",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("club_id", sa.BigInteger(), nullable=False),
        sa.Column("legacy_id", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("number", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("members_name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("title", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("first_name", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("last_name", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("photo_path", sa.String(length=512), nullable=False, server_default=""),
        sa.Column("preferred_name", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("first_names", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("paused", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("resigned", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("member_type", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("subs_expected", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("subs_paid", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("join_fee", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("paid_up_2026", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("photo_received", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("in_whatsapp", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("in_fb", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("age", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("new_member_2026", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("paid_up_card_sent", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("cr2023", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("cr2024", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("cr2025", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("details_confirmed_2026", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("full_address", sa.Text(), nullable=False, server_default=""),
        sa.Column("address_street", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("address_line_2", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("address_city", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("county", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("address_state_region", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("address_zip_postal", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("address_country", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("phone", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("mobile", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("email", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("ea_licence", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("licence_exp", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("car_reg", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("username", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("password", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("club_id", "number", name="uq_members_club_number"),
    )

    op.create_table(
        "newsletter_templates",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("club_id", sa.BigInteger(), nullable=False),
        sa.Column("template_key", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("club_id", "template_key", name="uq_newsletter_templates_club_template_key"),
    )

    op.create_index("ix_members_club_id", "members", ["club_id"])
    op.create_index("ix_members_club_number", "members", ["club_id", "number"])
    op.create_index("ix_newsletter_templates_club_id", "newsletter_templates", ["club_id"])
    op.create_index("ix_club_beats_club_id", "club_beats", ["club_id"])


def downgrade() -> None:
    op.drop_index("ix_club_beats_club_id", table_name="club_beats")
    op.drop_index("ix_newsletter_templates_club_id", table_name="newsletter_templates")
    op.drop_index("ix_members_club_number", table_name="members")
    op.drop_index("ix_members_club_id", table_name="members")
    op.drop_table("newsletter_templates")
    op.drop_table("members")
    op.drop_table("club_beats")
    op.drop_table("club_smtp_settings")
    op.drop_table("clubs")
    op.drop_table("app_settings")
