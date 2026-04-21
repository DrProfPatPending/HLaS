#!/usr/bin/env python3
"""Backfill and normalize club_beats.pools values in PostgreSQL.

Default mode is DRY RUN.
Use --apply to persist updates.
"""

from __future__ import annotations

import argparse
import os

from sqlalchemy import create_engine, text

from core.common import normalize_pools


def _column_exists(conn) -> bool:
    row = conn.execute(
        text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'club_beats'
              AND column_name = 'pools'
            LIMIT 1
            """
        )
    ).first()
    return row is not None


def backfill_pools(database_url: str, apply_changes: bool, club_short_name: str | None) -> int:
    engine = create_engine(database_url)

    examined = 0
    changed = 0

    with engine.begin() as conn:
        if not _column_exists(conn):
            print("ERROR: column club_beats.pools does not exist yet.")
            print("Run Alembic migration first: alembic upgrade head")
            return 2

        if club_short_name:
            rows = conn.execute(
                text(
                    """
                    SELECT b.id, b.club_id, b.beat_id, b.beat_name, b.pools
                    FROM club_beats b
                    JOIN clubs c ON c.id = b.club_id
                    WHERE c.short_name = :club
                    ORDER BY b.club_id, b.beat_name
                    """
                ),
                {"club": club_short_name},
            ).mappings().all()
        else:
            rows = conn.execute(
                text(
                    """
                    SELECT b.id, b.club_id, b.beat_id, b.beat_name, b.pools
                    FROM club_beats b
                    ORDER BY b.club_id, b.beat_name
                    """
                )
            ).mappings().all()

        for row in rows:
            examined += 1
            original = row["pools"]
            original_list = original if isinstance(original, list) else []
            normalized = normalize_pools(original_list)

            if original_list == normalized:
                continue

            changed += 1
            beat_label = f"{row['beat_id'] or '?'} ({row['beat_name'] or 'Unnamed'})"
            print(f"{('[APPLY]' if apply_changes else '[DRY]')} club_id={row['club_id']} beat={beat_label}: pools normalized")

            if apply_changes:
                conn.execute(
                    text("UPDATE club_beats SET pools = :pools WHERE id = :id"),
                    {"pools": normalized, "id": row["id"]},
                )

    print(f"Examined beats: {examined}")
    print(f"Changed beats: {changed}")
    print(f"Mode: {'APPLY' if apply_changes else 'DRY RUN'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill and normalize club_beats.pools in PostgreSQL")
    parser.add_argument(
        "--database-url",
        default="",
        help="PostgreSQL SQLAlchemy URL (defaults to DATABASE_URL env if set)",
    )
    parser.add_argument(
        "--club",
        default="",
        help="Optional club short name to restrict updates",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist updates (default is dry run)",
    )
    args = parser.parse_args()

    database_url = (args.database_url or "").strip() or os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        print("ERROR: DATABASE_URL is required (env or --database-url)")
        return 2

    if not database_url.startswith("postgresql"):
        print("ERROR: backfill_pools.py only supports PostgreSQL URLs")
        return 2

    return backfill_pools(database_url, args.apply, args.club.strip() or None)


if __name__ == "__main__":
    raise SystemExit(main())
