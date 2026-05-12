# Backend Script Execution Guide

This guide explains how to run backend development scripts locally or via Docker.

## Quick Start

### Option 1: Local venv (Fastest - Recommended for development)

```bash
# Activate the virtual environment
source backend-venv/bin/activate

# Run any backend script directly
python3 backend/sync_beats_postgres_to_json.py
python3 backend/import_club_logos_to_postgres.py -v
python3 backend/backup_cli.py --help

# Deactivate when done
deactivate
```

### Option 2: Docker Helper Script (Best for CI/CD and portability)

```bash
# Run scripts without activating venv
./run_backend_script.sh sync_beats_postgres_to_json.py
./run_backend_script.sh import_club_logos_to_postgres.py -v
./run_backend_script.sh backup_cli.py --help
```

---

## Detailed Setup

### Option 1: Local Python Virtual Environment

#### Initial Setup (One-time)

```bash
# 1. Create the virtual environment
python3 -m venv backend-venv

# 2. Activate it
source backend-venv/bin/activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Verify installation
python3 -c "import sqlalchemy; print(f'✅ SQLAlchemy installed')"
```

#### Using the venv

```bash
# Always activate first
cd /opt/HLaS
source backend-venv/bin/activate

# Run scripts as normal
python3 backend/sync_beats_postgres_to_json.py
python3 backend/import_club_logos_to_postgres.py

# Deactivate when done
deactivate
```

**Advantages:**
- Fast (no Docker overhead)
- Convenient for development
- Can use IDE integration
- Direct access to databases

**Disadvantages:**
- Only works on Linux/macOS with Python 3.13
- Requires local setup
- May not match container environment exactly

---

### Option 2: Docker Helper Script

#### Setup (One-time)

The helper script is already created and executable at:
```bash
/opt/HLaS/run_backend_script.sh
```

#### Using the helper

```bash
# Run scripts without activating anything
./run_backend_script.sh sync_beats_postgres_to_json.py
./run_backend_script.sh import_club_logos_to_postgres.py -v
./run_backend_script.sh backup_cli.py export-db

# Pass any arguments normally
./run_backend_script.sh my_script.py --arg1 value1 --arg2 value2

# Override container name if needed
HLAS_BACKEND_CONTAINER=custom-backend ./run_backend_script.sh sync_beats_postgres_to_json.py
```

**Advantages:**
- Works across all platforms (macOS, Linux, Windows with WSL)
- Guaranteed to match container environment
- No local dependencies
- Perfect for CI/CD pipelines
- Container must be running

**Disadvantages:**
- Slightly slower (Docker overhead)
- Requires Docker to be running

---

## Common Scripts

### Sync PostgreSQL → clubs.config.json

**Purpose:** Persist waypoints and beat data changes from database back to config file

```bash
# Option 1: Local venv
source backend-venv/bin/activate
python3 backend/sync_beats_postgres_to_json.py
deactivate

# Option 2: Docker helper
./run_backend_script.sh sync_beats_postgres_to_json.py
```

### Import Club Logos to PostgreSQL

**Purpose:** Load club logos from filesystem into database

```bash
# Option 1: Local venv
source backend-venv/bin/activate
python3 backend/import_club_logos_to_postgres.py
deactivate

# Option 2: Docker helper
./run_backend_script.sh import_club_logos_to_postgres.py
```

### Database Backup

**Purpose:** Create manual backup of PostgreSQL database

```bash
# Option 1: Local venv
source backend-venv/bin/activate
python3 backend/backup_cli.py export-db
deactivate

# Option 2: Docker helper
./run_backend_script.sh backup_cli.py export-db
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'sqlalchemy'"

**If using local venv:**
```bash
# Make sure venv is activated
source backend-venv/bin/activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

**If using Docker helper:**
```bash
# Check if backend container is running
docker ps | grep hlas-backend

# If not running, start it
docker compose up -d hlas-backend-1
```

### "container not found"

```bash
# List available containers
docker ps | grep hlas

# Check the container name and use environment variable
HLAS_BACKEND_CONTAINER=correct-name ./run_backend_script.sh sync_beats_postgres_to_json.py
```

### Python version mismatch

The local venv uses Python 3.13. If you have a different version:
```bash
# Try explicit Python 3.13
python3.13 -m venv backend-venv

# Or if unavailable, adapt to your Python 3.11+
python3.11 -m venv backend-venv
```

---

## .gitignore Entry

The `backend-venv` directory should be ignored (it already is). Never commit virtual environments to git:

```
backend-venv/
```

---

## Recommendations

- **For daily development:** Use local venv (faster iteration)
- **For CI/CD and deployment scripts:** Use Docker helper (consistency)
- **For one-off tasks:** Either method works fine

