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
