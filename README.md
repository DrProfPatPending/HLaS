# HLaS

HLaS is a fishing club membership management application with separate member and admin user experiences, PostgreSQL-backed runtime data, and Vue/Flask frontends for day-to-day club operations.

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
- Added a new Admin tab: **App Settings**.
- Added global **Date Format** configuration in App Settings with selectable format patterns.
- Added backend `/admin/app-settings` API to load/save global app settings.
- Restored the member login club dropdown loading from `/clubs`.
- Restored and improved Membership Admin sorting and filtering behavior.
- `Members_Name` opens Edit Member Details; `Number` opens member lookup/details.
- Edit Member navigation now uses the full matching result set instead of just the visible page.
- Member ID photos are imported into PostgreSQL and served DB-first with file fallback.
- Added reusable SQL verification packs in `Utilities/`.
- Added a new Beat Details member page with dedicated field-order configuration.
- Beat Details now reuses the Fishing Beats detail map logic, including upstream/downstream markers and parking locations.
- The post-login member home page now presents navigation actions vertically on the left with a placeholder `<Club> News and Updates` table in the center.
- Added database-backed club document management:
   - Club Admin and higher can upload/delete documents.
   - Members can view and download documents for their club.
   - Home page now shows a `<Club> Documents` table alongside `<Club> News and Updates`.

## Key Features
- **Distinct login and UI for admin/system users** at `/admin/` (AdminApp.vue)
- **Member/club users** use the main UI at `/` (App.vue)
- **Admin App Settings tab** for global application settings (starting with Date Format)
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

### Beat Details page

The new Beat Details page provides a dedicated beat-centric detail view separate from the Fishing Beats listing.

Current behavior:

- beat selector labels display `<Beat ID> <Beat Name>`
- detail fields use the `beat_details` field-order context from `field_order.json` / `app_settings`
- map display reuses the Fishing Beats detail map implementation
- map shows upstream and downstream limits plus any configured parking markers
- what3words locations are resolved through `/w3w/coordinates` when direct coordinates are unavailable

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
1. Install Node.js dependencies using npm `11.12.1`:
   ```bash
   cd frontend
   npx --yes npm@11.12.1 install
   ```
2. Start the Vue.js development server:
   ```bash
   npx --yes npm@11.12.1 run dev
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
- Starts frontend, waits the same delay, checks frontend URL, prints `Server Running` on success.
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

## Security

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

For further details, see the documentation in each folder.
