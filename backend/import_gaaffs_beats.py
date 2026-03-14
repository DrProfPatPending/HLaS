#!/usr/bin/env python3
"""Import GAAFFS beat data from CSV into clubs.config.json."""

import csv
import json
import os
import re
from typing import Dict, List

BACKEND_DIR = os.path.dirname(__file__)
CLUBS_CONFIG_PATH = os.path.join(BACKEND_DIR, 'clubs.config.json')
BEATS_CSV_PATH = os.path.join(BACKEND_DIR, 'GAAFFS_beats.csv')
CLUB_SHORT_NAME = 'GAAFFS'
REQUIRED_COLUMNS = [
    'Beat_ID',
    'River',
    'Beat_Name',
    'Position',
    'Beat_Upstream',
    'Beat_Downstream',
    'Beat_Description',
]


def normalize_what3words_value(raw_value: str) -> str:
    value = str(raw_value or '').strip()
    if not value:
        return ''

    without_slashes = re.sub(r'^/+', '', value).strip()
    words = [word.strip() for word in without_slashes.split('.')]

    if len(words) != 3 or any(not word for word in words):
        return value

    if not all(re.fullmatch(r'[A-Za-z]+', word) for word in words):
        return value

    return f"///{'.'.join(word.lower() for word in words)}"


def normalize_beat_row(row: Dict[str, str]) -> Dict[str, str]:
    beat_upstream = str(row.get('Beat_Upstream', '')).strip()
    beat_downstream = str(row.get('Beat_Downstream', '')).strip()

    return {
        'Beat_Name': str(row.get('Beat_Name', '')).strip(),
        'Beat_ID': str(row.get('Beat_ID', '')).strip(),
        'River': str(row.get('River', '')).strip(),
        'Position': str(row.get('Position', '')).strip(),
        'Beat_Upstream': normalize_what3words_value(beat_upstream),
        'Beat_Downstream': normalize_what3words_value(beat_downstream),
        'Beat_Description': str(row.get('Beat_Description', '')).strip(),
    }


def load_beats_from_csv(csv_path: str) -> List[Dict[str, str]]:
    with open(csv_path, 'r', encoding='utf-8-sig', newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames or []

        missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing_columns:
            raise ValueError(
                'CSV missing required columns: ' + ', '.join(missing_columns)
            )

        beats = []
        for row in reader:
            if not row:
                continue
            if not any(str(row.get(column, '')).strip() for column in REQUIRED_COLUMNS):
                continue
            beats.append(normalize_beat_row(row))

    return beats


def load_clubs_config(config_path: str) -> Dict[str, List[Dict[str, str]]]:
    with open(config_path, 'r', encoding='utf-8') as config_file:
        loaded = json.load(config_file)
    if not isinstance(loaded, dict) or 'clubs' not in loaded or not isinstance(loaded['clubs'], list):
        raise ValueError('clubs.config.json must contain a top-level "clubs" array')
    return loaded


def save_clubs_config(config_path: str, payload: Dict[str, List[Dict[str, str]]]) -> None:
    with open(config_path, 'w', encoding='utf-8') as config_file:
        json.dump(payload, config_file, indent=2)
        config_file.write('\n')


def import_gaaffs_beats() -> int:
    if not os.path.exists(BEATS_CSV_PATH):
        raise FileNotFoundError(f'CSV file not found: {BEATS_CSV_PATH}')
    if not os.path.exists(CLUBS_CONFIG_PATH):
        raise FileNotFoundError(f'Config file not found: {CLUBS_CONFIG_PATH}')

    beats = load_beats_from_csv(BEATS_CSV_PATH)
    config_payload = load_clubs_config(CLUBS_CONFIG_PATH)

    clubs = config_payload['clubs']
    updated = False
    for club in clubs:
        if isinstance(club, dict) and str(club.get('shortName', '')).strip() == CLUB_SHORT_NAME:
            club['beats'] = beats
            updated = True
            break

    if not updated:
        raise ValueError(f'Club with shortName "{CLUB_SHORT_NAME}" not found')

    save_clubs_config(CLUBS_CONFIG_PATH, config_payload)
    print(f'Imported {len(beats)} beats into {CLUB_SHORT_NAME}')
    return len(beats)


if __name__ == '__main__':
    import_gaaffs_beats()
