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
