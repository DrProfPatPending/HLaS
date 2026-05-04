#!/usr/bin/env python3
"""
Import club background images from backend/club_logos folder into PostgreSQL.
Similar to import_club_logos_to_postgres.py but for background images.
"""

import os
import mimetypes
from sqlalchemy import create_engine, text

# Get database URL from environment or use default
POSTGRES_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://hlas:hlas@postgres:5432/hlas')

# Directory containing background PNG files
BACKGROUND_DIR = os.path.getenv(
    'BACKGROUND_DIR',
    '/opt/HLaS/backend/club_logos' if os.path.exists('/opt/HLaS/backend/club_logos') else '/app/club_logos'
)


def main():
    """Import all *_background.png files from BACKGROUND_DIR into the club_backgrounds table."""
    print(f"Importing club backgrounds from: {BACKGROUND_DIR}")
    print(f"Database URL: {POSTGRES_URL}")

    engine = create_engine(POSTGRES_URL, future=True)

    with engine.begin() as conn:
        # Get all club short names from the clubs table
        clubs = conn.execute(text('SELECT short_name FROM clubs ORDER BY short_name')).fetchall()
        print(f"\nFound {len(clubs)} clubs")

        imported_count = 0
        skipped_count = 0

        for club in clubs:
            short_name = club[0]  # Extract short_name from row tuple
            background_path = os.path.join(BACKGROUND_DIR, f'{short_name}_background.png')

            if not os.path.isfile(background_path):
                print(f'  ⊘ No background file found for {short_name}, skipping.')
                skipped_count += 1
                continue

            with open(background_path, 'rb') as f:
                image_data = f.read()

            mime_type, _ = mimetypes.guess_type(background_path)
            if not mime_type:
                mime_type = 'image/png'

            # Upsert background
            conn.execute(text('''
                INSERT INTO club_backgrounds (club_short_name, image_data, mime_type, updated_at)
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
            print(f'  ✓ Imported background for {short_name}')
            imported_count += 1

    print(f'\n✓ Import complete: {imported_count} backgrounds imported, {skipped_count} skipped.')


if __name__ == '__main__':
    main()
