#!/usr/bin/env python

import argparse
import json
import os
import shutil
from typing import Dict, List, Optional, Tuple


BACKEND_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
FRONTEND_LOGOS_DIR = os.path.join(PROJECT_ROOT, 'frontend', 'logos')
BACKEND_LOGOS_DIR = os.path.join(BACKEND_DIR, 'club_logos')
CLUBS_CONFIG_PATH = os.path.join(BACKEND_DIR, 'clubs.config.json')


def load_clubs() -> List[Dict[str, str]]:
    with open(CLUBS_CONFIG_PATH, 'r', encoding='utf-8') as config_file:
        payload = json.load(config_file)

    clubs = payload.get('clubs') if isinstance(payload, dict) else payload
    if not isinstance(clubs, list):
        raise ValueError('clubs.config.json must contain a clubs list')
    return clubs


def save_clubs(clubs: List[Dict[str, str]]) -> None:
    with open(CLUBS_CONFIG_PATH, 'w', encoding='utf-8') as config_file:
        json.dump({'clubs': clubs}, config_file, indent=2)


def build_logo_index() -> Dict[str, List[str]]:
    if not os.path.isdir(FRONTEND_LOGOS_DIR):
        return {}

    files = [name for name in os.listdir(FRONTEND_LOGOS_DIR) if name.lower().endswith('.png')]
    index: Dict[str, List[str]] = {}
    for file_name in files:
        upper_name = file_name.upper()
        for token in ('_LOGO_50PX.PNG', '_LOGO.PNG', '.PNG'):
            if upper_name.endswith(token):
                club_key = upper_name[: -len(token)]
                index.setdefault(club_key, []).append(file_name)
                break
    return index


def pick_source_logo(short_name: str, logo_index: Dict[str, List[str]]) -> Optional[str]:
    candidates = logo_index.get(short_name.upper(), [])
    if not candidates:
        return None

    priority_suffixes = ['_Logo_50px.png', '_Logo.png', '.png']
    sorted_candidates = sorted(candidates)
    for suffix in priority_suffixes:
        for candidate in sorted_candidates:
            if candidate.endswith(suffix):
                return candidate
    return sorted_candidates[0]


def migrate(dry_run: bool = False) -> Tuple[int, int]:
    clubs = load_clubs()
    logo_index = build_logo_index()
    os.makedirs(BACKEND_LOGOS_DIR, exist_ok=True)

    migrated_count = 0
    missing_count = 0

    for club in clubs:
        short_name = str(club.get('shortName', '')).strip()
        if not short_name:
            continue

        source_logo_name = pick_source_logo(short_name, logo_index)
        if not source_logo_name:
            missing_count += 1
            print(f'[missing] No frontend logo found for {short_name}')
            continue

        source_path = os.path.join(FRONTEND_LOGOS_DIR, source_logo_name)
        target_path = os.path.join(BACKEND_LOGOS_DIR, f'{short_name}.png')
        logo_url = f'/club_logo/{short_name}'

        print(f'[migrate] {short_name}: {source_logo_name} -> backend/club_logos/{short_name}.png')
        if not dry_run:
            shutil.copyfile(source_path, target_path)
            club['logoUrl'] = logo_url
        migrated_count += 1

    if not dry_run:
        save_clubs(clubs)

    return migrated_count, missing_count


def main() -> None:
    parser = argparse.ArgumentParser(description='Migrate club logos from frontend/logos to backend/club_logos.')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without writing files.')
    args = parser.parse_args()

    migrated_count, missing_count = migrate(dry_run=args.dry_run)
    mode_label = 'DRY RUN' if args.dry_run else 'DONE'
    print(f'[{mode_label}] Migrated logos: {migrated_count}, clubs without matching logo: {missing_count}')


if __name__ == '__main__':
    main()
