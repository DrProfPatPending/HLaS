#!/usr/bin/env python3
"""
Sync Fishing Beats from PostgreSQL database to clubs.config.json

This script exports beats from the PostgreSQL club_beats table for each club
and updates the JSON configuration file.
"""

import json
import os
import sys
from typing import Dict, List
from sqlalchemy import select

def load_env_vars():
    """Load environment variables"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

def sync_beats_to_json():
    """Sync beats from PostgreSQL to JSON file"""
    load_env_vars()
    
    # Import after loading env vars
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
    from db import get_postgres_backend
    
    backend = get_postgres_backend()
    session = backend['session_factory']()
    
    try:
        clubs_table = backend['clubs_table']
        club_beats_table = backend['club_beats_table']
        
        # Load clubs config
        config_path = os.path.join(os.path.dirname(__file__), 'backend', 'clubs.config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Fetch all clubs from PostgreSQL
        clubs_rows = session.execute(select(clubs_table)).fetchall()
        
        for club_row in clubs_rows:
            club_id = club_row.id
            short_name = club_row.short_name
            
            # Find club in config
            club_idx = None
            for i, c in enumerate(config['clubs']):
                if c.get('shortName') == short_name:
                    club_idx = i
                    break
            
            if club_idx is None:
                print(f"⚠️  Club {short_name} not in JSON config, skipping...")
                continue
            
            # Fetch beats from PostgreSQL for this club
            beat_rows = session.execute(
                select(club_beats_table).where(club_beats_table.c.club_id == club_id)
            ).fetchall()
            
            # Convert database rows to JSON format
            beats = []
            for row in beat_rows:
                beat = {
                    'Beat_Name': row.beat_name or '',
                    'Beat_ID': row.beat_id or '',
                    'River': row.river or '',
                    'Position': row.position or '',
                    'Beat_Upstream': row.beat_upstream or '',
                    'Beat_Downstream': row.beat_downstream or '',
                    'Beat_Description': row.beat_description or '',
                    'Detailed_Description': row.detailed_description or '',
                    'Beat_Upstream_Latitude': row.beat_upstream_latitude or '',
                    'Beat_Upstream_Longitude': row.beat_upstream_longitude or '',
                    'Beat_Downstream_Latitude': row.beat_downstream_latitude or '',
                    'Beat_Downstream_Longitude': row.beat_downstream_longitude or '',
                    'Parking_Locations': row.parking_locations or [],
                }
                beats.append(beat)
            
            # Update config
            config['clubs'][club_idx]['beats'] = beats
            print(f"✅ Updated {short_name}: synced {len(beats)} beats from PostgreSQL")
        
        # Write updated config back to JSON
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n✅ Successfully synced all beats from PostgreSQL to {config_path}")
        return True
        
    except Exception as exc:
        print(f"❌ Error syncing beats: {exc}", file=sys.stderr)
        return False
    finally:
        session.close()

if __name__ == '__main__':
    success = sync_beats_to_json()
    sys.exit(0 if success else 1)
