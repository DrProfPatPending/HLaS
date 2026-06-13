# Alembic migrations (PostgreSQL baseline)

This folder contains the initial migration scaffold for moving HLaS storage from JSON + per-club SQLite to PostgreSQL.

### Language Convention

- User-facing copy and documentation in this repository should default to British English spelling (for example: recognised, localisation, authorised).
- Keep external API/library identifiers unchanged where spelling is fixed by the platform (for example: `wp_localize_script`).

## Files

- `../alembic.ini` Alembic configuration
- `env.py` migration runtime configuration
- `versions/20260317_0001_initial_postgres_baseline.py` initial schema baseline
- `../db_models.py` SQLAlchemy metadata used for future autogenerate workflows

## Baseline schema includes

- `app_settings` for app/server configuration key-values (JSONB)
- `clubs` for club metadata
- `club_smtp_settings` for per-club SMTP config
- `club_beats` for club beat records (including parking locations as JSONB)
- `members` for member content rows (club-scoped)
- `newsletter_templates` for club-scoped templates

## Runbook

From `backend/`:

1. Set database URL:

   - `export DATABASE_URL='postgresql+psycopg://<user>:<password>@<host>:5432/<db>'`

2. Apply baseline migration:

   - `alembic upgrade head`

3. Confirm revision state:

   - `alembic current`

## Notes

- This step creates the target PostgreSQL schema only; it does not yet migrate data from existing SQLite databases or JSON files.
- Existing app runtime continues unchanged until data-access refactor/cutover is implemented.
