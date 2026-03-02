import pandas as pd
import sqlite3
import os
import csv

DB_PATH = os.path.join(os.path.dirname(__file__), 'members.db')
EXCEL_FILE = 'members.xlsx'  # Replace with your actual Excel filename
CSV_FILE = 'Members_2026.csv'
DB_FILE = 'members.db'

def import_csv_to_sqlite(csv_path, db_path):
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)
        columns = [h.strip().replace(' ', '_').replace('-', '_') for h in headers]
        # Add username and password fields
        columns += ['username', 'password']
        col_defs = ', '.join([f'"{col}" TEXT' for col in columns])

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(f'DROP TABLE IF EXISTS members')
        c.execute(f'CREATE TABLE members ({col_defs})')

        for row in reader:
            # Copy email to username, set password to 'password'
            email_idx = headers.index('E-Mail') if 'E-Mail' in headers else None
            username = row[email_idx] if email_idx is not None else ''
            row_extended = row + [username, 'password']
            placeholders = ', '.join(['?'] * len(row_extended))
            c.execute(f'INSERT INTO members VALUES ({placeholders})', row_extended)
        conn.commit()
        conn.close()

if __name__ == '__main__':
    csv_path = os.path.join(os.path.dirname(__file__), CSV_FILE)
    db_path = os.path.join(os.path.dirname(__file__), DB_FILE)
    import_csv_to_sqlite(csv_path, db_path)

def import_members_from_excel(excel_file=EXCEL_FILE):
    df = pd.read_excel(excel_file)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for _, row in df.iterrows():
        c.execute('INSERT INTO members (name, email, phone, membership_type) VALUES (?, ?, ?, ?)',
                  (row['name'], row.get('email', ''), row.get('phone', ''), row.get('membership_type', '')))
    conn.commit()
    conn.close()
    print('Import complete.')

if __name__ == '__main__':
    csv_path = os.path.join(os.path.dirname(__file__), CSV_FILE)
    db_path = os.path.join(os.path.dirname(__file__), DB_FILE)
    import_csv_to_sqlite(csv_path, db_path)
