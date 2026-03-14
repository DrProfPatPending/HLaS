#!/usr/bin/env python3
"""Import TEST beat data from CSV into clubs.config.json."""

import os

from import_beats_common import import_club_beats

BACKEND_DIR = os.path.dirname(__file__)
CLUBS_CONFIG_PATH = os.path.join(BACKEND_DIR, 'clubs.config.json')
BEATS_CSV_PATH = os.path.join(BACKEND_DIR, 'TEST_beats.csv')
CLUB_SHORT_NAME = 'TEST'


def import_test_beats() -> int:
    return import_club_beats(CLUB_SHORT_NAME, BEATS_CSV_PATH, CLUBS_CONFIG_PATH)


if __name__ == '__main__':
    import_test_beats()
