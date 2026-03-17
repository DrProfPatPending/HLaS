import os
from datetime import datetime

from sqlalchemy import MetaData, and_, create_engine, select, text
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

from core.common import LEGACY_TO_POSTGRES_MEMBER_COLUMNS

_postgres_cache = {}


def is_postgres_reads_enabled():
    flag_value = os.getenv('HLAS_USE_POSTGRES_READS', os.getenv('USE_POSTGRES_READS', '')).strip().lower()
    return flag_value in {'1', 'true', 'yes', 'on'} and bool(os.getenv('DATABASE_URL', '').strip())


def is_postgres_writes_enabled():
    return is_postgres_reads_enabled()


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
        metadata.reflect(
            bind=engine,
            only=[
                'app_settings',
                'clubs',
                'club_smtp_settings',
                'club_beats',
                'members',
                'newsletter_templates',
                'member_sessions',
                'member_refresh_sessions',
            ],
        )
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


def _parse_date(raw_value):
    value = str(raw_value or '').strip()
    if not value:
        return None

    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(value).date()
    except Exception:
        return None


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
