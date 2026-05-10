#!/usr/bin/env python3
import sys
import mimetypes
from pathlib import Path
from sqlalchemy import create_engine, text

# Get paths and DB config
background_dir = Path('/app/club_logos')
db_url = 'postgresql+psycopg://hlas:hlas@postgres:5432/hlas'

print(f"Importing backgrounds from: {background_dir}")
print(f"Database URL: {db_url}")

engine = create_engine(db_url, future=True)

with engine.begin() as conn:
    # Get clubs
    clubs = conn.execute(text('SELECT short_name FROM clubs ORDER BY short_name')).fetchall()
    print(f"Found {len(clubs)} clubs\n")
    
    for club in clubs:
        short_name = club[0]
        bg_file = background_dir / f'{short_name}_background.png'
        
        if not bg_file.exists():
            print(f'  ⊘ {short_name}: no background file')
            continue
        
        # Read image
        image_data = bg_file.read_bytes()
        mime_type = 'image/png'
        
        # Upsert to database
        conn.execute(text('''
            INSERT INTO club_backgrounds (club_short_name, image_data, mime_type, updated_at)
            VALUES (:short_name, :data, :mime, now())
            ON CONFLICT (club_short_name) DO UPDATE SET
                image_data = EXCLUDED.image_data,
                mime_type = EXCLUDED.mime_type,
                updated_at = now()
        '''), {'short_name': short_name, 'data': image_data, 'mime': mime_type})
        
        print(f'  ✓ {short_name}: imported ({len(image_data):,} bytes)')

print('\n✓ Done!')
