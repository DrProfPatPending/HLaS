#!/usr/bin/env python3
"""
Link all users in app_users to the GAAFFS club in member_user_links.
Assumes each user has a corresponding member in the GAAFFS members table (by email/username).
"""
import os
import sqlite3
from sqlalchemy import create_engine, text

# Config
SQLITE_DB = os.path.join(os.path.dirname(__file__), 'GAAFFS.db')
POSTGRES_URL = os.environ.get('POSTGRES_URL', 'postgresql+psycopg2://hlas:hlas@localhost:5433/hlas')
CLUB_SHORT_NAME = 'GAAFFS'

def main():
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute('SELECT Number, username FROM members WHERE username != ""')
    member_map = {username: number for number, username in sqlite_cur.fetchall()}

    # Connect to Postgres
    engine = create_engine(POSTGRES_URL, future=True)
    with engine.begin() as conn:
        # Get club_id for GAAFFS
        club_id = conn.execute(text('SELECT id FROM clubs WHERE short_name = :club'), {'club': CLUB_SHORT_NAME}).scalar()
        if not club_id:
            print('GAAFFS club not found in clubs table!')
            return
        # Get all users
        users = conn.execute(text('SELECT id, username FROM app_users')).fetchall()
        # For each user, find matching member in GAAFFS.db and link
        for user in users:
            user_id = user.id
            username = user.username
            member_number = member_map.get(username)
            if not member_number:
                print(f'No member found for user {username}, skipping.')
                continue
            # Find member_id in members table
            member_id = conn.execute(text('SELECT id FROM members WHERE club_id = :club_id AND number = :number'), {'club_id': club_id, 'number': member_number}).scalar()
            if not member_id:
                print(f'No member_id found for user {username} (number {member_number}), skipping.')
                continue
            # Insert link if not exists
            conn.execute(text('''
                INSERT INTO member_user_links (user_id, member_id, club_id, is_primary)
                VALUES (:user_id, :member_id, :club_id, true)
                ON CONFLICT (user_id, member_id) DO NOTHING
            '''), {'user_id': user_id, 'member_id': member_id, 'club_id': club_id})
    print('✓ Linked all users to GAAFFS club.')

if __name__ == '__main__':
    main()
