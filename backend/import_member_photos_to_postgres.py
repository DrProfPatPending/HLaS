#!/usr/bin/env python3
"""
Import member ID photos from ID_photos/<CLUB>/ into PostgreSQL member_photos.

Matching strategy:
1. For each active club, read members with non-blank photo_path.
2. Look for the file in ../ID_photos/<club_short_name>/<photo_path>.
3. Upsert into member_photos by member_id.

Usage:
  POSTGRES_URL=postgresql+psycopg://hlas:hlas@localhost:5433/hlas python backend/import_member_photos_to_postgres.py
"""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path

from sqlalchemy import create_engine, text

POSTGRES_URL = os.environ.get('POSTGRES_URL', 'postgresql+psycopg://hlas:hlas@localhost:5433/hlas')
SCRIPT_DIR = Path(__file__).resolve().parent
PHOTO_ROOT = Path(os.environ.get('HLAS_PHOTO_ROOT', str(SCRIPT_DIR.parent / 'ID_photos')))


def guess_mime_type(file_path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or 'image/jpeg'


def main() -> None:
    engine = create_engine(POSTGRES_URL, future=True)
    imported = 0
    missing = 0
    skipped = 0

    with engine.begin() as conn:
        clubs = conn.execute(text("""
            SELECT id, short_name
            FROM clubs
            WHERE is_active = TRUE
            ORDER BY short_name
        """)).mappings().all()

        for club in clubs:
            club_id = club['id']
            short_name = club['short_name']
            club_dir = PHOTO_ROOT / short_name
            if not club_dir.is_dir():
                print(f'No photo directory for {short_name}, skipping club.')
                continue

            members = conn.execute(text("""
                SELECT id, number, members_name, photo_path
                FROM members
                WHERE club_id = :club_id
                  AND TRIM(COALESCE(photo_path, '')) <> ''
                ORDER BY id
            """), {'club_id': club_id}).mappings().all()

            for member in members:
                file_name = str(member['photo_path']).strip()
                if not file_name:
                    skipped += 1
                    continue

                file_path = club_dir / file_name
                if not file_path.is_file():
                    missing += 1
                    print(f"Missing file for {short_name} member #{member['number']}: {file_name}")
                    continue

                with file_path.open('rb') as handle:
                    image_data = handle.read()

                conn.execute(text("""
                    INSERT INTO member_photos (club_id, member_id, filename, mime_type, image_data, updated_at)
                    VALUES (:club_id, :member_id, :filename, :mime_type, :image_data, NOW())
                    ON CONFLICT (member_id) DO UPDATE SET
                        club_id = EXCLUDED.club_id,
                        filename = EXCLUDED.filename,
                        mime_type = EXCLUDED.mime_type,
                        image_data = EXCLUDED.image_data,
                        updated_at = NOW()
                """), {
                    'club_id': club_id,
                    'member_id': member['id'],
                    'filename': file_name,
                    'mime_type': guess_mime_type(file_path),
                    'image_data': image_data,
                })
                imported += 1

    print(f'Imported/updated member photos: {imported}')
    print(f'Missing source files: {missing}')
    print(f'Skipped members: {skipped}')


if __name__ == '__main__':
    main()
