from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Date,
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
import uuid
import re
import shutil

app = Flask(__name__)
CORS(app)

# Store database configurations per club in Flask's g object
DB_DIR = os.path.dirname(__file__)
FILTERABLE_COLUMNS = ['ID', 'Number', 'Members_Name', 'Member_Type', 'Paid_Up_2026', 'Paused', 'E_Mail', 'Mobile', 'Car_Reg', 'EA_Licence', 'Licence_Exp', 'Resigned']
SERVER_CONFIG_PATH = os.path.join(DB_DIR, 'server.config.json')
CLUBS_CONFIG_PATH = os.path.join(DB_DIR, 'clubs.config.json')
CLUB_LOGOS_DIR = os.path.join(DB_DIR, 'club_logos')
CLUB_DB_TEMPLATE_PATH = os.path.join(DB_DIR, 'template.db')

# Cache for club database engines and metadata
_club_db_cache = {}

# In-memory admin session tokens (cleared on restart)
_admin_tokens = set()


def get_club_logo_path(short_name):
    return os.path.join(CLUB_LOGOS_DIR, f'{short_name}.png')


def get_club_logo_url(short_name):
    return f'/club_logo/{short_name}'


def save_uploaded_logo(short_name, logo_file):
    if logo_file is None or not logo_file.filename:
        return ''

    file_name_lower = logo_file.filename.lower()
    if not file_name_lower.endswith('.png'):
        raise ValueError('Logo file must be a PNG (.png)')

    content = logo_file.read()
    if not content.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Logo file content is not a valid PNG')

    os.makedirs(CLUB_LOGOS_DIR, exist_ok=True)
    with open(get_club_logo_path(short_name), 'wb') as logo_out:
        logo_out.write(content)

    return get_club_logo_url(short_name)


def create_empty_club_database(short_name):
    if not os.path.exists(CLUB_DB_TEMPLATE_PATH):
        raise FileNotFoundError('Database template template.db was not found')

    target_db_path = os.path.join(DB_DIR, f'{short_name}.db')
    if os.path.exists(target_db_path):
        raise FileExistsError(f'Database for {short_name} already exists')

    shutil.copyfile(CLUB_DB_TEMPLATE_PATH, target_db_path)


def load_clubs_config():
    default_clubs = [
        {
            'fullName': 'GAAFFS',
            'shortName': 'GAAFFS',
            'description': 'GAAFFS fishing club members',
            'websiteUrl': 'https://example.com/gaaffs',
            'adminEmail': 'admin@gaaffs.example.com',
            'logoUrl': '',
        },
        {
            'fullName': 'CTC',
            'shortName': 'CTC',
            'description': 'CTC fishing club members',
            'websiteUrl': 'https://example.com/ctc',
            'adminEmail': 'admin@ctc.example.com',
            'logoUrl': '',
        },
    ]

    if not os.path.exists(CLUBS_CONFIG_PATH):
        return default_clubs

    try:
        with open(CLUBS_CONFIG_PATH, 'r', encoding='utf-8') as config_file:
            loaded_config = json.load(config_file)
    except (OSError, json.JSONDecodeError):
        return default_clubs

    source_clubs = loaded_config.get('clubs') if isinstance(loaded_config, dict) else loaded_config
    if not isinstance(source_clubs, list):
        return default_clubs

    normalized_clubs = []
    for club in source_clubs:
        if not isinstance(club, dict):
            continue
        short_name = str(club.get('shortName', '')).strip()
        if not short_name:
            continue
        normalized_clubs.append({
            'fullName': str(club.get('fullName', short_name)).strip() or short_name,
            'shortName': short_name,
            'description': str(club.get('description', '')).strip(),
            'websiteUrl': str(club.get('websiteUrl', '')).strip(),
            'adminEmail': str(club.get('adminEmail', '')).strip(),
            'logoUrl': str(club.get('logoUrl', '')).strip() or (get_club_logo_url(short_name) if os.path.exists(get_club_logo_path(short_name)) else ''),
        })

    return normalized_clubs or default_clubs


def load_server_config():
    default_config = {
        'server': {
            'host': '127.0.0.1',
            'port': 5050,
            'url': 'http://127.0.0.1:5050',
        },
        'startup': {
            'delayMs': 3000,
        },
        'runtime': {
            'debug': False,
            'useReloader': False,
        },
        'logging': {
            'level': 'INFO',
        },
    }

    if not os.path.exists(SERVER_CONFIG_PATH):
        return default_config

    try:
        with open(SERVER_CONFIG_PATH, 'r', encoding='utf-8') as config_file:
            loaded_config = json.load(config_file)
    except (OSError, json.JSONDecodeError):
        return default_config

    merged = default_config.copy()
    for section in ('server', 'startup', 'runtime', 'logging'):
        merged[section] = {**default_config.get(section, {}), **loaded_config.get(section, {})}
    # Admin section is merged shallowly as a flat dict
    if 'admin' in loaded_config:
        merged['admin'] = loaded_config['admin']
    return merged

def save_clubs_config(clubs):
    """Overwrite clubs.config.json with the supplied list."""
    with open(CLUBS_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump({'clubs': clubs}, f, indent=2)


def get_admin_config():
    """Return admin credentials from server config, with safe defaults."""
    config = load_server_config()
    return config.get('admin', {'username': 'admin', 'password': 'admin123'})


def require_admin_token():
    """Return True if the request carries a valid admin Bearer token."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    return auth_header[7:] in _admin_tokens


def get_db_for_club(club):
    """Get or create database engine and session for the specified club."""
    if club not in _club_db_cache:
        db_path = os.path.join(DB_DIR, f'{club}.db')
        database_url = f"sqlite:///{db_path.replace(os.sep, '/')}"
        engine = create_engine(database_url, future=True)
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        
        # Load metadata for this club's database
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
                raise RuntimeError(f'Could not determine a primary key for members table in {club}.db')
            members_table.append_constraint(PrimaryKeyConstraint(members_table.c[fallback_primary_key]))
        
        class Member:
            pass
        
        mapper_registry.map_imperatively(Member, members_table)
        
        _club_db_cache[club] = {
            'engine': engine,
            'session_factory': session_factory,
            'mapper_registry': mapper_registry,
            'metadata': metadata,
            'members_table': members_table,
            'Member': Member
        }
    
    cache = _club_db_cache[club]
    session = cache['session_factory']()
    return {
        'session': session,
        'members_table': cache['members_table'],
        'Member': cache['Member'],
        'mapper_registry': cache['mapper_registry']
    }

def get_column(column_name, members_table):
    """Get column from members table."""
    return members_table.c.get(column_name)


def wildcard_to_sql_like(value):
    escaped = value.replace('\\', '\\\\')
    escaped = escaped.replace('%', '\\%').replace('_', '\\_')
    escaped = escaped.replace('*', '%').replace('?', '_')
    return escaped


def initialize_database(club):
    """Initialize database for a club if it doesn't exist."""
    db_path = os.path.join(DB_DIR, f'{club}.db')
    database_url = f"sqlite:///{db_path.replace(os.sep, '/')}"
    engine = create_engine(database_url, future=True)
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
    config = load_server_config()
    configured_level = config.get('logging', {}).get('level', 'INFO')
    log_level = os.getenv('LOG_LEVEL', str(configured_level)).upper()
    app.logger.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    for handler in app.logger.handlers:
        handler.setFormatter(formatter)
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)


def log_database_target(club):
    app.logger.info(json.dumps({
        'event': 'database.selected',
        'club': club,
        'db_path': os.path.join(DB_DIR, f'{club}.db'),
    }))


def member_to_dict(member, members_table):
    return {column.name: getattr(member, column.name) for column in members_table.columns}


def get_column(column_name, members_table):
    """Get column from members table."""
    return members_table.c.get(column_name)


@app.teardown_appcontext
def remove_session(exception=None):
    pass  # Individual sessions are managed per request


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


@app.route('/clubs', methods=['GET'])
def get_clubs():
    return jsonify({'clubs': load_clubs_config()})


@app.route('/member_photo/<club>/<path:filename>', methods=['GET'])
def member_photo(club, filename):
    # Validate club name to prevent directory traversal
    valid_clubs = get_valid_club_short_names()
    if club not in valid_clubs:
        return jsonify({'error': 'Invalid club'}), 404
    photo_dir = os.path.join(DB_DIR, 'ID_photos', club)
    if not os.path.isdir(photo_dir):
        return jsonify({'error': 'Photo directory not found'}), 404
    return send_from_directory(photo_dir, filename)


@app.route('/club_logo/<short_name>', methods=['GET'])
def club_logo(short_name):
    logo_path = get_club_logo_path(short_name)
    if not os.path.exists(logo_path):
        return jsonify({'error': 'Logo not found'}), 404
    return send_from_directory(CLUB_LOGOS_DIR, os.path.basename(logo_path))


def get_valid_club_short_names():
    clubs = load_clubs_config()
    return {
        str(club.get('shortName', '')).strip()
        for club in clubs
        if isinstance(club, dict) and str(club.get('shortName', '')).strip()
    }


@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    club = data.get('club', 'GAAFFS')  # Default to GAAFFS if not provided
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    valid_clubs = get_valid_club_short_names()
    if club not in valid_clubs:
        return jsonify({'error': 'Invalid club selection'}), 400

    log_database_target(club)
    db_info = get_db_for_club(club)
    session = db_info['session']
    members_table = db_info['members_table']
    Member = db_info['Member']
    
    password_column = get_column('password', members_table)
    name_column = get_column('Members_Name', members_table)
    username_column = get_column('username', members_table)

    if password_column is None or (name_column is None and username_column is None):
        return jsonify({'success': False, 'error': 'Login columns are missing from members table'}), 500

    # Try matching by Members_Name
    user = None
    if name_column is not None:
        query = select(Member).where(name_column == username)
        user = session.scalars(query).first()
        if user:
            stored_password = getattr(user, password_column.name)
            if check_password_hash(stored_password, password):
                user_dict = member_to_dict(user, members_table)
                user_dict.pop('password', None)
                return jsonify({'success': True, 'user': user_dict})
            else:
                user = None  # Password didn't match, reset user

    # Try matching by username column
    if username_column is not None and user is None:
        query = select(Member).where(username_column == username)
        user = session.scalars(query).first()
        if user:
            stored_password = getattr(user, password_column.name)
            if check_password_hash(stored_password, password):
                user_dict = member_to_dict(user, members_table)
                user_dict.pop('password', None)
                return jsonify({'success': True, 'user': user_dict})

    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401


@app.route('/members', methods=['GET'])
def get_members():
    club = request.args.get('club', 'GAAFFS')  # Default to GAAFFS if not provided
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    sort_by = request.args.get('sort_by')
    sort_order = request.args.get('sort_order', 'asc')

    log_database_target(club)
    db_info = get_db_for_club(club)
    session = db_info['session']
    members_table = db_info['members_table']
    Member = db_info['Member']

    filters = []
    for column_name in FILTERABLE_COLUMNS:
        raw_filter = request.args.get(column_name)
        if raw_filter is None:
            continue

        filter_value = raw_filter.strip()
        if not filter_value:
            continue

        column = get_column(column_name, members_table)
        if column is None:
            continue

        if filter_value == '[BLANK]':
            filters.append(or_(column.is_(None), cast(column, String) == ''))
        else:
            filters.append(cast(column, String).ilike(wildcard_to_sql_like(filter_value), escape='\\'))

    members_query = select(Member)
    total_query = select(func.count()).select_from(members_table)

    if filters:
        filter_expression = and_(*filters)
        members_query = members_query.where(filter_expression)
        total_query = total_query.where(filter_expression)

    # Apply sorting if requested
    if sort_by:
        sort_column = get_column(sort_by, members_table)
        if sort_column is not None:
            # Cast numeric columns to Integer for proper numeric sorting
            if sort_by in ('Number', 'ID'):
                sort_expression = cast(sort_column, Integer)
            # Cast date columns to Date for proper date sorting
            elif sort_by == 'Licence_Exp':
                sort_expression = cast(sort_column, Date)
            else:
                sort_expression = sort_column
            
            if sort_order == 'desc':
                members_query = members_query.order_by(sort_expression.desc())
            else:
                members_query = members_query.order_by(sort_expression.asc())

    members_query = members_query.limit(limit).offset(offset)
    members = session.scalars(members_query).all()
    total = session.execute(total_query).scalar_one()

    members_payload = [member_to_dict(member, members_table) for member in members]
    return jsonify({'members': members_payload, 'total': total})


@app.route('/members', methods=['POST'])
def add_member():
    data = request.json or {}
    club = data.get('club', 'GAAFFS')  # Default to GAAFFS if not provided
    log_database_target(club)
    db_info = get_db_for_club(club)
    session = db_info['session']
    members_table = db_info['members_table']
    Member = db_info['Member']
    
    member = Member()
    for field_name in ('Members_Name', 'Number', 'Member_Type', 'Paid_Up_2026'):
        if get_column(field_name, members_table) is not None:
            setattr(member, field_name, data.get(field_name))

    session.add(member)
    session.commit()
    return jsonify({'status': 'success'})


@app.route('/members/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    data = request.json or {}
    club = data.get('club', 'GAAFFS')  # Default to GAAFFS if not provided
    log_database_target(club)
    db_info = get_db_for_club(club)
    session = db_info['session']
    members_table = db_info['members_table']
    Member = db_info['Member']
    
    id_column = get_column('id', members_table) or get_column('ID', members_table)
    if id_column is None:
        return jsonify({'error': 'No ID column available for update'}), 400

    member = session.scalars(select(Member).where(id_column == member_id)).first()
    if member is None:
        return jsonify({'error': 'Member not found'}), 404

    reserved_fields = {'club', 'ID', 'id'}
    for field_name, field_value in data.items():
        if field_name in reserved_fields:
            continue
        if get_column(field_name, members_table) is None:
            continue
        if field_name == 'password' and field_value:
            if not str(field_value).startswith(('scrypt:', 'pbkdf2:', 'bcrypt:')):
                field_value = generate_password_hash(str(field_value))
        setattr(member, field_name, field_value)

    session.commit()
    return jsonify({'status': 'success'})


@app.route('/members/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    club = request.args.get('club', 'GAAFFS')  # Default to GAAFFS if not provided
    log_database_target(club)
    db_info = get_db_for_club(club)
    session = db_info['session']
    members_table = db_info['members_table']
    Member = db_info['Member']
    
    id_column = get_column('id', members_table) or get_column('ID', members_table)
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
    club = request.args.get('club', 'GAAFFS')  # Default to GAAFFS if not provided
    log_database_target(club)
    db_info = get_db_for_club(club)
    session = db_info['session']
    members_table = db_info['members_table']
    Member = db_info['Member']
    
    number_column = get_column('Number', members_table)
    if number_column is None:
        return jsonify({'error': 'Number column not found'}), 500

    member = session.scalars(select(Member).where(number_column == number)).first()
    if member is None:
        return jsonify({'error': 'Member not found'}), 404

    return jsonify(member_to_dict(member, members_table))


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.json or {}
    username = data.get('username', '')
    password = data.get('password', '')

    admin_cfg = get_admin_config()
    stored_password = admin_cfg.get('password', '')

    # Support both plain-text and werkzeug-hashed passwords in the config
    try:
        if stored_password.startswith(('scrypt:', 'pbkdf2:', 'bcrypt:')):
            valid = check_password_hash(stored_password, password)
        else:
            valid = (password == stored_password)
    except Exception:
        valid = False

    if username == admin_cfg.get('username', 'admin') and valid:
        token = str(uuid.uuid4())
        _admin_tokens.add(token)
        return jsonify({'success': True, 'token': token})
    return jsonify({'success': False, 'error': 'Invalid admin credentials'}), 401


@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        _admin_tokens.discard(auth_header[7:])
    return jsonify({'success': True})


@app.route('/admin/clubs', methods=['GET'])
def admin_get_clubs():
    if not require_admin_token():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'clubs': load_clubs_config()})


@app.route('/admin/clubs', methods=['POST'])
def admin_add_club():
    if not require_admin_token():
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.form if request.form else (request.json or {})
    short_name = str(data.get('shortName', '')).strip()
    if not short_name:
        return jsonify({'error': 'shortName is required'}), 400
    if not re.fullmatch(r'[A-Za-z0-9_-]+', short_name):
        return jsonify({'error': 'shortName may only contain letters, numbers, underscore, and hyphen'}), 400

    clubs = load_clubs_config()
    if any(c.get('shortName') == short_name for c in clubs):
        return jsonify({'error': f'Club "{short_name}" already exists'}), 409

    logo_url = ''
    logo_file = request.files.get('logoFile')
    logo_path = get_club_logo_path(short_name)
    if logo_file and logo_file.filename:
        try:
            logo_url = save_uploaded_logo(short_name, logo_file)
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400

    try:
        create_empty_club_database(short_name)
    except FileExistsError as exc:
        if logo_url and os.path.exists(logo_path):
            os.remove(logo_path)
        return jsonify({'error': str(exc)}), 409
    except FileNotFoundError as exc:
        if logo_url and os.path.exists(logo_path):
            os.remove(logo_path)
        return jsonify({'error': str(exc)}), 500
    except Exception as exc:
        if logo_url and os.path.exists(logo_path):
            os.remove(logo_path)
        return jsonify({'error': f'Failed to create database for {short_name}: {exc}'}), 500

    clubs.append({
        'fullName': str(data.get('fullName', short_name)).strip(),
        'shortName': short_name,
        'description': str(data.get('description', '')).strip(),
        'websiteUrl': str(data.get('websiteUrl', '')).strip(),
        'adminEmail': str(data.get('adminEmail', '')).strip(),
        'logoUrl': logo_url,
    })
    save_clubs_config(clubs)
    return jsonify({'success': True})


@app.route('/admin/clubs/<short_name>', methods=['PUT'])
def admin_update_club(short_name):
    if not require_admin_token():
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    clubs = load_clubs_config()
    for i, club in enumerate(clubs):
        if club.get('shortName') == short_name:
            clubs[i] = {
                'fullName': str(data.get('fullName', club.get('fullName', short_name))).strip(),
                'shortName': short_name,
                'description': str(data.get('description', club.get('description', ''))).strip(),
                'websiteUrl': str(data.get('websiteUrl', club.get('websiteUrl', ''))).strip(),
                'adminEmail': str(data.get('adminEmail', club.get('adminEmail', ''))).strip(),
                'logoUrl': str(data.get('logoUrl', club.get('logoUrl', ''))).strip(),
            }
            save_clubs_config(clubs)
            return jsonify({'success': True})
    return jsonify({'error': f'Club "{short_name}" not found'}), 404


@app.route('/admin/clubs/<short_name>', methods=['DELETE'])
def admin_delete_club(short_name):
    if not require_admin_token():
        return jsonify({'error': 'Unauthorized'}), 401
    clubs = load_clubs_config()
    updated = [c for c in clubs if c.get('shortName') != short_name]
    if len(updated) == len(clubs):
        return jsonify({'error': f'Club "{short_name}" not found'}), 404
    save_clubs_config(updated)
    return jsonify({'success': True})


if __name__ == '__main__':
    config = load_server_config()
    server_config = config.get('server', {})
    runtime_config = config.get('runtime', {})

    host = server_config.get('host', '127.0.0.1')
    port = int(server_config.get('port', 5050))
    debug = bool(runtime_config.get('debug', False))
    use_reloader = bool(runtime_config.get('useReloader', False))

    configure_logging()
    # Databases are now initialized on-demand per club
    app.run(host=host, port=port, debug=debug, use_reloader=use_reloader)
