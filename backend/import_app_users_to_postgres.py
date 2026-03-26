#!/usr/bin/env python3
"""
Import users from GAAFFS.db (SQLite) into the central app_users table in PostgreSQL,
setting the default password to 'P&55W0rd' for all users.
"""
import os
import sys
import sqlite3
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash

# Config
SQLITE_DB = os.path.join(os.path.dirname(__file__), 'GAAFFS.db')
POSTGRES_URL = os.environ.get('POSTGRES_URL', 'postgresql+psycopg2://hlas:hlas@localhost:5433/hlas')
DEFAULT_PASSWORD = 'P&55W0rd'

def main():
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute('SELECT username, E_Mail, Members_Name FROM members WHERE username != ""')
    users = sqlite_cur.fetchall()
    print(f"Found {len(users)} users in GAAFFS.db")

    # Connect to Postgres
    engine = create_engine(POSTGRES_URL, future=True)
    with engine.connect() as conn:
        for username, email, display_name in users:
            if not username:
                continue
            password_hash = generate_password_hash(DEFAULT_PASSWORD)
            trans = conn.begin()
            try:
                conn.execute(text('''
                    INSERT INTO app_users (username, email, display_name, password_hash, is_active)
                    VALUES (:username, :email, :display_name, :password_hash, true)
                '''), {
                    'username': username,
                    'email': email or username,
                    'display_name': display_name or username,
                    'password_hash': password_hash
                })
                trans.commit()
            except Exception as e:
                trans.rollback()
                # If duplicate, update instead
                if 'duplicate key value violates unique constraint' in str(e):
                    trans2 = conn.begin()
                    try:
                        conn.execute(text('''
                            UPDATE app_users SET
                                email = :email,
                                display_name = :display_name,
                                password_hash = :password_hash,
                                is_active = true
                            WHERE username = :username
                        '''), {
                            'username': username,
                            'email': email or username,
                            'display_name': display_name or username,
                            'password_hash': password_hash
                        })
                        trans2.commit()
                    except Exception as e2:
                        trans2.rollback()
                        print(f"Error updating user {username}: {e2}")
                else:
                    print(f"Error importing user {username}: {e}")
    print("✓ Imported users into app_users table in PostgreSQL.")

if __name__ == '__main__':
    main()
