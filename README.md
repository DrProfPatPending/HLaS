# Fishing Club Membership Management Web Application

This project is a simple web application for managing the membership of a fishing club. It consists of:

- **Backend:** Python Flask REST API with SQLite database
- **Frontend:** Vue.js application for member management
- **Excel Import:** Script to import member data from Excel into the database

## Project Structure
- `backend/` - Flask API and database
- `frontend/` - Vue.js app
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
2. (Optional) Set a database URL. If not set, the app uses local SQLite at `backend/members.db`.
   - PostgreSQL driver support is provided via `psycopg[binary]` in `backend/requirements.txt`.
   - PowerShell:
   ```powershell
   $env:DATABASE_URL = "sqlite:///D:/OneDrive/Development/HLAS/HLaS/backend/members.db"
   ```
   - PostgreSQL example:
   ```powershell
   $env:DATABASE_URL = "postgresql+psycopg://username:password@localhost:5432/hlas"
   ```
3. Run the Flask server:
   ```bash
   flask run
   ```

### Frontend
1. Install Node.js dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Start the Vue.js development server:
   ```bash
   npm run serve
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
