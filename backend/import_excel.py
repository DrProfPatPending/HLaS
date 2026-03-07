import csv
import os
import pandas as pd
from sqlalchemy import create_engine, text

DB_PATH = os.path.join(os.path.dirname(__file__), 'members.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"
EXCEL_FILE = 'members.xlsx'
CSV_FILE = 'Members_2026.csv'
DB_FILE = 'members.db'


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
            row_extended = row + [username, 'password']
            insert_parameters = {str(index): value for index, value in enumerate(row_extended)}
            connection.execute(insert_sql, insert_parameters)


def import_members_from_excel(excel_file=EXCEL_FILE):
    dataframe = pd.read_excel(excel_file)
    engine = create_engine(DATABASE_URL, future=True)

    members_dataframe = dataframe.rename(columns={
        'name': 'Members_Name',
        'email': 'E_Mail',
        'phone': 'Mobile',
        'membership_type': 'Member_Type',
    })

    members_dataframe.to_sql('members', con=engine, if_exists='append', index=False)
    print('Import complete.')


if __name__ == '__main__':
    csv_path = os.path.join(os.path.dirname(__file__), CSV_FILE)
    db_path = os.path.join(os.path.dirname(__file__), DB_FILE)
    import_csv_to_sqlite(csv_path, db_path)
