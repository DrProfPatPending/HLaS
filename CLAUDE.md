# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

It is tracked on `main` only and reaches the other branches through the usual merges, so keep it to facts that hold on every branch:
- On `ctc-dev` / `ctc-production`, also read CTC_SETUP.md, which holds the CTC branch and deployment facts (it isn't on `main`).
- Machine-specific notes (a server's broken venv, local paths) go in a gitignored `CLAUDE.local.md` on that machine.

## What this is
HLaS: a multi-club fishing-club membership app (clubs CTC, GAAFFS, LADFFA, TEST). Flask backend + Vue 3/Vuetify/Vite frontend (also wrapped as iOS/Android apps via Capacitor), PostgreSQL, Caddy reverse proxy, plus a WordPress site with a custom plugin (`wordpress-plugin/hlas-integration`). Use British English in user-facing copy and docs.

## Rules
- Never run `hlas_build.sh` with `--target production` or `--target ctc-production`, and never commit, merge or push to `production` or `ctc-production`, unless explicitly asked in the current conversation.
- Always pass `--local` to `hlas_build.sh` unless told otherwise: without it the script runs `git checkout <branch>` and `git reset --hard origin/<branch>`, discarding uncommitted work. The default target is `development`.
- Before reporting a change as complete, run the relevant checks and say which ones ran (and any that couldn't run):
  - backend: `make check`
  - frontend (from `frontend/`): `npx vite build --outDir <scratch dir>`, plus `node --test *.test.mjs` on branches that have frontend tests. `frontend/dist/` may contain root-owned files from Docker builds, so a plain `npm run build` can fail with `EACCES`.

## Commands
Backend (venv lives at `../backend-venv`, created by `make -C backend venv`):
- All backend tests (what CI runs): `make check` (= `make -C backend test`)
- One test file / case, from `backend/`:
  `../backend-venv/bin/python -m unittest tests.test_field_order_routes`
  `../backend-venv/bin/python -m unittest tests.test_field_order_routes.FieldOrderRoutesPersistenceTests.<method>`
- Tests are stdlib `unittest`, discovered as `backend/tests/test_*.py`; they use temp dirs / in-memory SQLAlchemy, not a live Postgres.
- If the venv is unusable, the backend image includes the tests: `docker exec -w /app hlas-backend-1 python -m unittest tests.<module>`.
- Migrations (Alembic, from `backend/`, needs `DATABASE_URL=postgresql+psycopg://...`): `alembic upgrade head`, `alembic current`. Revisions are named `YYYYMMDD_NNNN_*.py`; watch for multiple heads (there are existing merge revisions).

Frontend (from `frontend/`, Node per the root `.nvmrc`, npm 12):
- `npm run dev` — Vite on 127.0.0.1:8080, proxies `/api/*` → `http://127.0.0.1:5050` (stripping `/api`)
- `npm run build` — builds two entry points: `index.html` (member app, `src/main.js` → `App.vue`) and `admin.html` (admin app, `src/admin.js` → `AdminApp.vue`)
- Tests, where present: `*.test.mjs` in `frontend/` (Node test runner rendering components via Vite SSR with a stubbed `store.js`)
- Mobile: `npm run mobile:*` scripts; `make ios-sim` / `make ios-release` from repo root

Full stack / deployment (Docker Compose):
- `./start.sh` / `./stop.sh` — run backend + Vite dev server locally without Docker
- `make development` — tests, frontend build, dev compose (`.env.dev`, prod compose + `docker-compose.dev.yml`), health check
- `make dev-up|dev-down|dev-logs|dev-health`, `make prod-*` equivalents
- `./hlas_build.sh` — the deploy script (`--target`, `--local`, `--quick`, `--app-only`, `--nohealth`, `--clean`, `--clean-only`, …); options table in DEPLOYMENT.md
- `./health_check_prod.sh`, `./health_check_dev.sh`
- `./run_backend_script.sh <script.py> [args]` — run a backend script inside the running backend container (`hlas-backend-1`, override with `HLAS_BACKEND_CONTAINER`); see BACKEND_SCRIPTS.md

## Branches and environments
- `main` → development/testing; `production` → live VPS (`anglerconnect.cloud`), merged from `main` only after testing.
- CTC (cambridgetroutclub.org) has its own branches: develop on `ctc-dev`, promote to `ctc-production`. See CTC_SETUP.md on those branches.
- `ctc-dev` and `main` have diverged, and `main` lacks the ctc-dev stack files. To test a `main`-based change on hlastest, apply it to a branch cut from `ctc-dev` rather than building `main` there.
- What is waiting to be promoted is `git log origin/<target>..origin/<source>`, so push commits for it to be accurate. Reasons for changes live in GitHub issues and the issue logs, not in a separate tracking file.
- Caddy configs per environment live in `deploy/caddy/` (`Caddyfile.prod`, `Caddyfile.dev`, plus the CTC ones described in CTC_SETUP.md), selected by explicit volume mounts / `hlas_build.sh` target. Don't edit a production one when changing dev routing. See CADDYFILE_CONFIGURATION.md.

## Backend architecture
- `backend/app.py` holds `create_app()`, which builds a `route_deps` dict of shared helpers (DB accessors, auth checks, config loaders, normalisers) and passes it into each blueprint factory in `backend/routes/*_routes.py` (`create_<area>_blueprint(route_deps)`). New routes should take what they need from `route_deps` rather than importing from `app.py` (avoids circular imports). Gunicorn serves `app:app` on port 5050.
- Auth/RBAC: `auth/session_tokens.py` (bearer tokens, short TTLs via `HLAS_MEMBER_*_TTL_SECONDS`), `auth/principal.py`, and `security/permissions.py` — the single table of roles (`user` < `committee`, `club_admin` < `club_manager` < `app_admin` < `app_owner`) and permission strings. Guard routes with `require_permission('<perm>')` and add new permissions there.
- Root-level and `backend/` `import_*` / `sync_*` / `migrate_*` scripts are one-off data tools, normally run via `./run_backend_script.sh`.

### Data storage (PostgreSQL vs files)
- One switch: PostgreSQL mode is on when `HLAS_USE_POSTGRES_READS` is true **and** `DATABASE_URL` is set. `is_postgres_writes_enabled()` just returns the read flag; `HLAS_USE_POSTGRES_WRITES` is ignored. Every deployment runs with it on.
- Nothing is written to both stores. In PostgreSQL mode, reads and writes go only to PostgreSQL. The SQLite (`backend/<CLUB>.db` via `db/club_db.py`) and JSON branches run only when the switch is off.
- **Have a fallback branch** (`if is_postgres_*_enabled(): … else: SQLite/JSON`): members, catch returns, newsletter templates, clubs config (`clubs.config.json`), field order, app/club settings, mini-sites, public routes. When editing these routes, keep the fallback branch working.
- **PostgreSQL only, no fallback:** club documents, app users / roles / sessions (role routes return 503 without PostgreSQL), beat map rotations, backups. New features follow this pattern.
- **Files as defaults under DB rows:** `backend/field_order.json` is merged under each club's `club_field_order` row (`club_field_order` → `app_settings` global → JSON). Binary assets (logos, backgrounds, heroes, member ID photos) are DB-first with a filesystem fallback (`backend/club_logos/` etc.).
- **File → PostgreSQL sync on the first request after startup** (`_register_beats_sync_startup` / `_register_logos_sync_startup` in `app.py`; check them on your branch, as the CTC branches add an on/off switch):
  - Beats: clubs with **no** `club_beats` rows are seeded from the image's `backend/clubs.config.json`; clubs that already have beats are left alone, so beat edits made in the app survive restarts. To push JSON beat changes into an existing club, run `sync_beats_json_to_postgres.py --replace`, which deletes and re-inserts its beats, so export app edits first with `sync_beats_postgres_to_json.py`.
  - Logos and backgrounds are upserted from `club_logos/<CLUB>.png` / `<CLUB>_background.png` every time, so committing a new file is how an existing club's logo or background is changed. The app only accepts these images when a club is created (`POST /admin/clubs`); a new club's background goes only to PostgreSQL and its logo only to `club_logos/`.
- `backend/clubs.config.json` is **generated**: edit per-club sources in `backend/clubs/<CLUB>/club.json` (listed in `backend/clubs/manifest.json`), then `make clubs-build` (`make clubs-check` to validate). Containers read the config file mounted at `/config/clubs.config.json`; the startup beats sync reads the copy baked into the image.
- Exporting with `sync_beats_postgres_to_json.py` (`--mode aggregate|split|both`) has pitfalls:
  - It writes only the clubs active in the source database and rewrites the target config and `manifest.json` to match, so running it against a single-club database drops every other club.
  - Its output includes each club's `smtp` block, passwords included.
  - Run inside a container, its default paths are in the image layer (`/app/...`, not bind-mounted), so the output is lost when the container is recreated.

  Safe pattern: export to temp paths (`--config-path` pointing at a copy of the current config, plus `--clubs-dir` and `--manifest-path`), `docker cp` the result out, merge only the club you need into `backend/clubs/<CLUB>/club.json` and `backend/clubs.config.json`, and check its `smtp` block has no password before committing.

## Frontend architecture
- Two separate SPAs sharing `src/`: member app (`components/*.vue`, incl. `MiniSite/` public club pages under `/club/<CODE>/`) and admin app (`components/admin/`, API in `services/adminApi.js`).
- `src/store.js` is the shared reactive store and API base for the member app (club context, permissions, date formatting, `calculateAgeFromDOB`, default member sort). Member-facing data requests pass `?club=<SHORT_NAME>`.
- In Docker, the frontend is served behind Caddy with the backend at `/api`.
- Mini-site HTML content is sanitised with DOMPurify (`components/MiniSite/sanitizeMiniSiteContent.js`).

## Docs and issue tracking
- README.md (feature changelog), DEPLOYMENT.md, MINI_SITE*.md, BACKUP_SYSTEM.md, WORDPRESS_INTEGRATION_*.md cover their areas in depth; CTC_SETUP.md on the CTC branches.
- Issues: GitHub issues are the source of truth. `CTC_CHAIRMAN_FEEDBACK_ISSUE_LOG.md` indexes CTC feedback; shared-code changes get a `CORE-NN` row in `CORE_ISSUE_LOG.md` that references the club item.
