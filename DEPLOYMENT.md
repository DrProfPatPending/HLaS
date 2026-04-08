# Option 3 Migration: Separation of Admin/System and Member/Club User Flows

## Summary
This release implements a full separation between admin/system users and member/club users, as per Option 3 of the migration plan. The backend, frontend, and API logic have been refactored to support distinct authentication, session, and UI flows for each user type.

This guide also reflects later operational changes, including PostgreSQL-backed member photo storage, restored Membership Admin behavior, and reusable SQL verification packs.
It also now covers the Beat Details member page, dedicated field-order config for that view, and the redesigned member home dashboard.
It now also covers PostgreSQL-backed club document storage and Home dashboard document visibility.

---

## Backend Changes

- **Session Tokens:**
   - All session and refresh tokens now include a `user_type` field (`admin` or `member`).
   - Token creation and validation logic updated to propagate and check `user_type`.

- **Principal Context:**
   - The principal context (used for permission checks) now includes `user_type`.
   - All permission and authentication checks can distinguish between admin/system and member/club users.

- **API Endpoints:**
   - Admin/system endpoints (`/admin/*`) do not require a club context and are accessible to users with `app_admin` or `app_owner` roles.
   - Member/club endpoints require a valid club context, but global admin roles can access any club.
   - `require_authenticated` and `require_permission` now allow admin/system users to access endpoints without a club context.
   - `club.update` now permits `club_admin` (in addition to club manager/app admins) so Club Information edits can be performed from the member UI.
   - `club.delete` remains restricted to `app_admin` / `app_owner` and is only exposed via AdminApp/admin routes.

- **Database Migration:**
   - Alembic migration added to include `user_type` in session tables.
   - Member photos now have a PostgreSQL table (`member_photos`) for binary image storage.
   - Club documents now have a PostgreSQL table (`club_documents`) for binary file storage.

- **Document API Endpoints:**
   - `GET /documents?club=<SHORT_NAME>` for authenticated listing
   - `GET /documents/<id>/download?club=<SHORT_NAME>` for authenticated downloads
   - `POST /documents` for uploads (Club Admin+ via `document.club.manage`)
   - `DELETE /documents/<id>?club=<SHORT_NAME>` for deletes (Club Admin+)

- **Club Settings API Endpoints:**
   - `GET /club-settings?club=<SHORT_NAME>` for loading club-scoped member settings
   - `PUT /club-settings` for saving club-scoped member settings (Club Admin/Membership Admin gate via `member.club.list`)
   - Current setting scope includes Catch Return field visibility used by both the form and recent-returns table columns

---

## Frontend Changes

- **Entry Points:**
   - `/admin/` loads the admin UI (`AdminApp.vue`) for admin/system users.
   - `/` loads the member/club UI (`App.vue`) for club users.
   - Vite and nginx are configured to serve the correct entry point for each route.

- **State Management:**
   - Defensive logic in `store.js` and components to handle cases where no club context is present (for admin/system users).

- **UI Separation:**
   - Admin UI and member UI are fully separated at the entrypoint and component level.
- **App Settings (Admin):**
   - new admin tab for global application settings
   - first setting is a global **Date Format** picker
   - settings are managed via `/admin/app-settings`
- **Membership Admin:**
   - sorting and filtering restored
   - `Members_Name` opens Edit Member Details
   - `Number` opens member lookup/details
   - Previous/Next navigation in edit view now operates on the full filtered result set rather than one page
- **Beat Details:**
   - dedicated member page added for beat-focused viewing
   - dropdown labels show `<Beat ID> <Beat Name>`
   - detail page reuses Fishing Beats map behavior for upstream/downstream markers and parking locations
   - field order and visibility are stored under the `beat_details` context
   - users with `club_admin` role can Edit/Save the selected beat details
   - users with `club_admin` role can Add a new beat and Delete the currently selected beat
   - users without `club_admin` role remain read-only in Beat Details
- **Home dashboard:**
   - post-login member home page now uses a left-side vertical action stack
   - central placeholder `News and Updates` table is present until backend news/message endpoints are implemented
   - `Documents` table is shown alongside news and backed by live document APIs
- **Club Information editing:**
   - member-facing Club Information page now supports inline Edit/Save for users with `club_admin` role
   - users without `club_admin` remain read-only
   - no delete action is exposed in member UI
- **Frontend build environment:**
   - frontend package metadata now targets npm `11.12.1`
   - local startup scripts invoke `npx --yes npm@11.12.1` for the Vite dev server
   - Docker frontend builds install npm `11.12.1` before `npm ci` / `npm run build`
- **Member photo display:**
   - Edit Member Details displays the member photo again
   - photo routes support DB-first retrieval in PostgreSQL mode
- **Document management UX:**
   - Club Admin+ users can upload/delete supported files (`.pdf`, `.xls`, `.xlsx`, `.doc`, `.docx`)
   - all authenticated members can download club documents

---

## Testing

- Both admin/system and member/club login flows are supported and tested at the code level.
- Admin/system users can access all admin features without specifying a club.
- Member/club users require a valid club context for protected endpoints.

---

## Deployment Notes

- Ensure the backend can connect to the database (container DNS must resolve the database hostname).
- Run Alembic migrations to update the session tables.
- Run Alembic migrations to create/update additive tables including `member_photos`, `catch_returns`, and `club_documents`.
- Rebuild the frontend to ensure both admin and member UIs are up to date.
- Live Docker PostgreSQL is published on host port `5433` (`5433 -> 5432`).
- In member-facing deployments behind Caddy, frontend should call backend via `/api`.
- If Beat Details columns are changed in admin field-order tooling, ensure the `beat_details` context is included in the persisted `field_order` payload.
- App Settings persistence:
   - PostgreSQL mode: `app_settings(scope='global', key='app_settings')`
   - JSON fallback: `backend/app_settings.json`
- Club Settings persistence:
   - PostgreSQL mode: `app_settings(scope='club:<SHORT_NAME>', key='club_settings')`
   - JSON fallback: `backend/club_settings.json`

### Member photo deployment steps

After deploying backend code that includes `member_photos` support:

1. Ensure PostgreSQL runtime mode is enabled:
   - `DATABASE_URL` set
   - `HLAS_USE_POSTGRES_READS=true`
2. Create or refresh the `member_photos` table.
   - Normal path: run Alembic migrations.
   - Fallback path: the app runtime will create the table idempotently when PostgreSQL mode starts.
3. Import photos:

   ```bash
   cd /opt/hlas/backend
   POSTGRES_URL='postgresql+psycopg://hlas:hlas@localhost:5433/hlas' python import_member_photos_to_postgres.py
   ```

4. Restart backend containers/processes so the new routes are active.

### Club documents deployment steps

After deploying backend/frontend code that includes `club_documents` support:

1. Ensure PostgreSQL runtime mode is enabled:
   - `DATABASE_URL` set
   - `HLAS_USE_POSTGRES_READS=true`
2. Run Alembic migrations:

   ```bash
   cd /opt/hlas/backend
   alembic upgrade head
   ```

3. Restart backend and frontend containers/processes.
4. Validate endpoints and UI:
   - `GET /api/documents?club=<SHORT_NAME>` returns JSON
   - Home page shows `<Club> Documents` beside `<Club> News and Updates`
   - Club Admin+ can upload/delete; members can download

### Alembic caveat on older live databases

Some live databases may contain an `alembic_version` value that does not exist in this repository's current migration chain.

If Alembic reports an unknown revision:
- do not force an arbitrary revision change without reviewing migration history
- use the app's idempotent runtime bootstrap as a short-term safe path for additive objects such as `member_photos`
- reconcile `alembic_version` separately before relying on future schema migrations in production

---

## Files Changed
- `backend/auth/session_tokens.py`
- `backend/auth/principal.py`
- `backend/routes/admin_routes.py`, `member_routes.py`, `admin_user_routes.py`, etc.
- `backend/db/postgres_backend.py`
- `backend/migrations/versions/20260326_0007_add_user_type_to_sessions.py`
- `frontend/AdminApp.vue`, `App.vue`, `src/store.js`, etc.
- `frontend/vite.config.js`, `admin.html`, `index.html`

---

## Authors
- Migration and refactor by: GitHub Copilot and DrProfPatPending

---

For further details, see code comments and commit history.
# HLaS Production Deployment (Docker + VPS)

This bundle deploys HLaS with three containers:

- `backend`: Flask API served by Gunicorn
- `frontend`: Vue production build served by Nginx
- `caddy`: reverse proxy + TLS (Let's Encrypt)

## 1) Prerequisites

- A Linux VPS (Ubuntu recommended)
- DNS `A` record pointing your domain to the VPS IP
- Docker Engine + Compose plugin on VPS
- A container registry (GHCR or Docker Hub)

## 2) Files in this bundle

- `backend/Dockerfile`
- `frontend/Dockerfile`
- `docker-compose.prod.yml`
- `deploy/caddy/Caddyfile`
- `deploy/nginx/frontend.conf`
- `deploy/local/publish.ps1`
- `deploy/vps/deploy.sh`
- `deploy/vps/verify-and-deploy.sh`
- `deploy/vps/bootstrap-ubuntu.sh`
- `.env.prod.example`

## 3) Build and push images (local machine)

Frontend image builds now standardize on npm `11.12.1` inside [frontend/Dockerfile](frontend/Dockerfile), so local and container builds use the same npm major/minor version.

1. Copy `.env.prod.example` to `.env.prod` and set values.
   - Token TTL defaults now included in the template:
     - `HLAS_MEMBER_TOKEN_TTL_SECONDS=300`
     - `HLAS_MEMBER_REFRESH_TOKEN_TTL_SECONDS=600`
2. Login to your registry (example GHCR):
   ```powershell
   echo <YOUR_GITHUB_TOKEN> | docker login ghcr.io -u <YOUR_GITHUB_USERNAME> --password-stdin
   ```
3. Build and push images:
   ```powershell
   .\deploy\local\publish.ps1 -EnvFile .env.prod
   ```

## 4) Prepare VPS

### Option A: Bootstrap Docker automatically (Ubuntu)

```bash
sudo bash deploy/vps/bootstrap-ubuntu.sh
```

### Option B: Existing Docker install

Skip bootstrap if Docker + Compose are already installed.

## 5) Copy deployment files to VPS

Copy the repo (or at least these files) to the VPS, e.g. `/opt/hlas`.

Required on VPS:

- `docker-compose.prod.yml`
- `deploy/caddy/Caddyfile`
- `deploy/vps/deploy.sh`
- `.env.prod` (with real values)

## 6) Deploy on VPS

```bash
cd /opt/hlas
chmod +x deploy/vps/deploy.sh
./deploy/vps/deploy.sh
```

This script:

- pulls newest images
- runs `docker compose up -d --remove-orphans`
- prunes dangling images
- prints service status

### Optional safer production preflight + rollout script

Use the reusable verification/deploy helper to catch common production rollout mistakes such as stale shell environment overrides, wrong image tags, wrong database driver URL, or incorrect PostgreSQL volume binding.

Verify only:

```bash
cd /opt/hlas
chmod +x deploy/vps/verify-and-deploy.sh
./deploy/vps/verify-and-deploy.sh verify
```

Verify and deploy:

```bash
cd /opt/hlas
chmod +x deploy/vps/verify-and-deploy.sh
./deploy/vps/verify-and-deploy.sh deploy
```

The script will:

- clear known stale shell environment overrides before running Compose
- verify `main` is checked out
- verify backend/frontend image tags resolve to `:latest`
- verify `DATABASE_URL` resolves to `postgresql+psycopg://...`
- verify PostgreSQL uses the expected external volume `hlas_postgres_data`
- in `deploy` mode, pull `main`, rebuild backend/frontend, restart services in order, and verify backend `/clubs`

## 7) Data persistence

Backend data is persisted in Docker volume `hlas_data` via `HLAS_DATA_DIR=/data`.
This includes:

- club databases (`*.db`)
- `clubs.config.json`
- `server.config.json`
- `club_logos/`
- `ID_photos/`

Notes:
- `ID_photos/` may still be present even after photo import, because file fallback remains available.
- PostgreSQL can now serve member photos directly from the `member_photos` table.

## 8) Routing and TLS

- Public HTTPS endpoint is served by Caddy
- `/api/*` is forwarded to backend and stripped to backend routes
- all other paths are forwarded to frontend
- Caddy issues and renews certs automatically for `DOMAIN`

## 9) Update workflow

1. Build + push new images (`publish.ps1`)
2. SSH into VPS and run:
   ```bash
   cd /opt/hlas
   ./deploy/vps/deploy.sh
   ```
3. If member photo storage changes were included, run the import script once after deployment.

## 10) Troubleshooting

- Service status:
  ```bash
  docker compose --env-file .env.prod -f docker-compose.prod.yml ps
  ```
- Logs:
  ```bash
  docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f caddy frontend backend
  ```
- Verify DNS: `DOMAIN` must resolve to VPS public IP
- Ensure firewall allows ports `80` and `443`
- Docker Postgres host port is `5433`, not `5432`
- If the login club dropdown is empty, test `/api/clubs`
- If member photos do not show, verify:
   - `member_photos` contains rows
   - backend is running updated code
   - `/api/member_photo/...` returns image bytes

### Useful operational SQL/scripts

- Paused-field verification packs:
   - `Utilities/member_paused_verification_pack.sql`
   - `Utilities/member_paused_verification_pack_psql.sql`

### Field-order persistence note

Current runtime-configured field-order contexts include both:

- `fishing_beats`
- `beat_details`

If `app_settings(scope='global', key='field_order')` exists, it is treated as the runtime source of truth. Keep it aligned with `backend/field_order.json` when deploying manual config updates.
