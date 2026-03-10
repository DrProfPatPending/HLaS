#!/usr/bin/env python

import argparse
import os
import sqlite3
from typing import Dict, List, Optional

from werkzeug.security import generate_password_hash


def get_columns(cursor: sqlite3.Cursor) -> List[sqlite3.Row]:
    return cursor.execute('PRAGMA table_info(members)').fetchall()


def get_next_integer_id(cursor: sqlite3.Cursor, column_name: str) -> str:
    max_id = cursor.execute(
        f"SELECT MAX(CAST({column_name} AS INTEGER)) FROM members WHERE {column_name} IS NOT NULL AND TRIM(CAST({column_name} AS TEXT)) <> ''"
    ).fetchone()[0]
    next_id = 1 if max_id is None else int(max_id) + 1
    return str(next_id)


def upsert_login_user(
    db_path: str,
    username: str,
    password: str,
    member_name: str,
    email: str,
    member_number: str,
) -> str:
    if not os.path.exists(db_path):
        raise FileNotFoundError(f'Database not found: {db_path}')

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        table_exists = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='members'"
        ).fetchone()
        if not table_exists:
            raise RuntimeError('members table not found')

        columns = get_columns(cursor)
        column_names = [col[1] for col in columns]

        if 'username' not in column_names or 'password' not in column_names:
            raise RuntimeError('members table must include username and password columns')

        required_columns = [
            col[1]
            for col in columns
            if col[3] == 1 and col[4] is None and col[5] == 0
        ]

        hashed_password = generate_password_hash(password)
        existing = cursor.execute(
            'SELECT rowid FROM members WHERE username = ? LIMIT 1',
            (username,),
        ).fetchone()

        id_column = 'ID' if 'ID' in column_names else ('id' if 'id' in column_names else None)

        if existing:
            updates: List[str] = ['password = ?']
            values: List[str] = [hashed_password]

            if 'E_Mail' in column_names:
                updates.append('E_Mail = ?')
                values.append(email)
            if 'Members_Name' in column_names:
                updates.append('Members_Name = ?')
                values.append(member_name)
            if 'Number' in column_names:
                updates.append('Number = ?')
                values.append(member_number)

            if id_column is not None:
                existing_id = cursor.execute(
                    f'SELECT {id_column} FROM members WHERE rowid = ?',
                    (existing[0],),
                ).fetchone()[0]
                if existing_id is None or str(existing_id).strip() == '':
                    updates.append(f'{id_column} = ?')
                    values.append(get_next_integer_id(cursor, id_column))

            values.append(existing[0])
            cursor.execute(
                f"UPDATE members SET {', '.join(updates)} WHERE rowid = ?",
                values,
            )
            action = 'updated'
        else:
            insert_values: Dict[str, str] = {col_name: '' for col_name in required_columns}

            if id_column is not None:
                insert_values[id_column] = get_next_integer_id(cursor, id_column)
            if 'Number' in column_names:
                insert_values['Number'] = member_number
            if 'Members_Name' in column_names:
                insert_values['Members_Name'] = member_name
            if 'E_Mail' in column_names:
                insert_values['E_Mail'] = email
            insert_values['username'] = username
            insert_values['password'] = hashed_password

            insert_columns = [col_name for col_name in insert_values.keys() if col_name in column_names]
            if not insert_columns:
                raise RuntimeError('No columns available for insert')

            placeholders = ', '.join(['?'] * len(insert_columns))
            cursor.execute(
                f"INSERT INTO members ({', '.join(insert_columns)}) VALUES ({placeholders})",
                [insert_values[col_name] for col_name in insert_columns],
            )
            action = 'inserted'

        conn.commit()

        verification = cursor.execute(
            'SELECT username, Number, Members_Name, E_Mail FROM members WHERE username = ? LIMIT 1',
            (username,),
        ).fetchone()
        if not verification:
            raise RuntimeError('Upsert verification failed')

        return action
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description='Insert or update a login user in a club database safely.')
    parser.add_argument('--club', required=True, help='Club short name (e.g. TEST, CTC, GAAFFS)')
    parser.add_argument('--username', required=True, help='Login username')
    parser.add_argument('--password', required=True, help='Plain password to hash and store')
    parser.add_argument('--name', default='Rob Scoffin', help='Members_Name value')
    parser.add_argument('--email', default='', help='E_Mail value')
    parser.add_argument('--member-number', default='15', help='Number value')
    parser.add_argument('--db-dir', default=os.path.dirname(__file__), help='Directory containing <club>.db files')
    args = parser.parse_args()

    db_path = os.path.join(args.db_dir, f'{args.club}.db')
    action = upsert_login_user(
        db_path=db_path,
        username=args.username,
        password=args.password,
        member_name=args.name,
        email=args.email or args.username,
        member_number=args.member_number,
    )
    print(f'{action}: {db_path} -> {args.username}')


if __name__ == '__main__':
    main()
