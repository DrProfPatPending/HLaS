"""Seed PostgreSQL from legacy JSON + SQLite sources

Revision ID: 20260317_0002
Revises: 20260317_0001
Create Date: 2026-03-17 00:30:00
"""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import sqlite3
from typing import Any

from alembic import op
import sqlalchemy as sa

revision = "20260317_0002"
down_revision = "20260317_0001"
branch_labels = None
depends_on = None


DEFAULT_NEWSLETTER_TEMPLATES = [
    {
        "template_key": "club-update",
        "name": "Club Update",
        "subject": "<Club> Newsletter Update",
        "body": (
            "Dear <Title> <Last_Name>,\n\n"
            "This is your latest newsletter update from <Club>.\n\n"
            "Your membership number is <Number>.\n\n"
            "Kind regards,\n"
            "<Club> Committee"
        ),
    },
    {
        "template_key": "membership-reminder",
        "name": "Membership Reminder",
        "subject": "<Club> Membership Reminder",
        "body": (
            "Hello <Preferred_Name>,\n\n"
            "This is a friendly reminder from <Club> regarding your membership renewal.\n\n"
            "Name:   <Members_Name>\n"
            "Number: <Number>\n\n"
            "Please ensure your subscription is up to date.\n\n"
            "Kind regards,\n"
            "<Club> Committee"
        ),
    },
]


def _backend_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _legacy_data_dir() -> Path:
    raw_path = os.getenv("LEGACY_DATA_DIR") or os.getenv("HLAS_DATA_DIR")
    if raw_path:
        return Path(raw_path)
    return _backend_dir()


def _read_json_file(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def _safe_json(value: Any, fallback: Any) -> Any:
    if value is None:
        return fallback
    return value


def _parse_date(value: Any):
    text = _safe_str(value)
    if not text:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return None


def _sqlite_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cur.fetchone() is not None


def upgrade() -> None:
    bind = op.get_bind()

    app_settings = sa.table(
        "app_settings",
        sa.column("scope", sa.String()),
        sa.column("key", sa.String()),
        sa.column("value", sa.JSON()),
    )
    clubs = sa.table(
        "clubs",
        sa.column("id", sa.BigInteger()),
        sa.column("short_name", sa.String()),
        sa.column("full_name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("website_url", sa.String()),
        sa.column("admin_email", sa.String()),
        sa.column("logo_url", sa.String()),
        sa.column("is_active", sa.Boolean()),
    )
    club_smtp_settings = sa.table(
        "club_smtp_settings",
        sa.column("club_id", sa.BigInteger()),
        sa.column("host", sa.String()),
        sa.column("port", sa.Integer()),
        sa.column("username", sa.String()),
        sa.column("password", sa.String()),
        sa.column("from_email", sa.String()),
        sa.column("from_name", sa.String()),
        sa.column("use_ssl", sa.Boolean()),
        sa.column("use_tls", sa.Boolean()),
    )
    club_beats = sa.table(
        "club_beats",
        sa.column("club_id", sa.BigInteger()),
        sa.column("beat_name", sa.String()),
        sa.column("beat_id", sa.String()),
        sa.column("river", sa.String()),
        sa.column("position", sa.String()),
        sa.column("beat_upstream", sa.String()),
        sa.column("beat_downstream", sa.String()),
        sa.column("beat_description", sa.Text()),
        sa.column("detailed_description", sa.Text()),
        sa.column("beat_upstream_latitude", sa.String()),
        sa.column("beat_upstream_longitude", sa.String()),
        sa.column("beat_downstream_latitude", sa.String()),
        sa.column("beat_downstream_longitude", sa.String()),
        sa.column("parking_locations", sa.JSON()),
    )
    members = sa.table(
        "members",
        sa.column("club_id", sa.BigInteger()),
        sa.column("legacy_id", sa.String()),
        sa.column("number", sa.String()),
        sa.column("members_name", sa.String()),
        sa.column("title", sa.String()),
        sa.column("first_name", sa.String()),
        sa.column("last_name", sa.String()),
        sa.column("photo_path", sa.String()),
        sa.column("preferred_name", sa.String()),
        sa.column("first_names", sa.String()),
        sa.column("paused", sa.String()),
        sa.column("resigned", sa.String()),
        sa.column("member_type", sa.String()),
        sa.column("subs_expected", sa.String()),
        sa.column("subs_paid", sa.String()),
        sa.column("join_fee", sa.String()),
        sa.column("paid_up_2026", sa.String()),
        sa.column("photo_received", sa.String()),
        sa.column("in_whatsapp", sa.String()),
        sa.column("in_fb", sa.String()),
        sa.column("date_of_birth", sa.Date()),
        sa.column("age", sa.String()),
        sa.column("new_member_2026", sa.String()),
        sa.column("paid_up_card_sent", sa.String()),
        sa.column("cr2023", sa.String()),
        sa.column("cr2024", sa.String()),
        sa.column("cr2025", sa.String()),
        sa.column("details_confirmed_2026", sa.String()),
        sa.column("full_address", sa.Text()),
        sa.column("address_street", sa.String()),
        sa.column("address_line_2", sa.String()),
        sa.column("address_city", sa.String()),
        sa.column("county", sa.String()),
        sa.column("address_state_region", sa.String()),
        sa.column("address_zip_postal", sa.String()),
        sa.column("address_country", sa.String()),
        sa.column("phone", sa.String()),
        sa.column("mobile", sa.String()),
        sa.column("email", sa.String()),
        sa.column("ea_licence", sa.String()),
        sa.column("licence_exp", sa.String()),
        sa.column("car_reg", sa.String()),
        sa.column("username", sa.String()),
        sa.column("password", sa.String()),
    )
    newsletter_templates = sa.table(
        "newsletter_templates",
        sa.column("club_id", sa.BigInteger()),
        sa.column("template_key", sa.String()),
        sa.column("name", sa.String()),
        sa.column("subject", sa.Text()),
        sa.column("body", sa.Text()),
    )

    already_seeded = bind.execute(sa.text("SELECT COUNT(*) FROM clubs")).scalar_one()
    if already_seeded and int(already_seeded) > 0:
        return

    legacy_dir = _legacy_data_dir()
    server_config = _read_json_file(legacy_dir / "server.config.json", {})
    clubs_payload = _read_json_file(legacy_dir / "clubs.config.json", {"clubs": []})
    clubs_list = clubs_payload.get("clubs", []) if isinstance(clubs_payload, dict) else []

    bind.execute(
        app_settings.insert().values(
            scope="global",
            key="server_config",
            value=_safe_json(server_config, {}),
        )
    )

    club_id_by_short_name: dict[str, int] = {}

    for club in clubs_list:
        short_name = _safe_str(club.get("shortName"))
        if not short_name:
            continue

        inserted_club_id = bind.execute(
            clubs.insert()
            .values(
                short_name=short_name,
                full_name=_safe_str(club.get("fullName")) or short_name,
                description=_safe_str(club.get("description")),
                website_url=_safe_str(club.get("websiteUrl")),
                admin_email=_safe_str(club.get("adminEmail")),
                logo_url=_safe_str(club.get("logoUrl")),
                is_active=True,
            )
            .returning(clubs.c.id)
        ).scalar_one()

        club_id = int(inserted_club_id)
        club_id_by_short_name[short_name] = club_id

        smtp = club.get("smtp") if isinstance(club.get("smtp"), dict) else {}
        smtp_port_text = _safe_str(smtp.get("port"))
        try:
            smtp_port = int(smtp_port_text) if smtp_port_text else 587
        except ValueError:
            smtp_port = 587

        bind.execute(
            club_smtp_settings.insert().values(
                club_id=club_id,
                host=_safe_str(smtp.get("host")),
                port=smtp_port,
                username=_safe_str(smtp.get("username")),
                password=_safe_str(smtp.get("password")),
                from_email=_safe_str(smtp.get("fromEmail")) or _safe_str(club.get("adminEmail")),
                from_name=_safe_str(smtp.get("fromName")) or f"{short_name} Newsletter",
                use_ssl=_safe_bool(smtp.get("useSsl"), False),
                use_tls=_safe_bool(smtp.get("useTls"), True),
            )
        )

        beats = club.get("beats") if isinstance(club.get("beats"), list) else []
        beat_rows = []
        for beat in beats:
            if not isinstance(beat, dict):
                continue
            beat_rows.append(
                {
                    "club_id": club_id,
                    "beat_name": _safe_str(beat.get("Beat_Name")),
                    "beat_id": _safe_str(beat.get("Beat_ID")),
                    "river": _safe_str(beat.get("River")),
                    "position": _safe_str(beat.get("Position")),
                    "beat_upstream": _safe_str(beat.get("Beat_Upstream")),
                    "beat_downstream": _safe_str(beat.get("Beat_Downstream")),
                    "beat_description": _safe_str(beat.get("Beat_Description")),
                    "detailed_description": _safe_str(beat.get("Detailed_Description")),
                    "beat_upstream_latitude": _safe_str(beat.get("Beat_Upstream_Latitude")),
                    "beat_upstream_longitude": _safe_str(beat.get("Beat_Upstream_Longitude")),
                    "beat_downstream_latitude": _safe_str(beat.get("Beat_Downstream_Latitude")),
                    "beat_downstream_longitude": _safe_str(beat.get("Beat_Downstream_Longitude")),
                    "parking_locations": _safe_json(beat.get("Parking_Locations"), []),
                }
            )
        if beat_rows:
            bind.execute(club_beats.insert(), beat_rows)

    for short_name, club_id in club_id_by_short_name.items():
        sqlite_path = legacy_dir / f"{short_name}.db"
        if not sqlite_path.exists():
            continue

        sqlite_conn = sqlite3.connect(str(sqlite_path))
        sqlite_conn.row_factory = sqlite3.Row
        cur = sqlite_conn.cursor()

        if _sqlite_table_exists(sqlite_conn, "members"):
            cur.execute("SELECT * FROM members")
            member_rows = []
            for row in cur.fetchall():
                record = dict(row)
                member_rows.append(
                    {
                        "club_id": club_id,
                        "legacy_id": _safe_str(record.get("ID")),
                        "number": _safe_str(record.get("Number")),
                        "members_name": _safe_str(record.get("Members_Name")),
                        "title": _safe_str(record.get("Title")),
                        "first_name": _safe_str(record.get("First_Name")),
                        "last_name": _safe_str(record.get("Last_Name")),
                        "photo_path": _safe_str(record.get("Photo_Path")),
                        "preferred_name": _safe_str(record.get("Preferred_Name")),
                        "first_names": _safe_str(record.get("First_Names")),
                        "paused": _safe_str(record.get("Paused")),
                        "resigned": _safe_str(record.get("Resigned")),
                        "member_type": _safe_str(record.get("Member_Type")),
                        "subs_expected": _safe_str(record.get("Subs_Expected")),
                        "subs_paid": _safe_str(record.get("Subs_paid")),
                        "join_fee": _safe_str(record.get("Join_Fee")),
                        "paid_up_2026": _safe_str(record.get("Paid_Up_2026")),
                        "photo_received": _safe_str(record.get("Photo_Received")),
                        "in_whatsapp": _safe_str(record.get("In_WhatsApp")),
                        "in_fb": _safe_str(record.get("In_FB")),
                        "date_of_birth": _parse_date(record.get("Date_of_Birth")),
                        "age": _safe_str(record.get("Age")),
                        "new_member_2026": _safe_str(record.get("New_Member_2026")),
                        "paid_up_card_sent": _safe_str(record.get("Paid_up_Card_Sent")),
                        "cr2023": _safe_str(record.get("CR2023")),
                        "cr2024": _safe_str(record.get("CR2024")),
                        "cr2025": _safe_str(record.get("CR2025")),
                        "details_confirmed_2026": _safe_str(record.get("Details_Confirmed_2026")),
                        "full_address": _safe_str(record.get("Full_Address")),
                        "address_street": _safe_str(record.get("Address___Street_Address")),
                        "address_line_2": _safe_str(record.get("Address___Address_Line_2")),
                        "address_city": _safe_str(record.get("Address___City")),
                        "county": _safe_str(record.get("County")),
                        "address_state_region": _safe_str(record.get("Address___State/Prov/Region")),
                        "address_zip_postal": _safe_str(record.get("Address___ZIP/Postal")),
                        "address_country": _safe_str(record.get("Address___Country")),
                        "phone": _safe_str(record.get("Phone")),
                        "mobile": _safe_str(record.get("Mobile")),
                        "email": _safe_str(record.get("E_Mail")),
                        "ea_licence": _safe_str(record.get("EA_Licence")),
                        "licence_exp": _safe_str(record.get("Licence_Exp")),
                        "car_reg": _safe_str(record.get("Car_Reg")),
                        "username": _safe_str(record.get("username")),
                        "password": _safe_str(record.get("password")),
                    }
                )

            if member_rows:
                bind.execute(members.insert(), member_rows)

        template_rows = []
        if _sqlite_table_exists(sqlite_conn, "newsletter_templates"):
            cur.execute("SELECT id, name, subject, body FROM newsletter_templates")
            for row in cur.fetchall():
                template_rows.append(
                    {
                        "club_id": club_id,
                        "template_key": _safe_str(row["id"]) or f"template-{len(template_rows) + 1}",
                        "name": _safe_str(row["name"]),
                        "subject": _safe_str(row["subject"]),
                        "body": _safe_str(row["body"]),
                    }
                )

        if not template_rows:
            for template in DEFAULT_NEWSLETTER_TEMPLATES:
                template_rows.append(
                    {
                        "club_id": club_id,
                        "template_key": template["template_key"],
                        "name": template["name"],
                        "subject": template["subject"],
                        "body": template["body"],
                    }
                )

        bind.execute(newsletter_templates.insert(), template_rows)
        sqlite_conn.close()


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM newsletter_templates"))
    bind.execute(sa.text("DELETE FROM members"))
    bind.execute(sa.text("DELETE FROM club_beats"))
    bind.execute(sa.text("DELETE FROM club_smtp_settings"))
    bind.execute(sa.text("DELETE FROM clubs"))
    bind.execute(sa.text("DELETE FROM app_settings WHERE key = 'server_config' AND scope = 'global'"))
