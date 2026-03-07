from flask import Flask, request, jsonify, g
from flask_cors import CORS
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    PrimaryKeyConstraint,
    cast,
    func,
    select,
    and_,
    or_,
)
from sqlalchemy.orm import registry, scoped_session, sessionmaker
import os
import json
import logging
import time

app = Flask(__name__)
CORS(app)
DB_PATH = os.path.join(os.path.dirname(__file__), 'members.db')
DEFAULT_DATABASE_URL = f"sqlite:///{DB_PATH.replace(os.sep, '/')}"
DATABASE_URL = os.getenv('DATABASE_URL', DEFAULT_DATABASE_URL)

FILTERABLE_COLUMNS = ['ID', 'Number', 'Members_Name', 'Member_Type', 'Paid_Up_2026', 'Paused', 'E_Mail', 'Mobile', 'Car_Reg', 'EA_Licence']

engine = create_engine(DATABASE_URL, future=True)
session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
SessionLocal = scoped_session(session_factory)

mapper_registry = registry()
metadata = mapper_registry.metadata

members_table = Table('members', metadata, autoload_with=engine)

if len(members_table.primary_key.columns) == 0:
    fallback_primary_key = None
    for candidate_key in ('ID', 'id', 'Number', 'username'):
        if candidate_key in members_table.c:
            fallback_primary_key = candidate_key
            break
    if fallback_primary_key is None:
        raise RuntimeError('Could not determine a primary key for members table')
    members_table.append_constraint(PrimaryKeyConstraint(members_table.c[fallback_primary_key]))


class Member:
    pass


mapper_registry.map_imperatively(Member, members_table)


def wildcard_to_sql_like(value):
    escaped = value.replace('\\', '\\\\')
    escaped = escaped.replace('%', '\\%').replace('_', '\\_')
    escaped = escaped.replace('*', '%').replace('?', '_')
    return escaped


def initialize_database():
    bootstrap_metadata = MetaData()
    Table(
        'members',
        bootstrap_metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('name', String, nullable=False),
        Column('email', String),
        Column('phone', String),
        Column('membership_type', String),
        Column('password', String),
    )
    bootstrap_metadata.create_all(bind=engine)


def configure_logging():
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    app.logger.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    for handler in app.logger.handlers:
        handler.setFormatter(formatter)
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)


def log_database_target():
    safe_database_url = engine.url.render_as_string(hide_password=True)
    app.logger.info(json.dumps({
        'event': 'startup.database_target',
        'database_url': safe_database_url,
    }))


def member_to_dict(member):
    return {column.name: getattr(member, column.name) for column in members_table.columns}


def get_column(column_name):
    return members_table.c.get(column_name)


@app.teardown_appcontext
def remove_session(exception=None):
    SessionLocal.remove()


@app.before_request
def start_request_timer():
    g.request_start_time = time.perf_counter()


@app.after_request
def log_request(response):
    start_time = getattr(g, 'request_start_time', None)
    duration_ms = None
    if start_time is not None:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    app.logger.info(json.dumps({
        'event': 'http.request',
        'method': request.method,
        'path': request.path,
        'query_string': request.query_string.decode('utf-8'),
        'status_code': response.status_code,
        'duration_ms': duration_ms,
    }))
    return response


@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    session = SessionLocal()
    password_column = get_column('password')
    name_column = get_column('Members_Name')
    username_column = get_column('username')

    if password_column is None or (name_column is None and username_column is None):
        return jsonify({'success': False, 'error': 'Login columns are missing from members table'}), 500

    query = select(Member)
    if name_column is not None:
        query = query.where(name_column == username, password_column == password)
        user = session.scalars(query).first()
        if user:
            user_dict = member_to_dict(user)
            user_dict.pop('password', None)
            return jsonify({'success': True, 'user': user_dict})

    if username_column is not None:
        query = select(Member).where(username_column == username, password_column == password)
        user = session.scalars(query).first()
        if user:
            user_dict = member_to_dict(user)
            user_dict.pop('password', None)
            return jsonify({'success': True, 'user': user_dict})

    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401


@app.route('/members', methods=['GET'])
def get_members():
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    sort_by = request.args.get('sort_by')
    sort_order = request.args.get('sort_order', 'asc')

    filters = []
    for column_name in FILTERABLE_COLUMNS:
        raw_filter = request.args.get(column_name)
        if raw_filter is None:
            continue

        filter_value = raw_filter.strip()
        if not filter_value:
            continue

        column = get_column(column_name)
        if column is None:
            continue

        if filter_value == '[BLANK]':
            filters.append(or_(column.is_(None), cast(column, String) == ''))
        else:
            filters.append(cast(column, String).ilike(wildcard_to_sql_like(filter_value), escape='\\'))

    session = SessionLocal()
    members_query = select(Member)
    total_query = select(func.count()).select_from(members_table)

    if filters:
        filter_expression = and_(*filters)
        members_query = members_query.where(filter_expression)
        total_query = total_query.where(filter_expression)

    # Apply sorting if requested
    if sort_by:
        sort_column = get_column(sort_by)
        if sort_column is not None:
            # Cast numeric columns to Integer for proper numeric sorting
            if sort_by in ('Number', 'ID'):
                sort_expression = cast(sort_column, Integer)
            else:
                sort_expression = sort_column
            
            if sort_order == 'desc':
                members_query = members_query.order_by(sort_expression.desc())
            else:
                members_query = members_query.order_by(sort_expression.asc())

    members_query = members_query.limit(limit).offset(offset)
    members = session.scalars(members_query).all()
    total = session.execute(total_query).scalar_one()

    members_payload = [member_to_dict(member) for member in members]
    return jsonify({'members': members_payload, 'total': total})


@app.route('/members', methods=['POST'])
def add_member():
    data = request.json or {}
    session = SessionLocal()
    member = Member()
    for field_name in ('Members_Name', 'Number', 'Member_Type', 'Paid_Up_2026'):
        if get_column(field_name) is not None:
            setattr(member, field_name, data.get(field_name))

    session.add(member)
    session.commit()
    return jsonify({'status': 'success'})


@app.route('/members/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    data = request.json or {}
    session = SessionLocal()
    id_column = get_column('id') or get_column('ID')
    if id_column is None:
        return jsonify({'error': 'No ID column available for update'}), 400

    member = session.scalars(select(Member).where(id_column == member_id)).first()
    if member is None:
        return jsonify({'error': 'Member not found'}), 404

    for field_name in ('Members_Name', 'Number', 'Member_Type', 'Paid_Up_2026'):
        if get_column(field_name) is not None:
            setattr(member, field_name, data.get(field_name))

    session.commit()
    return jsonify({'status': 'success'})


@app.route('/members/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    session = SessionLocal()
    id_column = get_column('id') or get_column('ID')
    if id_column is None:
        return jsonify({'error': 'No ID column available for delete'}), 400

    member = session.scalars(select(Member).where(id_column == member_id)).first()
    if member is None:
        return jsonify({'error': 'Member not found'}), 404

    session.delete(member)
    session.commit()
    return jsonify({'status': 'success'})


@app.route('/member_by_number/<number>', methods=['GET'])
def get_member_by_number(number):
    session = SessionLocal()
    number_column = get_column('Number')
    if number_column is None:
        return jsonify({'error': 'Number column not found'}), 500

    member = session.scalars(select(Member).where(number_column == number)).first()
    if member is None:
        return jsonify({'error': 'Member not found'}), 404

    return jsonify(member_to_dict(member))


if __name__ == '__main__':
    configure_logging()
    log_database_target()
    initialize_database()
    app.run(debug=True)
