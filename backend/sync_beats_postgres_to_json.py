#!/usr/bin/env python3
"""
Sync club configuration data from PostgreSQL database to clubs.config.json

This script reads club data from PostgreSQL and writes it back to clubs.config.json,
preserving any JSON-only fields already present in the file while updating the live
database-backed club content.
"""

import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List
from sqlalchemy import create_engine, select
from sqlalchemy.exc import SQLAlchemyError


def load_env_vars():
    """Load environment variables"""
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


def load_clubs_from_postgres(db_url: str) -> List[Dict[str, Any]]:
    """Load complete club records from PostgreSQL database
    
    Args:
        db_url: Database connection string
        
    Returns:
        List of normalized club dictionaries
    """
    sys.path.insert(0, os.path.dirname(__file__))
    from db_models import clubs as clubs_table, club_beats as club_beats_table, club_smtp_settings as club_smtp_table
    
    engine = create_engine(db_url)
    clubs_by_short_name: Dict[str, Dict[str, Any]] = {}
    
    with engine.begin() as connection:
        # Get all active clubs from PostgreSQL
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


def update_config_file(config_path: Path, clubs_from_postgres: List[Dict[str, Any]], 
                       verbose: bool = True) -> bool:
    """Update clubs.config.json with club data from PostgreSQL
    
    Args:
        config_path: Path to clubs.config.json file
        clubs_from_postgres: List of normalized club dictionaries
        verbose: If True, print progress messages
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load existing config
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        existing_clubs = config.get('clubs', []) if isinstance(config, dict) else []
        existing_by_short_name = {
            club.get('shortName'): club
            for club in existing_clubs
            if isinstance(club, dict) and club.get('shortName')
        }

        updated_clubs = []
        
        # Replace club entries with the PostgreSQL-backed source of truth
        for club in clubs_from_postgres:
            short_name = club.get('shortName')
            merged_club = deepcopy(existing_by_short_name.get(short_name, {}))
            merged_club.update(club)
            updated_clubs.append(merged_club)
            if verbose:
                beat_count = len(merged_club.get('beats', []))
                social_count = len(merged_club.get('socialMedia', []))
                print(f'✅ Updated {short_name}: {beat_count} beats, {social_count} social links')

        removed_clubs = [
            club.get('shortName')
            for club in existing_clubs
            if isinstance(club, dict)
            and club.get('shortName')
            and club.get('shortName') not in {item.get('shortName') for item in clubs_from_postgres}
        ]

        if removed_clubs and verbose:
            print(f'⚠️  Removed from JSON because they are not active in PostgreSQL: {", ".join(sorted(removed_clubs))}')
        
        # Write updated config back to file
        if isinstance(config, dict):
            config['clubs'] = updated_clubs
        else:
            config = {'clubs': updated_clubs}

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
            f.write('\n')
        
        if verbose:
            print(f'\n✅ Sync complete: {len(updated_clubs)} clubs written')
        
        return True
        
    except Exception as exc:
        if verbose:
            print(f'❌ Error: {exc}', file=sys.stderr)
        return False


def sync_beats_from_postgres(verbose: bool = True) -> bool:
    """Backward-compatible wrapper for syncing clubs from PostgreSQL to clubs.config.json
    
    Args:
        verbose: If True, print progress messages
        
    Returns:
        True if successful, False otherwise
    """
    return sync_clubs_from_postgres(verbose=verbose)


def sync_clubs_from_postgres(verbose: bool = True) -> bool:
    """Main function to sync clubs from PostgreSQL to clubs.config.json"""
    load_env_vars()
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        if verbose:
            print('❌ DATABASE_URL not configured')
        return False
    
    try:
        # Load clubs from PostgreSQL
        if verbose:
            print('📖 Loading club data from PostgreSQL...')
        clubs_from_postgres = load_clubs_from_postgres(db_url)
        
        # Get path to clubs.config.json
        config_path = Path(__file__).parent / 'clubs.config.json'
        if not config_path.exists():
            if verbose:
                print(f'❌ Configuration file not found: {config_path}')
            return False
        
        # Update config file
        if verbose:
            print(f'📝 Updating {config_path}')
        
        return update_config_file(config_path, clubs_from_postgres, verbose=verbose)
        
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
        description='Sync club configuration data from PostgreSQL to clubs.config.json'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress output'
    )
    
    args = parser.parse_args()
    
    success = sync_clubs_from_postgres(verbose=not args.quiet)
    sys.exit(0 if success else 1)
