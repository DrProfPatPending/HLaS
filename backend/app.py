from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import atexit

app = Flask(__name__)
CORS(app)
DB_PATH = os.path.join(os.path.dirname(__file__), 'members.db')
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

FILTERABLE_COLUMNS = ['ID', 'Number', 'Members_Name', 'Member_Type', 'Paid_Up_2026', 'Paused', 'E_Mail', 'Mobile', 'Car_Reg', 'EA_Licence']

def cleanup():
    # Remove the global database connection object
    conn.close()

atexit.register(cleanup)

def wildcard_to_sql_like(value):
    escaped = value.replace('\\', '\\\\')
    escaped = escaped.replace('%', '\\%').replace('_', '\\_')
    escaped = escaped.replace('*', '%').replace('?', '_')
    return escaped

# Database setup
def init_db():
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        membership_type TEXT,
        password TEXT
    )''')
    conn.commit()

# CRUD endpoints
# Login endpoint (by username)
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    # Try both Members Name and name fields for compatibility
    c.execute('SELECT * FROM members WHERE "Members_Name" = ? AND password = ? COLLATE BINARY', (username, password))
    user = c.fetchone()
    if not user:
        c.execute('SELECT * FROM members WHERE username = ? AND password = ? COLLATE BINARY', (username, password))
        user = c.fetchone()
    if user:
        user_dict = dict(user)
        user_dict.pop('password', None)
        return jsonify({'success': True, 'user': user_dict})
    else:
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/members', methods=['GET'])
def get_members():
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))

    where_clauses = []
    where_params = []
    for column in FILTERABLE_COLUMNS:
        raw_filter = request.args.get(column)
        if raw_filter is None:
            continue
        filter_value = raw_filter.strip()
        if not filter_value:
            continue

        if filter_value == '[BLANK]':
            where_clauses.append(f'("{column}" IS NULL OR CAST("{column}" AS TEXT) = \'\')')
        else:
            where_clauses.append(f'CAST("{column}" AS TEXT) LIKE ? ESCAPE "\\" COLLATE NOCASE')
            where_params.append(wildcard_to_sql_like(filter_value))

    where_sql = ''
    if where_clauses:
        where_sql = ' WHERE ' + ' AND '.join(where_clauses)

    c = conn.cursor()
    c.execute(f'SELECT * FROM members{where_sql} LIMIT ? OFFSET ?', (*where_params, limit, offset))
    rows = c.fetchall()
    if rows:
        print('DEBUG: First row returned from members:', dict(rows[0]))
    else:
        print('DEBUG: No rows returned from members table.')
    members = [dict(row) for row in rows]
    # No need to add Row field; use 'ID' from the database
    c.execute(f'SELECT COUNT(*) FROM members{where_sql}', where_params)
    total = c.fetchone()[0]
    return jsonify({'members': members, 'total': total})

@app.route('/members', methods=['POST'])
def add_member():
    data = request.json
    c = conn.cursor()
    c.execute('INSERT INTO members (Members_Name, Number, Member_Type, Paid_Up_2026) VALUES (?, ?, ?, ?)',
              (data.get('Members_Name'), data.get('Number'), data.get('Member_Type'), data.get('Paid_Up_2026')))
    conn.commit()
    return jsonify({'status': 'success'})

@app.route('/members/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    data = request.json
    c = conn.cursor()
    c.execute('UPDATE members SET Members_Name=?, Number=?, Member_Type=?, Paid_Up_2026=? WHERE id=?',
              (data.get('Members_Name'), data.get('Number'), data.get('Member_Type'), data.get('Paid_Up_2026'), member_id))
    conn.commit()
    return jsonify({'status': 'success'})

@app.route('/members/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    c = conn.cursor()
    c.execute('DELETE FROM members WHERE id=?', (member_id,))
    conn.commit()
    return jsonify({'status': 'success'})


# Retrieve all data for a member by membership number
@app.route('/member_by_number/<number>', methods=['GET'])
def get_member_by_number(number):
    c = conn.cursor()
    c.execute('SELECT * FROM members WHERE Number = ?', (number,))
    row = c.fetchone()
    if row:
        return jsonify(dict(row))
    else:
        return jsonify({'error': 'Member not found'}), 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
