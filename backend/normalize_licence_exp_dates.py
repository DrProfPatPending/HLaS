#!/usr/bin/env python3
"""Normalize legacy members.licence_exp values to YYYY-MM-DD.

Default mode is DRY RUN (no database writes).
Use --apply to persist updates.

Supports:
- PostgreSQL members table (preferred)
- SQLite club DB files (optional via --sqlite-all or --sqlite-db)

Accepted legacy input patterns include:
- YYYY-MM-DD
- YYYY-MM
- YYYY/MM
- DD/MM/YYYY
- DD-MM-YYYY
- DD/MM/YY
- DD-MM-YY
- MM/YYYY
- MM-YYYY
- MM/YY
- MM-YY

Two-digit year pivot:
- 00..49 => 2000..2049
- 50..99 => 1950..1999
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy import create_engine, text


TWO_DIGIT_YEAR_PIVOT = 50


@dataclass
class NormalizeResult:
    normalized: Optional[str]
    reason: str


def _normalize_two_digit_year(yy: str) -> Optional[str]:
    if not yy.isdigit() or len(yy) != 2:
        return None
    year = int(yy)
    if year >= TWO_DIGIT_YEAR_PIVOT:
        return f"19{yy}"
    return f"20{yy}"


def _valid_ymd(year: str, month: str, day: str) -> bool:
    if not (year.isdigit() and month.isdigit() and day.isdigit()):
        return False
    y = int(year)
    m = int(month)
    d = int(day)
    if y < 1900 or y > 2100:
        return False
    if m < 1 or m > 12:
        return False
    if d < 1 or d > 31:
        return False
    # Lightweight validation only; no per-month day cap needed for this normalization pass.
    return True


def normalize_licence_exp(raw_value: str) -> NormalizeResult:
    raw = str(raw_value or "").strip()
    if not raw:
        return NormalizeResult(None, "empty")

    lowered = raw.lower()
    if lowered in {"n/a", "na", "none", "unknown", "-"}:
        return NormalizeResult(None, "non-date token")

    # YYYY-MM-DD
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        y, m, d = raw.split("-")
        if _valid_ymd(y, m, d):
            return NormalizeResult(f"{y}-{m}-{d}", "already normalized")
        return NormalizeResult(None, "invalid y-m-d")

    # YYYY-MM or YYYY/MM -> YYYY-MM-01
    if re.fullmatch(r"\d{4}-\d{2}", raw):
        y, m = raw.split("-")
        if _valid_ymd(y, m, "01"):
            return NormalizeResult(f"{y}-{m}-01", "year-month")
        return NormalizeResult(None, "invalid year-month")
    if re.fullmatch(r"\d{4}/\d{2}", raw):
        y, m = raw.split("/")
        if _valid_ymd(y, m, "01"):
            return NormalizeResult(f"{y}-{m}-01", "year/month")
        return NormalizeResult(None, "invalid year/month")

    # DD/MM/YYYY, DD-MM-YYYY
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", raw):
        d, m, y = raw.split("/")
        if _valid_ymd(y, m, d):
            return NormalizeResult(f"{y}-{m}-{d}", "day/month/year")
        return NormalizeResult(None, "invalid day/month/year")
    if re.fullmatch(r"\d{2}-\d{2}-\d{4}", raw):
        d, m, y = raw.split("-")
        if _valid_ymd(y, m, d):
            return NormalizeResult(f"{y}-{m}-{d}", "day-month-year")
        return NormalizeResult(None, "invalid day-month-year")

    # DD/MM/YY, DD-MM-YY
    if re.fullmatch(r"\d{2}/\d{2}/\d{2}", raw):
        d, m, yy = raw.split("/")
        y = _normalize_two_digit_year(yy)
        if y and _valid_ymd(y, m, d):
            return NormalizeResult(f"{y}-{m}-{d}", "day/month/two-digit-year")
        return NormalizeResult(None, "invalid day/month/two-digit-year")
    if re.fullmatch(r"\d{2}-\d{2}-\d{2}", raw):
        d, m, yy = raw.split("-")
        y = _normalize_two_digit_year(yy)
        if y and _valid_ymd(y, m, d):
            return NormalizeResult(f"{y}-{m}-{d}", "day-month-two-digit-year")
        return NormalizeResult(None, "invalid day-month-two-digit-year")

    # MM/YYYY, MM-YYYY -> YYYY-MM-01
    if re.fullmatch(r"\d{2}/\d{4}", raw):
        m, y = raw.split("/")
        if _valid_ymd(y, m, "01"):
            return NormalizeResult(f"{y}-{m}-01", "month/year")
        return NormalizeResult(None, "invalid month/year")
    if re.fullmatch(r"\d{2}-\d{4}", raw):
        m, y = raw.split("-")
        if _valid_ymd(y, m, "01"):
            return NormalizeResult(f"{y}-{m}-01", "month-year")
        return NormalizeResult(None, "invalid month-year")

    # MM/YY, MM-YY -> YYYY-MM-01
    if re.fullmatch(r"\d{2}/\d{2}", raw):
        m, yy = raw.split("/")
        y = _normalize_two_digit_year(yy)
        if y and _valid_ymd(y, m, "01"):
            return NormalizeResult(f"{y}-{m}-01", "month/two-digit-year")
        return NormalizeResult(None, "invalid month/two-digit-year")
    if re.fullmatch(r"\d{2}-\d{2}", raw):
        m, yy = raw.split("-")
        y = _normalize_two_digit_year(yy)
        if y and _valid_ymd(y, m, "01"):
            return NormalizeResult(f"{y}-{m}-01", "month-two-digit-year")
        return NormalizeResult(None, "invalid month-two-digit-year")

    return NormalizeResult(None, "unrecognized format")


def normalize_postgres(database_url: str, apply_changes: bool, club_short_name: Optional[str]) -> None:
    engine = create_engine(database_url)
    total_examined = 0
    total_changed = 0
    total_skipped = 0

    with engine.begin() as conn:
        if club_short_name:
            rows = conn.execute(
                text(
                    """
                    SELECT m.id, m.licence_exp, c.short_name
                    FROM members m
                    JOIN clubs c ON c.id = m.club_id
                    WHERE c.short_name = :club
                      AND COALESCE(TRIM(m.licence_exp), '') <> ''
                    ORDER BY m.id
                    """
                ),
                {"club": club_short_name},
            ).mappings().all()
        else:
            rows = conn.execute(
                text(
                    """
                    SELECT m.id, m.licence_exp, c.short_name
                    FROM members m
                    JOIN clubs c ON c.id = m.club_id
                    WHERE COALESCE(TRIM(m.licence_exp), '') <> ''
                    ORDER BY c.short_name, m.id
                    """
                )
            ).mappings().all()

        for row in rows:
            total_examined += 1
            original = str(row["licence_exp"] or "").strip()
            result = normalize_licence_exp(original)
            if not result.normalized:
                total_skipped += 1
                continue
            if result.normalized == original:
                continue

            total_changed += 1
            print(
                f"[POSTGRES] club={row['short_name']} member_id={row['id']} "
                f"{original!r} -> {result.normalized!r} ({result.reason})"
            )

            if apply_changes:
                conn.execute(
                    text("UPDATE members SET licence_exp = :value WHERE id = :member_id"),
                    {"value": result.normalized, "member_id": row["id"]},
                )

    mode = "APPLY" if apply_changes else "DRY-RUN"
    print(f"\n[POSTGRES][{mode}] examined={total_examined} changed={total_changed} skipped={total_skipped}")


def _iter_sqlite_paths(backend_dir: Path, explicit_db: Optional[str], sqlite_all: bool) -> Iterable[Path]:
    if explicit_db:
        yield Path(explicit_db).resolve()
        return

    if sqlite_all:
        for candidate in sorted(backend_dir.glob("*.db")):
            if candidate.name == "template.db":
                continue
            yield candidate.resolve()


def normalize_sqlite(db_paths: Iterable[Path], apply_changes: bool) -> None:
    for db_path in db_paths:
        if not db_path.exists():
            print(f"[SQLITE] skipping missing db: {db_path}")
            continue

        engine = create_engine(f"sqlite:///{db_path}")
        total_examined = 0
        total_changed = 0
        total_skipped = 0

        with engine.begin() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT rowid AS _rowid, Licence_Exp
                    FROM members
                    WHERE COALESCE(TRIM(Licence_Exp), '') <> ''
                    ORDER BY rowid
                    """
                )
            ).mappings().all()

            for row in rows:
                total_examined += 1
                original = str(row["Licence_Exp"] or "").strip()
                result = normalize_licence_exp(original)
                if not result.normalized:
                    total_skipped += 1
                    continue
                if result.normalized == original:
                    continue

                total_changed += 1
                print(
                    f"[SQLITE] db={db_path.name} rowid={row['_rowid']} "
                    f"{original!r} -> {result.normalized!r} ({result.reason})"
                )

                if apply_changes:
                    conn.execute(
                        text("UPDATE members SET Licence_Exp = :value WHERE rowid = :rowid"),
                        {"value": result.normalized, "rowid": row["_rowid"]},
                    )

        mode = "APPLY" if apply_changes else "DRY-RUN"
        print(
            f"[SQLITE:{db_path.name}][{mode}] examined={total_examined} "
            f"changed={total_changed} skipped={total_skipped}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize legacy Licence_Exp values to YYYY-MM-DD")
    parser.add_argument("--apply", action="store_true", help="Persist updates (default is dry-run)")
    parser.add_argument(
        "--database-url",
        default="",
        help="PostgreSQL SQLAlchemy URL (defaults to DATABASE_URL env if set)",
    )
    parser.add_argument("--club", default="", help="Optional club short name filter for PostgreSQL mode")
    parser.add_argument("--sqlite-all", action="store_true", help="Process all backend/*.db SQLite databases")
    parser.add_argument("--sqlite-db", default="", help="Process a single SQLite database path")
    args = parser.parse_args()

    backend_dir = Path(__file__).resolve().parent
    database_url = (args.database_url or "").strip()
    if not database_url:
        import os

        database_url = os.getenv("DATABASE_URL", "").strip()

    used_any_mode = False
    if database_url.startswith("postgresql"):
        used_any_mode = True
        normalize_postgres(database_url, args.apply, args.club.strip() or None)

    sqlite_paths = list(_iter_sqlite_paths(backend_dir, args.sqlite_db.strip() or None, args.sqlite_all))
    if sqlite_paths:
        used_any_mode = True
        normalize_sqlite(sqlite_paths, args.apply)

    if not used_any_mode:
        print("No data source selected.")
        print("Use one of:")
        print("  - set DATABASE_URL to a PostgreSQL URL (or pass --database-url)")
        print("  - pass --sqlite-all")
        print("  - pass --sqlite-db /path/to/club.db")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
