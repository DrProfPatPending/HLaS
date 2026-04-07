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
            user_id BIGINT,
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
    ensure_user_id_column_sql = text(
        """
        ALTER TABLE member_sessions
        ADD COLUMN IF NOT EXISTS user_id BIGINT
        """
    )
    create_user_index_sql = text(
        """
        CREATE INDEX IF NOT EXISTS ix_member_sessions_user_id
        ON member_sessions (user_id)
        """
    )
    ensure_user_type_column_sql = text(
        """
        ALTER TABLE member_sessions
        ADD COLUMN IF NOT EXISTS user_type VARCHAR(16) DEFAULT 'member'
        """
    )
    with engine.begin() as conn:
        conn.execute(create_table_sql)
        conn.execute(ensure_user_id_column_sql)
        conn.execute(ensure_user_type_column_sql)
        conn.execute(create_index_sql)
        conn.execute(create_user_index_sql)


def ensure_postgres_member_refresh_sessions_table(engine):
    create_table_sql = text(
        """
        CREATE TABLE IF NOT EXISTS member_refresh_sessions (
            refresh_token_hash VARCHAR(64) PRIMARY KEY,
            user_id BIGINT,
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
    ensure_user_id_column_sql = text(
        """
        ALTER TABLE member_refresh_sessions
        ADD COLUMN IF NOT EXISTS user_id BIGINT
        """
    )
    create_user_index_sql = text(
        """
        CREATE INDEX IF NOT EXISTS ix_member_refresh_sessions_user_id
        ON member_refresh_sessions (user_id)
        """
    )
    ensure_user_type_column_sql = text(
        """
        ALTER TABLE member_refresh_sessions
        ADD COLUMN IF NOT EXISTS user_type VARCHAR(16) DEFAULT 'member'
        """
    )
    with engine.begin() as conn:
        conn.execute(create_table_sql)
        conn.execute(ensure_user_id_column_sql)
        conn.execute(ensure_user_type_column_sql)
        conn.execute(create_index_sql)
        conn.execute(create_user_index_sql)


def ensure_postgres_rbac_tables(engine):
    """Ensure RBAC tables exist. Idempotent — mirrors the Alembic RBAC migration.
    Keeps the app functional whether or not Alembic has been run yet.
    """
    statements = [
        text(
            """
            CREATE TABLE IF NOT EXISTS roles (
                id         BIGSERIAL PRIMARY KEY,
                code       VARCHAR(32)  NOT NULL UNIQUE,
                name       VARCHAR(120) NOT NULL,
                scope_type VARCHAR(16)  NOT NULL DEFAULT 'club',
                is_system  BOOLEAN      NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
            )
            """
        ),
        text(
            """
            CREATE TABLE IF NOT EXISTS member_role_assignments (
                id                   BIGSERIAL PRIMARY KEY,
                user_id              BIGINT          REFERENCES app_users(id) ON DELETE SET NULL,
                role_id              BIGINT NOT NULL REFERENCES roles(id)   ON DELETE CASCADE,
                club_id              BIGINT          REFERENCES clubs(id)   ON DELETE CASCADE,
                granted_by_member_id BIGINT          REFERENCES members(id) ON DELETE SET NULL,
                granted_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                revoked_at           TIMESTAMPTZ
            )
            """
        ),
        # Partial unique indexes enforce one active assignment per (user, role) pair,
        # handling NULLable club_id correctly for global vs club-scoped roles.
        text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_mra_user_role_club_active
            ON member_role_assignments (user_id, role_id, club_id)
            WHERE club_id IS NOT NULL AND revoked_at IS NULL
            """
        ),
        text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_mra_user_role_global_active
            ON member_role_assignments (user_id, role_id)
            WHERE club_id IS NULL AND revoked_at IS NULL
            """
        ),
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_mra_user_id
            ON member_role_assignments (user_id)
            """
        ),
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_mra_club_role
            ON member_role_assignments (club_id, role_id)
            """
        ),
        text(
            """
            CREATE TABLE IF NOT EXISTS security_audit_log (
                id               BIGSERIAL PRIMARY KEY,
                actor_member_id  BIGINT      REFERENCES members(id) ON DELETE SET NULL,
                action           VARCHAR(64) NOT NULL,
                target_type      VARCHAR(32) NOT NULL,
                target_id        BIGINT,
                club_id          BIGINT      REFERENCES clubs(id) ON DELETE SET NULL,
                metadata         JSONB       NOT NULL DEFAULT '{}',
                created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        ),
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_sal_actor_member_id
            ON security_audit_log (actor_member_id)
            """
        ),
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_sal_action_created_at
            ON security_audit_log (action, created_at DESC)
            """
        ),
    ]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(stmt)


def ensure_postgres_global_user_tables(engine):
    """Ensure Phase 2 global-user tables exist (non-breaking foundation)."""
    statements = [
        text(
            """
            CREATE TABLE IF NOT EXISTS app_users (
                id               BIGSERIAL PRIMARY KEY,
                username         VARCHAR(255) NOT NULL DEFAULT '',
                email            VARCHAR(255) NOT NULL DEFAULT '',
                display_name     VARCHAR(255) NOT NULL DEFAULT '',
                password_hash    VARCHAR(255) NOT NULL DEFAULT '',
                is_active        BOOLEAN      NOT NULL DEFAULT TRUE,
                created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
            )
            """
        ),
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_app_users_username
            ON app_users (username)
            """
        ),
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_app_users_email
            ON app_users (email)
            """
        ),
        text(
            """
            CREATE TABLE IF NOT EXISTS member_user_links (
                id         BIGSERIAL PRIMARY KEY,
                user_id    BIGINT NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
                member_id  BIGINT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
                club_id    BIGINT NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
                is_primary BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_member_user_links_member_id UNIQUE (member_id),
                CONSTRAINT uq_member_user_links_user_member UNIQUE (user_id, member_id)
            )
            """
        ),
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_member_user_links_user_id
            ON member_user_links (user_id)
            """
        ),
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_member_user_links_club_id
            ON member_user_links (club_id)
            """
        ),
        # Seed app_users + member_user_links together for members that are not yet linked.
        # Uses a CTE with ROW_NUMBER to correlate inserted user IDs back to member IDs without
        # needing a legacy_member_id backlink column.
        # For fully-migrated databases this is a no-op (WHERE NOT EXISTS short-circuits).
        text(
            """
            WITH members_without_users AS (
                SELECT
                    m.id       AS member_id,
                    m.club_id,
                    COALESCE(m.username, '')                                                         AS username,
                    COALESCE(m.email, '')                                                            AS email,
                    COALESCE(NULLIF(m.members_name, ''), NULLIF(m.username, ''), 'member-' || m.id::text) AS display_name,
                    COALESCE(m.password, '')                                                         AS password_hash
                FROM members m
                WHERE NOT EXISTS (SELECT 1 FROM member_user_links mul WHERE mul.member_id = m.id)
                ORDER BY m.id
            ),
            new_users AS (
                INSERT INTO app_users (username, email, display_name, password_hash, is_active)
                SELECT username, email, display_name, password_hash, TRUE
                FROM members_without_users
                ORDER BY member_id
                ON CONFLICT DO NOTHING
                RETURNING id
            ),
            ranked_new_users AS (
                SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS rn FROM new_users
            ),
            ranked_members AS (
                SELECT member_id, club_id, ROW_NUMBER() OVER (ORDER BY member_id) AS rn
                FROM members_without_users
            )
            INSERT INTO member_user_links (user_id, member_id, club_id, is_primary)
            SELECT rnu.id, rm.member_id, rm.club_id, TRUE
            FROM ranked_new_users rnu
            JOIN ranked_members rm ON rm.rn = rnu.rn
            ON CONFLICT DO NOTHING
            """
        ),
    ]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(stmt)


def ensure_postgres_member_photos_table(engine):
    statements = [
        text(
            """
            CREATE TABLE IF NOT EXISTS member_photos (
                id         BIGSERIAL PRIMARY KEY,
                club_id    BIGINT NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
                member_id  BIGINT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
                filename   VARCHAR(512) NOT NULL DEFAULT '',
                mime_type  VARCHAR(64) NOT NULL DEFAULT 'image/jpeg',
                image_data BYTEA NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_member_photos_member_id UNIQUE (member_id)
            )
            """
        ),
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_member_photos_club_id
            ON member_photos (club_id)
            """
        ),
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_member_photos_club_filename
            ON member_photos (club_id, filename)
            """
        ),
    ]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(stmt)


def ensure_postgres_catch_returns_table(engine):
    statements = [
        text(
            """
            CREATE TABLE IF NOT EXISTS catch_returns (
                id                BIGSERIAL PRIMARY KEY,
                club_id           BIGINT NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
                member_id         BIGINT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
                session_date      DATE NOT NULL,
                beat_id           VARCHAR(64) NOT NULL DEFAULT '',
                small_trout       INTEGER NOT NULL DEFAULT 0,
                medium_trout      INTEGER NOT NULL DEFAULT 0,
                large_trout       INTEGER NOT NULL DEFAULT 0,
                small_grayling    INTEGER NOT NULL DEFAULT 0,
                medium_grayling   INTEGER NOT NULL DEFAULT 0,
                large_grayling    INTEGER NOT NULL DEFAULT 0,
                other_fish        INTEGER NOT NULL DEFAULT 0,
                flies_used        TEXT NOT NULL DEFAULT '',
                weather_conditions TEXT NOT NULL DEFAULT '',
                predator_damage   TEXT NOT NULL DEFAULT '',
                created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT ck_catch_returns_small_trout_nonneg CHECK (small_trout >= 0),
                CONSTRAINT ck_catch_returns_medium_trout_nonneg CHECK (medium_trout >= 0),
                CONSTRAINT ck_catch_returns_large_trout_nonneg CHECK (large_trout >= 0),
                CONSTRAINT ck_catch_returns_small_grayling_nonneg CHECK (small_grayling >= 0),
                CONSTRAINT ck_catch_returns_medium_grayling_nonneg CHECK (medium_grayling >= 0),
                CONSTRAINT ck_catch_returns_large_grayling_nonneg CHECK (large_grayling >= 0),
                CONSTRAINT ck_catch_returns_other_fish_nonneg CHECK (other_fish >= 0)
            )
            """
        ),
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_catch_returns_club_member_date
            ON catch_returns (club_id, member_id, session_date DESC)
            """
        ),
    ]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(stmt)


def ensure_postgres_role_assignment_user_id(engine):
    """Idempotently add user_id FK to member_role_assignments and backfill.

    Must be called AFTER both ensure_postgres_rbac_tables and
    ensure_postgres_global_user_tables so that both referenced tables exist.
    """
    statements = [
        text(
            """
            ALTER TABLE member_role_assignments
            ADD COLUMN IF NOT EXISTS user_id BIGINT REFERENCES app_users(id) ON DELETE SET NULL
            """
        ),
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_mra_user_id
            ON member_role_assignments (user_id)
            """
        ),
        # NOTE: the backfill UPDATE (SET user_id FROM member_user_links WHERE mul.member_id = mra.member_id)
        # was removed; mra.member_id was dropped in migration 0007 and all assignments
        # were backfilled during migration 0006.
        text(
            """
            WITH ranked AS (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY user_id, role_id, club_id
                        ORDER BY granted_at DESC, id DESC
                    ) AS rn
                FROM member_role_assignments
                WHERE revoked_at IS NULL
                  AND club_id IS NOT NULL
                  AND user_id IS NOT NULL
            )
            UPDATE member_role_assignments mra
            SET revoked_at = NOW()
            FROM ranked
            WHERE ranked.id = mra.id
              AND ranked.rn > 1
            """
        ),
        text(
            """
            WITH ranked AS (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY user_id, role_id
                        ORDER BY granted_at DESC, id DESC
                    ) AS rn
                FROM member_role_assignments
                WHERE revoked_at IS NULL
                  AND club_id IS NULL
                  AND user_id IS NOT NULL
            )
            UPDATE member_role_assignments mra
            SET revoked_at = NOW()
            FROM ranked
            WHERE ranked.id = mra.id
              AND ranked.rn > 1
            """
        ),
        text("DROP INDEX IF EXISTS uq_mra_member_role_club_active"),
        text("DROP INDEX IF EXISTS uq_mra_member_role_global_active"),
        text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_mra_user_role_club_active
            ON member_role_assignments (user_id, role_id, club_id)
            WHERE club_id IS NOT NULL AND revoked_at IS NULL
            """
        ),
        text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_mra_user_role_global_active
            ON member_role_assignments (user_id, role_id)
            WHERE club_id IS NULL AND revoked_at IS NULL
            """
        ),
    ]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(stmt)


def get_postgres_backend():
    database_url = os.getenv('DATABASE_URL', '').strip()
    if not database_url:
        raise RuntimeError('DATABASE_URL is not configured')

    # Ensure psycopg driver is specified (not psycopg2)
    if database_url.startswith('postgresql://') and 'psycopg' not in database_url:
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://')
    elif database_url.startswith('postgres://') and 'psycopg' not in database_url:
        database_url = database_url.replace('postgres://', 'postgresql+psycopg://')

    cache_key = database_url
    if cache_key not in _postgres_cache:
        engine = create_engine(database_url, future=True)
        ensure_postgres_member_sessions_table(engine)
        ensure_postgres_member_refresh_sessions_table(engine)
        ensure_postgres_global_user_tables(engine)
        ensure_postgres_rbac_tables(engine)
        ensure_postgres_role_assignment_user_id(engine)
        ensure_postgres_member_photos_table(engine)
        ensure_postgres_catch_returns_table(engine)
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
                'app_users',
                'member_user_links',
                'member_photos',
                'catch_returns',
                'roles',
                'member_role_assignments',
                'security_audit_log',
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
            'app_users_table': metadata.tables['app_users'],
            'member_user_links_table': metadata.tables['member_user_links'],
            'member_photos_table': metadata.tables['member_photos'],
            'catch_returns_table': metadata.tables['catch_returns'],
            'roles_table': metadata.tables['roles'],
            'member_role_assignments_table': metadata.tables['member_role_assignments'],
            'security_audit_log_table': metadata.tables['security_audit_log'],
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
