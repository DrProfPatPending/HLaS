#!/usr/bin/env python3
"""
Sync Fishing Beats from clubs.config.json to PostgreSQL database

By default this only seeds clubs that have no beats in PostgreSQL yet, so
beats edited in the app are never overwritten (this is what runs on backend
startup). Pass --replace to delete and re-insert every club's beats from the
JSON file instead; export app edits first with sync_beats_postgres_to_json.py.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.exc import SQLAlchemyError

def load_env_vars():
    """Load environment variables"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

def load_beats_from_json(config_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Load beats from clubs.config.json"""
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    beats_by_club = {}
    for club in config.get('clubs', []):
        short_name = club.get('shortName')
        beats = club.get('beats', [])
        if short_name:
            beats_by_club[short_name] = beats
    
    return beats_by_club

def _beat_values(club_id: int, beat_data: Dict[str, Any]) -> Dict[str, Any]:
    return dict(
        club_id=club_id,
        beat_name=beat_data.get('Beat_Name', ''),
        beat_id=beat_data.get('Beat_ID', ''),
        river=beat_data.get('River', ''),
        position=beat_data.get('Position', ''),
        beat_upstream=beat_data.get('Beat_Upstream', ''),
        beat_downstream=beat_data.get('Beat_Downstream', ''),
        beat_description=beat_data.get('Beat_Description', ''),
        detailed_description=beat_data.get('Detailed_Description', ''),
        beat_upstream_latitude=beat_data.get('Beat_Upstream_Latitude', ''),
        beat_upstream_longitude=beat_data.get('Beat_Upstream_Longitude', ''),
        beat_downstream_latitude=beat_data.get('Beat_Downstream_Latitude', ''),
        beat_downstream_longitude=beat_data.get('Beat_Downstream_Longitude', ''),
        parking_locations=beat_data.get('Parking_Locations', []),
        pools=beat_data.get('Pools', []),
        waypoints=beat_data.get('Waypoints', []),
    )


def sync_club_beats(connection, clubs_table, club_beats_table, beats_by_club,
                    dry_run: bool = False, verbose: bool = True,
                    replace_existing: bool = False) -> int:
    """Copy JSON beats into club_beats for each active club; return beats written.

    Clubs that already have beats are skipped unless replace_existing is True,
    in which case their rows are deleted and re-inserted from the JSON.
    """
    total_beats_synced = 0
    clubs_rows = connection.execute(
        select(clubs_table.c.id, clubs_table.c.short_name).where(clubs_table.c.is_active.is_(True))
    ).fetchall()

    for club_row in clubs_rows:
        club_id = club_row.id
        short_name = club_row.short_name
        json_beats = beats_by_club.get(short_name, [])

        if not json_beats:
            if verbose:
                print(f'⚠️  No beats in JSON for {short_name}')
            continue

        existing_count = connection.execute(
            select(func.count()).select_from(club_beats_table).where(club_beats_table.c.club_id == club_id)
        ).scalar_one()

        if existing_count and not replace_existing:
            if verbose:
                print(f'⏭️  Kept {short_name}: {existing_count} beats already in PostgreSQL (use --replace to overwrite)')
            continue

        if not dry_run:
            if existing_count:
                connection.execute(
                    delete(club_beats_table).where(club_beats_table.c.club_id == club_id)
                )
            for beat_data in json_beats:
                connection.execute(club_beats_table.insert().values(**_beat_values(club_id, beat_data)))

        if verbose:
            action = 'Replaced' if existing_count else 'Seeded'
            print(f'✅ {action} {short_name}: {len(json_beats)} beats')
        total_beats_synced += len(json_beats)

    return total_beats_synced


def sync_beats_to_postgres(dry_run: bool = False, verbose: bool = True,
                           replace_existing: bool = False) -> bool:
    """Sync beats from clubs.config.json to PostgreSQL database
    
    Args:
        dry_run: If True, don't write to database
        verbose: If True, print progress messages
        replace_existing: If True, overwrite clubs that already have beats
    
    Returns:
        True if successful, False otherwise
    """
    load_env_vars()
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        if verbose:
            print('❌ DATABASE_URL not configured')
        return False
    
    try:
        # Setup path and imports
        sys.path.insert(0, os.path.dirname(__file__))
        from db_models import clubs as clubs_table, club_beats as club_beats_table
        
        # Create engine
        engine = create_engine(db_url)
        
        # Load beats from JSON
        config_path = Path(__file__).parent / 'clubs.config.json'
        if not config_path.exists():
            if verbose:
                print(f'❌ Configuration file not found: {config_path}')
            return False
        
        beats_by_club = load_beats_from_json(config_path)
        if verbose:
            print(f'📖 Loaded beats from {config_path}')
        
        with engine.begin() as connection:
            total_beats_synced = sync_club_beats(
                connection, clubs_table, club_beats_table, beats_by_club,
                dry_run=dry_run, verbose=verbose, replace_existing=replace_existing,
            )

        if verbose:
            mode = '(dry-run)' if dry_run else ''
            print(f'\n✅ Sync complete {mode}: {total_beats_synced} total beats')
        
        return True
        
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
        description='Sync Fishing Beats from clubs.config.json to PostgreSQL'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without writing to database'
    )
    parser.add_argument(
        '--replace',
        action='store_true',
        help="Delete and re-insert every club's beats from the JSON, even clubs that already have beats"
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress output'
    )
    
    args = parser.parse_args()
    
    success = sync_beats_to_postgres(
        dry_run=args.dry_run,
        verbose=not args.quiet,
        replace_existing=args.replace,
    )
    sys.exit(0 if success else 1)
