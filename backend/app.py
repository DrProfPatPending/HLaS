from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)
DB_PATH = os.path.join(os.path.dirname(__file__), 'members.db')

# Database setup
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        membership_type TEXT,
        password TEXT
    )''')
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
        conn.close()
        if user:
            user_dict = dict(user)
            user_dict.pop('password', None)
            return jsonify({'success': True, 'user': user_dict})
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    conn.commit()
    conn.close()

init_db()

# CRUD endpoints
@app.route('/members', methods=['GET'])
def get_members():
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM members LIMIT ? OFFSET ?', (limit, offset))
    rows = c.fetchall()
    if rows:
        print('DEBUG: First row returned from members:', dict(rows[0]))
    else:
        print('DEBUG: No rows returned from members table.')
    members = [dict(row) for row in rows]
    # Get total count for pagination
    c.execute('SELECT COUNT(*) FROM members')
    total = c.fetchone()[0]
    conn.close()
    return jsonify({'members': members, 'total': total})

@app.route('/members', methods=['POST'])
def add_member():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO members (Members_Name, Number, Member_Type, Paid_Up_2026) VALUES (?, ?, ?, ?)',
              (data.get('Members_Name'), data.get('Number'), data.get('Member_Type'), data.get('Paid_Up_2026')))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/members/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE members SET Members_Name=?, Number=?, Member_Type=?, Paid_Up_2026=? WHERE id=?',
              (data.get('Members_Name'), data.get('Number'), data.get('Member_Type'), data.get('Paid_Up_2026'), member_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/members/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM members WHERE id=?', (member_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})


# Retrieve all data for a member by membership number
@app.route('/member_by_number/<number>', methods=['GET'])
def get_member_by_number(number):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM members WHERE Number = ?', (number,))
    row = c.fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    else:
        return jsonify({'error': 'Member not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
