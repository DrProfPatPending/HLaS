#!/usr/bin/env python3
"""Template importer for a new club's beat CSV file.

Usage:
1) Copy this file to something like import_myclub_beats.py
2) Set CLUB_SHORT_NAME and BEATS_CSV_FILENAME below
3) Run: python3 backend/import_myclub_beats.py
"""

import os

from import_beats_common import import_club_beats

BACKEND_DIR = os.path.dirname(__file__)
CLUBS_CONFIG_PATH = os.path.join(BACKEND_DIR, 'clubs.config.json')

# TODO: change these two values for your new club
CLUB_SHORT_NAME = 'REPLACE_WITH_SHORT_NAME'
BEATS_CSV_FILENAME = 'REPLACE_WITH_SHORT_NAME_beats.csv'
BEATS_CSV_PATH = os.path.join(BACKEND_DIR, BEATS_CSV_FILENAME)


def import_new_club_beats() -> int:
    if CLUB_SHORT_NAME == 'REPLACE_WITH_SHORT_NAME' or BEATS_CSV_FILENAME == 'REPLACE_WITH_SHORT_NAME_beats.csv':
        raise ValueError('Set CLUB_SHORT_NAME and BEATS_CSV_FILENAME before running this script')

    return import_club_beats(CLUB_SHORT_NAME, BEATS_CSV_PATH, CLUBS_CONFIG_PATH)


if __name__ == '__main__':
    import_new_club_beats()
