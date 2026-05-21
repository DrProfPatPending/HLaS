#!/usr/bin/env python3
"""Sync club configuration data from PostgreSQL to aggregate and/or split JSON."""

import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

try:
    from sqlalchemy.exc import SQLAlchemyError
except Exception:  # pragma: no cover
    class SQLAlchemyError(Exception):
        pass


BACKEND_DIR = Path(__file__).parent
DEFAULT_CONFIG_PATH = BACKEND_DIR / 'clubs.config.json'
DEFAULT_CLUBS_DIR = BACKEND_DIR / 'clubs'
DEFAULT_MANIFEST_PATH = DEFAULT_CLUBS_DIR / 'manifest.json'


def load_env_vars() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def _position_sort_key(value: Any) -> tuple[int, int | str, str]:
    raw = str(value or '').strip()
    if raw.isdigit():
        return (0, int(raw), raw)
    return (1, raw, raw)


def _normalize_beat_row(beat_row: Any) -> Dict[str, Any]:
    beat_dict = dict(beat_row._mapping)
    beat_dict.pop('id', None)
    beat_dict.pop('club_id', None)
    beat_dict.pop('created_at', None)
    beat_dict.pop('updated_at', None)

    return {
        'Beat_Name': beat_dict.get('beat_name', ''),
        'Beat_ID': beat_dict.get('beat_id', ''),
        'River': beat_dict.get('river', ''),
        'Position': beat_dict.get('position', ''),
        'Beat_Upstream': beat_dict.get('beat_upstream', ''),
        'Beat_Downstream': beat_dict.get('beat_downstream', ''),
        'Beat_Description': beat_dict.get('beat_description', ''),
        'Detailed_Description': beat_dict.get('detailed_description', ''),
        'Beat_Upstream_Latitude': beat_dict.get('beat_upstream_latitude', ''),
        'Beat_Upstream_Longitude': beat_dict.get('beat_upstream_longitude', ''),
        'Beat_Downstream_Latitude': beat_dict.get('beat_downstream_latitude', ''),
        'Beat_Downstream_Longitude': beat_dict.get('beat_downstream_longitude', ''),
        'Parking_Locations': beat_dict.get('parking_locations', []) or [],
        'Pools': beat_dict.get('pools', []) or [],
        'Waypoints': beat_dict.get('waypoints', []) or [],
    }


def _normalize_club_row(club_row: Any, smtp_row: Any, beats: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        'fullName': club_row.full_name or club_row.short_name,
        'shortName': club_row.short_name,
        'description': club_row.description or '',
        'websiteUrl': club_row.website_url or '',
        'adminEmail': club_row.admin_email or '',
        'logoUrl': club_row.logo_url or '',
        'whatsappGroups': club_row.whatsapp_groups or '',
        'socialMedia': club_row.social_media if isinstance(club_row.social_media, list) else [],
        'officers': club_row.officers if isinstance(club_row.officers, list) else [],
        'beats': sorted(beats, key=lambda b: (_position_sort_key(b.get('Position')), b.get('Beat_Name', ''))),
        'smtp': {
            'host': getattr(smtp_row, 'host', '') or '',
            'port': getattr(smtp_row, 'port', 587) or 587,
            'username': getattr(smtp_row, 'username', '') or '',
            'password': getattr(smtp_row, 'password', '') or '',
            'fromEmail': getattr(smtp_row, 'from_email', '') or '',
            'fromName': getattr(smtp_row, 'from_name', '') or '',
            'useSsl': bool(getattr(smtp_row, 'use_ssl', False)) if smtp_row is not None else False,
            'useTls': bool(getattr(smtp_row, 'use_tls', True)) if smtp_row is not None else True,
        },
    }


def _load_json(path: Path) -> Any:
    with path.open('r', encoding='utf-8') as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2)
        handle.write('\n')


def _load_existing_by_short_name(config_path: Path) -> Dict[str, Dict[str, Any]]:
    if not config_path.exists():
        return {}

    payload = _load_json(config_path)
    clubs = payload.get('clubs', []) if isinstance(payload, dict) else []
    return {
        club.get('shortName'): club
        for club in clubs
        if isinstance(club, dict) and club.get('shortName')
    }


def load_clubs_from_postgres(db_url: str) -> List[Dict[str, Any]]:
    try:
        from sqlalchemy import create_engine, select
    except Exception as exc:
        raise RuntimeError('SQLAlchemy is required to sync from PostgreSQL') from exc

    sys.path.insert(0, os.path.dirname(__file__))
    from db_models import clubs as clubs_table, club_beats as club_beats_table, club_smtp_settings as club_smtp_table

    engine = create_engine(db_url)
    clubs_by_short_name: Dict[str, Dict[str, Any]] = {}

    with engine.begin() as connection:
        clubs_result = connection.execute(
            select(clubs_table).where(clubs_table.c.is_active.is_(True)).order_by(clubs_table.c.short_name.asc())
        )
        clubs_rows = clubs_result.fetchall()
        club_ids = [club_row.id for club_row in clubs_rows]

        smtp_rows = connection.execute(
            select(club_smtp_table).where(club_smtp_table.c.club_id.in_(club_ids))
        ).fetchall() if club_ids else []

        beats_rows = connection.execute(
            select(club_beats_table).where(club_beats_table.c.club_id.in_(club_ids)).order_by(
                club_beats_table.c.club_id.asc(), club_beats_table.c.beat_name.asc()
            )
        ).fetchall() if club_ids else []

    smtp_by_club_id = {row.club_id: row for row in smtp_rows}
    beats_by_club_id: Dict[Any, List[Dict[str, Any]]] = {}
    for beat_row in beats_rows:
        beats_by_club_id.setdefault(beat_row.club_id, []).append(_normalize_beat_row(beat_row))

    for club_row in clubs_rows:
        short_name = club_row.short_name
        smtp_row = smtp_by_club_id.get(club_row.id)
        beats = beats_by_club_id.get(club_row.id, [])
        clubs_by_short_name[short_name] = _normalize_club_row(club_row, smtp_row, beats)

    return [clubs_by_short_name[short_name] for short_name in sorted(clubs_by_short_name)]


def merge_with_existing(
    clubs_from_postgres: List[Dict[str, Any]],
    existing_by_short_name: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    merged_clubs: List[Dict[str, Any]] = []
    for club in clubs_from_postgres:
        short_name = club.get('shortName')
        merged_club = deepcopy(existing_by_short_name.get(short_name, {}))
        merged_club.update(club)
        merged_clubs.append(merged_club)
    merged_clubs.sort(key=lambda item: item.get('shortName', ''))
    return merged_clubs


def update_config_file(config_path: Path, merged_clubs: List[Dict[str, Any]], verbose: bool = True) -> bool:
    try:
        config = {'clubs': merged_clubs}
        _write_json(config_path, config)

        if verbose:
            for club in merged_clubs:
                short_name = club.get('shortName', '')
                beat_count = len(club.get('beats', []))
                social_count = len(club.get('socialMedia', []))
                print(f'✅ Updated {short_name}: {beat_count} beats, {social_count} social links')
            print(f'\n✅ Aggregate sync complete: {len(merged_clubs)} clubs written to {config_path}')

        return True

    except Exception as exc:
        if verbose:
            print(f'❌ Error: {exc}', file=sys.stderr)
        return False


def update_split_files(
    clubs_dir: Path,
    manifest_path: Path,
    merged_clubs: List[Dict[str, Any]],
    verbose: bool = True,
) -> bool:
    try:
        manifest_entries: List[Dict[str, Any]] = []

        for club in merged_clubs:
            short_name = str(club.get('shortName', '')).strip()
            if not short_name:
                continue

            club_dir = clubs_dir / short_name
            club_file = club_dir / 'club.json'

            (club_dir / 'assets').mkdir(parents=True, exist_ok=True)
            (club_dir / 'imports' / 'beats').mkdir(parents=True, exist_ok=True)
            (club_dir / 'imports' / 'members').mkdir(parents=True, exist_ok=True)
            (club_dir / 'member_id_photos').mkdir(parents=True, exist_ok=True)

            for gitkeep_path in [
                club_dir / 'imports' / 'beats' / '.gitkeep',
                club_dir / 'imports' / 'members' / '.gitkeep',
                club_dir / 'member_id_photos' / '.gitkeep',
            ]:
                if not gitkeep_path.exists():
                    gitkeep_path.write_text('', encoding='utf-8')

            _write_json(club_file, club)
            manifest_entries.append(
                {
                    'shortName': short_name,
                    'path': f'{short_name}/club.json',
                    'enabled': True,
                }
            )

            if verbose:
                print(f'✅ Wrote split club file: {club_file}')

        manifest_entries.sort(key=lambda item: item.get('shortName', ''))
        manifest_payload = {
            'version': 1,
            'description': 'Club source manifest for generating backend/clubs.config.json',
            'clubs': manifest_entries,
        }
        _write_json(manifest_path, manifest_payload)

        if verbose:
            print(f'✅ Manifest updated: {manifest_path}')
            print(f'\n✅ Split sync complete: {len(manifest_entries)} clubs written under {clubs_dir}')
        return True
    except Exception as exc:
        if verbose:
            print(f'❌ Error: {exc}', file=sys.stderr)
        return False


def sync_beats_from_postgres(verbose: bool = True) -> bool:
    return sync_clubs_from_postgres(verbose=verbose)


def sync_clubs_from_postgres(
    verbose: bool = True,
    mode: str = 'aggregate',
    config_path: Path = DEFAULT_CONFIG_PATH,
    clubs_dir: Path = DEFAULT_CLUBS_DIR,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> bool:
    load_env_vars()

    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        if verbose:
            print('❌ DATABASE_URL not configured')
        return False

    try:
        if verbose:
            print('📖 Loading club data from PostgreSQL...')
        clubs_from_postgres = load_clubs_from_postgres(db_url)

        existing_by_short_name = _load_existing_by_short_name(config_path)
        merged_clubs = merge_with_existing(clubs_from_postgres, existing_by_short_name)

        if mode not in {'aggregate', 'split', 'both'}:
            if verbose:
                print(f"❌ Invalid mode: {mode}")
            return False

        success = True

        if mode in {'aggregate', 'both'}:
            if verbose:
                print(f'📝 Updating aggregate config: {config_path}')
            success = success and update_config_file(config_path, merged_clubs, verbose=verbose)

        if mode in {'split', 'both'}:
            if verbose:
                print(f'📝 Updating split config under: {clubs_dir}')
            success = success and update_split_files(clubs_dir, manifest_path, merged_clubs, verbose=verbose)

        return success

    except SQLAlchemyError as exc:
        if verbose:
            print(f'❌ Database error: {exc}', file=sys.stderr)
        return False
    except Exception as exc:
        if verbose:
            print(f'❌ Error: {exc}', file=sys.stderr)
        return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Sync club configuration data from PostgreSQL to aggregate and/or split JSON'
    )
    parser.add_argument(
        '--mode',
        choices=['aggregate', 'split', 'both'],
        default='aggregate',
        help="Output mode: aggregate (clubs.config.json), split (backend/clubs), or both"
    )
    parser.add_argument(
        '--config-path',
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help='Path to aggregate clubs.config.json'
    )
    parser.add_argument(
        '--clubs-dir',
        type=Path,
        default=DEFAULT_CLUBS_DIR,
        help='Path to split clubs directory'
    )
    parser.add_argument(
        '--manifest-path',
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help='Path to split manifest.json'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress output'
    )

    args = parser.parse_args()

    success = sync_clubs_from_postgres(
        verbose=not args.quiet,
        mode=args.mode,
        config_path=args.config_path,
        clubs_dir=args.clubs_dir,
        manifest_path=args.manifest_path,
    )
    sys.exit(0 if success else 1)
