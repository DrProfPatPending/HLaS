#!/usr/bin/env python3
"""
Sync Fishing Beats from PostgreSQL via API export to clubs.config.json

This script exports beats from the SQL database via the API endpoint
and updates the JSON configuration file.
"""

import json
import os
import sys
import requests
from pathlib import Path

def get_clubs_from_config():
    """Load club list from JSON config"""
    config_path = Path(__file__).parent / "backend" / "clubs.config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config.get("clubs", [])

def sync_beats_via_api(base_url="http://localhost:5050"):
    """Sync beats from PostgreSQL to JSON file via API"""
    
    config_path = Path(__file__).parent / "backend" / "clubs.config.json"
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    clubs = config.get("clubs", [])
    updated_count = 0
    
    for club_idx, club in enumerate(clubs):
        short_name = club.get("shortName")
        if not short_name:
            continue
        
        # Call export API
        export_url = f"{base_url}/admin/clubs/{short_name}/beats/export"
        
        try:
            response = requests.get(export_url)
            if response.status_code == 200:
                data = response.json()
                beats = data.get("beats", [])
                config["clubs"][club_idx]["beats"] = beats
                print(f"✅ Updated {short_name}: synced {len(beats)} beats from PostgreSQL")
                updated_count += 1
            elif response.status_code == 401:
                print(f"⚠️  Skipping {short_name}: authentication required (401)")
            else:
                print(f"⚠️  Failed to export beats for {short_name}: HTTP {response.status_code}")
        except Exception as exc:
            print(f"⚠️  Error exporting beats for {short_name}: {exc}")
    
    # Write updated config back to JSON
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Successfully synced {updated_count} club(s) to {config_path}")
    return updated_count > 0

if __name__ == '__main__':
    try:
        success = sync_beats_via_api()
        sys.exit(0 if success else 1)
    except Exception as exc:
        print(f"❌ Error: {exc}", file=sys.stderr)
        sys.exit(1)
