#!/usr/bin/env python3
"""Shared helpers for importing club beat CSV data into clubs.config.json."""

import csv
import json
import os
import re
from typing import Dict, List

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
            raise ValueError('CSV missing required columns: ' + ', '.join(missing_columns))

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


def import_club_beats(club_short_name: str, csv_path: str, config_path: str) -> int:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f'CSV file not found: {csv_path}')

    if not os.path.exists(config_path):
        raise FileNotFoundError(f'Config file not found: {config_path}')

    beats = load_beats_from_csv(csv_path)
    config_payload = load_clubs_config(config_path)

    updated = False
    for club in config_payload['clubs']:
        if isinstance(club, dict) and str(club.get('shortName', '')).strip() == club_short_name:
            club['beats'] = beats
            updated = True
            break

    if not updated:
        raise ValueError(f'Club with shortName "{club_short_name}" not found')

    save_clubs_config(config_path, config_payload)
    print(f'Imported {len(beats)} beats into {club_short_name}')
    return len(beats)
