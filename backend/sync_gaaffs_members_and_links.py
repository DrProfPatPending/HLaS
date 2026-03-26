#!/usr/bin/env python3
"""
Synchronize all members from GAAFFS.db into the Postgres members table for club GAAFFS,
then link all corresponding users in app_users to their member records in member_user_links.
"""
import os
import sqlite3
from sqlalchemy import create_engine, text

SQLITE_DB = os.path.join(os.path.dirname(__file__), 'GAAFFS.db')
POSTGRES_URL = os.environ.get('POSTGRES_URL', 'postgresql+psycopg2://hlas:hlas@localhost:5433/hlas')
CLUB_SHORT_NAME = 'GAAFFS'

def main():
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute('SELECT * FROM members WHERE username != ""')
    members = sqlite_cur.fetchall()
    columns = [desc[0] for desc in sqlite_cur.description]
    col_map = {col.lower(): i for i, col in enumerate(columns)}

    # Connect to Postgres
    engine = create_engine(POSTGRES_URL, future=True)
    with engine.begin() as conn:
        # Get club_id for GAAFFS
        club_id = conn.execute(text('SELECT id FROM clubs WHERE short_name = :club'), {'club': CLUB_SHORT_NAME}).scalar()
        if not club_id:
            print('GAAFFS club not found in clubs table!')
            return
        # Insert/update all members into Postgres members table for GAAFFS
        for row in members:
            number = row[col_map['number']]
            username = row[col_map['username']]
            email = row[col_map['e_mail']] if 'e_mail' in col_map else row[col_map['email']]
            members_name = row[col_map['members_name']]
            # Upsert member by (club_id, number)
            conn.execute(text('''
                INSERT INTO members (club_id, number, username, email, members_name)
                VALUES (:club_id, :number, :username, :email, :members_name)
                ON CONFLICT (club_id, number) DO UPDATE SET
                    username = EXCLUDED.username,
                    email = EXCLUDED.email,
                    members_name = EXCLUDED.members_name
            '''), {
                'club_id': club_id,
                'number': number,
                'username': username,
                'email': email,
                'members_name': members_name
            })
        # Link users to members
        users = conn.execute(text('SELECT id, username FROM app_users')).fetchall()
        for user in users:
            user_id = user.id
            username = user.username
            # Find member_id by username and club_id
            member_id = conn.execute(text('SELECT id FROM members WHERE club_id = :club_id AND username = :username'), {'club_id': club_id, 'username': username}).scalar()
            if not member_id:
                print(f'No member_id found for user {username}, skipping.')
                continue
            # Insert link if not exists
            conn.execute(text('''
                INSERT INTO member_user_links (user_id, member_id, club_id, is_primary)
                VALUES (:user_id, :member_id, :club_id, true)
                ON CONFLICT (user_id, member_id) DO NOTHING
            '''), {'user_id': user_id, 'member_id': member_id, 'club_id': club_id})
    print('✓ Synchronized all GAAFFS members and linked users.')

if __name__ == '__main__':
    main()
