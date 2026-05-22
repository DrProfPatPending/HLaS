# HLaS

HLaS is a fishing club membership management application with separate member and admin user experiences, PostgreSQL-backed runtime data, and Vue/Flask frontends for day-to-day club operations.

## ⚡ Deployment Strategy (May 2026)

HLaS uses a **two-branch deployment model** for stability and safe development:

- **`main` branch** — Active development and testing. Local and staging environments.
- **`production` branch** — Live codebase deployed on VPS (`anglerconnect.cloud`). Only receives tested, verified changes.

**Workflow:**
1. Develop and test thoroughly on `main`
2. Promote tested changes to `production` via `git merge main`
3. VPS deployment scripts (`hlas_build.sh`, `rebuild_frontend.sh`) automatically pull from `production`

Production runtime verification command:

```bash
./health_check_prod.sh
```

This runs `docker compose ps`, service runtime checks, HTTPS smoke probes (main/API/WordPress), PostgreSQL readiness using `POSTGRES_USER` from `.env.prod`, and a recent log scan.

**See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions, rollback procedures, and best practices.**

## Current Application Highlights
- Distinct member UI and admin UI entry points.
- PostgreSQL-backed reads and writes for clubs, members, roles, newsletters, field order, and member photos.
- Member ID photos can now be stored and served from PostgreSQL via the `member_photos` table.
- Club documents can be stored in PostgreSQL (binary) and surfaced on the member Home page.
- Membership Admin includes sorting, filtering, linked member lookup, and linked member edit navigation.
- Fishing Beats field order, visibility, and minimum width settings are configurable.
- Beat Details now has its own dedicated field-order and visibility configuration context.
- The post-login home page now uses a dashboard layout with a left-side action stack and a central club news/update panel.

## Recent Changes
- **Build Script Enhancements (May 2026):**
   - `hlas_build.sh` now accepts a comprehensive set of CLI options:
   - `--full` / `-f` (default): passes `--no-cache` to `docker compose build` — full layer rebuild, safe for production deploys
   - `--quick` / `-Q`: omits `--no-cache`, reusing Docker layer cache for significantly faster iterative dev rebuilds
   - `--clean` / `-c`: runs `docker system prune -f` after a successful build to remove dangling images; only fires on success
   - `--nohealth` / `-n`: skips the post-start health checks; useful for CI or restricted network environments
   - `--local` / `-l`: skip `git fetch/reset` and build from the local working tree
   - `--target` / `-t`, `--directory` / `-d`, `--verbose` / `-v`, `--quiet` / `-q` also available
   - See DEPLOYMENT.md for a full options table and examples

- **Age Field Calculated at Runtime (May 2026):**
   - The `Age` field in **Personal Info** (My Club page) and **Membership Admin** is now a dynamic, calculated value derived from the member's `Date_of_Birth` and the current date
   - No manual updates to the `Age` column are needed; the displayed value is always accurate
   - Whole-year birthday logic correctly adjusts if the birthday has not yet occurred this year
   - Falls back gracefully to the stored `Age` value if `Date_of_Birth` is absent

- **Split Club Config Tooling (May 2026):**
   - `backend/build_clubs_config.py`: validates and assembles aggregate `clubs.config.json` from per-club source files
   - `backend/scaffold_club_layout.py`: scaffolds the `backend/clubs/<CLUB>/` directory layout from aggregate config
   - `backend/sync_beats_postgres_to_json.py`: rewritten with `--mode aggregate|split|both` and lazy SQLAlchemy import
   - `Makefile` targets: `clubs-build`, `clubs-check`, `clubs-scaffold-copy`
   - `backend/clubs/` tree with `CTC`, `GAAFFS`, `LADFFA`, `TEST` layouts and `manifest.json` committed to all branches

- **Beat Details Route Waypoints (May 2026):**
   - Beats now support an ordered `Waypoints` list (sequence, W3W stub, lat/lon, description).
   - The map draws a route polyline through waypoints instead of the old straight-line boundary.
   - The old downstream→pools→upstream polyline has been removed.
   - Pool markers (numbered) and parking markers (P) remain unchanged.
   - A **Show/Hide Waypoints** toggle button appears on the map when waypoints are present, revealing small grey dot markers at each waypoint position for development verification.
   - The Beat Details edit form includes a full Waypoints editor (Add / Remove rows).
   - **GPX import:** click *Import GPX* in the edit form to load a `.gpx` file exported from OS Maps Pro (or any GPX-compatible source). Track points (`<trkpt>`) or route points (`<rtept>`) are parsed client-side; no API key required.
   - Backend: new `waypoints` JSONB column on `club_beats` (migration `20260511_0001`); `normalize_waypoints()` in `core/common.py`; waypoints read/written in `app.py` and `admin_routes.py`.

- **Deployment Strategy (May 2026):**
   - Implemented separate `main` (development) and `production` (VPS deployed) branches
   - VPS deployment scripts updated to pull from `production` branch only
   - Ensures live clubs (CTC, GAAFFS, LADFFA) only run thoroughly tested code
   - Environment-specific Caddyfile configurations (`Caddyfile.prod` for production, `Caddyfile.dev` for dev)
   - Build script validation ensures correct SSL/TLS configuration is present before deployment
   - Easy rollback procedure available if issues occur
   - See DEPLOYMENT.md for workflow details

- **Club Mini Site UI Refinements (May 2026):**
   - Compact page headers: 100px height with 14pt titles (90px/12pt on mobile)
   - Compact hero banner: 100px with background image display
   - Expanded navigation logo: 100px height for better brand visibility
   - Background image section: Positioned prominently on Home page
   - Club background images: PostgreSQL-backed storage and admin upload capability
   - Applied consistent compact styling across all pages (Home, About, Join, Our Waters, Contact)

- **Club Mini Sites:** Optional public-facing marketing websites for each club.
   - Per-club configuration (enabled/disabled, title, tagline, description, hero image).
   - Desktop: Full mini site with navigation, hero section, featured content, social links.
   - Mobile/Responsive: Placeholder with message to view on desktop, with link to login.
   - Public access via `/club/{clubCode}/` (no authentication required).
   - Admin UI in Club Settings to manage mini site configuration.
   - Separate public API endpoint `/api/club/{id}/mini-site` for external integration.
   - Club background image storage in PostgreSQL with admin upload capability.
   - See **Comprehensive backup & snapshot system:** Database and file backups for disaster recovery.
   - Full snapshots combine database (`pg_dump`) and file system backups into versioned archives.
   - Upload snapshots to AWS S3, MinIO, DigitalOcean Spaces, or any S3-compatible storage.
   - Automated cleanup policies (retention by age or snapshot count).
   - CLI tool (`backup_cli.py`) for manual operations and cron scheduling.
   - REST API endpoints for programmatic access (gated by `app_admin`/`app_owner`).
   - See `BACKUP_SYSTEM.md` and `BACKUP_QUICK_START.md` for complete documentation.
- **Mobile responsive navigation:** the main Navigation Bar now switches to a 2-column grid layout at ≤ 768 px, containing buttons sized to 80 % of the screen width, stacked above page content.
- **Mobile full-width layout:** the application shell, nav card, subnav card, and all content containers now expand to 100 % window width in responsive mode, with content areas independently centred at 80 vw.
- **Beat Details page restructure:** the read-only Beat Details page now shows:
   1. A compact 2-column quick-info bar with **River** and **Beat Name** at the top.
   2. The interactive map directly below the quick-info bar.
   3. The full details table (2-column and 4-column rows) below the map.
- **Beat Details responsive table:** on screens ≤ 1000 px the details table collapses from the 4-cell per row layout into a 2-column label/value grid, preventing horizontal overflow.
- **Frontend dependency upgrades (April 2026):** `vue 3.5.33`, `vuetify 4.0.6`, `vite 8.0.10`, `axios 1.15.2`; security fix: `follow-redirects` updated via `npm audit fix` (GHSA-r4q5-vmmm-2653).
- Added a new Admin tab: **App Settings**.
- Added global **Date Format** configuration in App Settings with selectable format patterns.
- Added backend `/admin/app-settings` API to load/save global app settings.
- Added a new member-facing **Club Settings** page (role-gated the same as Membership Admin).
- Added club-level Catch Return field visibility configuration that Club Admin users can manage.
- Catch Return form fields and the **My Recent Returns** columns now show/hide based on club settings.
- Added backend `/club-settings` API to load/save per-club member settings.
- Restored the member login club dropdown loading from `/clubs`.
- Restored and improved Membership Admin sorting and filtering behavior.
- `Members_Name` opens Edit Member Details; `Number` opens member lookup/details.
- Edit Member navigation now uses the full matching result set instead of just the visible page.
- Member ID photos are imported into PostgreSQL and served DB-first with file fallback.
- Added reusable SQL verification packs in `Utilities/`.
- Added a new Beat Details member page with dedicated field-order configuration.
- Beat Details now supports **Route Waypoints** for river route mapping:
   - Ordered waypoints (sequence, W3W stub, lat/lon, description) define the river route.
   - Map draws a connected polyline through waypoints; old straight boundary line removed.
   - Waypoint dot markers can be toggled on/off via a map button (for development verification).
   - GPX import: export a route from OS Maps Pro (or equivalent) as `.gpx` and import it directly in the beat editor — track points and route points are both supported.
- Beat Details now reuses the Fishing Beats detail map logic, including upstream/downstream markers and parking locations.
- The post-login member home page now presents navigation actions vertically on the left with a placeholder `<Club> News and Updates` table in the center.
- Added database-backed club document management:
   - Club Admin and higher can upload/delete documents.
   - Members can view and download documents for their club.
   - Home page now shows a `<Club> Documents` table alongside `<Club> News and Updates`.
- Added Club Information inline editing for `club_admin` users in the member UI:
   - `Edit` / `Save` controls are shown only when the logged-in user has the Club Admin role.
   - Club profile fields (website, admin email, description, display name) can be updated from the Club Information section.
   - Club deletion remains App Admin/App Owner-only via AdminApp and admin routes.
- Added Beat Details management controls for `club_admin` users in the member UI:
   - `Edit` / `Save` controls for updating all selected beat details.
   - `Add` to create a new beat entry.
   - `Delete` to remove the currently selected beat.
   - These controls are role-gated and hidden for users without `club_admin`.
- Added Membership Admin bulk export for filtered members:
   - New `Export Filtered` action with `CSV` / `JSON` format selector.
   - Export respects current table filters and sort order.
   - If no filters are set, export includes all members in the selected club.
   - Export is downloaded from backend endpoint `GET /members/export`.
- Added Field Order `Display As` customization:
   - Admin users can now define per-column display labels per context.
   - Field name remains fixed in config/data, while UI header text can be customized.
   - Membership Admin table now uses configured `Display As` values for headers and filter placeholders.
- Added **Fishing Beats import/export** functionality:
   - Backend `/admin/clubs/<club>/beats/export` API exports beats from PostgreSQL as JSON.
   - Backend `/admin/clubs/<club>/beats/import` API accepts beats JSON and updates the config.
   - Helper scripts for syncing beats between PostgreSQL and `clubs.config.json`:
     - `sync_beats_postgres_to_json.py` for direct database synchronization.
     - `sync_beats_via_api.py` for API-based import/export.
   - Beats data is now synchronized from PostgreSQL to JSON configuration for deployment.

## Key Features
- **Distinct login and UI for admin/system users** at `/admin/` (AdminApp.vue)
- **Member/club users** use the main UI at `/` (App.vue)
- **Admin App Settings tab** for global application settings (starting with Date Format)
- **Club Settings page** for club-scoped Catch Return visibility controls
- **Session tokens** and **principal context** now include `user_type` for robust permission checks
- **API endpoints** allow admin/system users to operate globally, without requiring a club context
- **Frontend and backend code** refactored for clean separation and maintainability

## Admin App Settings

The Admin UI now includes an **App Settings** tab.

Current setting:

- **Date Format** (global): choose from supported patterns such as:
   - `DD/MM/YY`
   - `DD/MM/YYYY`
   - `DD-MMM-YYYY`
   - `YYYY-MM-DD`
   - `MMM DD, YYYY`
   - `DD MMM YYYY`
   - `MM/DD/YYYY`

Backend endpoints:

- `GET /admin/app-settings`
- `PUT /admin/app-settings`

Persistence behavior:

- PostgreSQL mode: stored in `app_settings` with `scope='global'` and `key='app_settings'`
- Fallback: `backend/app_settings.json`

How to use Date Format:

1. Sign in at `/admin/` with an admin account.
2. Open the **App Settings** tab.
3. In **Date Format**, select the required format pattern.
4. Click **Save App Settings**.
5. Refresh member/admin pages that display dates to confirm the selected format is in effect.

## Member UI updates

### Home dashboard

After member login, the main page now shows:

- a vertical action menu on the left for member workflows such as Membership Admin, Beat Details, Club Information, My Club, Fishing Beats, Club Store, and Newsletters
- a central `News and Updates` panel titled with the active club name
- a `Documents` panel beside the news panel, showing club documents from backend storage
- placeholder rows for alerts and messages until the backend-backed news feed is implemented

### Club Information page

Club Information remains visible to members, with role-gated editing support.

Current behavior:

- Users with `club_admin` role see `Edit` / `Save` controls in the member-facing Club Information section.
- Users without `club_admin` role see the page in read-only mode.
- Editing updates the active club profile through backend `club.update` permission checks.
- Club deletion is not available in member UI and remains restricted to AdminApp (`app_admin` / `app_owner`).

### Club documents

Club documents are now stored in PostgreSQL and shown on the Home dashboard.

Current behavior:

- Supported upload file types: `.pdf`, `.xls`, `.xlsx`, `.doc`, `.docx`
- Upload/delete actions are permission-protected via `document.club.manage`
- Club Admin, Club Manager, App Admin, and App Owner can upload/delete
- Authenticated members can list and download documents for their club
- Uploads are limited to 20 MB per file

Storage:

- PostgreSQL table: `club_documents`
- File bytes are stored in `file_data` (`BYTEA`) with metadata (title, filename, MIME type, size, timestamps)

Backend routes:

- `GET /documents?club=<SHORT_NAME>`
- `GET /documents/<document_id>/download?club=<SHORT_NAME>`
- `POST /documents` (multipart form: `club`, `file`, optional `title`)
- `DELETE /documents/<document_id>?club=<SHORT_NAME>`

### Club Settings page

Club settings are now configurable in the member UI for users who can access Membership Admin.

Current behavior:

- A new **Club Settings** action appears below **Membership Admin** in the left navigation for users with `member.club.list` permission.
- Club Settings includes a **Catch Return Fields** visibility list (Yes/No per field).
- Saved settings are scoped to the currently logged-in club.
- Catch Return uses these settings to control both:
   - which input fields are shown in the entry form
   - which columns are shown in **My Recent Returns** (including settings-aware Notes behavior)

Backend routes:

- `GET /club-settings?club=<SHORT_NAME>`
- `PUT /club-settings`

Permissions:

- Read: authenticated member for the scoped club
- Update: `member.club.list` (same gate used for Membership Admin)

### Membership Admin bulk export

Membership Admin now supports one-click export of member rows using the currently active table state.

Current behavior:

- Export action is available in Membership Admin with a format dropdown (`CSV` or `JSON`).
- Export button label is dynamic:
   - `Export All` when no filters are active
   - `Export Filtered` when one or more filters are active
- Export request includes the current filters and sort settings.
- If no filters are active, all members for the current club are exported.
- Sensitive fields such as password are excluded from export output.

Backend route:

- `GET /members/export?club=<SHORT_NAME>&format=csv|json`

Permissions:

- Read/export: `member.club.list` (same gate used for Membership Admin table access)

### Field Order Configuration

The Admin Field Order page provides comprehensive control over table display and column sizing:

**Editable fields per column:**

- **Field Order:** Reorder columns using Top/↑/↓/Bottom buttons
- **Display As:** Custom label for column header (defaults to field name if blank)
- **Show Column:** Toggle visibility of the column
- **Read Only:** Prevent non-admin users from editing that field in editable contexts
- **Min Width (px):** Minimum pixel width constraint (fallback if no explicit width set)
- **Width:** Fixed width or flexible sizing
  - Enter pixel value (e.g., `120px` or just `120`)
  - Enter percentage (e.g., `50%`)
  - Enter `flex` or `auto` for flexible columns that grow to fill remaining space
  - Leave blank to use Min Width or default behavior

**Width configuration pattern:**

The system uses a priority-based approach:
1. If `Width` is explicitly set → use that value
2. If `Width` is `flex` → column grows to fill available space
3. If `Min Width` is set → use as minimum constraint only
4. Otherwise → use browser default

**Example configuration** (home_documents table):
```json
{
  "home_documents": ["Title", "Size", "Actions"],
  "widths": {
    "home_documents": {
      "Title": "flex",
      "Size": "80px",
      "Actions": "120px"
    }
  }
}
```
This creates a layout where:
- **Title**  column is flexible and takes remaining space
- **Size** column stays fixed at 80px
- **Actions** column stays fixed at 120px

**Persistence:**

- Admin UI: `Admin` tab → `Field Order` button
- Editable contexts include: `membership_admin`, `fishing_beats`, `beat_details`, `home_news`, `home_documents`
- Changes are persisted via `/admin/field-order` endpoint
- Storage: PostgreSQL (`app_settings` with `scope='global'`) or fallback to `backend/field_order.json`
- `read_only` is stored inside the same JSON payload (`app_settings.value`), so no SQL schema migration is required
- Load/save paths normalize `read_only` across JSON + PostgreSQL to keep both sources consistent during sync/fallback

**Read-only behavior:**

- Applies to all Field Order contexts that have editable controls: `my_club`, `membership_admin`, `beat_details`, `home_news`, `home_documents`, `news_updates`
- Non-admin users cannot edit fields marked read-only
- Admin-role users (`club_admin`, `app_admin`, `app_owner`) can still edit read-only fields as an override
- UI disables read-only inputs, and update payloads are sanitized to prevent bypassing via client-side requests

### Beat Details page

The Beat Details page provides a dedicated beat-centric detail view separate from the Fishing Beats listing.

Page layout (read-only mode):

1. **Quick-info bar** — a compact 2-column table showing **River** and **Beat Name** immediately after the beat selector.
2. **Map** — interactive Leaflet map directly below the quick-info bar, showing upstream/downstream limits and parking markers.
3. **Details table** — full field-order-driven table below the map, with 2-column compact rows and 4-column wide rows for descriptions, parking, and pools.

Responsive behaviour:

- On screens ≤ 1 000 px the details table collapses to a 2-column label/value grid to prevent horizontal overflow.

Other behaviour:

- beat selector labels display `<Beat ID> <Beat Name>`
- detail fields use the `beat_details` field-order context from `field_order.json` / `app_settings`
- what3words locations are resolved through `/w3w/coordinates` when direct coordinates are unavailable
- users with `club_admin` role can edit/save beat details for the selected beat
- users with `club_admin` role can add new beats and delete the selected beat
- users without `club_admin` role see the page in read-only mode

Configuration sources:

- file fallback: `backend/field_order.json`
- PostgreSQL runtime source of truth: `app_settings(scope='global', key='field_order')`

See DEPLOYMENT.md for full technical details and migration notes.
# Fishing Club Membership Management Web Application

This project is a web application for managing the membership of a fishing club. It consists of:

- **Backend:** Python Flask REST API with PostgreSQL runtime support and legacy SQLite source/fallback support
- **Frontend:** Vue.js application for member management
- **Excel Import:** Script to import member data from Excel into the database

## Project Structure
- `backend/` - Flask API and database
- `frontend/` - Vue.js app
- `Utilities/` - reusable SQL and operational helper assets
- `.github/copilot-instructions.md` - Workspace instructions

## Local checks

- Run backend unit/integration checks with:
   - `make check`
- This runs the backend tests under `backend/tests` (using `backend-venv` when available).

## Makefile workflow (master + components)

The repository now uses a master Makefile at the root and component Makefiles in:

- `backend/Makefile`
- `frontend/Makefile`

Recommended entry points:

- `make development` → dev overlay cycle (`build + up + health`)
- `make production` → production cycle (`build + up + health`)
- `make check` → backend checks/tests
- `make help` → list all available targets

Environment-specific compose helpers:

- Dev overlay: `make dev-up`, `make dev-down`, `make dev-health`, `make dev-logs`, `make dev-ps`
- Production: `make prod-up`, `make prod-down`, `make prod-health`, `make prod-logs`, `make prod-ps`

iOS on macOS:

- Run the simulator build with a custom destination name if needed:
   - `make ios-sim IOS_SIMULATOR="iPhone 16 Pro"`
- The default simulator destination is `iPhone 16 Pro`.

## Field Order sync

- Sync live PostgreSQL `field_order` settings into JSON fallback with:
   - `make sync-field-order-from-db`
- Script used by this target:
   - `./sync_field_order_postgres_to_json.sh [ENV_FILE] [COMPOSE_FILE] [OUTPUT_FILE]`

## Setup Instructions

### Backend
1. Create a Python virtual environment and install dependencies:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. (Optional) Set a database URL. If not set, the app uses local SQLite databases in `backend/`.
   - PostgreSQL driver support is provided via `psycopg[binary]` in `backend/requirements.txt`.
   - PowerShell:
   ```powershell
   $env:DATABASE_URL = "sqlite:///D:/OneDrive/Development/HLAS/HLaS/backend/members.db"
   ```
   - PostgreSQL example:
   ```powershell
   $env:DATABASE_URL = "postgresql+psycopg://username:password@localhost:5432/hlas"
   ```
3. Enable PostgreSQL-backed runtime mode if using Postgres:
   ```bash
   export DATABASE_URL="postgresql+psycopg://hlas:hlas@localhost:5433/hlas"
   export HLAS_USE_POSTGRES_READS=true
   ```
4. Run the Flask server:
   ```bash
   flask run
   ```

### Member photos in PostgreSQL

Member photos are now supported in PostgreSQL via the `member_photos` table.

- Files are imported from `ID_photos/<CLUB>/`
- Live routes read photo bytes from PostgreSQL first
- Existing file-based fallback is retained for rollout safety

Import existing photos:

```bash
cd backend
POSTGRES_URL='postgresql+psycopg://hlas:hlas@localhost:5433/hlas' python import_member_photos_to_postgres.py
```

Runtime photo routes:
- `/member_photo/<club>/<filename>`
- `/member_photo_for_member/<club>/<member_id>`

### Club documents in PostgreSQL

The `club_documents` table stores uploaded club files directly in PostgreSQL.

If deploying to an existing environment, run migrations to create the table:

```bash
cd backend
alembic upgrade head
```

Then restart backend/frontend services so the Home documents panel and upload APIs are active.

### SQL utilities

Reusable SQL verification packs are stored in `Utilities/`:

- `Utilities/member_paused_verification_pack.sql`
- `Utilities/member_paused_verification_pack_psql.sql`

The `psql` version can be run like this:

```bash
psql "postgresql://hlas:hlas@hlastest:5433/hlas" -v club='GAAFFS' -f Utilities/member_paused_verification_pack_psql.sql
```

### Licence expiry date normalization utility

To normalize legacy `Licence_Exp` values into canonical `YYYY-MM-DD`, use:

`backend/normalize_licence_exp_dates.py`

Default mode is dry-run (no writes). Use `--apply` to persist updates.

Examples:

```bash
cd backend

# PostgreSQL dry-run (uses DATABASE_URL)
python normalize_licence_exp_dates.py

# PostgreSQL apply for one club only
python normalize_licence_exp_dates.py --club GAAFFS --apply

# SQLite dry-run across all backend .db files
python normalize_licence_exp_dates.py --sqlite-all

# SQLite apply for a single DB
python normalize_licence_exp_dates.py --sqlite-db ./GAAFFS.db --apply
```

### Field-order configuration contexts

Field ordering and column visibility are now stored per context. Current member-facing contexts include:

- `fishing_beats`
- `beat_details`

When PostgreSQL runtime mode is enabled, updates are persisted in `app_settings`. The JSON file in `backend/field_order.json` remains the fallback source.

### Frontend
Frontend tooling now targets:

- Node.js 20+
- npm `11.12.1`

The frontend package metadata declares `packageManager: npm@11.12.1`, and the startup scripts use that npm version explicitly.

1. Install Node.js dependencies using npm `11.12.1`:
   ```bash
   cd frontend
   npx --yes npm@11.12.1 install
   ```
2. Start the Vue.js development server:
   ```bash
   npx --yes npm@11.12.1 run dev
   ```
3. Build the production frontend bundle:
   ```bash
   npx --yes npm@11.12.1 run build
   ```

### Browser tab icon (favicon)

Place these files in `frontend/public/`:
- `favicon.ico` (recommended multi-size ICO including 16x16 and 32x32)
- `favicon-32x32.png` (PNG fallback)
- `favicon-16x16.png` (PNG fallback)

The frontend HTML already references these files via `<%= BASE_URL %>`.

### One-command startup scripts

From the repository root (`HLaS`), you can start both servers with a configurable delay (in milliseconds).

- Windows PowerShell:
   ```powershell
   .\start.ps1 -DelayMs 3000 -BackendPort 5050 -FrontendPort 8080
   ```

Optional TLS switches (PowerShell):
- `-TlsOff`: disable HTTPS for both backend and frontend for this run.
- `-BackendTlsOff`: disable HTTPS for backend only for this run.
- `-FrontendTlsOff`: disable HTTPS for frontend only for this run.
- `-UseBackendCertFiles`: force backend HTTPS using certificate files.
- `-BackendCertFile` / `-BackendKeyFile`: cert/key paths used with `-UseBackendCertFiles`.

Example using cert files:
```powershell
.\start.ps1 -UseBackendCertFiles -BackendCertFile .\backend\certs\dev-cert.pem -BackendKeyFile .\backend\certs\dev-key.pem
```

- Linux/macOS Bash:
   ```bash
   chmod +x ./start.sh
   BACKEND_PORT=5050 FRONTEND_PORT=8080 ./start.sh --delay-ms 3000
   ```

Optional TLS switches (Bash):
- `--tls-off`: disable HTTPS for both backend and frontend for this run.
- `--backend-tls-off`: disable HTTPS for backend only for this run.
- `--frontend-tls-off`: disable HTTPS for frontend only for this run.
- `--use-backend-cert-files`: force backend HTTPS using certificate files.
- `--backend-cert-file <path>` / `--backend-key-file <path>`: cert/key paths used with `--use-backend-cert-files`.

Example using cert files:
```bash
./start.sh --use-backend-cert-files --backend-cert-file ./backend/certs/dev-cert.pem --backend-key-file ./backend/certs/dev-key.pem
```

Behavior:
- Starts backend, waits `DelayMs`, checks backend URL, prints `Backend Running` on success.
- Prints `Server Not Running` and aborts if backend health check fails.
- Starts frontend with `npx --yes npm@11.12.1 run dev`, waits the same delay, checks frontend URL, prints `Server Running` on success.
- Prints `Server Not Running` if frontend health check fails.

Optional URL overrides:
- PowerShell parameters: `-BackendUrl`, `-FrontendUrl`
- Bash environment variables: `BACKEND_URL`, `FRONTEND_URL`

Optional port overrides:
- PowerShell parameters: `-BackendPort`, `-FrontendPort`
- Bash environment variables: `BACKEND_PORT`, `FRONTEND_PORT`

### JSON server configuration

Both servers now load startup defaults from JSON config files:

- `backend/server.config.json`
- `frontend/server.config.json`

These files are parsed automatically during startup by:

- `start.ps1`
- `start.sh`
- `backend/app.py` (when running backend directly)
- `frontend/vue.config.js` (when running frontend directly)

#### `backend/server.config.json`

```json
{
   "server": {
      "host": "192.168.50.57",
      "port": 5050,
      "url": "https://192.168.50.57:5050"
   },
   "tls": {
      "enabled": true,
      "adhoc": true,
      "certFile": "",
      "keyFile": ""
   },
   "startup": {
      "delayMs": 3000
   },
   "runtime": {
      "debug": false,
      "useReloader": false
   },
   "logging": {
      "level": "INFO"
   }
}
```

Key fields:
- `server.host` / `server.port`: backend bind address and port
- `server.url`: canonical backend URL used by startup health checks
- `tls.enabled`: enable HTTPS for backend runtime
- `tls.adhoc`: use Flask/Werkzeug adhoc self-signed cert (dev only)
- `tls.certFile` / `tls.keyFile`: optional cert/key paths (used when `tls.adhoc` is `false`)
- `startup.delayMs`: default startup delay used by scripts
- `runtime.debug` / `runtime.useReloader`: backend runtime flags
- `logging.level`: default Flask log level (can be overridden by `LOG_LEVEL`)

#### `frontend/server.config.json`

```json
{
   "server": {
      "host": "192.168.50.57",
      "port": 8080,
      "url": "https://192.168.50.57:8080"
   },
   "tls": {
      "enabled": true,
      "certFile": "",
      "keyFile": ""
   },
   "api": {
      "backendUrl": "https://192.168.50.57:5050"
   },
   "startup": {
      "delayMs": 3000
   }
}
```

Key fields:
- `server.host` / `server.port`: frontend dev server bind address and port
- `server.url`: canonical frontend URL used by startup health checks
- `tls.enabled`: enable HTTPS for Vue dev server
- `tls.certFile` / `tls.keyFile`: optional cert/key paths; if omitted, Vue dev server uses generated dev cert
- `api.backendUrl`: backend API base URL injected as `VUE_APP_BACKEND_URL`
- `startup.delayMs`: default startup delay used by scripts

HTTPS note:
- When frontend HTTPS is enabled, backend should also use HTTPS to avoid browser mixed-content blocks.

#### Local development certificate (created for this repo)

The repository is configured to use a shared dev certificate pair:

- `backend/certs/dev-cert.pem`
- `backend/certs/dev-key.pem`

These paths are already wired in:

- `backend/server.config.json` (`tls.adhoc` is set to `false`)
- `frontend/server.config.json`

To trust this cert on Windows (avoid browser warnings), import it into `CurrentUser\Root`:

```powershell
Import-Certificate -FilePath .\backend\certs\dev-cert.pem -CertStoreLocation Cert:\CurrentUser\Root
```

If your LAN IP changes, regenerate the certificate with the new IP in Subject Alternative Name (SAN) and keep both config files pointing to the updated cert/key.

#### Trusting the Caddy CA on macOS (remote dev server — hlastest)

When using the Docker/Caddy-based dev server (`hlastest`), Caddy generates its own local root CA rather than using the shared cert files above. Use `trust_caddy_mac.sh` to fetch that CA certificate over SSH and install it into the macOS Login Keychain, so Safari and all other macOS TLS clients trust the dev server without warnings. No `sudo` is required.

**Prerequisites:** SSH access to the dev server (`ssh rob@hlastest` must work), and the HLaS Docker stack must be running on that server with the dev Compose override (see below).

#### Starting the dev stack on hlastest

The dev server uses `docker-compose.dev.yml` as a Compose override. This swaps the Caddy configuration from the production Caddyfile (which tries Let's Encrypt) to [deploy/caddy/Caddyfile.dev](deploy/caddy/Caddyfile.dev), which uses Caddy's internal (local) CA and responds to the `hlastest` and `wordpress.hlastest` hostnames. The same override also sets WordPress `WP_HOME` and `WP_SITEURL` to `https://wordpress.hlastest` for local testing.

```bash
# On hlastest — start or restart with the dev override
docker compose -f docker-compose.prod.yml -f docker-compose.dev.yml up -d
```

Without this override, Caddy will repeatedly fail ACME challenges for `anglerconnect.cloud` and the HTTPS handshake for `hlastest` will be rejected entirely.

Dev URLs: `https://hlastest` and `https://wordpress.hlastest`

For URL-path-based multi-club WordPress styling (Phase 1), paste this into **WordPress Admin → HLaS Settings → Club Theme Map (JSON)**:

```json
{
   "CTC": {
      "primary_color": "#1a5490",
      "secondary_color": "#f2f7fc",
      "text_color": "#1f2933",
      "border_color": "#cfd8e3",
      "error_color": "#b42318",
      "success_color": "#2e7d32",
      "logo_url": "https://wordpress.hlastest/wp-content/uploads/club-logos/ctc-logo.png",
      "hero_image_url": "https://wordpress.hlastest/wp-content/uploads/club-heroes/ctc-hero.jpg"
   },
   "GAAFFS": {
      "primary_color": "#1f6f43",
      "secondary_color": "#edf8f1",
      "text_color": "#1f2933",
      "border_color": "#c9e3d3",
      "error_color": "#b42318",
      "success_color": "#2e7d32",
      "logo_url": "https://wordpress.hlastest/wp-content/uploads/club-logos/gaaffs-logo.png",
      "hero_image_url": "https://wordpress.hlastest/wp-content/uploads/club-heroes/gaaffs-hero.jpg"
   },
   "LADFFA": {
      "primary_color": "#7a1f3d",
      "secondary_color": "#fbf0f4",
      "text_color": "#1f2933",
      "border_color": "#e9c8d3",
      "error_color": "#b42318",
      "success_color": "#2e7d32",
      "logo_url": "https://wordpress.hlastest/wp-content/uploads/club-logos/ladffa-logo.png",
      "hero_image_url": "https://wordpress.hlastest/wp-content/uploads/club-heroes/ladffa-hero.jpg"
   }
}
```

Keep the structure and replace only `logo_url`/`hero_image_url` if your media paths differ.

First test URL: `https://wordpress.hlastest/club/GAAFFS/` (swap `GAAFFS` for `CTC` or `LADFFA` to verify club-specific styling and assets).

Single dynamic landing page setup (WordPress):

1. Create one WordPress page with slug `club`.
2. Add HLaS shortcodes to that page (club attribute optional).
3. In WordPress Admin, go to **Settings → Permalinks** and click **Save Changes** once.

After that, requests like `https://wordpress.hlastest/club/CTC/` and `https://wordpress.hlastest/club/GAAFFS/` are served by the same WordPress page, with club context resolved from the URL.

Quick runtime verification for the dev stack:

```bash
./health_check_dev.sh
```

This script runs:
- `docker compose -f docker-compose.prod.yml -f docker-compose.dev.yml ps`
- recent logs for core services
- smoke checks for `http://localhost`, `https://hlastest`, `https://wordpress.hlastest`, and backend `/clubs`

```bash
# Run with defaults (rob@hlastest, /opt/HLaS)
./trust_caddy_mac.sh

# Override host, user, or remote path if needed
./trust_caddy_mac.sh -h mydevserver -u alice -p /home/alice/hlas
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `-h HOST` | `hlastest` | SSH hostname or IP of the dev server |
| `-u USER` | `rob` | SSH username |
| `-p PATH` | `/opt/HLaS` | Path to the HLaS installation on the remote server |

The script will install the cert into your Login Keychain (no Mac password required). After it completes, quit and relaunch Safari if it is already open, then browse to `https://hlastest`.

Re-run the script if Caddy ever regenerates its root CA (e.g. after a `caddy` container rebuild that wipes its `/data` volume).

#### Override precedence

- Explicit script parameters / environment variables still take precedence.
- If no override is supplied, values are taken from the JSON config files.
- If config files are missing or invalid, built-in safe defaults are used.

#### Quick change (new LAN IP)

If your PC IP changes (for example from DHCP), update these values:

1. In `backend/server.config.json`
   - `server.host`
   - `server.url`
2. In `frontend/server.config.json`
   - `server.host`
   - `server.url`
   - `api.backendUrl`

Then restart both servers with `./stop` + `./start` (`stop.ps1` / `start.ps1` on Windows).

### Club login dropdown configuration

The login screen club dropdown is loaded from:

- `backend/clubs.config.json`

Format:

```json
{
   "clubs": [
      {
         "fullName": "GAAFFS",
         "shortName": "GAAFFS",
         "description": "GAAFFS fishing club members",
         "websiteUrl": "https://example.com/gaaffs",
         "adminEmail": "admin@gaaffs.example.com",
         "logoUrl": "/club_logo/GAAFFS"
      }
   ]
}
```

Notes:
- `shortName` is used as the login `club` value (must match your backend DB naming, e.g. `GAAFFS.db`, `CTC.db`).
- `logoUrl` is optional; when present, frontend uses this backend URL for the club logo.
- The frontend fetches clubs from backend endpoint `/clubs` at startup.
- If the member login club dropdown appears empty, verify that `/clubs` is returning data and that the frontend `loadClubs()` function is calling `/clubs`.

### Frontend UI framework (Vuetify)

The Vue frontend now uses Vuetify (Vue 3) as its component framework.

- Plugin setup: `frontend/src/plugins/vuetify.js`
- App wiring: `frontend/src/main.js` and `frontend/src/admin.js`
- Build integration: `frontend/vite.config.js` (`vite-plugin-vuetify` with auto import)

Current migration approach:
- Shared primitives (`frontend/src/components/ui`) wrap framework components.
- Screens consume `AppButton`, `AppCard`, and `AppStatusBadge` instead of framework components directly.
- This keeps reskinning and future framework changes centralized.

### Mobile shells (Capacitor)

The frontend now includes Capacitor project wiring for Android and iOS.

Key files/folders:
- `frontend/capacitor.config.ts`
- `frontend/android/`
- `frontend/ios/`

Useful commands (from `frontend/`):
- `npm run cap:sync` — build web app and sync into both native projects
- `npm run mobile:android` — build + sync Android project
- `npm run mobile:ios` — build + sync iOS project
- `npm run cap:open:android` — open Android project in Android Studio
- `npm run cap:open:ios` — open iOS project in Xcode

Environment profile commands:
- `npm run mobile:which-env` (default mode inspection)
- `npm run mobile:which-env:dev|stage|prod`
- `npm run mobile:sync:dev`
- `npm run mobile:sync:stage`
- `npm run mobile:sync:prod`
- `npm run mobile:android:dev|stage|prod`
- `npm run mobile:ios:dev|stage|prod`

Capacitor profile behaviour:
- Profiles are selected via the sync helper (`frontend/scripts/capacitor-sync.mjs`) and passed as `CAPACITOR_PROFILE=dev|stage|prod`.
- `frontend/capacitor.config.ts` now maps profile-specific app identifiers:
   - prod: `com.hlas.app`
   - stage: `com.hlas.app.stage`
   - dev: `com.hlas.app.dev`
- `server.cleartext` is profile-aware:
   - prod: `false` (production-safe default)
   - stage/dev: `true` (local/staging HTTP flexibility)

Mobile env profile files:
- `frontend/.env.mobile-dev`
- `frontend/.env.mobile-stage`
- `frontend/.env.mobile-prod`

Environment note for device builds:
- Preferred: set `VITE_MOBILE_BACKEND_URL` to a reachable backend URL for real devices/emulators.
- Fallbacks:
   - `VITE_BACKEND_URL` (shared web/mobile override)
   - native default if unset (`http://10.0.2.2:5050` on Android emulator, `http://localhost:5050` on iOS simulator)
   - web default `${window.location.origin}/api` when not running in Capacitor

Phase 6 mobile hardening included:
- Safe-area support via viewport-fit and CSS env insets.
- Native keyboard resize handling (`Keyboard` plugin) with runtime keyboard-open class.
- Native status bar behavior (`StatusBar` plugin with non-overlay webview).
- Capacitor server cleartext support enabled for local/staging profiles and disabled in production profile.

iOS host requirements:
- iOS builds/signing require macOS + Xcode + CocoaPods.
- Platform files can exist on Linux/Windows, but native iOS build steps must run on macOS.

Release process:
- See `MOBILE_RELEASE_CHECKLIST.md` for dev/stage/prod mobile release gates and store submission flow.
- For first-time iOS upload setup (Xcode signing + TestFlight), see `IOS_TESTFLIGHT_FIRST_UPLOAD.md`.

Optional runtime theming (Phase 2 white-labelling):

```json
{
   "clubs": [
      {
         "shortName": "GAAFFS",
         "cssVariables": {
            "--app-color-link": "#0f4c81",
            "--app-color-text-primary": "#17324d",
            "--app-color-state-brand": "#21633a"
         }
      }
   ]
}
```

Theme notes:
- Only CSS variables prefixed with `--app-` are applied.
- Runtime club theme values are merged over the defaults in `frontend/src/styles/design-tokens.css`.
- You can place variables under `cssVariables`, `theme.cssVariables`, or `branding.cssVariables` on each club object.

### Phase 7 pilot reskin (GAAFFS + CTC)

Pilot white-label theme profiles have been added for `GAAFFS` and `CTC` in:

- `backend/clubs.config.json` → `clubs[].cssVariables`

Quick validation checklist:
- Start backend/frontend as normal.
- Select/login with `GAAFFS` and confirm its green/teal palette is applied.
- Switch to `CTC` and confirm its purple-toned palette is applied.
- Switch to a club without `cssVariables` and verify fallback to default token values.
- For mobile shell builds, run `npm run cap:sync` in `frontend/` and reopen native projects.

Quick browser-console check:
- Open DevTools Console on member or admin UI.
- Run `hlasThemeDebug.dumpThemeVariables()` to print active `--app-*` variables.
- Optional: run `hlasThemeDebug.dumpThemeVariables('--app-color-')` to focus on color tokens only.

### New club database template

When a new club is created in Club Admin, backend now provisions the club database by copying:

- `backend/template.db`

This template currently contains the full schema plus a single seed member row for Rob Scoffin (member number `15`).

### One-time logo migration (frontend -> backend)

To migrate existing logos from `frontend/logos` into backend-managed storage (`backend/club_logos`) and populate `logoUrl` in `backend/clubs.config.json`:

```powershell
cd backend
python migrate_club_logos.py
```

Dry run:

```powershell
cd backend
python migrate_club_logos.py --dry-run
```

### Hardened login-user upsert helper

To safely insert/update a club login row (including hashed password and guaranteed non-null `ID` where applicable):

```powershell
cd backend
python upsert_login_user.py --club TEST --username rob@scoffin.com --password password --name "Rob Scoffin" --email rob@scoffin.com --member-number 15
```

Notes:
- Prevents the `Invalid credentials` issue caused by rows with null `ID` in schemas that rely on `ID` as primary-key fallback.
- Always stores password as a Werkzeug hash (never plain text).

### Stop scripts

From the repository root (`HLaS`), stop backend and frontend servers:

- Windows PowerShell:
   ```powershell
   .\stop.ps1 -BackendPort 5050 -FrontendPort 8080
   ```

- Linux/macOS Bash:
   ```bash
   chmod +x ./stop.sh
   BACKEND_PORT=5050 FRONTEND_PORT=8080 ./stop.sh
   ```

Optional port overrides:
- PowerShell parameters: `-BackendPort`, `-FrontendPort`
- Bash environment variables: `BACKEND_PORT`, `FRONTEND_PORT`

### Excel Import
- The backend import script uses `backend/GAAFFS_Members_2026.csv`.
- If you want to import a different file, update `CSV_FILE` in `backend/import_excel.py`.

### Beats Importers

Beat CSV files are imported into the `beats` array in `backend/clubs.config.json`.

Required CSV columns:
- `Beat_ID`
- `River`
- `Beat_Name`
- `Position`
- `Beat_Upstream`
- `Beat_Downstream`
- `Beat_Description`

Optional CSV columns:
- `Detailed_Description`
- `Beat_Upstream_Latitude`
- `Beat_Upstream_Longitude`
- `Beat_Downstream_Latitude`
- `Beat_Downstream_Longitude`

Optional beat JSON fields (for map annotations in `clubs.config.json`):
- `Parking_Locations` (array of objects)
   - `Name`
   - `Description`
   - `Latitude`
   - `Longitude`

Notes:
- If `WHAT3WORDS_API_KEY` is configured for the backend, the Fishing Beats inset map can resolve What3Words locations directly.
- If What3Words lookup is unavailable, the map uses the optional coordinate fallback fields above.
- Parking pushpins are rendered from `Parking_Locations` when valid coordinates are present.

Example CSV (`<CLUB>_beats.csv`):

```csv
Beat_ID,River,Beat_Name,Position,Beat_Upstream,Beat_Downstream,Beat_Upstream_Latitude,Beat_Upstream_Longitude,Beat_Downstream_Latitude,Beat_Downstream_Longitude,Beat_Description,Detailed_Description
A,Witham,Ponton A,3,///coffee.pastels.excellent,///hunk.calms.hardens,52.9089,-0.5621,52.9065,-0.5592,Upstream of Bridge,"Access from the farm gate opposite the bridge; fish upstream in low water."
B,Witham,Ponton B,4,///hunk.calms.hardens,///rectangular.leaps.nearing,52.9065,-0.5592,52.9037,-0.5534,Downstream of Bridge,"Best in evening hatch windows; watch footing near the cut bank."
```

Available club-specific scripts:
- `backend/import_gaaffs_beats.py` (expects `backend/GAAFFS_beats.csv`)
- `backend/import_ctc_beats.py` (expects `backend/CTC_beats.csv`)
- `backend/import_ladffa_beats.py` (expects `backend/LADFFA_beats.csv`)
- `backend/import_test_beats.py` (expects `backend/TEST_beats.csv`)

Run an importer:

```bash
python3 backend/import_gaaffs_beats.py
```

Generic template for new clubs:
- Copy `backend/import_club_beats_template.py` to a new file (e.g. `backend/import_myclub_beats.py`)
- Set `CLUB_SHORT_NAME` and `BEATS_CSV_FILENAME`
- Run your new script with `python3`

Shared helper module:
- `backend/import_beats_common.py` (CSV validation, mapping, and What3Words normalization)

Available sync scripts:
- `sync_beats_postgres_to_json.py` (export PostgreSQL beats to JSON config - local dev)
- `sync_beats_via_api.py` (API-based beats export/import - local dev)
- `backend/sync_beats_json_to_postgres.py` (import JSON beats to PostgreSQL - VPS production)
  - Used automatically on backend startup
  - Can be run manually with `--dry-run` flag

## Syncing Fishing Beats between Development and Production

After updating fishing beats in your local development PostgreSQL database, use the export/import API to sync changes to the VPS:


### Local Development: Export and Commit

1. **Export beats from PostgreSQL to JSON config:**

   ```bash
   # Option 1: Direct database sync (fastest, requires DATABASE_URL)
   python3 sync_beats_postgres_to_json.py
   
   # Option 2: Via API (requires running backend on localhost:5050)
   python3 sync_beats_via_api.py
   ```

2. **Commit the updated `clubs.config.json`:**

   ```bash
   git add backend/clubs.config.json
   git commit -m "Sync beats from local PostgreSQL: <brief description>"
   git push origin main
   ```

### VPS Production: Automatic Beats Sync

After pulling the updated main branch on the VPS:

1. **Restart the backend container:**

   ```bash
   docker compose down backend
   docker compose up -d backend
   ```

2. **Beats automatically sync on startup:**
   - Backend startup hook runs `sync_beats_json_to_postgres.py`
   - PostgreSQL `club_beats` table is populated from `clubs.config.json`
   - Check container logs for sync status: `docker compose logs backend | grep -i beats`

3. **Manual sync (optional):**
   
   If you need to resync without restarting:
   ```bash
   # Dry-run first to preview changes
   docker exec hlas-backend-1 python3 /app/sync_beats_json_to_postgres.py --dry-run
   
   # Actually sync beats
   docker exec hlas-backend-1 python3 /app/sync_beats_json_to_postgres.py
   ```

### API Endpoints

- **Export:** `GET /admin/clubs/<club>/beats/export` → returns JSON beats array
- **Import (JSON):** `POST /admin/clubs/<club>/beats/import` → accepts `{"beats": [...]}` payload

## Security

## Mobile Responsive UI

The application is optimised for mobile devices with the following responsive breakpoints:

| Breakpoint | Behaviour |
|---|---|
| ≤ 1 000 px | Navigation sidebar stacks above content; sticky positioning disabled |
| ≤ 768 px | Navigation buttons switch to a 2-column grid layout at 80 vw; all content areas expand to 100 % window width and are centred at 80 vw |
| ≤ 400 px | Home greeting font sizes reduced for very small screens |

Responsive rules are all located in the `@media` blocks at the bottom of `frontend/App.vue`.

Per-page responsive rules:

- **Beat Details** — details table collapses to a 2-column label/value grid (≤ 1 000 px), defined in `frontend/src/components/BeatDetails.vue`.
- **Catch Return** — responsive adjustments at ≤ 720 px.
- **Membership Admin** — responsive adjustments at ≤ 1 000 px / ≥ 1 001 px.
- **Newsletters** — layout adjustments at ≤ 900 px.

## Frontend Dependencies

Current pinned versions (as of April 2026):

| Package | Version |
|---|---|
| vue | ^3.5.33 |
| vuetify | ^4.0.6 |
| vite | ^8.0.10 |
| axios | ^1.15.2 |
| leaflet | ^1.9.4 |
| @capacitor/core | ^8.3.1 |
| @capacitor/android | ^8.3.1 |
| @capacitor/ios | ^8.3.1 |

Security audit status: **0 vulnerabilities** (last checked April 2026).

## Production deployment (Docker + VPS)

Production containerization and VPS rollout instructions are in:

- `DEPLOYMENT.md`

### Trusting test TLS certificate on Windows (Edge + Chrome)

When using Caddy `tls internal` for the test server, trust the local CA certificate on each Windows client.

Certificate file:

- `deploy/caddy/caddy-local-root.crt`

Edge and Chrome both use the Windows certificate store, so one import covers both browsers.

Install for all users (recommended, run PowerShell as Administrator):

```powershell
Import-Certificate -FilePath .\deploy\caddy\caddy-local-root.crt -CertStoreLocation Cert:\LocalMachine\Root
```

Install for current user only (no admin rights):

```powershell
Import-Certificate -FilePath .\deploy\caddy\caddy-local-root.crt -CertStoreLocation Cert:\CurrentUser\Root
```

GUI alternative:

1. Run `certmgr.msc` (current user) or `certlm.msc` (local machine).
2. Open `Trusted Root Certification Authorities` -> `Certificates`.
3. Import `caddy-local-root.crt` into that store.

After import, fully restart Edge/Chrome and test:

- `https://HLaSTest`
- `https://192.168.50.221`

### Password Encryption
- All passwords are encrypted using Werkzeug's `scrypt` algorithm before storage
- Passwords are never stored as plain text in the database
- The default password for imported members is `password` (hashed)
- Password hashes are automatically generated during CSV import
- Migration script available: `backend/migrate_passwords.py` to hash existing plain-text passwords

---

## Documentation

For comprehensive information on specific features and operations, refer to:

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment architecture, backend changes, API endpoints
- **[MINI_SITE.md](MINI_SITE.md)** - Club mini sites feature guide, configuration, and API reference
- **[BACKUP_SYSTEM.md](BACKUP_SYSTEM.md)** - Backup system setup, usage, troubleshooting, and best practices
- **[BACKUP_QUICK_START.md](BACKUP_QUICK_START.md)** - 5-minute backup system setup guide
- **[BACKUP_SCHEDULING_GUIDE.md](BACKUP_SCHEDULING_GUIDE.md)** - Automated backup scheduling (cron, systemd, Docker)
- **[.env.backup.example](.env.backup.example)** - Backup system configuration template
- **[docker-compose.backup.yml](docker-compose.backup.yml)** - Docker Compose examples for automated backups
- **[backend/install_backup_scheduler.sh](backend/install_backup_scheduler.sh)** - Interactive backup scheduling setup tool
- **[MOBILE_RELEASE_CHECKLIST.md](MOBILE_RELEASE_CHECKLIST.md)** - iOS TestFlight release process
- **[IOS_TESTFLIGHT_FIRST_UPLOAD.md](IOS_TESTFLIGHT_FIRST_UPLOAD.md)** - Initial TestFlight setup

For further details, see the documentation in each folder.
