#!/usr/bin/env python3
"""
Import club logo PNG files from backend/club_logos/{CLUB}.png into the club_logos table in Postgres.
"""
import os
from sqlalchemy import create_engine, text
import mimetypes

LOGO_DIR = os.path.join(os.path.dirname(__file__), 'club_logos')
POSTGRES_URL = os.environ.get('POSTGRES_URL', 'postgresql+psycopg2://hlas:hlas@localhost:5433/hlas')

def main():
    engine = create_engine(POSTGRES_URL, future=True)
    with engine.begin() as conn:
        # Get all club short names from the clubs table
        clubs = conn.execute(text('SELECT short_name FROM clubs')).fetchall()
        for club in clubs:
            short_name = club.short_name
            logo_path = os.path.join(LOGO_DIR, f'{short_name}.png')
            if not os.path.isfile(logo_path):
                print(f'No logo file found for {short_name}, skipping.')
                continue
            with open(logo_path, 'rb') as f:
                image_data = f.read()
            mime_type, _ = mimetypes.guess_type(logo_path)
            if not mime_type:
                mime_type = 'image/png'
            # Upsert logo
            conn.execute(text('''
                INSERT INTO club_logos (club_short_name, image_data, mime_type, updated_at)
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
            print(f'Imported logo for {short_name}')
    print('✓ All club logos imported.')

if __name__ == '__main__':
    main()
