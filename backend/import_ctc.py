#!/usr/bin/env python
"""
Script to import CTC_Members_2026.csv into CTC.db
"""

import csv
import os
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash

def import_csv_to_sqlite(csv_path, db_path):
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url, future=True)

    with open(csv_path, newline='', encoding='utf-8') as csvfile, engine.begin() as connection:
        reader = csv.reader(csvfile)
        headers = next(reader)

        if headers and headers[0].startswith('\ufeff'):
            headers[0] = headers[0].replace('\ufeff', '')

        source_columns = [header.strip().replace(' ', '_').replace('-', '_') for header in headers]
        all_columns = source_columns + ['username', 'password']
        column_definition_sql = ', '.join([f'"{column_name}" TEXT' for column_name in all_columns])

        connection.execute(text('DROP TABLE IF EXISTS members'))
        connection.execute(text(f'CREATE TABLE members ({column_definition_sql})'))

        placeholders_sql = ', '.join([f':{index}' for index in range(len(all_columns))])
        insert_sql = text(f'INSERT INTO members VALUES ({placeholders_sql})')

        email_index = headers.index('E-Mail') if 'E-Mail' in headers else None
        for row in reader:
            username = row[email_index] if email_index is not None and email_index < len(row) else ''
            # Hash the default password for security
            hashed_password = generate_password_hash('password')
            row_extended = row + [username, hashed_password]
            insert_parameters = {str(index): value for index, value in enumerate(row_extended)}
            connection.execute(insert_sql, insert_parameters)

if __name__ == '__main__':
    backend_dir = os.path.dirname(__file__)
    csv_path = os.path.join(backend_dir, 'CTC_Members_2026.csv')
    db_path = os.path.join(backend_dir, 'CTC.db')
    
    print(f"Importing {csv_path} into {db_path}...")
    import_csv_to_sqlite(csv_path, db_path)
    print(f"✓ Successfully imported CTC_Members_2026.csv into CTC.db")
