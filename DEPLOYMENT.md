# Option 3 Migration: Separation of Admin/System and Member/Club User Flows

## Summary
This release implements a full separation between admin/system users and member/club users, as per Option 3 of the migration plan. The backend, frontend, and API logic have been refactored to support distinct authentication, session, and UI flows for each user type.

This guide also reflects later operational changes, including PostgreSQL-backed member photo storage, restored Membership Admin behavior, and reusable SQL verification packs.
It also now covers the Beat Details member page, dedicated field-order config for that view, and the redesigned member home dashboard.
It now also covers PostgreSQL-backed club document storage and Home dashboard document visibility.

---

## Deployment Strategy & Branch Management (May 2026)

### Overview

HLaS uses a **two-branch deployment strategy** to ensure production stability while enabling safe development:

- **`main` branch**: Development and active feature development. Used locally and in testing environments.
- **`production` branch**: Deployed codebase running on the VPS server (`cambridgetroutclub.org`). Only receives thoroughly tested, verified changes.

This separation ensures that experimental changes on `main` never affect the live clubs (CTC, GAAFFS, LADFFA) without careful validation first.

### Deployment Workflow

#### Step 1: Develop and Test on `main`

1. Clone or pull the latest `main` branch:
   ```bash
   git clone https://github.com/DrProfPatPending/HLaS.git
   cd hlas
   git checkout main
   ```

2. Create a feature branch for new work (optional):
   ```bash
   git checkout -b feature/my-feature
   ```

3. Make changes, test locally, and commit:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin feature/my-feature  # or push to main if no feature branch
   ```

4. Test thoroughly in a local Docker environment:
   ```bash
   docker compose -f docker-compose.prod.yml build
   docker compose -f docker-compose.prod.yml up
   # Test against http://localhost
   docker compose down
   ```

#### Step 2: Promote to `production` (VPS Deployment)

Once changes are tested and verified on `main`, promote them to `production`:

1. **On your local machine**, switch to production and merge main:
   ```bash
   git checkout production
   git merge main
   git push origin production
   ```

2. **On the VPS**, pull the updated production branch and restart services:
   ```bash
   ssh hlas@cambridgetroutclub.org
   cd /opt/hlas
   git checkout production
   git pull origin production
   ```

3. **Restart the application** using one of the deployment scripts:
   ```bash
   # Full backend + frontend rebuild
   ./hlas_build.sh
   
   # Or just rebuild frontend
   ./rebuild_frontend.sh
   ```

4. **Verify deployment** by checking application health:
   ```bash
   docker compose ps
   docker compose logs backend | tail -20
   docker compose logs frontend | tail -20
   ```

5. **Test in browser**: Visit `https://cambridgetroutclub.org` and verify functionality

### Environment-Specific Configuration Management

**Caddyfile (SSL/TLS Proxy Configuration)**

HLaS uses separate, version-controlled Caddyfile configurations for development and production:

- **`deploy/caddy/Caddyfile.prod`** — Production configuration
  - Domain: `cambridgetroutclub.org`
  - TLS: Let's Encrypt automatic certificate management
  - Used by `docker-compose.prod.yml` on VPS deployments

- **`deploy/caddy/Caddyfile.dev`** — Development configuration
  - Domain: `hlastest` (local development server)
  - TLS: Caddy internal CA (self-signed, requires trust installation)
  - Used by `docker-compose.dev.yml` override on dev/test servers

**How It Works:**

1. **Docker Compose Volume Mounts** explicitly reference environment-specific files:
   ```yaml
   # Production (docker-compose.prod.yml)
   caddy:
     volumes:
       - ./deploy/caddy/Caddyfile.prod:/etc/caddy/Caddyfile:ro
   
   # Development (docker-compose.dev.yml override)
   caddy:
     volumes:
       - ./deploy/caddy/Caddyfile.dev:/etc/caddy/Caddyfile:ro
   ```

2. **Build Script Validation** (`hlas_build.sh`) ensures the production Caddyfile exists:
   ```bash
   if [ ! -f "deploy/caddy/Caddyfile.prod" ]; then
       echo "✗ ERROR: Production Caddyfile not found!"
       exit 1
   fi
   ```

This design prevents accidental use of dev configuration in production, even when git rebases pull changes from the main branch. Both Caddyfile configurations are version-controlled in git and protected from overwrites.

### Deployment Scripts

Two convenience scripts automate the VPS deployment process:

**`hlas_build.sh`** — Full rebuild (backend & frontend)
- Validates `Caddyfile.prod` exists
- Checks out `production` branch
- Pulls latest code
- Rebuilds backend and frontend containers
- Restarts all services via docker-compose

**`rebuild_frontend.sh`** — Frontend-only rebuild
- Checks out `production` branch  
- Pulls latest code
- Rebuilds frontend container only
- Restarts frontend and caddy

Both scripts automatically pull from the `production` branch, ensuring only tested, promoted code is deployed. The `hlas_build.sh` script includes validation to ensure the production Caddyfile configuration is present before proceeding.

### Rollback Procedure

If a production deployment causes issues:

1. **Identify the previous good commit**:
   ```bash
   git log --oneline production
   ```

2. **Revert to the previous commit**:
   ```bash
   cd /opt/hlas
   git revert <commit-hash>
   git push origin production
   ./hlas_build.sh  # Redeploy
   ```

   Or **force reset** if you don't want a revert commit:
   ```bash
   git reset --hard <commit-hash>
   git push -f origin production
   ./hlas_build.sh
   ```

### Git Configuration on VPS

To enable pushing/pulling from the VPS, configure git with your credentials:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

Verify configuration:
```bash
git config --global user.name
git config --global user.email
```

### Database Migrations

Some deployments may include Alembic database schema migrations:

1. Migrations run **automatically** during container startup via the health check scripts
2. For manual migration trigger:
   ```bash
   docker compose --env-file .env.prod -f docker-compose.prod.yml run --rm backend alembic upgrade head
   ```

3. To verify applied migrations:
   ```bash
   docker exec hlas-postgres-1 psql -U hlas -d hlas -c "SELECT * FROM alembic_version;"
   ```

### Best Practices

1. ✅ **Always test on `main` before promoting to `production`**
2. ✅ **Use descriptive commit messages** so deployment history is clear
3. ✅ **Keep production deployments within business hours** when you can monitor
4. ✅ **Document any breaking changes** in commit messages
5. ✅ **Keep `Caddyfile.prod` and `Caddyfile.dev` in sync** — version control both files
6. ❌ **Never force-push to `main`** — this becomes the development timeline  
7. ❌ **Never hotfix directly on `production`** — always go through `main` first for testing
8. ❌ **Don't skip database migrations** — they're essential for feature compatibility
9. ❌ **Don't modify the working directory Caddyfile** — always update the versioned `Caddyfile.prod` or `Caddyfile.dev` files

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

- **Fishing Beats Management API Endpoints:**
   - `GET /admin/clubs/<club>/beats/export` exports beats from PostgreSQL as JSON (Club Admin+ via `club.update`)
   - `POST /admin/clubs/<club>/beats/import` accepts beats JSON and updates the JSON config (Club Admin+ via `club.update`)
   - These endpoints enable bidirectional sync between PostgreSQL `club_beats` table and `clubs.config.json`
   - Helper scripts for programmatic sync:
     - `sync_beats_postgres_to_json.py` - exports PostgreSQL beats to JSON config (local dev)
     - `sync_beats_via_api.py` - API-based export/import (local dev)
     - `sync_beats_json_to_postgres.py` - imports JSON beats to PostgreSQL (VPS production)
   - **Automatic startup sync:** Backend startup hook runs `sync_beats_json_to_postgres.py` automatically
     - Ensures PostgreSQL club_beats table always matches `clubs.config.json` on container start
     - Only runs if PostgreSQL writes are enabled
     - Non-blocking (catches and logs errors)

- **Club Settings API Endpoints:**
   - `GET /club-settings?club=<SHORT_NAME>` for loading club-scoped member settings
   - `PUT /club-settings` for saving club-scoped member settings (Club Admin/Membership Admin gate via `member.club.list`)
   - Current setting scope includes Catch Return field visibility used by both the form and recent-returns table columns

- **Membership Export API Endpoint:**
   - `GET /members/export?club=<SHORT_NAME>&format=csv|json`
   - Exports members using the same active filters/sort as Membership Admin
   - If no filters are provided, exports all members for the scoped club
   - Requires `member.club.list`

- **Field Order Configuration:**
   - Admin UI provides comprehensive table column management at `/admin/` → Field Order tab
   - Each context (e.g., `home_documents`, `fishing_beats`) can be configured independently
   - Editable properties per column:
     - **Display As:** Custom header label (blank = use field name)
     - **Show Column:** Toggle column visibility
     - **Min Width:** Minimum pixel width constraint (fallback constraint)
     - **Width:** Explicit width setting or flexible sizing:
       - Pixel values: `80px` (or just `80`)
       - Percentages: `50%`
       - **`flex` or `auto`:** Flexible column that grows to fill remaining space
       - Blank: Use Min Width or browser default
   - Width priority: explicit Width > Min Width > browser default
   - Example use case: set Size column to `80px`, Actions to `120px`, Title to `flex`
   - Configure via Admin UI: `/admin/field-order`
   - Configuration structure in `field_order.json`:
     ```json
     {
       "home_documents": ["Title", "Size", "Actions"],
       "widths": {
         "home_documents": {
           "Title": "flex",
           "Size": "80px",
           "Actions": "120px"
         }
       },
       "minimum_widths": {
         "home_documents": {
           "Title": 180,
           "Size": 80,
           "Actions": 120
         }
       }
     }
     ```

- **Club Mini Site API Endpoints:**
   - `GET /mini-site?club=<SHORT_NAME>` for loading club mini site configuration (authenticated, requires `club.read`)
   - `PUT /mini-site?club=<SHORT_NAME>` for saving mini site configuration (Club Admin+ via `club.update`)
   - `GET /club/<club_short_name>/mini-site` public endpoint (no auth) for fetching enabled mini site config
   - POST/GET operations return: `enabled`, `title`, `tagline`, `description`, `hero_image_url`, `pages`, `social_links`

- **Database Migration:**
   - Alembic migration `20260504_0001_club_mini_sites_table.py` creates `club_mini_sites` table
   - Table schema: `club_id` (unique FK to clubs), `enabled`, `title`, `tagline`, `description`, `hero_image_url`, `pages` (JSONB), `social_links` (JSONB)
   - Indexed on `club_id` (unique) and `enabled` for fast lookups

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
   - Added `Export Filtered` action with `CSV` / `JSON` format selector
   - Export button label now adapts to filter state (`Export All` vs `Export Filtered`)
   - Export respects current filter and sort state; defaults to all club members when no filters are set
   - Field headers and filter placeholders now support Admin-configurable `Display As` labels
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
- **Club Settings:**
   - member-facing Club Settings page allows clubs to configure:
     - Catch Return field visibility (which fields appear in the form and recent returns table)
     - Club Mini Site (marketing website configuration for each club)
   - Club Admin+ users can manage these settings
   - Settings are stored in PostgreSQL and applied cluster-wide

- **Club Mini Sites:**
   - Optional public-facing marketing websites for each club (per-club configuration)
   - Desktop users: Full mini site with navigation, hero section, club content, social links footer
   - Mobile/Responsive users: Placeholder with message directing to desktop mode
   - Public access via `/club/{clubCode}/` (no authentication required)
   - Admin UI in Club Settings to enable/disable and configure mini site (title, tagline, description, hero image)
   - Separate public API endpoint `/api/club/{id}/mini-site` for external integration
   - PostgreSQL table: `club_mini_sites` with per-club settings (indexed on `club_id` and `enabled`)

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
- Membership export output:
   - CSV and JSON are generated on demand by backend; no schema migration required
   - Export excludes sensitive fields such as `password`
- Field-order display labels:
   - Stored in existing field-order JSON/app_settings payload under `display_names`
   - No database schema migration required

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

### Fishing Beats sync deployment steps

After deploying backend code that includes beats export/import and automatic startup sync:

#### On Local Development Machine

1. Update beats in PostgreSQL as needed
2. Export beats from PostgreSQL to JSON config:

   **Option A: Via API (requires running backend)**
   ```bash
   cd /opt/HLaS
   python3 sync_beats_via_api.py
   ```

   **Option B: Direct database sync (requires DATABASE_URL)**
   ```bash
   cd /opt/HLaS
   docker exec hlas-backend-1 python3 /app/sync_beats_json_to_postgres.py
   ```

3. Commit updated beats to git:
   ```bash
   git add backend/clubs.config.json
   git commit -m "Sync beats from dev PostgreSQL"
   git push origin main
   ```

#### On VPS Production

**Automatic sync (default approach):**

1. Pull updated code from production branch:
   ```bash
   cd /opt/hlas
   git checkout production
   git pull origin production
   ```

2. Restart backend container:
   ```bash
   docker compose down backend
   docker compose up -d backend
   ```

> **Note**: The `production` branch is the deployed codebase on the VPS. Promote changes to production only after testing on the `main` branch.

3. Backend startup hook automatically runs `sync_beats_json_to_postgres.py`:
   - PostgreSQL `club_beats` table is populated from `clubs.config.json`
   - Beats synced for all active clubs
   - Check container logs: `docker compose logs backend | grep -i beats`

**Manual sync (if needed):**

You can also manually sync beats at any time without restarting:

```bash
# Test without writing (dry-run)
docker exec hlas-backend-1 python3 /app/sync_beats_json_to_postgres.py --dry-run

# Actually sync beats to PostgreSQL
docker exec hlas-backend-1 python3 /app/sync_beats_json_to_postgres.py
```

Or via API (requires admin token):

```bash
curl -X POST https://<YOUR_VPS_DOMAIN>/api/admin/clubs/GAAFFS/beats/import \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{"beats": [...]}'
```

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

### Backup & Snapshot System

A comprehensive backup solution has been implemented to protect both PostgreSQL database and file assets:

- **Backup API Endpoints:**
   - `GET /admin/backups/snapshots` - List all snapshots
   - `POST /admin/backups/snapshots/create/full` - Create full snapshot (database + files)
   - `POST /admin/backups/snapshots/create/database` - Create database-only snapshot
   - `POST /admin/backups/snapshots/create/filesystem` - Create filesystem-only snapshot
   - `POST /admin/backups/snapshots/{id}/upload` - Upload snapshot to cloud storage
   - `GET /admin/backups/snapshots/{id}/download` - Download snapshot
   - `DELETE /admin/backups/snapshots/{id}` - Delete snapshot
   - `POST /admin/backups/cleanup` - Cleanup old snapshots per retention policy
   - `GET /admin/backups/status` - System status and statistics

- **Permissions:**
   - `backup.create` - Create new snapshots
   - `backup.read` - List and view snapshot details
   - `backup.download` - Download snapshot files
   - `backup.delete` - Delete snapshots
   - Restricted to `app_admin` and `app_owner` roles only

- **CLI Tool:**
   - `python3 backend/backup_cli.py create-full` - Manual full backup
   - `python3 backend/backup_cli.py list` - List snapshots
   - `python3 backend/backup_cli.py status` - System status
   - `python3 backend/backup_cli.py cleanup` - Cleanup old snapshots
   - `python3 backend/backup_cli.py schedule` - Setup automated scheduling

- **Cloud Storage Integration:**
   - Supports AWS S3, MinIO, DigitalOcean Spaces, or any S3-compatible service
   - Upload snapshots to cloud for off-site redundancy
   - Configure via environment variables or API

- **Setup:**
   - See `BACKUP_SYSTEM.md` for comprehensive setup and usage guide
   - See `BACKUP_QUICK_START.md` for 5-minute quick start
   - Configuration template: `.env.backup.example`
   - Docker Compose example: `docker-compose.backup.yml`

### Club Mini Sites

Optional public-facing marketing websites for each club:

- **Configuration:**
   - Access via Club Settings page (member UI → Club Settings)
   - Club Admin+ users can enable/disable and configure per-club mini site
   - Configurable fields: `enabled`, `title`, `tagline`, `description`, `hero_image_url`
   - Store images externally (e.g., CDN, S3) and reference via URL

- **Public Access:**
   - Desktop view: Full mini site at `/club/{clubCode}/`
   - Mobile/Responsive view: Placeholder at `/club/{clubCode}/` with link to desktop
   - Public API: `GET /api/club/{id}/mini-site` (no authentication required)

- **API Endpoints (Authenticated):**
   - `GET /mini-site?club=<SHORT_NAME>` - Fetch mini site config (requires `club.read`)
   - `PUT /mini-site?club=<SHORT_NAME>` - Update mini site config (Club Admin+ via `club.update`)

- **Routing:**
   - `/club/{clubCode}/` - Mini site landing page (or login if disabled)
   - `/club/{clubCode}/login/` - Login page (always accessible, any device)

- **Future Enhancements:**
   - Admin UI for editing page content and gallery
   - Email contact forms with club-specific email routing
   - Event calendar integration
   - Member testimonials and gallery

### Useful operational SQL/scripts

- Paused-field verification packs:
   - `Utilities/member_paused_verification_pack.sql`
   - `Utilities/member_paused_verification_pack_psql.sql`

### Field-order persistence note

Current runtime-configured field-order contexts include both:

- `fishing_beats`
- `beat_details`

If `app_settings(scope='global', key='field_order')` exists, it is treated as the runtime source of truth. Keep it aligned with `backend/field_order.json` when deploying manual config updates.
