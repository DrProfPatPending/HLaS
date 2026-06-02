#!/usr/bin/env python3
"""
Import club hero images from backend/club_logos folder into PostgreSQL.
Similar to import_club_backgrounds_to_postgres.py but for hero images.
"""

import os as os_module
import mimetypes
from sqlalchemy import create_engine, text

# Get database URL from environment or use default
POSTGRES_URL = os_module.getenv('DATABASE_URL', 'postgresql+psycopg://hlas:hlas@postgres:5432/hlas')

# Directory containing hero PNG files
HERO_DIR = os_module.getenv(
    'HERO_DIR',
    '/opt/HLaS/backend/club_logos' if os_module.path.exists('/opt/HLaS/backend/club_logos') else '/app/club_logos'
)


def main():
    """Import all *_hero.png files from HERO_DIR into the club_heroes table."""
    print(f"Importing club hero images from: {HERO_DIR}")
    print(f"Database URL: {POSTGRES_URL}")

    engine = create_engine(POSTGRES_URL, future=True)

    with engine.begin() as conn:
        clubs = conn.execute(text('SELECT short_name FROM clubs ORDER BY short_name')).fetchall()
        print(f"\nFound {len(clubs)} clubs")

        imported_count = 0
        skipped_count = 0

        for club in clubs:
            short_name = club[0]
            hero_path = os_module.path.join(HERO_DIR, f'{short_name}_hero.png')

            if not os_module.path.isfile(hero_path):
                print(f'  ⊘ No hero file found for {short_name}, skipping.')
                skipped_count += 1
                continue

            with open(hero_path, 'rb') as f:
                image_data = f.read()

            mime_type, _ = mimetypes.guess_type(hero_path)
            if not mime_type:
                mime_type = 'image/png'

            conn.execute(text('''
                INSERT INTO club_heroes (club_short_name, image_data, mime_type, updated_at)
                VALUES (:club_short_name, :image_data, :mime_type, now())
                ON CONFLICT (club_short_name) DO UPDATE SET
                    image_data = EXCLUDED.image_data,
                    mime_type = EXCLUDED.mime_type,
                    updated_at = now()
            '''), {
                'club_short_name': short_name,
                'image_data': image_data,
                'mime_type': mime_type
            })
            print(f'  ✓ Imported hero image for {short_name}')
            imported_count += 1

    print(f'\n✓ Import complete: {imported_count} hero images imported, {skipped_count} skipped.')


if __name__ == '__main__':
    main()
