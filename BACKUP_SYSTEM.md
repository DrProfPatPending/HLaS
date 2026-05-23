# HLaS Backup & Snapshot System

A comprehensive backup solution for the HLaS system with support for database snapshots, filesystem backups, and cloud storage integration.

### Language Convention

- User-facing copy and documentation in this repository should default to British English spelling (for example: recognised, localisation, authorised).
- Keep external API/library identifiers unchanged where spelling is fixed by the platform (for example: `wp_localize_script`).

### Deployment Script Reference

If you are rebuilding/deploying with `./hlas_build.sh`, note these CLI pairs:

- `--clean` / `-c` enables post-build Docker prune
- `--noclean` / `--no-clean` / `-C` explicitly disables post-build prune
- `--verbose` / `-v` enables command output
- `--quiet` / `-q` and `--noverbose` / `--no-verbose` / `-V` suppress command output

The script uses **last flag wins** semantics (for example, `--clean -C` ends with no clean).

Canonical reference for all current `hlas_build.sh` options: see [DEPLOYMENT.md](DEPLOYMENT.md) (Deployment Scripts options table).

## Overview

The backup system provides:

- **Database Snapshots**: PostgreSQL backups using `pg_dump`
- **Filesystem Backups**: Tarball archives of critical files (logos, photos, documents, configs)
- **Full Snapshots**: Combined database + filesystem backups
- **Cloud Integration**: Upload to AWS S3, MinIO, DigitalOcean Spaces, or any S3-compatible service
- **Snapshot Management**: List, download, delete, and cleanup operations
- **Retention Policies**: Automatic cleanup of old snapshots
- **CLI Tools**: Command-line utilities for administrators
- **API Endpoints**: HTTP API for web UI integration
- **Scheduled Backups**: Automated backups via cron

## Architecture

```
HLaS Backup System
├── BackupManager (backup.py)
│   ├── Create snapshots (database, filesystem, full)
│   ├── List/info/delete snapshots
│   ├── Cleanup old snapshots
│   └── SQLite metadata database
├── CloudBackupUploader (backup.py)
│   ├── Upload to S3-compatible storage
│   ├── Download from cloud
│   └── List cloud snapshots
├── API Routes (routes/backup_routes.py)
│   ├── /admin/backups/snapshots (CRUD)
│   ├── /admin/backups/snapshots/create/* (create operations)
│   ├── /admin/backups/cloud/* (cloud storage)
│   └── /admin/backups/status (system status)
└── CLI Tool (backup_cli.py)
    ├── Manual snapshot creation
    ├── Cloud uploads
    ├── Backup scheduling
    └── System management
```

## Installation

### 1. Add Dependencies

Add to `backend/requirements.txt`:

```
boto3>=1.26.0          # AWS S3 SDK (optional, only if using cloud storage)
python-crontab>=2.6.0  # Cron scheduling (optional, for --schedule command)
```

Install:
```bash
cd backend
pip install -r requirements.txt
```

### 2. Register API Routes

In `backend/app.py`, add this after creating the Flask app:

```python
from routes.backup_routes import create_backup_routes
from auth import require_permission

# ... existing code ...

# Register backup routes (after other routes)
if os.getenv('ENABLE_BACKUPS', 'true').lower() == 'true':
    create_backup_routes(app, get_principal_context, require_permission)
```

### 3. Add Backup Permissions

In your roles/permissions system, add these permissions:

```python
# Admin permission scopes
'backup.create'    # Create snapshots
'backup.read'      # View snapshots
'backup.download'  # Download snapshots
'backup.delete'    # Delete snapshots
```

### 4. Create Backup Directory

```bash
mkdir -p /data/backups
```

### 5. Docker Compose Configuration

Add to `docker-compose.prod.yml`:

```yaml
services:
  backend:
    environment:
      HLAS_BACKUP_DIR: /data/backups
      ENABLE_BACKUPS: "true"
    volumes:
      - hlas_backups:/data/backups
      # ... existing volumes ...

volumes:
  hlas_backups:
    external: true
    name: hlas_backups
```

Create the volume:
```bash
docker volume create hlas_backups
```

## Usage

### API Endpoints

#### List Snapshots
```bash
GET /admin/backups/snapshots?type=full&limit=10
```

Response:
```json
{
  "success": true,
  "count": 2,
  "snapshots": [
    {
      "id": "full-2026-01-15T10-30-45.123456",
      "snapshot_type": "full",
      "size_bytes": 1073741824,
      "created_at": "2026-01-15T10:30:45.123456",
      "description": "Pre-maintenance backup",
      "file_count": 1500,
      "status": "success"
    }
  ]
}
```

#### Get Snapshot Info
```bash
GET /admin/backups/snapshots/full-2026-01-15T10-30-45.123456
```

#### Create Database Snapshot
```bash
POST /admin/backups/snapshots/create/database
Content-Type: application/json

{
  "description": "Daily backup",
  "compress": true
}
```

#### Create Filesystem Snapshot
```bash
POST /admin/backups/snapshots/create/filesystem
Content-Type: application/json

{
  "directories": ["/data", "/app/club_logos"],
  "description": "File assets backup",
  "compress": true
}
```

#### Create Full Snapshot
```bash
POST /admin/backups/snapshots/create/full
Content-Type: application/json

{
  "description": "Complete system backup",
  "compress": true
}
```

#### Cleanup Old Snapshots
```bash
POST /admin/backups/cleanup
Content-Type: application/json

{
  "days": 30,
  "max_snapshots": 10
}
```

#### Download Snapshot
```bash
GET /admin/backups/snapshots/full-2026-01-15T10-30-45.123456/download
```

#### Backup Status
```bash
GET /admin/backups/status
```

Response:
```json
{
  "success": true,
  "backup_dir": "/data/backups",
  "total_snapshots": 15,
  "recent_snapshots": 5,
  "total_size_bytes": 53687091200,
  "latest_snapshot": { ... }
}
```

### CLI Commands

#### Create Snapshots

```bash
# Database only
python3 backend/backup_cli.py create-db \
  --description="Pre-release backup"

# Filesystem only
python3 backend/backup_cli.py create-fs \
  --dirs="/data,/app/club_logos" \
  --description="File assets"

# Full backup (both database + filesystem)
python3 backend/backup_cli.py create-full \
  --description="Complete system backup"
```

#### List Snapshots

```bash
# All snapshots
python3 backend/backup_cli.py list

# Filter by type
python3 backend/backup_cli.py list --type=database --limit=5
```

#### View Snapshot Details

```bash
python3 backend/backup_cli.py info full-2026-01-15T10-30-45.123456
```

#### Delete Snapshot

```bash
# With confirmation prompt
python3 backend/backup_cli.py delete full-2026-01-15T10-30-45.123456

# Force delete without prompt
python3 backend/backup_cli.py delete full-2026-01-15T10-30-45.123456 --force
```

#### Cleanup Old Snapshots

```bash
# Delete snapshots older than 30 days
python3 backend/backup_cli.py cleanup --days=30

# Keep only 10 most recent snapshots
python3 backend/backup_cli.py cleanup --max=10

# Combine both policies
python3 backend/backup_cli.py cleanup --days=30 --max=10
```

#### View System Status

```bash
python3 backend/backup_cli.py status
```

Output:
```
=== HLaS Backup System Status ===

Backup directory: /data/backups
Total snapshots: 15
Total size: 50.25 GB

Latest snapshots:
  full-2026-01-15T10-30-45 (1024.5 MB) - 2026-01-15 10:30:45
  db-2026-01-14T09-15-22 (256.3 MB) - 2026-01-14 09:15:22
  fs-2026-01-10T02-00-00 (512.0 MB) - 2026-01-10 02:00:00

Cloud storage: Not configured
```

## Cloud Storage Integration

The backup system supports any S3-compatible storage:

- **AWS S3**
- **MinIO** (self-hosted)
- **DigitalOcean Spaces**
- **Wasabi**
- **Backblaze B2** (via S3 API)
- Other S3-compatible services

### Configuration

#### Via API

```bash
POST /admin/backups/cloud/config
Content-Type: application/json

{
  "bucket": "my-backups",
  "region": "us-east-1",
  "access_key": "AKIA...",
  "secret_key": "wJal...",
  "endpoint_url": "https://s3.amazonaws.com"  # Optional, for custom endpoints
}
```

#### Via Environment Variables

```bash
# AWS S3
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="wJal..."
export BACKUP_CLOUD_BUCKET="my-backups"
export BACKUP_CLOUD_REGION="us-east-1"

# MinIO / other S3-compatible
export BACKUP_CLOUD_ENDPOINT="https://minio.example.com:9000"
```

#### Via Docker Compose

```yaml
services:
  backend:
    environment:
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      BACKUP_CLOUD_BUCKET: my-backups
      BACKUP_CLOUD_REGION: us-east-1
      # BACKUP_CLOUD_ENDPOINT: https://minio.example.com (optional)
```

### Upload to Cloud

```bash
# Via API
POST /admin/backups/snapshots/{snapshot_id}/upload
Content-Type: application/json

{
  "object_key": "snapshots/2026-01/full-backup"
}
```

```bash
# Via CLI
python3 backend/backup_cli.py upload full-2026-01-15T10-30-45 \
  --bucket=my-backups \
  --key=snapshots/2026-01/full-backup
```

## Scheduling Backups

Automated backups can be scheduled using:

1. **Interactive Setup (Recommended)** - Guided configuration tool
2. **Cron** - Traditional Linux task scheduler
3. **Systemd Timers** - Modern Linux approach
4. **Docker Compose** - Container-based scheduling

### Quick Start

```bash
# Run the interactive setup assistant
chmod +x backend/install_backup_scheduler.sh
./backend/install_backup_scheduler.sh
```

This will guide you through the entire setup process.

### Manual Setup Options

For detailed instructions on each scheduling method, see:

**[→ BACKUP_SCHEDULING_GUIDE.md](BACKUP_SCHEDULING_GUIDE.md)** - Comprehensive guide with examples

Quick reference:

```bash
# Cron-based (traditional)
cd backend
export DATABASE_URL="postgresql://..."
./schedule_backups_cron.sh daily

# Systemd timers (modern, recommended)
sudo cp backend/hlas-backup.service /etc/systemd/system/
sudo cp backend/hlas-backup.timer /etc/systemd/system/
sudo systemctl enable hlas-backup.timer
sudo systemctl start hlas-backup.timer
```

### Available Scheduling Templates

- **[schedule_backups_cron.sh](backend/schedule_backups_cron.sh)** - Cron setup script
- **[hlas-backup.service](backend/hlas-backup.service)** - Systemd service unit
- **[hlas-backup.timer](backend/hlas-backup.timer)** - Systemd timer unit
- **[SYSTEMD_TIMER_EXAMPLES.md](backend/SYSTEMD_TIMER_EXAMPLES.md)** - Timer schedule examples
- **[install_backup_scheduler.sh](backend/install_backup_scheduler.sh)** - Interactive setup tool

#### Restore Database

```bash
# Extract database dump
gunzip database.sql.gz

# Restore to PostgreSQL
psql -U hlas -d hlas -f database.sql
```

#### Restore Filesystem

```bash
# Extract tarball
tar -xzf filesystem.tar.gz -C /

# Or verify contents first
tar -tzf filesystem.tar.gz | head -20
```

#### Restore Full Snapshot

```bash
# Extract full snapshot directory
cd /data/backups/snapshots/full-2026-01-15T10-30-45

# Restore database
gunzip -k database.sql.gz
psql -U hlas -d hlas -f database.sql

# Restore filesystem
cd ../..
tar -xzf snapshots/full-2026-01-15T10-30-45/filesystem.tar.gz -C /
```

## Backup Strategy Recommendations

### Small Deployments (< 10 GB)
- **Daily full backups** at 2 AM
- **Retention**: Keep 7-14 most recent snapshots
- **Storage**: Local disk or cloud storage
- **RPO**: 24 hours (Recovery Point Objective)
- **RTO**: 1-2 hours (Recovery Time Objective)

### Medium Deployments (10-100 GB)
- **Daily full backups** at 2 AM
- **Weekly cloud uploads** to redundant storage
- **Retention**: Keep 7 local + 4 cloud backups
- **Storage**: Local disk + cloud storage (S3, MinIO)
- **RPO**: 24 hours
- **RTO**: 2-4 hours

### Large Deployments (> 100 GB)
- **Incremental database backups** daily
- **Full backups** weekly
- **Hourly filesystem snapshots** (if needed)
- **Daily cloud uploads**
- **Multi-region replication**
- **Retention**: Keep 30+ days on disk, 90 days in cloud
- **Storage**: Local fast storage + Glacier for long-term
- **RPO**: 1 hour
- **RTO**: 1-2 hours

### Development/Testing
- **On-demand snapshots** before major changes
- **Retention**: Keep 3-5 recent snapshots
- **Storage**: Local disk only

## Monitoring & Alerts

### Monitor Backup Log

```bash
# Follow backup logs
tail -f /var/log/hlas-backup.log

# Search for errors
grep ERROR /var/log/hlas-backup.log
```

### Check Backup Status via API

```bash
# Get current status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5050/admin/backups/status
```

### Set Up Email Alerts

Add to backup script:

```bash
#!/bin/bash
LOG_FILE="/var/log/hlas-backup.log"
EMAIL="admin@example.com"

python3 /opt/HLaS/backend/backup_cli.py create-full >> "$LOG_FILE" 2>&1

if [ $? -ne 0 ]; then
  tail -20 "$LOG_FILE" | mail -s "HLaS Backup Failed" "$EMAIL"
fi
```

## Troubleshooting

### "DATABASE_URL not configured"

```bash
# Check environment variable
echo $DATABASE_URL

# Or in Docker
docker exec hlas-backend env | grep DATABASE_URL
```

### "pg_dump: command not found"

Install PostgreSQL client tools:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-client

# macOS
brew install postgresql

# Alpine
apk add postgresql-client
```

### "boto3 not installed"

```bash
pip install boto3
```

### Upload to S3 fails

Check credentials:
```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export BACKUP_CLOUD_BUCKET="..."

python3 backend/backup_cli.py upload <snapshot-id>
```

### Out of Disk Space

Delete old snapshots:
```bash
python3 backend/backup_cli.py cleanup --days=7 --max=5
```

## Permission Model

The backup system uses role-based permissions integrated with HLaS RBAC system. Permissions are stored in `backend/security/permissions.py` and enforced on all API endpoints.

### Backup Permissions

```python
{
  'backup.create': 'Create new snapshots (database, filesystem, full)',
  'backup.read': 'List and view snapshot details',
  'backup.download': 'Download snapshot files',
  'backup.delete': 'Delete snapshots',
}
```

### Role-Based Access Control

Backup permissions are restricted to system-level administrators:

| Role | Permissions | Scope |
|------|-------------|-------|
| `app_owner` | `backup.*` (all) | System-wide, all clubs |
| `app_admin` | `backup.*` (all) | System-wide, all clubs |
| `club_manager` | None | Limited to club-scoped data |
| `club_admin` | None | Limited to club-scoped data |
| `user` | None | Limited to self-data |

### Why Admin-Only?

Backup operations are restricted because they:
1. Provide access to sensitive system data
2. Can impact system availability during backups
3. Include database and file system data for all clubs
4. Require trusted administrator oversight
5. Should not be delegated to club-level admins

### Permission Enforcement

All backup API endpoints require `@require_backup_permission` decorator:

```python
@bp.route('/snapshots', methods=['GET'])
@require_backup_permission('read')
def list_snapshots():
    # Only app_admin and app_owner can call this
    ...
```

If a user without the required permission attempts to access a backup endpoint:
- API returns `401 Unauthorized` if not authenticated
- API returns `403 Forbidden` if authenticated but lacks permission

### Integration Points

The backup system hooks into HLaS authentication and authorization:

- `require_permission()` - Validates user roles before API access
- `Principal` context - Contains user roles and permissions
- Role assignments - Managed via `/admin/roles` API
- Audit logging - All backup operations can be logged for compliance

### Example: Checking User Permissions

```bash
# As app_owner or app_admin - SUCCESS
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:5050/admin/backups/snapshots
# Response: 200 OK with snapshot list

# As club_admin - FORBIDDEN
curl -H "Authorization: Bearer $CLUB_ADMIN_TOKEN" \
  http://localhost:5050/admin/backups/snapshots
# Response: 403 Forbidden

# Without token - UNAUTHORIZED
curl http://localhost:5050/admin/backups/snapshots
# Response: 401 Unauthorized
```

## Future Enhancements

Potential improvements:

1. **Incremental Backups**: Only backup changed files/data
2. **Deduplication**: Reduce storage by detecting duplicate blocks
3. **Restore UI**: Web interface for snapshot restore
4. **Backup Verification**: Periodically test restore to verify integrity
5. **Bandwidth Throttling**: Limit backup upload speed
6. **Encryption**: Encrypt snapshots before cloud upload
7. **Point-in-Time Recovery**: Restore to specific timestamps
8. **Differential Backup**: Backup changes since last backup
9. **Snapshot Compaction**: Merge old snapshots
10. **Cost Reporting**: Estimate cloud storage costs

## Support & Issues

For issues or questions:
1. Check the logs: `/var/log/hlas-backup.log`
2. Run status command: `python3 backend/backup_cli.py status`
3. Test connectivity: `python3 -c "import boto3; print('boto3 OK')"`
4. Verify permissions: Check user has `backup.*` roles assigned
