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

- Linux/macOS Bash:
   ```bash
   chmod +x ./start.sh
   BACKEND_PORT=5050 FRONTEND_PORT=8080 ./start.sh 3000
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
      "url": "http://192.168.50.57:5050"
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
- `startup.delayMs`: default startup delay used by scripts
- `runtime.debug` / `runtime.useReloader`: backend runtime flags
- `logging.level`: default Flask log level (can be overridden by `LOG_LEVEL`)

#### `frontend/server.config.json`

```json
{
   "server": {
      "host": "192.168.50.57",
      "port": 8080,
      "url": "http://192.168.50.57:8080"
   },
   "api": {
      "backendUrl": "http://192.168.50.57:5050"
   },
   "startup": {
      "delayMs": 3000
   }
}
```

Key fields:
- `server.host` / `server.port`: frontend dev server bind address and port
- `server.url`: canonical frontend URL used by startup health checks
- `api.backendUrl`: backend API base URL injected as `VUE_APP_BACKEND_URL`
- `startup.delayMs`: default startup delay used by scripts

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

### Password Encryption
- All passwords are encrypted using Werkzeug's `scrypt` algorithm before storage
- Passwords are never stored as plain text in the database
- The default password for imported members is `password` (hashed)
- Password hashes are automatically generated during CSV import
- Migration script available: `backend/migrate_passwords.py` to hash existing plain-text passwords

---

For further details, see the documentation in each folder.
