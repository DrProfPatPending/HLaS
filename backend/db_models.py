from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

metadata = MetaData()

app_settings = Table(
    "app_settings",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("scope", String(32), nullable=False, server_default="global"),
    Column("key", String(120), nullable=False),
    Column("value", JSONB, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint("scope", "key", name="uq_app_settings_scope_key"),
)

clubs = Table(
    "clubs",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("short_name", String(32), nullable=False, unique=True),
    Column("full_name", String(120), nullable=False),
    Column("description", Text, nullable=False, server_default=""),
    Column("website_url", String(255), nullable=False, server_default=""),
    Column("admin_email", String(255), nullable=False, server_default=""),
    Column("logo_url", String(255), nullable=False, server_default=""),
    Column("is_active", Boolean, nullable=False, server_default="true"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

club_smtp_settings = Table(
    "club_smtp_settings",
    metadata,
    Column("club_id", BigInteger, ForeignKey("clubs.id", ondelete="CASCADE"), primary_key=True),
    Column("host", String(255), nullable=False, server_default=""),
    Column("port", Integer, nullable=False, server_default="587"),
    Column("username", String(255), nullable=False, server_default=""),
    Column("password", String(255), nullable=False, server_default=""),
    Column("from_email", String(255), nullable=False, server_default=""),
    Column("from_name", String(255), nullable=False, server_default=""),
    Column("use_ssl", Boolean, nullable=False, server_default="false"),
    Column("use_tls", Boolean, nullable=False, server_default="true"),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

club_beats = Table(
    "club_beats",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("club_id", BigInteger, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
    Column("beat_name", String(255), nullable=False, server_default=""),
    Column("beat_id", String(64), nullable=False, server_default=""),
    Column("river", String(255), nullable=False, server_default=""),
    Column("position", String(120), nullable=False, server_default=""),
    Column("beat_upstream", String(120), nullable=False, server_default=""),
    Column("beat_downstream", String(120), nullable=False, server_default=""),
    Column("beat_description", Text, nullable=False, server_default=""),
    Column("detailed_description", Text, nullable=False, server_default=""),
    Column("beat_upstream_latitude", String(64), nullable=False, server_default=""),
    Column("beat_upstream_longitude", String(64), nullable=False, server_default=""),
    Column("beat_downstream_latitude", String(64), nullable=False, server_default=""),
    Column("beat_downstream_longitude", String(64), nullable=False, server_default=""),
    Column("parking_locations", JSONB, nullable=False, server_default="[]"),
    Column("pools", JSONB, nullable=False, server_default="[]"),
    Column("waypoints", JSONB, nullable=False, server_default="[]"),
    UniqueConstraint("club_id", "beat_id", name="uq_club_beats_club_id_beat_id"),
)

beat_map_rotations = Table(
    "beat_map_rotations",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("beat_id", BigInteger, ForeignKey("club_beats.id", ondelete="CASCADE"), nullable=False, unique=True),
    Column("rotation_bearing", Integer, nullable=False, server_default="0"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

members = Table(
    "members",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("club_id", BigInteger, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
    Column("legacy_id", String(64), nullable=False, server_default=""),
    Column("number", String(64), nullable=False, server_default=""),
    Column("members_name", String(255), nullable=False, server_default=""),
    Column("title", String(64), nullable=False, server_default=""),
    Column("first_name", String(120), nullable=False, server_default=""),
    Column("last_name", String(120), nullable=False, server_default=""),
    Column("photo_path", String(512), nullable=False, server_default=""),
    Column("preferred_name", String(120), nullable=False, server_default=""),
    Column("first_names", String(255), nullable=False, server_default=""),
    Column("paused", String(32), nullable=False, server_default=""),
    Column("resigned", String(32), nullable=False, server_default=""),
    Column("member_type", String(120), nullable=False, server_default=""),
    Column("subs_expected", String(64), nullable=False, server_default=""),
    Column("subs_paid", String(64), nullable=False, server_default=""),
    Column("join_fee", String(64), nullable=False, server_default=""),
    Column("paid_up_2026", String(64), nullable=False, server_default=""),
    Column("photo_received", String(64), nullable=False, server_default=""),
    Column("in_whatsapp", String(64), nullable=False, server_default=""),
    Column("in_fb", String(64), nullable=False, server_default=""),
    Column("date_of_birth", Date, nullable=True),
    Column("age", String(32), nullable=False, server_default=""),
    Column("new_member_2026", String(64), nullable=False, server_default=""),
    Column("paid_up_card_sent", String(64), nullable=False, server_default=""),
    Column("cr2023", String(64), nullable=False, server_default=""),
    Column("cr2024", String(64), nullable=False, server_default=""),
    Column("cr2025", String(64), nullable=False, server_default=""),
    Column("details_confirmed_2026", String(64), nullable=False, server_default=""),
    Column("full_address", Text, nullable=False, server_default=""),
    Column("address_street", String(255), nullable=False, server_default=""),
    Column("address_line_2", String(255), nullable=False, server_default=""),
    Column("address_city", String(120), nullable=False, server_default=""),
    Column("county", String(120), nullable=False, server_default=""),
    Column("address_state_region", String(120), nullable=False, server_default=""),
    Column("address_zip_postal", String(64), nullable=False, server_default=""),
    Column("address_country", String(120), nullable=False, server_default=""),
    Column("phone", String(64), nullable=False, server_default=""),
    Column("mobile", String(64), nullable=False, server_default=""),
    Column("email", String(255), nullable=False, server_default=""),
    Column("ea_licence", String(64), nullable=False, server_default=""),
    Column("licence_exp", String(64), nullable=False, server_default=""),
    Column("car_reg", String(64), nullable=False, server_default=""),
    Column("username", String(255), nullable=False, server_default=""),
    Column("password", String(255), nullable=False, server_default=""),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint("club_id", "number", name="uq_members_club_number"),
)

app_users = Table(
    "app_users",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("username", String(255), nullable=False, server_default=""),
    Column("email", String(255), nullable=False, server_default=""),
    Column("display_name", String(255), nullable=False, server_default=""),
    Column("password_hash", String(255), nullable=False, server_default=""),
    Column("is_active", Boolean, nullable=False, server_default="true"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

member_user_links = Table(
    "member_user_links",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("user_id", BigInteger, ForeignKey("app_users.id", ondelete="CASCADE"), nullable=False),
    Column("member_id", BigInteger, ForeignKey("members.id", ondelete="CASCADE"), nullable=False),
    Column("club_id", BigInteger, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
    Column("is_primary", Boolean, nullable=False, server_default="true"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint("member_id", name="uq_member_user_links_member_id"),
    UniqueConstraint("user_id", "member_id", name="uq_member_user_links_user_member"),
)

member_photos = Table(
    "member_photos",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("club_id", BigInteger, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
    Column("member_id", BigInteger, ForeignKey("members.id", ondelete="CASCADE"), nullable=False),
    Column("filename", String(512), nullable=False, server_default=""),
    Column("mime_type", String(64), nullable=False, server_default="image/jpeg"),
    Column("image_data", LargeBinary, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint("member_id", name="uq_member_photos_member_id"),
)

catch_returns = Table(
    "catch_returns",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("club_id", BigInteger, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
    Column("member_id", BigInteger, ForeignKey("members.id", ondelete="CASCADE"), nullable=False),
    Column("session_date", Date, nullable=False),
    Column("beat_id", String(64), nullable=False, server_default=""),
    Column("small_trout", Integer, nullable=False, server_default="0"),
    Column("medium_trout", Integer, nullable=False, server_default="0"),
    Column("large_trout", Integer, nullable=False, server_default="0"),
    Column("small_grayling", Integer, nullable=False, server_default="0"),
    Column("medium_grayling", Integer, nullable=False, server_default="0"),
    Column("large_grayling", Integer, nullable=False, server_default="0"),
    Column("other_fish", Integer, nullable=False, server_default="0"),
    Column("flies_used", Text, nullable=False, server_default=""),
    Column("weather_conditions", Text, nullable=False, server_default=""),
    Column("predator_damage", Text, nullable=False, server_default=""),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

club_documents = Table(
    "club_documents",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("club_id", BigInteger, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
    Column("title", String(255), nullable=False, server_default=""),
    Column("file_name", String(512), nullable=False, server_default=""),
    Column("file_ext", String(16), nullable=False, server_default=""),
    Column("mime_type", String(128), nullable=False, server_default="application/octet-stream"),
    Column("file_size", BigInteger, nullable=False, server_default="0"),
    Column("file_data", LargeBinary, nullable=False),
    Column("uploaded_by_user_id", BigInteger, ForeignKey("app_users.id", ondelete="SET NULL"), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

newsletter_templates = Table(
    "newsletter_templates",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("club_id", BigInteger, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
    Column("template_key", String(120), nullable=False, server_default=""),
    Column("name", String(255), nullable=False),
    Column("subject", Text, nullable=False),
    Column("body", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint("club_id", "template_key", name="uq_newsletter_templates_club_template_key"),
)

# ---------------------------------------------------------------------------
# RBAC tables
# ---------------------------------------------------------------------------

roles = Table(
    "roles",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("code", String(32), nullable=False, unique=True),
    Column("name", String(120), nullable=False),
    # 'global' roles apply across all clubs; 'club' roles are scoped to one club
    Column("scope_type", String(16), nullable=False, server_default="club"),
    # True for the five built-in roles seeded by migration
    Column("is_system", Boolean, nullable=False, server_default="false"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

member_role_assignments = Table(
    "member_role_assignments",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("user_id", BigInteger, ForeignKey("app_users.id", ondelete="SET NULL"), nullable=True),
    Column("role_id", BigInteger, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
    # NULL for globally-scoped roles (app_admin, app_owner)
    Column("club_id", BigInteger, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=True),
    Column("granted_by_member_id", BigInteger, ForeignKey("members.id", ondelete="SET NULL"), nullable=True),
    Column("granted_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    # NULL = active; set to revoke without deleting history
    Column("revoked_at", DateTime(timezone=True), nullable=True),
    # Uniqueness is enforced via partial indexes in the migration,
    # not a standard UniqueConstraint, due to nullable club_id.
)

club_logos = Table(
    "club_logos",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("club_short_name", String(32), unique=True, nullable=False),
    Column("image_data", LargeBinary, nullable=False),
    Column("mime_type", String(64), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

club_backgrounds = Table(
    "club_backgrounds",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("club_short_name", String(32), unique=True, nullable=False),
    Column("image_data", LargeBinary, nullable=False),
    Column("mime_type", String(64), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

club_mini_sites = Table(
    "club_mini_sites",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("club_id", BigInteger, ForeignKey("clubs.id", ondelete="CASCADE"), unique=True, nullable=False),
    Column("enabled", Boolean, nullable=False, server_default="false"),
    Column("title", String(255), nullable=False, server_default=""),
    Column("tagline", String(255), nullable=False, server_default=""),
    Column("hero_image_url", String(255), nullable=False, server_default=""),
    Column("description", Text, nullable=False, server_default=""),
    Column("pages", JSONB, nullable=False, server_default="[]"),
    Column("social_links", JSONB, nullable=False, server_default="{}"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

security_audit_log = Table(
    "security_audit_log",
    metadata,
    Column("id", BigInteger, primary_key=True),
    # NULL for system-generated actions (bootstrap, migrations)
    Column("actor_member_id", BigInteger, ForeignKey("members.id", ondelete="SET NULL"), nullable=True),
    # e.g. 'role.grant', 'role.revoke', 'member.delete', 'club.create'
    Column("action", String(64), nullable=False),
    # 'member', 'club', 'role_assignment', 'setting'
    Column("target_type", String(32), nullable=False),
    Column("target_id", BigInteger, nullable=True),
    # NULL for app-level events
    Column("club_id", BigInteger, ForeignKey("clubs.id", ondelete="SET NULL"), nullable=True),
    Column("metadata", JSONB, nullable=False, server_default="{}"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
