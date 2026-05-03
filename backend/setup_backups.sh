#!/bin/bash
# HLaS Backup System - Docker Compose Configuration Template
# 
# This script helps set up automated backups for HLaS
# Usage: ./setup-backups.sh

set -e

BACKUP_DIR="${BACKUP_DIR:=/data/backups}"
LOG_DIR="${LOG_DIR:=/var/log}"

echo "=========================================="
echo "HLaS Backup System Setup"
echo "=========================================="
echo ""

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "✓ Running in Docker container"
else
    echo "ℹ Not in Docker container (running on host)"
fi

# Create directories
echo "Creating backup directories..."
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOG_DIR"

# Check Python dependencies
echo ""
echo "Checking Python dependencies..."
python3 -c "import sqlite3; print('✓ sqlite3 available')" 2>/dev/null || echo "✗ sqlite3 not available"

# Check for PostgreSQL client
if command -v pg_dump &> /dev/null; then
    echo "✓ pg_dump available"
    pg_dump --version
else
    echo "✗ pg_dump not available. Install PostgreSQL client tools:"
    echo "  Ubuntu/Debian: sudo apt-get install postgresql-client"
    echo "  macOS: brew install postgresql"
    echo "  Alpine: apk add postgresql-client"
fi

# Check for cloud storage (optional)
echo ""
echo "Checking optional cloud storage support..."
python3 -c "import boto3; print('✓ boto3 available')" 2>/dev/null || echo "ℹ boto3 not installed (cloud storage disabled)"

# Database connection
echo ""
echo "Testing database connection..."
if [ -z "$DATABASE_URL" ]; then
    echo "✗ DATABASE_URL not set"
    echo "  Set it with: export DATABASE_URL='postgresql://user:pass@host:5432/dbname'"
else
    echo "✓ DATABASE_URL is set"
fi

# Backup directory permissions
echo ""
echo "Setting backup directory permissions..."
chmod 755 "$BACKUP_DIR"
echo "✓ Backup directory: $BACKUP_DIR"

# Create log file
touch "$LOG_DIR/hlas-backup.log"
chmod 666 "$LOG_DIR/hlas-backup.log"
echo "✓ Log file: $LOG_DIR/hlas-backup.log"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Test a backup: python3 backend/backup_cli.py create-full"
echo "2. View backups: python3 backend/backup_cli.py list"
echo "3. Set up scheduling: python3 backend/backup_cli.py schedule --interval=daily --type=full"
echo "4. Configure cloud storage (optional):"
echo "   export BACKUP_CLOUD_BUCKET='my-bucket'"
echo "   export AWS_ACCESS_KEY_ID='...'"
echo "   export AWS_SECRET_ACCESS_KEY='...'"
echo ""
echo "Documentation: see BACKUP_SYSTEM.md"
echo ""
