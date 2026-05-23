# HLaS Backup System - Quick Start Guide

### Language Convention

- User-facing copy and documentation in this repository should default to British English spelling (for example: recognised, localisation, authorised).
- Keep external API/library identifiers unchanged where spelling is fixed by the platform (for example: `wp_localize_script`).

## 5-Minute Setup

### Step 1: Install Python Dependencies

```bash
cd backend
pip install boto3        # For cloud storage (optional)
```

### Step 2: Create Backup Directory

```bash
mkdir -p /data/backups
chmod 755 /data/backups
```

### Step 3: Create Docker Volume (if using Docker)

```bash
docker volume create hlas_backups
```

### Step 4: Register Routes in Backend

Edit `backend/app.py` and add after other route registrations:

```python
from routes.backup_routes import create_backup_routes

# After other route registrations
if os.getenv('ENABLE_BACKUPS', 'true').lower() == 'true':
    create_backup_routes(app, get_principal_context, require_permission)
```

### Step 5: Test It

```bash
# Create your first backup
python3 backend/backup_cli.py create-full --description="Initial backup"

# Check backup was created
python3 backend/backup_cli.py list

# View system status
python3 backend/backup_cli.py status
```

**✓ Backup system is now ready!**

---

## Enable Cloud Storage (Optional)

### AWS S3 Setup

```bash
# Set credentials
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="wJal..."
export BACKUP_CLOUD_BUCKET="my-hlas-backups"

# Upload a backup
python3 backend/backup_cli.py upload full-2026-01-15T10-30-45
```

### MinIO Setup (Self-Hosted)

```bash
# Set credentials
export AWS_ACCESS_KEY_ID="minioadmin"
export AWS_SECRET_ACCESS_KEY="minioadmin"
export BACKUP_CLOUD_BUCKET="backups"
export BACKUP_CLOUD_ENDPOINT="https://minio.example.com:9000"

# Upload a backup
python3 backend/backup_cli.py upload full-2026-01-15T10-30-45
```

---

## Automated Backups

### Option 1: Interactive Setup (Recommended)

Use the setup assistant for guided configuration:

```bash
chmod +x backend/install_backup_scheduler.sh
./backend/install_backup_scheduler.sh
```

This will:
- Check your system requirements
- Test database connectivity  
- Guide you through cron or systemd timer setup
- Run a test backup
- Show monitoring commands

### Option 2: Cron-Based Scheduling

```bash
cd backend
export DATABASE_URL="postgresql://user:pass@host:5432/db"
chmod +x schedule_backups_cron.sh
./schedule_backups_cron.sh daily        # Daily at 2 AM
./schedule_backups_cron.sh list         # View schedule
```

Available schedules:
- `daily` - Daily at 2 AM
- `hourly` - Every hour
- `weekly` - Daily + extra weekly

### Option 3: Systemd Timers (Modern Linux)

```bash
# Copy service files
sudo cp backend/hlas-backup.service /etc/systemd/system/
sudo cp backend/hlas-backup.timer /etc/systemd/system/

# Edit to set DATABASE_URL
sudo nano /etc/systemd/system/hlas-backup.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable hlas-backup.timer
sudo systemctl start hlas-backup.timer

# Monitor
sudo systemctl list-timers hlas-backup.timer
sudo journalctl -u hlas-backup -f
```

For detailed scheduling options, see [BACKUP_SCHEDULING_GUIDE.md](BACKUP_SCHEDULING_GUIDE.md).

---

## API Usage

### List Snapshots

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5050/admin/backups/snapshots
```

### Create Backup via API

```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"Pre-release backup"}' \
  http://localhost:5050/admin/backups/snapshots/create/full
```

### Download Snapshot

```bash
curl -H "Authorization: Bearer $TOKEN" \
  -O http://localhost:5050/admin/backups/snapshots/full-2026-01-15T10-30-45/download
```

---

## Common Commands

```bash
# Create snapshots
python3 backend/backup_cli.py create-full              # Full backup
python3 backend/backup_cli.py create-db                # Database only
python3 backend/backup_cli.py create-fs                # Filesystem only

# View backups
python3 backend/backup_cli.py list                     # List all
python3 backend/backup_cli.py list --type=full         # Filter by type
python3 backend/backup_cli.py info <snapshot-id>       # Details

# Delete/cleanup
python3 backend/backup_cli.py delete <snapshot-id>     # Delete one
python3 backend/backup_cli.py cleanup --days=30        # Delete old

# Cloud storage
python3 backend/backup_cli.py upload <snapshot-id>     # Upload to S3
python3 backend/backup_cli.py schedule --interval=daily --type=full

# System info
python3 backend/backup_cli.py status                   # Overall status
```

---

## WordPress Quick Backup

Use this helper to capture WordPress content before deploy/rebuild (MySQL + `wp-content`):

```bash
./backup_wordpress.sh
```

Default output location:

```bash
./backups/wordpress/wp_backup_<timestamp>/
```

Contents:
- `wordpress_db.sql.gz` (WordPress MySQL dump)
- `wp-content.tar.gz` (themes/plugins/uploads and related content)
- `backup_meta.txt` and `SHA256SUMS`

Optional arguments:

```bash
./backup_wordpress.sh --output-root /data/backups/wordpress
./backup_wordpress.sh --compose-file docker-compose.prod.yml --env-file .env.prod
```

Restore from a backup directory:

```bash
./restore_wordpress.sh --backup-dir ./backups/wordpress/wp_backup_<timestamp>
```

Force restore (non-interactive):

```bash
./restore_wordpress.sh --backup-dir ./backups/wordpress/wp_backup_<timestamp> --force
```

---

## Backup Sizes & Time Estimates

Typical values (will vary based on data):

| Backup Type | Size | Time (Local) | Time (to S3) |
|-------------|------|--------------|------------|
| Database only | 100-500 MB | 1-5 min | 5-15 min |
| Filesystem only | 500-5 GB | 2-10 min | 15-60 min |
| Full backup | 1-10 GB | 5-20 min | 30-120 min |

**Compression typically reduces size by 50-70%**

---

## Restore Procedures

### Restore from Local Backup

```bash
# Database restore
cd /data/backups/snapshots/full-2026-01-15T10-30-45
gunzip -k database.sql.gz
psql -U hlas -d hlas -f database.sql

# Filesystem restore
tar -xzf filesystem.tar.gz -C /
```

### Restore from Cloud (S3)

```bash
# Download from S3
aws s3 cp s3://my-bucket/snapshots/full-2026-01-15T10-30-45/ . --recursive

# Then follow local restore procedure above
```

---

## Monitoring

### Check Backup Logs

```bash
tail -f /var/log/hlas-backup.log
```

### Monitor via API

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5050/admin/backups/status
```

### Alert Setup

Create `/usr/local/bin/hlas-backup-check.sh`:

```bash
#!/bin/bash
LAST_BACKUP=$(ls -t /data/backups/snapshots/ | head -1)
LAST_BACKUP_TIME=$(basename $LAST_BACKUP | cut -d'-' -f3-4 | tr '-' ':')
NOW=$(date +%s)
LAST_TIME=$(date -d "$LAST_BACKUP_TIME" +%s 2>/dev/null || echo 0)
DIFF=$((NOW - LAST_TIME))

# Alert if backup older than 48 hours
if [ $DIFF -gt 172800 ]; then
  echo "Warning: Last backup is older than 48 hours" | \
  mail -s "HLaS Backup Alert" admin@example.com
fi
```

---

## Troubleshooting

### Error: "pg_dump: command not found"

Install PostgreSQL client:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-client

# macOS
brew install postgresql

# Alpine
apk add postgresql-client
```

### Error: "boto3 not installed"

```bash
pip install boto3
```

### Error: "DATABASE_URL not set"

```bash
export DATABASE_URL="postgresql://hlas:password@localhost:5432/hlas"
```

### Out of Disk Space

```bash
# Delete old backups
python3 backend/backup_cli.py cleanup --days=7

# Check disk usage
du -sh /data/backups/
```

### Cloud Upload Fails

```bash
# Check credentials
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY

# Test connectivity
python3 << 'EOF'
import boto3
s3 = boto3.client('s3', region_name='us-east-1')
s3.head_bucket(Bucket='my-hlas-backups')
print("✓ S3 connection successful")
EOF
```

---

## Recommended Setup

### For Small Deployments

```bash
# Daily full backup, keep 7 days
0 2 * * * python3 /opt/HLaS/backend/backup_cli.py create-full
```

### For Medium Deployments

```bash
# Daily backups + weekly cloud upload
0 2 * * * python3 /opt/HLaS/backend/backup_cli.py create-full
0 3 * * 0 python3 /opt/HLaS/backend/backup_cli.py upload latest --bucket=my-bucket
```

### For Large/Production Deployments

```bash
# Hourly database backups + daily full backups
0 * * * * python3 /opt/HLaS/backend/backup_cli.py create-db
0 2 * * * python3 /opt/HLaS/backend/backup_cli.py create-full
0 3 * * 0 python3 /opt/HLaS/backend/backup_cli.py upload latest --bucket=my-bucket
```

---

## Documentation

For detailed information, see:

- **BACKUP_SYSTEM.md** - Full documentation
- **docker-compose.backup.yml** - Docker setup examples
- **.env.backup.example** - Configuration reference

---

## Support

If you encounter issues:

1. Check logs: `tail -f /var/log/hlas-backup.log`
2. Test system: `python3 backend/backup_cli.py status`
3. Verify credentials: `echo $AWS_ACCESS_KEY_ID`
4. Review documentation: See BACKUP_SYSTEM.md
