#!/usr/bin/env python3
"""
Sync Fishing Beats from PostgreSQL database to clubs.config.json

This script reads beats from the PostgreSQL club_beats table and writes them back
to clubs.config.json, preserving the JSON structure while updating the beat data.
Useful for persisting beat data changes made via the API back to the config file.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy import create_engine, select
from sqlalchemy.exc import SQLAlchemyError


def load_env_vars():
    """Load environment variables"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def load_beats_from_postgres(db_url: str) -> Dict[str, List[Dict[str, Any]]]:
    """Load beats from PostgreSQL database
    
    Args:
        db_url: Database connection string
        
    Returns:
        Dictionary mapping club short_name to list of beats
    """
    sys.path.insert(0, os.path.dirname(__file__))
    from db_models import clubs as clubs_table, club_beats as club_beats_table
    
    engine = create_engine(db_url)
    beats_by_club = {}
    
    with engine.begin() as connection:
        # Get all active clubs from PostgreSQL
        clubs_result = connection.execute(
            select(clubs_table).where(clubs_table.c.is_active.is_(True))
        )
        clubs_rows = clubs_result.fetchall()
        
        for club_row in clubs_rows:
            club_id = club_row.id
            short_name = club_row.short_name
            
            # Get beats for this club from PostgreSQL
            beats_result = connection.execute(
                select(club_beats_table).where(club_beats_table.c.club_id == club_id)
            )
            beats_rows = beats_result.fetchall()
            
            beats = []
            for beat_row in beats_rows:
                beat_dict = dict(beat_row._mapping)
                # Remove database fields that shouldn't be in JSON
                beat_dict.pop('id', None)
                beat_dict.pop('club_id', None)
                beat_dict.pop('created_at', None)
                beat_dict.pop('updated_at', None)
                
                # Normalize field names for JSON (snake_case → PascalCase)
                beat_json = {
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
                beats.append(beat_json)
            
            if beats:
                # Sort beats by position for consistent ordering
                beats.sort(key=lambda b: (b.get('Position', '9999'), b.get('Beat_Name', '')))
                beats_by_club[short_name] = beats
    
    return beats_by_club


def update_config_file(config_path: Path, beats_by_club: Dict[str, List[Dict[str, Any]]], 
                       verbose: bool = True) -> bool:
    """Update clubs.config.json with beats from PostgreSQL
    
    Args:
        config_path: Path to clubs.config.json file
        beats_by_club: Dictionary mapping club short_name to beats
        verbose: If True, print progress messages
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load existing config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        total_beats_updated = 0
        
        # Update beats for each club
        for club in config.get('clubs', []):
            short_name = club.get('shortName')
            if short_name in beats_by_club:
                club['beats'] = beats_by_club[short_name]
                num_beats = len(beats_by_club[short_name])
                if verbose:
                    print(f'✅ Updated {short_name}: {num_beats} beats')
                total_beats_updated += num_beats
            else:
                if verbose:
                    print(f'⚠️  No beats in PostgreSQL for {short_name}')
        
        # Write updated config back to file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        if verbose:
            print(f'\n✅ Sync complete: {total_beats_updated} total beats')
        
        return True
        
    except Exception as exc:
        if verbose:
            print(f'❌ Error: {exc}', file=sys.stderr)
        return False


def sync_beats_from_postgres(verbose: bool = True) -> bool:
    """Main function to sync beats from PostgreSQL to clubs.config.json
    
    Args:
        verbose: If True, print progress messages
        
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
        # Load beats from PostgreSQL
        if verbose:
            print('📖 Loading beats from PostgreSQL...')
        beats_by_club = load_beats_from_postgres(db_url)
        
        # Get path to clubs.config.json
        config_path = Path(__file__).parent / 'clubs.config.json'
        if not config_path.exists():
            if verbose:
                print(f'❌ Configuration file not found: {config_path}')
            return False
        
        # Update config file
        if verbose:
            print(f'📝 Updating {config_path}')
        
        return update_config_file(config_path, beats_by_club, verbose=verbose)
        
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
        description='Sync Fishing Beats from PostgreSQL to clubs.config.json'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress output'
    )
    
    args = parser.parse_args()
    
    success = sync_beats_from_postgres(verbose=not args.quiet)
    sys.exit(0 if success else 1)
