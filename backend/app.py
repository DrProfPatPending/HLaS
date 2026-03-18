from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from email.message import EmailMessage
import smtplib
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
    text,
)
from sqlalchemy.orm import registry, scoped_session, sessionmaker
import os
import json
import logging
import time
import re
import shutil
from urllib.parse import quote
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from core.common import (
    FILTERABLE_COLUMNS,
    LEGACY_TO_POSTGRES_MEMBER_COLUMNS,
    NEWSLETTER_TEMPLATES,
    NEWSLETTER_TEMPLATE_TAGS,
    render_newsletter_template,
    normalize_beats,
    normalize_what3words_value,
    normalize_parking_locations,
    normalize_what3words_words,
    wildcard_to_sql_like,
    normalize_newsletter_filters,
)
from core.defaults import _default_clubs_config, _default_server_config
from db import (
    _build_postgres_member_values,
    _resolve_postgres_club_id,
    get_db_for_club,
    get_postgres_backend,
    get_read_db_for_club,
    initialize_database,
    is_postgres_reads_enabled,
    is_postgres_writes_enabled,
)
from auth import (
    extract_bearer_token,
    get_current_principal,
    get_member_refresh_session_from_token,
    issue_admin_token,
    issue_member_token_pair,
    load_member_roles,
    require_admin_token,
    require_authenticated,
    require_permission,
    require_member_token_for_club,
    require_self_or_permission,
    revoke_admin_token_from_request,
    revoke_member_refresh_token,
    revoke_member_session_token,
)

# Store database configurations per club in Flask's g object
DB_DIR = os.path.dirname(__file__)
APP_DATA_DIR = os.getenv('HLAS_DATA_DIR', DB_DIR)


SERVER_CONFIG_PATH = os.path.join(APP_DATA_DIR, 'server.config.json')
CLUBS_CONFIG_PATH = os.path.join(APP_DATA_DIR, 'clubs.config.json')
CLUB_LOGOS_DIR = os.path.join(APP_DATA_DIR, 'club_logos')
CLUB_DB_TEMPLATE_PATH = os.path.join(DB_DIR, 'template.db')


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

    target_db_path = os.path.join(APP_DATA_DIR, f'{short_name}.db')
    if os.path.exists(target_db_path):
        raise FileExistsError(f'Database for {short_name} already exists')

    shutil.copyfile(CLUB_DB_TEMPLATE_PATH, target_db_path)


def _load_clubs_config_from_json():
    default_clubs = _default_clubs_config()

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
        raw_smtp = club.get('smtp', {}) or {}
        normalized_clubs.append({
            'fullName': str(club.get('fullName', short_name)).strip() or short_name,
            'shortName': short_name,
            'description': str(club.get('description', '')).strip(),
            'websiteUrl': str(club.get('websiteUrl', '')).strip(),
            'adminEmail': str(club.get('adminEmail', '')).strip(),
            'logoUrl': str(club.get('logoUrl', '')).strip() or (get_club_logo_url(short_name) if os.path.exists(get_club_logo_path(short_name)) else ''),
            'beats': normalize_beats(club.get('beats', [])),
            'smtp': {
                'host': str(raw_smtp.get('host', '')).strip(),
                'port': int(raw_smtp.get('port', 587)) if str(raw_smtp.get('port', 587)).isdigit() else 587,
                'username': str(raw_smtp.get('username', '')).strip(),
                'password': str(raw_smtp.get('password', '')).strip(),
                'fromEmail': str(raw_smtp.get('fromEmail', '')).strip(),
                'fromName': str(raw_smtp.get('fromName', '')).strip(),
                'useSsl': bool(raw_smtp.get('useSsl', False)),
                'useTls': bool(raw_smtp.get('useTls', True)),
            },
        })

    return normalized_clubs or default_clubs


def _load_clubs_config_from_postgres():
    backend = get_postgres_backend()
    session = backend['session_factory']()
    clubs_table = backend['clubs_table']
    smtp_table = backend['club_smtp_settings_table']
    beats_table = backend['club_beats_table']

    try:
        club_rows = session.execute(
            select(clubs_table).where(clubs_table.c.is_active.is_(True)).order_by(clubs_table.c.short_name.asc())
        ).fetchall()
        if not club_rows:
            return []

        club_ids = [row.id for row in club_rows]
        smtp_rows = session.execute(
            select(smtp_table).where(smtp_table.c.club_id.in_(club_ids))
        ).fetchall()
        beat_rows = session.execute(
            select(beats_table).where(beats_table.c.club_id.in_(club_ids)).order_by(beats_table.c.club_id.asc(), beats_table.c.beat_name.asc())
        ).fetchall()
    finally:
        session.close()

    smtp_by_club_id = {row.club_id: row for row in smtp_rows}
    beats_by_club_id = {}
    for row in beat_rows:
        beats_by_club_id.setdefault(row.club_id, []).append({
            'Beat_Name': row.beat_name or '',
            'Beat_ID': row.beat_id or '',
            'River': row.river or '',
            'Position': row.position or '',
            'Beat_Upstream': row.beat_upstream or '',
            'Beat_Downstream': row.beat_downstream or '',
            'Beat_Description': row.beat_description or '',
            'Detailed_Description': row.detailed_description or '',
            'Beat_Upstream_Latitude': row.beat_upstream_latitude or '',
            'Beat_Upstream_Longitude': row.beat_upstream_longitude or '',
            'Beat_Downstream_Latitude': row.beat_downstream_latitude or '',
            'Beat_Downstream_Longitude': row.beat_downstream_longitude or '',
            'Parking_Locations': row.parking_locations or [],
        })

    normalized_clubs = []
    for row in club_rows:
        smtp_row = smtp_by_club_id.get(row.id)
        normalized_clubs.append({
            'fullName': row.full_name or row.short_name,
            'shortName': row.short_name,
            'description': row.description or '',
            'websiteUrl': row.website_url or '',
            'adminEmail': row.admin_email or '',
            'logoUrl': row.logo_url or '',
            'beats': normalize_beats(beats_by_club_id.get(row.id, [])),
            'smtp': {
                'host': getattr(smtp_row, 'host', '') or '',
                'port': getattr(smtp_row, 'port', 587) or 587,
                'username': getattr(smtp_row, 'username', '') or '',
                'password': getattr(smtp_row, 'password', '') or '',
                'fromEmail': getattr(smtp_row, 'from_email', '') or '',
                'fromName': getattr(smtp_row, 'from_name', '') or '',
                'useSsl': bool(getattr(smtp_row, 'use_ssl', False)) if smtp_row is not None else False,
                'useTls': bool(getattr(smtp_row, 'use_tls', True)) if smtp_row is not None else True,
            },
        })

    return normalized_clubs


def _load_server_config_from_json():
    default_config = _default_server_config()

    if not os.path.exists(SERVER_CONFIG_PATH):
        return default_config

    try:
        with open(SERVER_CONFIG_PATH, 'r', encoding='utf-8') as config_file:
            loaded_config = json.load(config_file)
    except (OSError, json.JSONDecodeError):
        return default_config

    merged = default_config.copy()
    for section in ('server', 'tls', 'startup', 'runtime', 'logging'):
        merged[section] = {**default_config.get(section, {}), **loaded_config.get(section, {})}
    if 'admin' in loaded_config:
        merged['admin'] = loaded_config['admin']
    return merged


def _load_server_config_from_postgres():
    default_config = _default_server_config()
    backend = get_postgres_backend()
    session = backend['session_factory']()
    app_settings_table = backend['app_settings_table']

    try:
        row = session.execute(
            select(app_settings_table.c.value).where(
                and_(app_settings_table.c.scope == 'global', app_settings_table.c.key == 'server_config')
            )
        ).first()
    finally:
        session.close()

    loaded_config = row[0] if row else {}
    if not isinstance(loaded_config, dict):
        return default_config

    merged = default_config.copy()
    for section in ('server', 'tls', 'startup', 'runtime', 'logging'):
        merged[section] = {**default_config.get(section, {}), **loaded_config.get(section, {})}
    if 'admin' in loaded_config:
        merged['admin'] = loaded_config['admin']
    return merged


def load_clubs_config():
    if is_postgres_reads_enabled():
        try:
            postgres_clubs = _load_clubs_config_from_postgres()
            if postgres_clubs:
                return postgres_clubs
        except Exception as exc:
            app.logger.warning(f'Failed to load clubs from PostgreSQL, falling back to JSON: {exc}')
    return _load_clubs_config_from_json()


def get_smtp_config_for_club(club_short_name):
    """Return SMTP settings for a club, falling back to environment variables."""
    clubs = load_clubs_config()
    club_cfg = next((c for c in clubs if c.get('shortName') == club_short_name), {})
    smtp = club_cfg.get('smtp', {}) or {}

    host      = smtp.get('host', '').strip()     or os.getenv('SMTP_HOST', '').strip()
    port_raw  = str(smtp.get('port', '') or os.getenv('SMTP_PORT', '587')).strip()
    username  = smtp.get('username', '').strip()  or os.getenv('SMTP_USERNAME', '').strip()
    password  = smtp.get('password', '').strip()  or os.getenv('SMTP_PASSWORD', '').strip()
    from_email = smtp.get('fromEmail', '').strip() or os.getenv('SMTP_FROM_EMAIL', username).strip()
    from_name  = smtp.get('fromName', '').strip()  or os.getenv('SMTP_FROM_NAME', f'{club_short_name} Newsletter').strip()

    # Boolean flags: club config takes precedence when explicitly set, else env vars
    if 'useSsl' in smtp:
        use_ssl = bool(smtp['useSsl'])
    else:
        use_ssl = os.getenv('SMTP_USE_SSL', 'false').strip().lower() in {'1', 'true', 'yes', 'on'}

    if 'useTls' in smtp:
        use_tls = bool(smtp['useTls'])
    else:
        use_tls = os.getenv('SMTP_USE_TLS', 'true').strip().lower() in {'1', 'true', 'yes', 'on'}

    try:
        port = int(port_raw)
    except ValueError:
        port = 587

    return {
        'host': host,
        'port': port,
        'username': username,
        'password': password,
        'fromEmail': from_email,
        'fromName': from_name,
        'useSsl': use_ssl,
        'useTls': use_tls,
    }


def load_server_config():
    if is_postgres_reads_enabled():
        try:
            return _load_server_config_from_postgres()
        except Exception as exc:
            app.logger.warning(f'Failed to load server config from PostgreSQL, falling back to JSON: {exc}')
    return _load_server_config_from_json()

def save_clubs_config(clubs):
    """Persist clubs config to PostgreSQL when enabled, else to clubs.config.json."""
    if not is_postgres_writes_enabled():
        with open(CLUBS_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump({'clubs': clubs}, f, indent=2)
        return

    backend = get_postgres_backend()
    session = backend['session_factory']()
    clubs_table = backend['clubs_table']
    smtp_table = backend['club_smtp_settings_table']
    beats_table = backend['club_beats_table']

    try:
        existing_rows = session.execute(select(clubs_table.c.id, clubs_table.c.short_name)).fetchall()
        existing_by_short_name = {row.short_name: row.id for row in existing_rows}

        incoming_short_names = set()
        for club in clubs:
            short_name = str(club.get('shortName', '')).strip()
            if not short_name:
                continue
            incoming_short_names.add(short_name)

            club_values = {
                'full_name': str(club.get('fullName', short_name)).strip() or short_name,
                'description': str(club.get('description', '')).strip(),
                'website_url': str(club.get('websiteUrl', '')).strip(),
                'admin_email': str(club.get('adminEmail', '')).strip(),
                'logo_url': str(club.get('logoUrl', '')).strip(),
                'is_active': True,
            }

            if short_name in existing_by_short_name:
                club_id = existing_by_short_name[short_name]
                session.execute(
                    clubs_table.update().where(clubs_table.c.id == club_id).values(**club_values)
                )
            else:
                club_id = session.execute(
                    clubs_table.insert().values(short_name=short_name, **club_values).returning(clubs_table.c.id)
                ).scalar_one()
                existing_by_short_name[short_name] = club_id

            raw_smtp = club.get('smtp', {}) if isinstance(club.get('smtp', {}), dict) else {}
            smtp_values = {
                'host': str(raw_smtp.get('host', '')).strip(),
                'port': int(raw_smtp.get('port', 587)) if str(raw_smtp.get('port', 587)).isdigit() else 587,
                'username': str(raw_smtp.get('username', '')).strip(),
                'password': str(raw_smtp.get('password', '')).strip(),
                'from_email': str(raw_smtp.get('fromEmail', '')).strip(),
                'from_name': str(raw_smtp.get('fromName', '')).strip(),
                'use_ssl': bool(raw_smtp.get('useSsl', False)),
                'use_tls': bool(raw_smtp.get('useTls', True)),
            }

            updated = session.execute(
                smtp_table.update().where(smtp_table.c.club_id == club_id).values(**smtp_values)
            )
            if updated.rowcount == 0:
                session.execute(smtp_table.insert().values(club_id=club_id, **smtp_values))

            session.execute(beats_table.delete().where(beats_table.c.club_id == club_id))
            beat_rows = []
            for beat in normalize_beats(club.get('beats', [])):
                beat_rows.append({
                    'club_id': club_id,
                    'beat_name': str(beat.get('Beat_Name', '')).strip(),
                    'beat_id': str(beat.get('Beat_ID', '')).strip(),
                    'river': str(beat.get('River', '')).strip(),
                    'position': str(beat.get('Position', '')).strip(),
                    'beat_upstream': str(beat.get('Beat_Upstream', '')).strip(),
                    'beat_downstream': str(beat.get('Beat_Downstream', '')).strip(),
                    'beat_description': str(beat.get('Beat_Description', '')).strip(),
                    'detailed_description': str(beat.get('Detailed_Description', '')).strip(),
                    'beat_upstream_latitude': str(beat.get('Beat_Upstream_Latitude', '')).strip(),
                    'beat_upstream_longitude': str(beat.get('Beat_Upstream_Longitude', '')).strip(),
                    'beat_downstream_latitude': str(beat.get('Beat_Downstream_Latitude', '')).strip(),
                    'beat_downstream_longitude': str(beat.get('Beat_Downstream_Longitude', '')).strip(),
                    'parking_locations': beat.get('Parking_Locations', []),
                })
            if beat_rows:
                session.execute(beats_table.insert(), beat_rows)

        removed_short_names = [name for name in existing_by_short_name.keys() if name not in incoming_short_names]
        if removed_short_names:
            session.execute(clubs_table.delete().where(clubs_table.c.short_name.in_(removed_short_names)))

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_admin_config():
    """Return admin credentials from server config, with safe defaults."""
    config = load_server_config()
    return config.get('admin', {'username': 'admin', 'password': 'admin123'})

def get_column(column_name, members_table):
    """Get column from members table."""
    return members_table.c.get(column_name)


def build_member_filters(members_table, normalized_filters):
    filters = []
    for column_name, filter_value in normalized_filters.items():
        column = get_column(column_name, members_table)
        if column is None:
            continue

        if filter_value == '[BLANK]':
            filters.append(or_(column.is_(None), cast(column, String) == ''))
        else:
            filters.append(cast(column, String).ilike(wildcard_to_sql_like(filter_value), escape='\\'))

    return filters


def get_identifier_column(members_table):
    id_column = get_column('id', members_table)
    if id_column is None:
        id_column = get_column('ID', members_table)
    if id_column is None:
        id_column = get_column('Number', members_table)
    return id_column


def configure_logging(app_context=None):
    """Configure logging for the Flask application.
    
    Loads logging configuration from server.config.json and environment variables,
    then applies it to the Flask app logger and werkzeug logger.
    
    Args:
        app_context: Optional Flask app instance to configure. If not provided,
                     uses the module-level app instance. This enables the function
                     to work both at module initialization and in tests.
    """
    if app_context is None:
        app_context = app
    
    config = load_server_config()
    configured_level = config.get('logging', {}).get('level', 'INFO')
    log_level = os.getenv('LOG_LEVEL', str(configured_level)).upper()
    app_context.logger.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    for handler in app_context.logger.handlers:
        handler.setFormatter(formatter)
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)


def log_database_target(club):
    if is_postgres_reads_enabled():
        app.logger.info(json.dumps({
            'event': 'database.selected',
            'club': club,
            'backend': 'postgresql',
            'database_url_configured': bool(os.getenv('DATABASE_URL', '').strip()),
        }))
        return

    app.logger.info(json.dumps({
        'event': 'database.selected',
        'club': club,
        'backend': 'sqlite',
        'db_path': os.path.join(APP_DATA_DIR, f'{club}.db'),
    }))


def member_to_dict(member, members_table):
    return {column.name: getattr(member, column.name) for column in members_table.columns}


def _register_infrastructure_hooks(app_instance):
    """Register teardown, before_request, and after_request hooks."""
    @app_instance.teardown_appcontext
    def remove_session(exception=None):
        pass  # Individual sessions are managed per request

    @app_instance.before_request
    def start_request_timer():
        g.request_start_time = time.perf_counter()

    @app_instance.after_request
    def log_request(response):
        start_time = getattr(g, 'request_start_time', None)
        duration_ms = None
        if start_time is not None:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        app_instance.logger.info(json.dumps({
            'event': 'http.request',
            'method': request.method,
            'path': request.path,
            'query_string': request.query_string.decode('utf-8'),
            'status_code': response.status_code,
            'duration_ms': duration_ms,
        }))
        return response


def get_valid_club_short_names():
    clubs = load_clubs_config()
    return {
        str(club.get('shortName', '')).strip()
        for club in clubs
        if isinstance(club, dict) and str(club.get('shortName', '')).strip()
    }


from routes import (
    create_admin_blueprint,
    create_member_blueprint,
    create_newsletter_blueprint,
    create_public_blueprint,
    create_role_blueprint,
)


def create_app():
    """Application factory function to create and configure the Flask app.
    
    This factory enables testability and allows multiple app instances
    to be created with different configurations. Returns a fully initialized
    Flask application ready to handle requests.
    
    Returns:
        Flask: Configured Flask application instance with blueprints registered
               and infrastructure hooks installed.
    """
    app_instance = Flask(__name__)
    CORS(app_instance)

    # Build dependency injection dictionary for routes
    route_deps = {
        'APP_DATA_DIR': APP_DATA_DIR,
        'CLUB_LOGOS_DIR': CLUB_LOGOS_DIR,
        'FILTERABLE_COLUMNS': FILTERABLE_COLUMNS,
        'NEWSLETTER_TEMPLATES': NEWSLETTER_TEMPLATES,
        'NEWSLETTER_TEMPLATE_TAGS': NEWSLETTER_TEMPLATE_TAGS,
        'load_clubs_config': load_clubs_config,
        'normalize_what3words_words': normalize_what3words_words,
        'get_valid_club_short_names': get_valid_club_short_names,
        'get_club_logo_path': get_club_logo_path,
        'log_database_target': log_database_target,
        'get_read_db_for_club': get_read_db_for_club,
        'get_db_for_club': get_db_for_club,
        'get_column': get_column,
        'get_identifier_column': get_identifier_column,
        'member_to_dict': member_to_dict,
        'issue_member_token_pair': issue_member_token_pair,
        'load_member_roles': load_member_roles,
        'extract_bearer_token': extract_bearer_token,
        'revoke_member_session_token': revoke_member_session_token,
        'revoke_member_refresh_token': revoke_member_refresh_token,
        'get_member_refresh_session_from_token': get_member_refresh_session_from_token,
        'get_current_principal': get_current_principal,
        'require_authenticated': require_authenticated,
        'require_member_token_for_club': require_member_token_for_club,
        'require_permission': require_permission,
        'require_self_or_permission': require_self_or_permission,
        'wildcard_to_sql_like': wildcard_to_sql_like,
        'is_postgres_writes_enabled': is_postgres_writes_enabled,
        'get_postgres_backend': get_postgres_backend,
        '_resolve_postgres_club_id': _resolve_postgres_club_id,
        '_build_postgres_member_values': _build_postgres_member_values,
        'normalize_newsletter_filters': normalize_newsletter_filters,
        'build_member_filters': build_member_filters,
        'render_newsletter_template': render_newsletter_template,
        'get_smtp_config_for_club': get_smtp_config_for_club,
        'get_admin_config': get_admin_config,
        'issue_admin_token': issue_admin_token,
        'revoke_admin_token_from_request': revoke_admin_token_from_request,
        'require_admin_token': require_admin_token,
        'save_clubs_config': save_clubs_config,
        'save_uploaded_logo': save_uploaded_logo,
        'create_empty_club_database': create_empty_club_database,
        'normalize_beats': normalize_beats,
    }

    # Register infrastructure hooks (teardown, before_request, after_request)
    _register_infrastructure_hooks(app_instance)

    # Register blueprints for route organization by domain
    app_instance.register_blueprint(create_public_blueprint(route_deps))
    app_instance.register_blueprint(create_member_blueprint(route_deps))
    app_instance.register_blueprint(create_newsletter_blueprint(route_deps))
    app_instance.register_blueprint(create_admin_blueprint(route_deps))
    app_instance.register_blueprint(create_role_blueprint(route_deps))

    return app_instance


# Module-level instance for backward compatibility with `from app import app`
app = create_app()



if __name__ == '__main__':
    config = load_server_config()
    server_config = config.get('server', {})
    tls_config = config.get('tls', {})
    runtime_config = config.get('runtime', {})

    host = server_config.get('host', '127.0.0.1')
    port = int(server_config.get('port', 5050))
    debug = bool(runtime_config.get('debug', False))
    use_reloader = bool(runtime_config.get('useReloader', False))

    ssl_context = None
    if bool(tls_config.get('enabled', False)):
        if bool(tls_config.get('adhoc', True)):
            ssl_context = 'adhoc'
        else:
            cert_file = str(tls_config.get('certFile', '')).strip()
            key_file = str(tls_config.get('keyFile', '')).strip()
            if not cert_file or not key_file:
                raise RuntimeError('TLS enabled but certFile/keyFile are not configured in backend/server.config.json')
            cert_path = cert_file if os.path.isabs(cert_file) else os.path.join(APP_DATA_DIR, cert_file)
            key_path = key_file if os.path.isabs(key_file) else os.path.join(APP_DATA_DIR, key_file)
            if not os.path.exists(cert_path):
                raise RuntimeError(f'TLS certificate file not found: {cert_path}')
            if not os.path.exists(key_path):
                raise RuntimeError(f'TLS key file not found: {key_path}')
            ssl_context = (cert_path, key_path)

    configure_logging()
    # Databases are now initialized on-demand per club
    app.run(host=host, port=port, debug=debug, use_reloader=use_reloader, ssl_context=ssl_context)
