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
import uuid
import re
import shutil
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

app = Flask(__name__)
CORS(app)

# Store database configurations per club in Flask's g object
DB_DIR = os.path.dirname(__file__)
APP_DATA_DIR = os.getenv('HLAS_DATA_DIR', DB_DIR)
FILTERABLE_COLUMNS = ['ID', 'Number', 'Members_Name', 'Member_Type', 'Paid_Up_2026', 'Paused', 'E_Mail', 'Mobile', 'Car_Reg', 'EA_Licence', 'Licence_Exp', 'Resigned']
LEGACY_TO_POSTGRES_MEMBER_COLUMNS = {
    'ID': 'legacy_id',
    'Number': 'number',
    'Members_Name': 'members_name',
    'Title': 'title',
    'First_Name': 'first_name',
    'Last_Name': 'last_name',
    'Photo_Path': 'photo_path',
    'Preferred_Name': 'preferred_name',
    'First_Names': 'first_names',
    'Paused': 'paused',
    'Resigned': 'resigned',
    'Member_Type': 'member_type',
    'Subs_Expected': 'subs_expected',
    'Subs_paid': 'subs_paid',
    'Join_Fee': 'join_fee',
    'Paid_Up_2026': 'paid_up_2026',
    'Photo_Received': 'photo_received',
    'In_WhatsApp': 'in_whatsapp',
    'In_FB': 'in_fb',
    'Date_of_Birth': 'date_of_birth',
    'Age': 'age',
    'New_Member_2026': 'new_member_2026',
    'Paid_up_Card_Sent': 'paid_up_card_sent',
    'CR2023': 'cr2023',
    'CR2024': 'cr2024',
    'CR2025': 'cr2025',
    'Details_Confirmed_2026': 'details_confirmed_2026',
    'Full_Address': 'full_address',
    'Address___Street_Address': 'address_street',
    'Address___Address_Line_2': 'address_line_2',
    'Address___City': 'address_city',
    'County': 'county',
    'Address___State/Prov/Region': 'address_state_region',
    'Address___ZIP/Postal': 'address_zip_postal',
    'Address___Country': 'address_country',
    'Phone': 'phone',
    'Mobile': 'mobile',
    'E_Mail': 'email',
    'EA_Licence': 'ea_licence',
    'Licence_Exp': 'licence_exp',
    'Car_Reg': 'car_reg',
    'username': 'username',
    'password': 'password',
}
NEWSLETTER_TEMPLATES = {
    'club-update': {
        'id': 'club-update',
        'name': 'Club Update',
        'subject': '<Club> Newsletter Update',
        'body': (
            'Dear <Title> <Last_Name>,\n\n'
            'This is your latest newsletter update from <Club>.\n\n'
            'Your membership number is <Number>.\n\n'
            'Kind regards,\n'
            '<Club> Committee'
        ),
    },
    'membership-reminder': {
        'id': 'membership-reminder',
        'name': 'Membership Reminder',
        'subject': '<Club> Membership Reminder',
        'body': (
            'Hello <Preferred_Name>,\n\n'
            'This is a friendly reminder from <Club> regarding your membership renewal.\n\n'
            'Name:   <Members_Name>\n'
            'Number: <Number>\n\n'
            'Please ensure your subscription is up to date.\n\n'
            'Kind regards,\n'
            '<Club> Committee'
        ),
    },
}

# Tags that can be embedded in newsletter templates as <Tag_Name>.
# Values map to either a DB column name (string) or a special key handled at render time.
NEWSLETTER_TEMPLATE_TAGS = [
    {'tag': 'Club',          'description': 'Club name',                   'source': 'special'},
    {'tag': 'Title',         'description': "Member's title (Mr/Mrs/etc)",  'source': 'column'},
    {'tag': 'First_Name',    'description': "Member's first name",          'source': 'column'},
    {'tag': 'Last_Name',     'description': "Member's last name",           'source': 'column'},
    {'tag': 'Preferred_Name','description': "Member's preferred name",      'source': 'column'},
    {'tag': 'Members_Name',  'description': 'Full name (as stored)',        'source': 'column'},
    {'tag': 'Number',        'description': 'Membership number',            'source': 'column'},
    {'tag': 'Member_Type',   'description': 'Membership type',              'source': 'column'},
    {'tag': 'E_Mail',        'description': "Member's email address",       'source': 'column'},
]
_TEMPLATE_TAG_RE = re.compile(r'<([A-Za-z_][A-Za-z0-9_]*)>')

def render_newsletter_template(template_str: str, context: dict) -> str:
    """Replace <Tag> placeholders in template_str using context dict.

    Unknown tags are left unchanged so authors can spot typos.
    """
    return _TEMPLATE_TAG_RE.sub(
        lambda m: str(context.get(m.group(1), m.group(0))),
        template_str,
    )


SERVER_CONFIG_PATH = os.path.join(APP_DATA_DIR, 'server.config.json')
CLUBS_CONFIG_PATH = os.path.join(APP_DATA_DIR, 'clubs.config.json')
CLUB_LOGOS_DIR = os.path.join(APP_DATA_DIR, 'club_logos')
CLUB_DB_TEMPLATE_PATH = os.path.join(DB_DIR, 'template.db')

# Cache for club database engines and metadata
_club_db_cache = {}
_postgres_cache = {}

# In-memory admin session tokens (cleared on restart)
_admin_tokens = set()
_member_tokens_fallback = {}
_member_refresh_tokens_fallback = {}

MEMBER_TOKEN_TTL_SECONDS = int(os.getenv('HLAS_MEMBER_TOKEN_TTL_SECONDS', '43200'))
MEMBER_REFRESH_TOKEN_TTL_SECONDS = int(os.getenv('HLAS_MEMBER_REFRESH_TOKEN_TTL_SECONDS', str(60 * 60 * 24 * 30)))


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


def normalize_beats(beats_source):
    if not isinstance(beats_source, list):
        return []

    normalized = []
    for beat in beats_source:
        if not isinstance(beat, dict):
            continue

        beat_upstream = str(beat.get('Beat_Upstream', '')).strip()
        beat_downstream = str(beat.get('Beat_Downstream', '')).strip()

        normalized.append({
            'Beat_Name': str(beat.get('Beat_Name', '')).strip(),
            'Beat_ID': str(beat.get('Beat_ID', '')).strip(),
            'River': str(beat.get('River', '')).strip(),
            'Position': str(beat.get('Position', '')).strip(),
            'Beat_Upstream': normalize_what3words_value(beat_upstream),
            'Beat_Downstream': normalize_what3words_value(beat_downstream),
            'Beat_Description': str(beat.get('Beat_Description', '')).strip(),
            'Detailed_Description': str(beat.get('Detailed_Description', '')).strip(),
            'Beat_Upstream_Latitude': str(beat.get('Beat_Upstream_Latitude', '')).strip(),
            'Beat_Upstream_Longitude': str(beat.get('Beat_Upstream_Longitude', '')).strip(),
            'Beat_Downstream_Latitude': str(beat.get('Beat_Downstream_Latitude', '')).strip(),
            'Beat_Downstream_Longitude': str(beat.get('Beat_Downstream_Longitude', '')).strip(),
            'Parking_Locations': normalize_parking_locations(beat.get('Parking_Locations', [])),
        })

    return normalized


def normalize_what3words_value(raw_value):
    value = str(raw_value or '').strip()
    if not value:
        return ''

    without_slashes = re.sub(r'^/+', '', value).strip()
    words = [word.strip() for word in without_slashes.split('.')]

    if len(words) != 3 or any(not word for word in words):
        return value

    if not all(re.fullmatch(r'[A-Za-z]+', word) for word in words):
        return value

    return f"///{'.'.join(word.lower() for word in words)}"


def normalize_parking_locations(parking_source):
    if not isinstance(parking_source, list):
        return []

    normalized = []
    for location in parking_source:
        if not isinstance(location, dict):
            continue
        normalized.append({
            'Name': str(location.get('Name', '')).strip(),
            'Location': normalize_what3words_words(location.get('Location', '')),
            'Description': str(location.get('Description', '')).strip(),
            'Latitude': str(location.get('Latitude', '')).strip(),
            'Longitude': str(location.get('Longitude', '')).strip(),
        })

    return normalized


def normalize_what3words_words(raw_value):
    value = str(raw_value or '').strip()
    if not value:
        return ''

    without_slashes = re.sub(r'^/+', '', value).strip().lower()
    words = [word.strip() for word in without_slashes.split('.')]

    if len(words) != 3 or any(not word for word in words):
        return ''

    if not all(re.fullmatch(r'[a-z]+', word) for word in words):
        return ''

    return '.'.join(words)


def is_postgres_reads_enabled():
    flag_value = os.getenv('HLAS_USE_POSTGRES_READS', os.getenv('USE_POSTGRES_READS', '')).strip().lower()
    return flag_value in {'1', 'true', 'yes', 'on'} and bool(os.getenv('DATABASE_URL', '').strip())


def is_postgres_writes_enabled():
    return is_postgres_reads_enabled()


def _hash_member_token(raw_token):
    return hashlib.sha256(str(raw_token or '').encode('utf-8')).hexdigest()


def _utcnow():
    return datetime.now(timezone.utc)


def _member_token_expiry():
    return _utcnow() + timedelta(seconds=max(60, MEMBER_TOKEN_TTL_SECONDS))


def _member_refresh_token_expiry():
    return _utcnow() + timedelta(seconds=max(300, MEMBER_REFRESH_TOKEN_TTL_SECONDS))


def ensure_postgres_member_sessions_table(engine):
    create_table_sql = text(
        """
        CREATE TABLE IF NOT EXISTS member_sessions (
            token_hash VARCHAR(64) PRIMARY KEY,
            member_id INTEGER NOT NULL,
            club_short_name VARCHAR(64) NOT NULL,
            username VARCHAR(255),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL,
            last_seen_at TIMESTAMPTZ,
            revoked_at TIMESTAMPTZ
        )
        """
    )
    create_index_sql = text(
        """
        CREATE INDEX IF NOT EXISTS ix_member_sessions_club_member
        ON member_sessions (club_short_name, member_id)
        """
    )
    with engine.begin() as conn:
        conn.execute(create_table_sql)
        conn.execute(create_index_sql)


def ensure_postgres_member_refresh_sessions_table(engine):
    create_table_sql = text(
        """
        CREATE TABLE IF NOT EXISTS member_refresh_sessions (
            refresh_token_hash VARCHAR(64) PRIMARY KEY,
            member_id INTEGER NOT NULL,
            club_short_name VARCHAR(64) NOT NULL,
            username VARCHAR(255),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL,
            last_seen_at TIMESTAMPTZ,
            revoked_at TIMESTAMPTZ
        )
        """
    )
    create_index_sql = text(
        """
        CREATE INDEX IF NOT EXISTS ix_member_refresh_sessions_club_member
        ON member_refresh_sessions (club_short_name, member_id)
        """
    )
    with engine.begin() as conn:
        conn.execute(create_table_sql)
        conn.execute(create_index_sql)


def get_postgres_backend():
    database_url = os.getenv('DATABASE_URL', '').strip()
    if not database_url:
        raise RuntimeError('DATABASE_URL is not configured')

    cache_key = database_url
    if cache_key not in _postgres_cache:
        engine = create_engine(database_url, future=True)
        ensure_postgres_member_sessions_table(engine)
        ensure_postgres_member_refresh_sessions_table(engine)
        metadata = MetaData()
        metadata.reflect(bind=engine, only=['app_settings', 'clubs', 'club_smtp_settings', 'club_beats', 'members', 'newsletter_templates', 'member_sessions', 'member_refresh_sessions'])
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        _postgres_cache[cache_key] = {
            'engine': engine,
            'metadata': metadata,
            'session_factory': session_factory,
            'app_settings_table': metadata.tables['app_settings'],
            'clubs_table': metadata.tables['clubs'],
            'club_smtp_settings_table': metadata.tables['club_smtp_settings'],
            'club_beats_table': metadata.tables['club_beats'],
            'members_table': metadata.tables['members'],
            'newsletter_templates_table': metadata.tables['newsletter_templates'],
            'member_sessions_table': metadata.tables['member_sessions'],
            'member_refresh_sessions_table': metadata.tables['member_refresh_sessions'],
            'read_club_cache': {},
        }
    return _postgres_cache[cache_key]


def _resolve_postgres_club_id(session, short_name):
    backend = get_postgres_backend()
    clubs_table = backend['clubs_table']
    return session.execute(
        select(clubs_table.c.id).where(
            and_(clubs_table.c.short_name == short_name, clubs_table.c.is_active.is_(True))
        )
    ).scalar_one_or_none()


def _build_postgres_member_values(data):
    values = {}
    for field_name, field_value in (data or {}).items():
        postgres_column = LEGACY_TO_POSTGRES_MEMBER_COLUMNS.get(field_name)
        if not postgres_column:
            continue
        if field_name == 'password' and field_value:
            if not str(field_value).startswith(('scrypt:', 'pbkdf2:', 'bcrypt:')):
                field_value = generate_password_hash(str(field_value))
        if postgres_column == 'date_of_birth':
            field_value = _parse_date(field_value)
        values[postgres_column] = field_value
    return values


def _parse_date(raw_value):
    value = str(raw_value or '').strip()
    if not value:
        return None

    from datetime import datetime

    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(value).date()
    except Exception:
        return None


def _default_clubs_config():
    return [
        {
            'fullName': 'GAAFFS',
            'shortName': 'GAAFFS',
            'description': 'GAAFFS fishing club members',
            'websiteUrl': 'https://example.com/gaaffs',
            'adminEmail': 'admin@gaaffs.example.com',
            'logoUrl': '',
            'beats': [],
        },
        {
            'fullName': 'CTC',
            'shortName': 'CTC',
            'description': 'CTC fishing club members',
            'websiteUrl': 'https://example.com/ctc',
            'adminEmail': 'admin@ctc.example.com',
            'logoUrl': '',
            'beats': [],
        },
    ]


def _default_server_config():
    return {
        'server': {
            'host': '127.0.0.1',
            'port': 5050,
            'url': 'http://127.0.0.1:5050',
        },
        'tls': {
            'enabled': False,
            'adhoc': True,
            'certFile': '',
            'keyFile': '',
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


def get_read_db_for_club(club):
    if not is_postgres_reads_enabled():
        return get_db_for_club(club)

    backend = get_postgres_backend()
    if club not in backend['read_club_cache']:
        session = backend['session_factory']()
        clubs_table = backend['clubs_table']
        members_base_table = backend['members_table']
        newsletter_base_table = backend['newsletter_templates_table']

        try:
            club_id = session.execute(
                select(clubs_table.c.id).where(
                    and_(clubs_table.c.short_name == club, clubs_table.c.is_active.is_(True))
                )
            ).scalar_one_or_none()
        finally:
            session.close()

        if club_id is None:
            raise RuntimeError(f'Club {club} not found in PostgreSQL')

        mapper_registry = registry()
        members_query = select(
            members_base_table.c.id.label('ID'),
            members_base_table.c.number.label('Number'),
            members_base_table.c.members_name.label('Members_Name'),
            members_base_table.c.title.label('Title'),
            members_base_table.c.first_name.label('First_Name'),
            members_base_table.c.last_name.label('Last_Name'),
            members_base_table.c.photo_path.label('Photo_Path'),
            members_base_table.c.preferred_name.label('Preferred_Name'),
            members_base_table.c.first_names.label('First_Names'),
            members_base_table.c.paused.label('Paused'),
            members_base_table.c.resigned.label('Resigned'),
            members_base_table.c.member_type.label('Member_Type'),
            members_base_table.c.subs_expected.label('Subs_Expected'),
            members_base_table.c.subs_paid.label('Subs_paid'),
            members_base_table.c.join_fee.label('Join_Fee'),
            members_base_table.c.paid_up_2026.label('Paid_Up_2026'),
            members_base_table.c.photo_received.label('Photo_Received'),
            members_base_table.c.in_whatsapp.label('In_WhatsApp'),
            members_base_table.c.in_fb.label('In_FB'),
            cast(members_base_table.c.date_of_birth, String).label('Date_of_Birth'),
            members_base_table.c.age.label('Age'),
            members_base_table.c.new_member_2026.label('New_Member_2026'),
            members_base_table.c.paid_up_card_sent.label('Paid_up_Card_Sent'),
            members_base_table.c.cr2023.label('CR2023'),
            members_base_table.c.cr2024.label('CR2024'),
            members_base_table.c.cr2025.label('CR2025'),
            members_base_table.c.details_confirmed_2026.label('Details_Confirmed_2026'),
            members_base_table.c.full_address.label('Full_Address'),
            members_base_table.c.address_street.label('Address___Street_Address'),
            members_base_table.c.address_line_2.label('Address___Address_Line_2'),
            members_base_table.c.address_city.label('Address___City'),
            members_base_table.c.county.label('County'),
            members_base_table.c.address_state_region.label('Address___State/Prov/Region'),
            members_base_table.c.address_zip_postal.label('Address___ZIP/Postal'),
            members_base_table.c.address_country.label('Address___Country'),
            members_base_table.c.phone.label('Phone'),
            members_base_table.c.mobile.label('Mobile'),
            members_base_table.c.email.label('E_Mail'),
            members_base_table.c.ea_licence.label('EA_Licence'),
            members_base_table.c.licence_exp.label('Licence_Exp'),
            members_base_table.c.car_reg.label('Car_Reg'),
            members_base_table.c.username.label('username'),
            members_base_table.c.password.label('password'),
        ).where(members_base_table.c.club_id == club_id).subquery(f'{club.lower()}_members_read')

        newsletter_query = select(
            newsletter_base_table.c.template_key.label('id'),
            newsletter_base_table.c.name.label('name'),
            newsletter_base_table.c.subject.label('subject'),
            newsletter_base_table.c.body.label('body'),
        ).where(newsletter_base_table.c.club_id == club_id).subquery(f'{club.lower()}_newsletter_templates_read')

        class Member:
            pass

        mapper_registry.map_imperatively(Member, members_query, primary_key=[members_query.c.ID])
        backend['read_club_cache'][club] = {
            'club_id': club_id,
            'mapper_registry': mapper_registry,
            'members_table': members_query,
            'newsletter_templates_table': newsletter_query,
            'Member': Member,
        }

    cache = backend['read_club_cache'][club]
    session = backend['session_factory']()
    return {
        'session': session,
        'engine': backend['engine'],
        'members_table': cache['members_table'],
        'newsletter_templates_table': cache['newsletter_templates_table'],
        'Member': cache['Member'],
        'mapper_registry': cache['mapper_registry'],
        'club_id': cache['club_id'],
    }


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


def require_admin_token():
    """Return True if the request carries a valid admin Bearer token."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    return auth_header[7:] in _admin_tokens


def _extract_bearer_token():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return ''
    return auth_header[7:].strip()


def issue_member_session_token(member_id, club_short_name, username):
    token_value = secrets.token_urlsafe(32)
    token_hash = _hash_member_token(token_value)
    expires_at = _member_token_expiry()

    if is_postgres_reads_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            session.execute(
                backend['member_sessions_table'].insert().values(
                    token_hash=token_hash,
                    member_id=int(member_id),
                    club_short_name=str(club_short_name or '').strip(),
                    username=str(username or '').strip(),
                    expires_at=expires_at,
                    last_seen_at=_utcnow(),
                )
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    else:
        _member_tokens_fallback[token_hash] = {
            'member_id': int(member_id),
            'club_short_name': str(club_short_name or '').strip(),
            'username': str(username or '').strip(),
            'expires_at': expires_at,
            'revoked_at': None,
            'last_seen_at': _utcnow(),
        }

    return token_value


def issue_member_refresh_token(member_id, club_short_name, username):
    token_value = secrets.token_urlsafe(48)
    token_hash = _hash_member_token(token_value)
    expires_at = _member_refresh_token_expiry()

    if is_postgres_reads_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            session.execute(
                backend['member_refresh_sessions_table'].insert().values(
                    refresh_token_hash=token_hash,
                    member_id=int(member_id),
                    club_short_name=str(club_short_name or '').strip(),
                    username=str(username or '').strip(),
                    expires_at=expires_at,
                    last_seen_at=_utcnow(),
                )
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    else:
        _member_refresh_tokens_fallback[token_hash] = {
            'member_id': int(member_id),
            'club_short_name': str(club_short_name or '').strip(),
            'username': str(username or '').strip(),
            'expires_at': expires_at,
            'revoked_at': None,
            'last_seen_at': _utcnow(),
        }

    return token_value


def revoke_member_refresh_token(token_value):
    token_hash = _hash_member_token(token_value)
    if is_postgres_reads_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            session.execute(
                backend['member_refresh_sessions_table'].update().where(
                    backend['member_refresh_sessions_table'].c.refresh_token_hash == token_hash
                ).values(revoked_at=_utcnow())
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    else:
        row = _member_refresh_tokens_fallback.get(token_hash)
        if row is not None:
            row['revoked_at'] = _utcnow()


def get_member_refresh_session_from_token(token_value):
    token_hash = _hash_member_token(token_value)
    now_value = _utcnow()
    if is_postgres_reads_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            row = session.execute(
                select(backend['member_refresh_sessions_table']).where(
                    and_(
                        backend['member_refresh_sessions_table'].c.refresh_token_hash == token_hash,
                        backend['member_refresh_sessions_table'].c.revoked_at.is_(None),
                        backend['member_refresh_sessions_table'].c.expires_at > now_value,
                    )
                )
            ).fetchone()
            if row is None:
                return None

            session.execute(
                backend['member_refresh_sessions_table'].update().where(
                    backend['member_refresh_sessions_table'].c.refresh_token_hash == token_hash
                ).values(last_seen_at=now_value)
            )
            session.commit()
            return {
                'member_id': row.member_id,
                'club_short_name': row.club_short_name,
                'username': row.username,
            }
        finally:
            session.close()

    row = _member_refresh_tokens_fallback.get(token_hash)
    if row is None:
        return None
    if row.get('revoked_at') is not None:
        return None
    if row.get('expires_at') is None or row['expires_at'] <= now_value:
        return None
    row['last_seen_at'] = now_value
    return {
        'member_id': row.get('member_id'),
        'club_short_name': row.get('club_short_name', ''),
        'username': row.get('username', ''),
    }


def issue_member_token_pair(member_id, club_short_name, username):
    access_token = issue_member_session_token(member_id, club_short_name, username)
    refresh_token = issue_member_refresh_token(member_id, club_short_name, username)
    return {
        'token': access_token,
        'refreshToken': refresh_token,
        'expiresInSeconds': MEMBER_TOKEN_TTL_SECONDS,
        'refreshExpiresInSeconds': MEMBER_REFRESH_TOKEN_TTL_SECONDS,
    }


def revoke_member_session_token(token_value):
    token_hash = _hash_member_token(token_value)
    if is_postgres_reads_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            session.execute(
                backend['member_sessions_table'].update().where(
                    backend['member_sessions_table'].c.token_hash == token_hash
                ).values(revoked_at=_utcnow())
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    else:
        row = _member_tokens_fallback.get(token_hash)
        if row is not None:
            row['revoked_at'] = _utcnow()


def get_member_session_from_token(token_value):
    token_hash = _hash_member_token(token_value)
    now_value = _utcnow()
    if is_postgres_reads_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            row = session.execute(
                select(backend['member_sessions_table']).where(
                    and_(
                        backend['member_sessions_table'].c.token_hash == token_hash,
                        backend['member_sessions_table'].c.revoked_at.is_(None),
                        backend['member_sessions_table'].c.expires_at > now_value,
                    )
                )
            ).fetchone()
            if row is None:
                return None

            session.execute(
                backend['member_sessions_table'].update().where(
                    backend['member_sessions_table'].c.token_hash == token_hash
                ).values(last_seen_at=now_value)
            )
            session.commit()
            return {
                'member_id': row.member_id,
                'club_short_name': row.club_short_name,
                'username': row.username,
            }
        finally:
            session.close()

    row = _member_tokens_fallback.get(token_hash)
    if row is None:
        return None
    if row.get('revoked_at') is not None:
        return None
    if row.get('expires_at') is None or row['expires_at'] <= now_value:
        return None
    row['last_seen_at'] = now_value
    return {
        'member_id': row.get('member_id'),
        'club_short_name': row.get('club_short_name', ''),
        'username': row.get('username', ''),
    }


def require_member_token_for_club(club_short_name):
    token_value = _extract_bearer_token()
    if not token_value:
        return jsonify({'error': 'Unauthorized'}), 401

    session_payload = get_member_session_from_token(token_value)
    if session_payload is None:
        return jsonify({'error': 'Unauthorized'}), 401

    expected = str(club_short_name or '').strip()
    actual = str(session_payload.get('club_short_name', '')).strip()
    if expected and actual and expected != actual:
        return jsonify({'error': 'Forbidden for selected club'}), 403

    g.member_session = session_payload
    return None


def ensure_newsletter_templates_table(engine):
    """Ensure newsletter_templates table exists; create with defaults if needed."""
    inspector_metadata = MetaData()
    inspector_metadata.reflect(bind=engine)
    
    if 'newsletter_templates' not in inspector_metadata.tables:
        # Table doesn't exist - create it
        template_metadata = MetaData()
        Table(
            'newsletter_templates',
            template_metadata,
            Column('id', String, primary_key=True),
            Column('name', String, nullable=False),
            Column('subject', String, nullable=False),
            Column('body', String, nullable=False),
        )
        template_metadata.create_all(bind=engine)
        
        # Insert default templates
        with engine.connect() as conn:
            conn.execute(
                '''INSERT INTO newsletter_templates (id, name, subject, body) VALUES (?, ?, ?, ?)''',
                [
                    ('club-update', 'Club Update', '<Club> Newsletter Update',
                     'Dear <Title> <Last_Name>,\n\nThis is your latest newsletter update from <Club>.\n\nYour membership number is <Number>.\n\nKind regards,\n<Club> Committee'),
                    ('membership-reminder', 'Membership Reminder', '<Club> Membership Reminder',
                     'Hello <Preferred_Name>,\n\nThis is a friendly reminder from <Club> regarding your membership renewal.\n\nName:   <Members_Name>\nNumber: <Number>\n\nPlease ensure your subscription is up to date.\n\nKind regards,\n<Club> Committee'),
                ]
            )
            conn.commit()


def get_db_for_club(club):
    """Get or create database engine and session for the specified club."""
    if club not in _club_db_cache:
        db_path = os.path.join(APP_DATA_DIR, f'{club}.db')
        database_url = f"sqlite:///{db_path.replace(os.sep, '/')}"
        engine = create_engine(database_url, future=True)
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        
        # Ensure newsletter templates table exists
        ensure_newsletter_templates_table(engine)
        
        # Load metadata for this club's database
        mapper_registry = registry()
        metadata = mapper_registry.metadata
        members_table = Table('members', metadata, autoload_with=engine)
        newsletter_templates_table = Table('newsletter_templates', metadata, autoload_with=engine)
        
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
            'newsletter_templates_table': newsletter_templates_table,
            'Member': Member
        }
    
    cache = _club_db_cache[club]
    session = cache['session_factory']()
    return {
        'session': session,
        'engine': cache['engine'],
        'members_table': cache['members_table'],
        'newsletter_templates_table': cache['newsletter_templates_table'],
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


def normalize_newsletter_filters(filters_source):
    if not isinstance(filters_source, dict):
        return {}

    normalized = {}
    for column_name in FILTERABLE_COLUMNS:
        raw_filter = filters_source.get(column_name)
        if raw_filter is None:
            continue

        filter_value = str(raw_filter).strip()
        if not filter_value:
            continue

        if filter_value == '[BLANK]':
            normalized[column_name] = '[BLANK]'
            continue

        has_wildcard = ('*' in filter_value) or ('?' in filter_value)
        normalized[column_name] = filter_value if has_wildcard else f'*{filter_value}*'

    return normalized


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


def initialize_database(club):
    """Initialize database for a club if it doesn't exist."""
    db_path = os.path.join(APP_DATA_DIR, f'{club}.db')
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


@app.route('/w3w/coordinates', methods=['GET'])
def w3w_coordinates():
    words_param = request.args.get('words', '')
    words = normalize_what3words_words(words_param)
    if not words:
        return jsonify({'error': 'Invalid what3words address'}), 400

    api_key = os.getenv('WHAT3WORDS_API_KEY', '').strip()
    if not api_key:
        return jsonify({'error': 'WHAT3WORDS_API_KEY is not configured'}), 503

    lookup_url = (
        'https://api.what3words.com/v3/convert-to-coordinates'
        f'?words={quote(words)}&key={quote(api_key)}'
    )

    try:
        with urlopen(lookup_url, timeout=8) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode('utf-8'))
        except Exception:
            payload = {'error': str(exc)}
        return jsonify({'error': payload.get('error', 'Failed to resolve what3words')}), 502
    except URLError:
        return jsonify({'error': 'Unable to reach what3words service'}), 502
    except Exception:
        return jsonify({'error': 'Failed to resolve what3words'}), 502

    coordinates = payload.get('coordinates', {}) if isinstance(payload, dict) else {}
    lat = coordinates.get('lat')
    lng = coordinates.get('lng')
    if lat is None or lng is None:
        return jsonify({'error': 'No coordinates returned for what3words'}), 404

    return jsonify({'words': words, 'lat': lat, 'lng': lng})


@app.route('/member_photo/<club>/<path:filename>', methods=['GET'])
def member_photo(club, filename):
    # Validate club name to prevent directory traversal
    valid_clubs = get_valid_club_short_names()
    if club not in valid_clubs:
        return jsonify({'error': 'Invalid club'}), 404
    photo_dir = os.path.join(APP_DATA_DIR, 'ID_photos', club)
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
    db_info = get_read_db_for_club(club)
    session = db_info['session']
    members_table = db_info['members_table']
    Member = db_info['Member']
    
    password_column = get_column('password', members_table)
    name_column = get_column('Members_Name', members_table)
    username_column = get_column('username', members_table)
    id_column = get_identifier_column(members_table)

    if password_column is None or id_column is None or (name_column is None and username_column is None):
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
                member_id = user_dict.get(id_column.name)
                token_payload = issue_member_token_pair(member_id, club, username)
                user_dict.pop('password', None)
                return jsonify({'success': True, 'user': user_dict, **token_payload})
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
                member_id = user_dict.get(id_column.name)
                token_payload = issue_member_token_pair(member_id, club, username)
                user_dict.pop('password', None)
                return jsonify({'success': True, 'user': user_dict, **token_payload})

    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401


@app.route('/logout', methods=['POST'])
def logout():
    token_value = _extract_bearer_token()
    data = request.json or {}
    refresh_token_value = str(data.get('refreshToken', '')).strip()
    if token_value:
        try:
            revoke_member_session_token(token_value)
        except Exception:
            app.logger.warning('Failed to revoke member session token during logout', exc_info=True)
    if refresh_token_value:
        try:
            revoke_member_refresh_token(refresh_token_value)
        except Exception:
            app.logger.warning('Failed to revoke member refresh token during logout', exc_info=True)
    return jsonify({'success': True})


@app.route('/token/refresh', methods=['POST'])
def refresh_member_token():
    data = request.json or {}
    refresh_token_value = str(data.get('refreshToken', '')).strip()
    if not refresh_token_value:
        return jsonify({'error': 'refreshToken is required'}), 400

    refresh_session = get_member_refresh_session_from_token(refresh_token_value)
    if refresh_session is None:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        revoke_member_refresh_token(refresh_token_value)
    except Exception:
        app.logger.warning('Failed to rotate refresh token', exc_info=True)
        return jsonify({'error': 'Failed to refresh session'}), 500

    token_payload = issue_member_token_pair(
        refresh_session.get('member_id'),
        refresh_session.get('club_short_name'),
        refresh_session.get('username'),
    )
    return jsonify({'success': True, **token_payload})


@app.route('/members', methods=['GET'])
def get_members():
    club = request.args.get('club', 'GAAFFS')  # Default to GAAFFS if not provided
    auth_error = require_member_token_for_club(club)
    if auth_error:
        return auth_error
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    sort_by = request.args.get('sort_by')
    sort_order = request.args.get('sort_order', 'asc')

    log_database_target(club)
    db_info = get_read_db_for_club(club)
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
    auth_error = require_member_token_for_club(club)
    if auth_error:
        return auth_error
    log_database_target(club)
    if is_postgres_writes_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            club_id = _resolve_postgres_club_id(session, club)
            if club_id is None:
                return jsonify({'error': 'Invalid club selection'}), 400

            values = _build_postgres_member_values(data)
            defaults = {}
            for required_key in ('members_name', 'number', 'member_type', 'paid_up_2026'):
                if required_key not in values:
                    defaults[required_key] = ''
            session.execute(backend['members_table'].insert().values(club_id=club_id, **defaults, **values))
            session.commit()
        except Exception as exc:
            session.rollback()
            return jsonify({'error': str(exc)}), 500
        finally:
            session.close()
    else:
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
    auth_error = require_member_token_for_club(club)
    if auth_error:
        return auth_error
    log_database_target(club)
    if is_postgres_writes_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            club_id = _resolve_postgres_club_id(session, club)
            if club_id is None:
                return jsonify({'error': 'Invalid club selection'}), 400

            values = _build_postgres_member_values({k: v for k, v in data.items() if k not in {'club', 'ID', 'id'}})
            if not values:
                return jsonify({'status': 'success'})

            updated = session.execute(
                backend['members_table'].update().where(
                    and_(backend['members_table'].c.club_id == club_id, backend['members_table'].c.id == member_id)
                ).values(**values)
            )
            if updated.rowcount == 0:
                return jsonify({'error': 'Member not found'}), 404
            session.commit()
        except Exception as exc:
            session.rollback()
            return jsonify({'error': str(exc)}), 500
        finally:
            session.close()
    else:
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
    auth_error = require_member_token_for_club(club)
    if auth_error:
        return auth_error
    log_database_target(club)
    if is_postgres_writes_enabled():
        backend = get_postgres_backend()
        session = backend['session_factory']()
        try:
            club_id = _resolve_postgres_club_id(session, club)
            if club_id is None:
                return jsonify({'error': 'Invalid club selection'}), 400
            deleted = session.execute(
                backend['members_table'].delete().where(
                    and_(backend['members_table'].c.club_id == club_id, backend['members_table'].c.id == member_id)
                )
            )
            if deleted.rowcount == 0:
                return jsonify({'error': 'Member not found'}), 404
            session.commit()
        except Exception as exc:
            session.rollback()
            return jsonify({'error': str(exc)}), 500
        finally:
            session.close()
    else:
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
    auth_error = require_member_token_for_club(club)
    if auth_error:
        return auth_error
    log_database_target(club)
    db_info = get_read_db_for_club(club)
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


@app.route('/newsletter/prepare_recipients', methods=['POST'])
def prepare_newsletter_recipients():
    data = request.json or {}
    club = data.get('club', 'GAAFFS')
    auth_error = require_member_token_for_club(club)
    if auth_error:
        return auth_error
    member_ids = data.get('memberIds', [])

    if not isinstance(member_ids, list) or not member_ids:
        return jsonify({'error': 'memberIds must be a non-empty list'}), 400

    valid_clubs = get_valid_club_short_names()
    if club not in valid_clubs:
        return jsonify({'error': 'Invalid club selection'}), 400

    selected_ids = {
        str(member_id).strip()
        for member_id in member_ids
        if str(member_id).strip()
    }
    if not selected_ids:
        return jsonify({'error': 'No valid member IDs supplied'}), 400

    log_database_target(club)
    db_info = get_read_db_for_club(club)
    session = db_info['session']
    members_table = db_info['members_table']
    Member = db_info['Member']

    id_column = get_column('id', members_table)
    if id_column is None:
        id_column = get_column('ID', members_table)
    if id_column is None:
        id_column = get_column('Number', members_table)
    if id_column is None:
        return jsonify({'error': 'No identifier column available in members table'}), 500

    matched_members = session.scalars(
        select(Member).where(cast(id_column, String).in_(list(selected_ids)))
    ).all()

    email_column = get_column('E_Mail', members_table)
    if email_column is None:
        email_column = get_column('email', members_table)
    name_column = get_column('Members_Name', members_table)
    if name_column is None:
        name_column = get_column('name', members_table)
    number_column = get_column('Number', members_table)
    member_type_column = get_column('Member_Type', members_table)
    paid_up_column = get_column('Paid_Up_2026', members_table)

    recipients = []
    missing_email_count = 0
    for member in matched_members:
        member_payload = member_to_dict(member, members_table)
        email_value = str(member_payload.get(email_column.name, '')).strip() if email_column is not None else ''

        if not email_value:
            missing_email_count += 1
            continue

        recipients.append({
            'memberId': member_payload.get(id_column.name),
            'Number': member_payload.get(number_column.name) if number_column is not None else '',
            'Members_Name': member_payload.get(name_column.name) if name_column is not None else '',
            'E_Mail': email_value,
            'Member_Type': member_payload.get(member_type_column.name) if member_type_column is not None else '',
            'Paid_Up_2026': member_payload.get(paid_up_column.name) if paid_up_column is not None else '',
        })

    return jsonify({
        'club': club,
        'selectedCount': len(selected_ids),
        'matchedCount': len(matched_members),
        'emailableCount': len(recipients),
        'missingEmailCount': missing_email_count,
        'emailWorkflowStatus': 'prepared_not_sent',
        'recipients': recipients,
    })


@app.route('/newsletter/templates', methods=['GET'])
def get_newsletter_templates():
    club = request.args.get('club', 'GAAFFS')
    auth_error = require_member_token_for_club(club)
    if auth_error:
        return auth_error
    # Sample context used to render the preview shown in the UI
    sample_context = {
        'Club':           club,
        'Title':          'Mr',
        'First_Name':     'John',
        'Last_Name':      'Smith',
        'Preferred_Name': 'John',
        'Members_Name':   'John Smith',
        'Number':         '42',
        'Member_Type':    'Standard',
        'E_Mail':         'john.smith@example.com',
    }

    try:
        db_info = get_read_db_for_club(club)
        session = db_info['session']
        newsletter_templates_table = db_info['newsletter_templates_table']
        
        # Fetch templates from database
        stmt = select(newsletter_templates_table)
        rows = session.execute(stmt).fetchall()
        session.close()
        
        templates = []
        for row in rows:
            templates.append({
                'id':              row.id,
                'name':            row.name,
                'subjectTemplate': row.subject,
                'bodyTemplate':    row.body,
                'previewSubject':  render_newsletter_template(row.subject, sample_context),
                'previewBody':     render_newsletter_template(row.body, sample_context),
            })
    except Exception as e:
        app.logger.warning(f'Error loading newsletter templates from database: {e}, using defaults')
        templates = [
            {
                'id':              template['id'],
                'name':            template['name'],
                'subjectTemplate': template['subject'],
                'bodyTemplate':    template['body'],
                'previewSubject':  render_newsletter_template(template['subject'], sample_context),
                'previewBody':     render_newsletter_template(template['body'], sample_context),
            }
            for template in NEWSLETTER_TEMPLATES.values()
        ]
    
    smtp_cfg = get_smtp_config_for_club(club)
    return jsonify({
        'templates': templates,
        'availableTags': NEWSLETTER_TEMPLATE_TAGS,
        'smtpFromEmail': smtp_cfg.get('fromEmail', ''),
        'smtpFromName': smtp_cfg.get('fromName', ''),
    })


@app.route('/newsletter/templates/<template_id>', methods=['PUT'])
def update_newsletter_template(template_id):
    """Update an existing newsletter template."""
    data = request.json or {}
    club = data.get('club', 'GAAFFS')
    auth_error = require_member_token_for_club(club)
    if auth_error:
        return auth_error
    name = data.get('name', '').strip()
    subject = data.get('subject', '').strip()
    body = data.get('body', '').strip()
    
    if not name or not subject or not body:
        return jsonify({'error': 'Template name, subject, and body are required'}), 400
    
    try:
        if is_postgres_writes_enabled():
            backend = get_postgres_backend()
            session = backend['session_factory']()
            club_id = _resolve_postgres_club_id(session, club)
            if club_id is None:
                return jsonify({'error': 'Invalid club selection'}), 400
            result = session.execute(
                backend['newsletter_templates_table'].update().where(
                    and_(
                        backend['newsletter_templates_table'].c.club_id == club_id,
                        backend['newsletter_templates_table'].c.template_key == template_id,
                    )
                ).values(name=name, subject=subject, body=body)
            )
            session.commit()
            session.close()
        else:
            db_info = get_db_for_club(club)
            session = db_info['session']
            newsletter_templates_table = db_info['newsletter_templates_table']

            stmt = newsletter_templates_table.update().where(
                newsletter_templates_table.c.id == template_id
            ).values(name=name, subject=subject, body=body)
            result = session.execute(stmt)
            session.commit()
            session.close()

        if result.rowcount == 0:
            return jsonify({'error': 'Template not found'}), 404

        return jsonify({'message': 'Template updated successfully', 'id': template_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/newsletter/templates/<template_id>', methods=['DELETE'])
def delete_newsletter_template(template_id):
    """Delete a newsletter template (except defaults)."""
    club = request.args.get('club', 'GAAFFS')
    auth_error = require_member_token_for_club(club)
    if auth_error:
        return auth_error
    
    # Prevent deletion of default templates
    if template_id in ('club-update', 'membership-reminder'):
        return jsonify({'error': 'Cannot delete default templates'}), 400
    
    try:
        if is_postgres_writes_enabled():
            backend = get_postgres_backend()
            session = backend['session_factory']()
            club_id = _resolve_postgres_club_id(session, club)
            if club_id is None:
                return jsonify({'error': 'Invalid club selection'}), 400
            result = session.execute(
                backend['newsletter_templates_table'].delete().where(
                    and_(
                        backend['newsletter_templates_table'].c.club_id == club_id,
                        backend['newsletter_templates_table'].c.template_key == template_id,
                    )
                )
            )
            session.commit()
            session.close()
        else:
            db_info = get_db_for_club(club)
            session = db_info['session']
            newsletter_templates_table = db_info['newsletter_templates_table']

            stmt = newsletter_templates_table.delete().where(
                newsletter_templates_table.c.id == template_id
            )
            result = session.execute(stmt)
            session.commit()
            session.close()

        if result.rowcount == 0:
            return jsonify({'error': 'Template not found'}), 404

        return jsonify({'message': 'Template deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/newsletter/templates', methods=['POST'])
def create_newsletter_template():
    """Create a new newsletter template."""
    data = request.json or {}
    club = data.get('club', 'GAAFFS')
    auth_error = require_member_token_for_club(club)
    if auth_error:
        return auth_error
    template_id = data.get('id', '').strip()
    name = data.get('name', '').strip()
    subject = data.get('subject', '').strip()
    body = data.get('body', '').strip()
    
    if not template_id or not name or not subject or not body:
        return jsonify({'error': 'Template id, name, subject, and body are required'}), 400
    
    # Validate template_id format
    if not re.match(r'^[a-z0-9\-]+$', template_id):
        return jsonify({'error': 'Template id must contain only lowercase letters, numbers, and hyphens'}), 400
    
    try:
        if is_postgres_writes_enabled():
            backend = get_postgres_backend()
            session = backend['session_factory']()
            club_id = _resolve_postgres_club_id(session, club)
            if club_id is None:
                return jsonify({'error': 'Invalid club selection'}), 400
            session.execute(
                backend['newsletter_templates_table'].insert().values(
                    club_id=club_id,
                    template_key=template_id,
                    name=name,
                    subject=subject,
                    body=body,
                )
            )
            session.commit()
            session.close()
        else:
            db_info = get_db_for_club(club)
            session = db_info['session']
            newsletter_templates_table = db_info['newsletter_templates_table']

            stmt = newsletter_templates_table.insert().values(
                id=template_id, name=name, subject=subject, body=body
            )
            session.execute(stmt)
            session.commit()
            session.close()

        return jsonify({'message': 'Template created successfully', 'id': template_id}), 201
    except Exception as e:
        if 'UNIQUE constraint failed' in str(e) or 'already exists' in str(e):
            return jsonify({'error': 'Template id already exists'}), 409
        return jsonify({'error': str(e)}), 500


@app.route('/newsletter/filtered_member_ids', methods=['POST'])
def get_newsletter_filtered_member_ids():
    data = request.json or {}
    club = data.get('club', 'GAAFFS')
    auth_error = require_member_token_for_club(club)
    if auth_error:
        return auth_error
    filters_source = data.get('filters', {})

    valid_clubs = get_valid_club_short_names()
    if club not in valid_clubs:
        return jsonify({'error': 'Invalid club selection'}), 400

    normalized_filters = normalize_newsletter_filters(filters_source)

    log_database_target(club)
    db_info = get_read_db_for_club(club)
    session = db_info['session']
    members_table = db_info['members_table']
    Member = db_info['Member']

    id_column = get_identifier_column(members_table)
    if id_column is None:
        return jsonify({'error': 'No identifier column available in members table'}), 500

    filters = build_member_filters(members_table, normalized_filters)
    query = select(Member)
    if filters:
        query = query.where(and_(*filters))

    matched_members = session.scalars(query).all()

    member_ids = []
    for member in matched_members:
        member_payload = member_to_dict(member, members_table)
        member_id = member_payload.get(id_column.name)
        if member_id is None:
            continue
        member_id_string = str(member_id).strip()
        if member_id_string:
            member_ids.append(member_id_string)

    return jsonify({
        'club': club,
        'matchedCount': len(member_ids),
        'memberIds': member_ids,
    })


@app.route('/newsletter/send', methods=['POST'])
def send_newsletter():
    data = request.json or {}
    club = data.get('club', 'GAAFFS')
    auth_error = require_member_token_for_club(club)
    if auth_error:
        return auth_error
    template_id = str(data.get('templateId', '')).strip()
    scope = str(data.get('scope', 'all_club')).strip().lower()
    member_ids = data.get('memberIds', [])
    filters_source = data.get('filters', {})

    valid_clubs = get_valid_club_short_names()
    if club not in valid_clubs:
        return jsonify({'error': 'Invalid club selection'}), 400

    # Load template from database first, fall back to hardcoded defaults
    template = None
    try:
        db_info_tmpl = get_read_db_for_club(club)
        sess_tmpl = db_info_tmpl['session']
        nl_tbl = db_info_tmpl['newsletter_templates_table']
        row = sess_tmpl.execute(select(nl_tbl).where(nl_tbl.c.id == template_id)).fetchone()
        sess_tmpl.close()
        if row:
            template = {'id': row.id, 'name': row.name, 'subject': row.subject, 'body': row.body}
    except Exception as tmpl_exc:
        app.logger.warning(f'Could not load template from DB: {tmpl_exc}')
    if template is None:
        template = NEWSLETTER_TEMPLATES.get(template_id)
    if template is None:
        return jsonify({'error': 'Invalid newsletter template selection'}), 400

    # Resolve per-club SMTP configuration
    smtp_cfg = get_smtp_config_for_club(club)
    smtp_host      = smtp_cfg['host']
    smtp_port      = smtp_cfg['port']
    smtp_username  = smtp_cfg['username']
    smtp_password  = smtp_cfg['password']
    smtp_from_email = smtp_cfg['fromEmail']
    smtp_from_name  = smtp_cfg['fromName']
    smtp_use_ssl   = smtp_cfg['useSsl']
    smtp_use_tls   = smtp_cfg['useTls']

    if not smtp_host or not smtp_from_email:
        return jsonify({'error': f'SMTP is not configured for club {club}. Set host and fromEmail in the club SMTP settings or via environment variables.'}), 503

    log_database_target(club)
    db_info = get_read_db_for_club(club)
    session = db_info['session']
    members_table = db_info['members_table']
    Member = db_info['Member']

    id_column = get_identifier_column(members_table)
    if id_column is None:
        return jsonify({'error': 'No identifier column available in members table'}), 500

    members_query = select(Member)
    selected_count = 0

    if scope == 'selected':
        if not isinstance(member_ids, list) or not member_ids:
            return jsonify({'error': 'memberIds must be a non-empty list when scope=selected'}), 400
        selected_ids = {
            str(member_id).strip()
            for member_id in member_ids
            if str(member_id).strip()
        }
        if not selected_ids:
            return jsonify({'error': 'No valid member IDs supplied'}), 400
        selected_count = len(selected_ids)
        members_query = members_query.where(cast(id_column, String).in_(list(selected_ids)))
    elif scope == 'all_filtered':
        normalized_filters = normalize_newsletter_filters(filters_source)
        filter_clauses = build_member_filters(members_table, normalized_filters)
        if filter_clauses:
            members_query = members_query.where(and_(*filter_clauses))
    elif scope == 'all_club':
        pass
    else:
        return jsonify({'error': 'Invalid scope. Expected one of: selected, all_filtered, all_club'}), 400

    matched_members = session.scalars(members_query).all()

    email_column = get_column('E_Mail', members_table)
    if email_column is None:
        email_column = get_column('email', members_table)
    name_column = get_column('Members_Name', members_table)
    if name_column is None:
        name_column = get_column('name', members_table)
    number_column = get_column('Number', members_table)

    recipients = []
    missing_email_count = 0

    # Pre-resolve optional tag columns once, outside the loop
    tag_column_map = {}
    for tag_info in NEWSLETTER_TEMPLATE_TAGS:
        if tag_info['source'] == 'column':
            col = get_column(tag_info['tag'], members_table)
            if col is not None:
                tag_column_map[tag_info['tag']] = col

    for member in matched_members:
        member_payload = member_to_dict(member, members_table)
        email_value = str(member_payload.get(email_column.name, '')).strip() if email_column is not None else ''
        if not email_value:
            missing_email_count += 1
            continue

        # Build per-member render context covering every known tag
        member_context = {'Club': club}
        for tag, col in tag_column_map.items():
            member_context[tag] = str(member_payload.get(col.name, '') or '').strip()

        recipients.append({
            'memberId': str(member_payload.get(id_column.name, '')).strip(),
            'context': member_context,
            'email': email_value,
        })

    if not recipients:
        return jsonify({'error': 'No emailable recipients matched the selected scope'}), 400

    sent_count = 0
    failed_deliveries = []

    try:
        if smtp_use_ssl:
            smtp_client = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20)
        else:
            smtp_client = smtplib.SMTP(smtp_host, smtp_port, timeout=20)

        with smtp_client as server:
            if not smtp_use_ssl and smtp_use_tls:
                server.starttls()
            if smtp_username:
                server.login(smtp_username, smtp_password)

            for recipient in recipients:
                render_ctx = recipient['context']
                subject = render_newsletter_template(template['subject'], render_ctx)
                body    = render_newsletter_template(template['body'],    render_ctx)

                message = EmailMessage()
                message['Subject'] = subject
                message['From'] = f'{smtp_from_name} <{smtp_from_email}>'
                message['To'] = recipient['email']
                message.set_content(body)

                try:
                    server.send_message(message)
                    sent_count += 1
                except Exception as exc:
                    failed_deliveries.append({
                        'email': recipient['email'],
                        'error': str(exc),
                    })
    except Exception as exc:
        return jsonify({'error': f'Failed to connect or authenticate with SMTP server: {exc}'}), 502

    return jsonify({
        'club': club,
        'templateId': template_id,
        'scope': scope,
        'selectedCount': selected_count,
        'matchedCount': len(matched_members),
        'emailableCount': len(recipients),
        'missingEmailCount': missing_email_count,
        'sentCount': sent_count,
        'failedCount': len(failed_deliveries),
        'failedDeliveries': failed_deliveries,
        'emailWorkflowStatus': 'sent',
    })


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

    if not is_postgres_writes_enabled():
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
        'beats': [],
        'smtp': {
            'host': '',
            'port': 587,
            'username': '',
            'password': '',
            'fromEmail': str(data.get('adminEmail', '')).strip(),
            'fromName': f"{str(data.get('fullName', short_name)).strip()} Newsletter",
            'useSsl': False,
            'useTls': True,
        },
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
            existing_smtp = club.get('smtp', {})
            incoming_smtp = data.get('smtp', existing_smtp) or existing_smtp
            raw_smtp = incoming_smtp if isinstance(incoming_smtp, dict) else {}
            clubs[i] = {
                'fullName': str(data.get('fullName', club.get('fullName', short_name))).strip(),
                'shortName': short_name,
                'description': str(data.get('description', club.get('description', ''))).strip(),
                'websiteUrl': str(data.get('websiteUrl', club.get('websiteUrl', ''))).strip(),
                'adminEmail': str(data.get('adminEmail', club.get('adminEmail', ''))).strip(),
                'logoUrl': str(data.get('logoUrl', club.get('logoUrl', ''))).strip(),
                'beats': normalize_beats(data.get('beats', club.get('beats', []))),
                'smtp': {
                    'host': str(raw_smtp.get('host', existing_smtp.get('host', ''))).strip(),
                    'port': int(raw_smtp.get('port', existing_smtp.get('port', 587))) if str(raw_smtp.get('port', existing_smtp.get('port', 587))).isdigit() else 587,
                    'username': str(raw_smtp.get('username', existing_smtp.get('username', ''))).strip(),
                    'password': str(raw_smtp.get('password', existing_smtp.get('password', ''))).strip(),
                    'fromEmail': str(raw_smtp.get('fromEmail', existing_smtp.get('fromEmail', ''))).strip(),
                    'fromName': str(raw_smtp.get('fromName', existing_smtp.get('fromName', ''))).strip(),
                    'useSsl': bool(raw_smtp.get('useSsl', existing_smtp.get('useSsl', False))),
                    'useTls': bool(raw_smtp.get('useTls', existing_smtp.get('useTls', True))),
                },
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


@app.route('/admin/clubs/<short_name>/smtp', methods=['GET'])
def admin_get_club_smtp(short_name):
    """Return the SMTP configuration for a club (password masked)."""
    if not require_admin_token():
        return jsonify({'error': 'Unauthorized'}), 401
    clubs = load_clubs_config()
    club = next((c for c in clubs if c.get('shortName') == short_name), None)
    if club is None:
        return jsonify({'error': f'Club "{short_name}" not found'}), 404
    smtp = club.get('smtp', {})
    # Return config with password masked for display (not the actual value)
    return jsonify({
        'shortName': short_name,
        'smtp': {
            'host': smtp.get('host', ''),
            'port': smtp.get('port', 587),
            'username': smtp.get('username', ''),
            'passwordSet': bool(smtp.get('password', '').strip()),
            'fromEmail': smtp.get('fromEmail', ''),
            'fromName': smtp.get('fromName', ''),
            'useSsl': smtp.get('useSsl', False),
            'useTls': smtp.get('useTls', True),
        }
    })


@app.route('/admin/clubs/<short_name>/smtp', methods=['PUT'])
def admin_update_club_smtp(short_name):
    """Update the SMTP configuration for a club."""
    if not require_admin_token():
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    clubs = load_clubs_config()
    for i, club in enumerate(clubs):
        if club.get('shortName') == short_name:
            existing_smtp = club.get('smtp', {}) or {}
            new_password = str(data.get('password', '')).strip()
            # Keep existing password if blank is supplied (avoid wiping it on every save)
            if not new_password:
                new_password = existing_smtp.get('password', '')
            clubs[i]['smtp'] = {
                'host': str(data.get('host', existing_smtp.get('host', ''))).strip(),
                'port': int(data.get('port', existing_smtp.get('port', 587))) if str(data.get('port', existing_smtp.get('port', 587))).isdigit() else 587,
                'username': str(data.get('username', existing_smtp.get('username', ''))).strip(),
                'password': new_password,
                'fromEmail': str(data.get('fromEmail', existing_smtp.get('fromEmail', ''))).strip(),
                'fromName': str(data.get('fromName', existing_smtp.get('fromName', ''))).strip(),
                'useSsl': bool(data.get('useSsl', existing_smtp.get('useSsl', False))),
                'useTls': bool(data.get('useTls', existing_smtp.get('useTls', True))),
            }
            save_clubs_config(clubs)
            return jsonify({'success': True})
    return jsonify({'error': f'Club "{short_name}" not found'}), 404


@app.route('/admin/clubs/<short_name>/smtp/test', methods=['POST'])
def admin_test_club_smtp(short_name):
    """Send a test email using the club's SMTP configuration."""
    if not require_admin_token():
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    to_email = str(data.get('toEmail', '')).strip()
    if not to_email:
        return jsonify({'error': 'toEmail is required'}), 400

    smtp_cfg = get_smtp_config_for_club(short_name)
    if not smtp_cfg['host'] or not smtp_cfg['fromEmail']:
        return jsonify({'error': f'SMTP is not configured for club {short_name}'}), 503

    try:
        message = EmailMessage()
        message['Subject'] = f'HLaS SMTP Test – {short_name}'
        message['From'] = f"{smtp_cfg['fromName']} <{smtp_cfg['fromEmail']}>"
        message['To'] = to_email
        message.set_content(f'This is a test email from the HLaS application for club {short_name}.\n\nIf you received this, SMTP is configured correctly.')

        if smtp_cfg['useSsl']:
            server = smtplib.SMTP_SSL(smtp_cfg['host'], smtp_cfg['port'], timeout=20)
        else:
            server = smtplib.SMTP(smtp_cfg['host'], smtp_cfg['port'], timeout=20)

        with server:
            if not smtp_cfg['useSsl'] and smtp_cfg['useTls']:
                server.starttls()
            if smtp_cfg['username']:
                server.login(smtp_cfg['username'], smtp_cfg['password'])
            server.send_message(message)

        return jsonify({'success': True, 'message': f'Test email sent to {to_email}'})
    except Exception as exc:
        return jsonify({'error': f'SMTP test failed: {exc}'}), 502


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
