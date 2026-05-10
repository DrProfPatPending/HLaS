#!/bin/bash
#
# HLaS Backup Scheduler - Cron Edition
#
# This script sets up automated backup scheduling using cron.
# It provides multiple preset schedules for different backup scenarios.
#
# Usage:
#   ./schedule_backups_cron.sh daily        # Daily full backup at 2 AM
#   ./schedule_backups_cron.sh hourly       # Hourly database backup
#   ./schedule_backups_cron.sh weekly       # Weekly full backup + daily db
#   ./schedule_backups_cron.sh remove       # Remove all backup cron jobs
#   ./schedule_backups_cron.sh list         # List current backup crons
#
# Prerequisites:
#   - cron daemon running
#   - Python and HLaS backup tools installed
#   - DATABASE_URL environment variable set
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/backup_cli.py"
LOG_DIR="/var/log"
LOG_FILE="$LOG_DIR/hlas-backup.log"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create log directory and file
mkdir -p "$LOG_DIR"
touch "$LOG_FILE"
chmod 666 "$LOG_FILE"

print_error() {
    echo -e "${RED}✗ Error: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if backup script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    print_error "Backup script not found: $SCRIPT_PATH"
    exit 1
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    print_error "DATABASE_URL environment variable not set"
    echo "Set it with: export DATABASE_URL='postgresql://user:pass@host:5432/db'"
    exit 1
fi

# List current cron jobs
list_cron_jobs() {
    echo ""
    echo "Current backup cron jobs:"
    echo "========================="
    crontab -l 2>/dev/null | grep -E "backup_cli|hlas-backup" || echo "No backup cron jobs found"
    echo ""
}

# Remove all backup-related cron jobs
remove_all_crons() {
    print_info "Removing all backup cron jobs..."
    
    # Create temporary file with non-backup crons
    TEMP_CRON=$(mktemp)
    crontab -l 2>/dev/null | grep -v -E "backup_cli|hlas-backup" > "$TEMP_CRON" || true
    
    if crontab "$TEMP_CRON"; then
        print_success "Backup cron jobs removed"
    else
        print_error "Failed to remove cron jobs"
        rm -f "$TEMP_CRON"
        exit 1
    fi
    
    rm -f "$TEMP_CRON"
}

# Wrapper function to set up a cron job
add_cron_job() {
    local schedule=$1
    local command=$2
    local description=$3
    
    print_info "Adding: $description"
    
    # Get current crontab
    TEMP_CRON=$(mktemp)
    crontab -l 2>/dev/null > "$TEMP_CRON" || true
    
    # Add new job (only if it doesn't already exist)
    if ! grep -q "$command" "$TEMP_CRON"; then
        echo "# $description" >> "$TEMP_CRON"
        echo "$schedule $command >> $LOG_FILE 2>&1" >> "$TEMP_CRON"
    else
        print_info "  (already exists, skipping)"
        rm -f "$TEMP_CRON"
        return
    fi
    
    # Install new crontab
    if crontab "$TEMP_CRON"; then
        print_success "  Added: $schedule"
    else
        print_error "  Failed to add cron job"
        rm -f "$TEMP_CRON"
        exit 1
    fi
    
    rm -f "$TEMP_CRON"
}

# Preset: Daily full backup
setup_daily() {
    echo ""
    echo "Setting up DAILY backup schedule"
    echo "================================="
    echo "Frequency: Daily at 2 AM UTC"
    echo "Type: Full snapshot (database + filesystem)"
    echo "Cleanup: Keep 7 recent snapshots"
    echo "Log: $LOG_FILE"
    echo ""
    
    remove_all_crons
    
    # Main backup job
    add_cron_job \
        "0 2 * * *" \
        "python3 $SCRIPT_PATH create-full --description='Daily automated backup'" \
        "Daily full backup at 2 AM"
    
    # Cleanup job (runs at 3 AM after backup completes)
    add_cron_job \
        "0 3 * * *" \
        "python3 $SCRIPT_PATH cleanup --days=30 --max=7" \
        "Daily cleanup (keep 7 recent snapshots)"
    
    echo ""
    print_success "Daily backup schedule configured"
    list_cron_jobs
}

# Preset: Hourly database backup
setup_hourly() {
    echo ""
    echo "Setting up HOURLY backup schedule"
    echo "=================================="
    echo "Frequency: Every hour"
    echo "Type: Database only (PostgreSQL)"
    echo "Cleanup: Keep 14 most recent hourly backups + 7 daily"
    echo "Log: $LOG_FILE"
    echo ""
    
    remove_all_crons
    
    # Hourly DB backup
    add_cron_job \
        "0 * * * *" \
        "python3 $SCRIPT_PATH create-db --description='Hourly database backup'" \
        "Hourly database backup"
    
    # Cleanup job (runs at 4 AM daily)
    add_cron_job \
        "0 4 * * *" \
        "python3 $SCRIPT_PATH cleanup --days=7 --max=14" \
        "Daily cleanup (keep 14 recent hourly backups)"
    
    echo ""
    print_success "Hourly backup schedule configured"
    list_cron_jobs
}

# Preset: Weekly + Daily
setup_weekly() {
    echo ""
    echo "Setting up WEEKLY + DAILY backup schedule"
    echo "=========================================="
    echo "Frequency: Full daily + Extra full weekly"
    echo "Type: Full snapshots (database + filesystem)"
    echo "Weekly: Sunday at 1 AM (with cleanup)"
    echo "Daily: Other days at 2 AM"
    echo "Cleanup: Keep 4 weekly + 3 daily"
    echo "Log: $LOG_FILE"
    echo ""
    
    remove_all_crons
    
    # Weekly full backup (Sunday)
    add_cron_job \
        "0 1 * * 0" \
        "python3 $SCRIPT_PATH create-full --description='Weekly full backup'" \
        "Weekly full backup (Sunday 1 AM)"
    
    # Daily full backup (Mon-Sat)
    add_cron_job \
        "0 2 * * 1-6" \
        "python3 $SCRIPT_PATH create-full --description='Daily full backup'" \
        "Daily full backup (Mon-Sat 2 AM)"
    
    # Cleanup job (runs at 3 AM daily)
    add_cron_job \
        "0 3 * * *" \
        "python3 $SCRIPT_PATH cleanup --days=30 --max=7" \
        "Daily cleanup (keep 7 recent snapshots)"
    
    echo ""
    print_success "Weekly + Daily backup schedule configured"
    list_cron_jobs
}

# Main
case "${1:-}" in
    daily)
        setup_daily
        ;;
    hourly)
        setup_hourly
        ;;
    weekly)
        setup_weekly
        ;;
    remove)
        remove_all_crons
        list_cron_jobs
        ;;
    list)
        list_cron_jobs
        ;;
    *)
        echo "HLaS Backup Scheduler - Cron Edition"
        echo ""
        echo "Usage: $0 <schedule>"
        echo ""
        echo "Available schedules:"
        echo "  daily              Full backup daily at 2 AM, cleanup old backups"
        echo "  hourly             Database backup hourly, cleanup old backups"
        echo "  weekly             Full backup daily + extra full backup weekly"
        echo "  remove             Remove all backup cron jobs"
        echo "  list               List current backup cron jobs"
        echo ""
        echo "Examples:"
        echo "  $0 daily              # Setup daily backups"
        echo "  $0 list               # View scheduled backups"
        echo "  $0 remove             # Cancel all backups"
        echo ""
        echo "Environment variables:"
        echo "  DATABASE_URL          PostgreSQL connection URI (required)"
        echo "  LOG_FILE              Log location (default: /var/log/hlas-backup.log)"
        echo ""
        exit 1
        ;;
esac
