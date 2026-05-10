#!/bin/bash
#
# HLaS Backup Scheduler Setup Assistant
#
# Interactive tool to help configure automated backups on Linux servers.
# Supports both cron and systemd timers.
#
# Usage:
#   sudo ./install_backup_scheduler.sh
#   ./install_backup_scheduler.sh (will ask for sudo when needed)
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="/opt/HLaS"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ Error: $1${NC}" >&2
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

prompt_yes_no() {
    local prompt=$1
    local response
    while true; do
        read -p "$(echo -e ${YELLOW}$prompt${NC}) (y/n): " response
        case "$response" in
            [yY]) return 0 ;;
            [nN]) return 1 ;;
            *) echo "Please answer y or n" ;;
        esac
    done
}

prompt_choice() {
    local prompt=$1
    shift
    local options=("$@")
    local choice
    
    echo ""
    echo "$prompt"
    for i in "${!options[@]}"; do
        echo "  $((i+1))) ${options[$i]}"
    done
    
    while true; do
        read -p "Choose (1-${#options[@]}): " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#options[@]}" ]; then
            echo "${options[$((choice-1))]}"
            return
        fi
        echo "Invalid choice"
    done
}

check_requirements() {
    print_header "Checking Requirements"
    
    # Check if we're in the right directory
    if [ ! -f "$BACKEND_DIR/backup_cli.py" ]; then
        print_error "Backup script not found: $BACKEND_DIR/backup_cli.py"
        echo "Make sure to run this from the HLaS project root or adjust PROJECT_ROOT"
        exit 1
    fi
    print_success "Found backup_cli.py"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found"
        exit 1
    fi
    print_success "Python 3 found"
    
    # Check for pg_dump
    if ! command -v pg_dump &> /dev/null; then
        print_info "pg_dump not found - install with: sudo apt-get install postgresql-client"
    else
        print_success "PostgreSQL client found"
    fi
    
    # Check systemd availability
    if command -v systemctl &> /dev/null; then
        print_success "Systemd found"
        USE_SYSTEMD=true
    else
        print_info "Systemd not found - will use cron-only setup"
        USE_SYSTEMD=false
    fi
}

setup_environment() {
    print_header "Environment Configuration"
    
    # Check if DATABASE_URL is set
    if [ -z "$DATABASE_URL" ]; then
        print_info "DATABASE_URL not set in environment"
        
        # Try to read from .env files
        if [ -f "$PROJECT_ROOT/.env.prod" ]; then
            print_info "Found .env.prod, reading DATABASE_URL..."
            DB_URL=$(grep "DATABASE_URL=" "$PROJECT_ROOT/.env.prod" | cut -d'=' -f2 | tr -d '"')
            if [ -n "$DB_URL" ]; then
                export DATABASE_URL="$DB_URL"
                print_success "DATABASE_URL loaded from .env.prod"
            fi
        fi
        
        if [ -z "$DATABASE_URL" ]; then
            print_info "Enter your PostgreSQL connection string"
            echo "Format: postgresql://user:password@host:port/database"
            read -p "DATABASE_URL: " DATABASE_URL
            export DATABASE_URL="$DATABASE_URL"
        fi
    else
        print_success "DATABASE_URL is set"
    fi
    
    # Test connection
    echo ""
    print_info "Testing database connection..."
    if python3 "$BACKEND_DIR/backup_cli.py" status &>/dev/null; then
        print_success "Database connection successful"
    else
        print_error "Database connection failed. Check DATABASE_URL"
        exit 1
    fi
}

setup_cron() {
    print_header "Cron Scheduler Setup"
    
    local schedule=$(prompt_choice "Select backup schedule:" \
        "Daily at 2 AM (recommended)" \
        "Hourly database backups" \
        "Weekly + daily hybrid" \
        "Custom (manual)")
    
    case "$schedule" in
        "Daily at 2 AM (recommended)")
            cd "$BACKEND_DIR"
            chmod +x schedule_backups_cron.sh
            export DATABASE_URL
            ./schedule_backups_cron.sh daily
            print_success "Daily cron backup scheduled"
            ;;
        "Hourly database backups")
            cd "$BACKEND_DIR"
            chmod +x schedule_backups_cron.sh
            export DATABASE_URL
            ./schedule_backups_cron.sh hourly
            print_success "Hourly cron backup scheduled"
            ;;
        "Weekly + daily hybrid")
            cd "$BACKEND_DIR"
            chmod +x schedule_backups_cron.sh
            export DATABASE_URL
            ./schedule_backups_cron.sh weekly
            print_success "Weekly + daily cron backup scheduled"
            ;;
        "Custom (manual)")
            print_info "Edit your crontab with: crontab -e"
            echo "See $BACKEND_DIR/schedule_backups_cron.sh for examples"
            ;;
    esac
}

setup_systemd() {
    print_header "Systemd Timer Setup"
    
    if [ "$USE_SYSTEMD" = false ]; then
        print_info "Systemd not available on this system"
        return
    fi
    
    if ! prompt_yes_no "Setup systemd timers?"; then
        print_info "Skipping systemd setup"
        return
    fi
    
    # Check if we need sudo
    if [ "$EUID" -ne 0 ]; then
        print_info "Need sudo to install systemd files. You may be prompted for password."
        sudo echo "✓ Sudo available" > /dev/null
    fi
    
    # Copy files
    print_info "Installing systemd service files..."
    
    if [ -f "$BACKEND_DIR/hlas-backup.service" ]; then
        sudo cp "$BACKEND_DIR/hlas-backup.service" /etc/systemd/system/
        print_success "Installed hlas-backup.service"
    else
        print_error "Service file not found: $BACKEND_DIR/hlas-backup.service"
        return
    fi
    
    if [ -f "$BACKEND_DIR/hlas-backup.timer" ]; then
        sudo cp "$BACKEND_DIR/hlas-backup.timer" /etc/systemd/system/
        print_success "Installed hlas-backup.timer"
    else
        print_error "Timer file not found: $BACKEND_DIR/hlas-backup.timer"
        return
    fi
    
    # Edit service file to set DATABASE_URL
    print_info "Updating DATABASE_URL in service file..."
    sudo sh -c "sed -i 's|^Environment=\"DATABASE_URL=.*\"|Environment=\"DATABASE_URL=$DATABASE_URL\"|' /etc/systemd/system/hlas-backup.service"
    print_success "DATABASE_URL configured"
    
    # Reload and start
    print_info "Reloading systemd..."
    sudo systemctl daemon-reload
    print_success "Systemd reloaded"
    
    print_info "Enabling timer..."
    sudo systemctl enable hlas-backup.timer
    print_success "Timer enabled"
    
    print_info "Starting timer..."
    sudo systemctl start hlas-backup.timer
    print_success "Timer started"
    
    # Show status
    echo ""
    sudo systemctl status hlas-backup.timer
}

verify_setup() {
    print_header "Verifying Setup"
    
    echo "Checking cron jobs:"
    if crontab -l 2>/dev/null | grep -q "backup_cli"; then
        print_success "Cron jobs found:"
        crontab -l | grep "backup_cli" | sed 's/^/  /'
    else
        print_info "No cron jobs found"
    fi
    
    echo ""
    echo "Checking systemd timers:"
    if sudo systemctl list-timers hlas-backup.timer 2>/dev/null; then
        :
    else
        print_info "No systemd timers found"
    fi
    
    echo ""
    echo "Log file location: /var/log/hlas-backup.log"
    if [ -f /var/log/hlas-backup.log ]; then
        print_success "Log file exists"
        echo "Latest entries:"
        tail -3 /var/log/hlas-backup.log | sed 's/^/  /'
    fi
}

test_backup() {
    print_header "Testing Backup"
    
    if ! prompt_yes_no "Run a test backup now?"; then
        print_info "Skipping test backup"
        return
    fi
    
    print_info "Creating test backup..."
    if python3 "$BACKEND_DIR/backup_cli.py" create-full --description="Test backup from setup"; then
        print_success "Test backup completed"
        
        print_info "Backup status:"
        python3 "$BACKEND_DIR/backup_cli.py" status | sed 's/^/  /'
    else
        print_error "Test backup failed"
    fi
}

show_next_steps() {
    print_header "Next Steps"
    
    cat << 'EOF'
1. Monitor Your Backups:
   - View status: python3 backend/backup_cli.py status
   - List backups: python3 backend/backup_cli.py list
   - View logs: tail -f /var/log/hlas-backup.log

2. For Systemd:
   - Check timer: sudo systemctl status hlas-backup.timer
   - View logs: sudo journalctl -u hlas-backup -f
   - Run now: sudo systemctl start hlas-backup.service

3. For Cron:
   - View schedule: crontab -l | grep backup_cli
   - Edit schedule: crontab -e
   - Check logs: grep CRON /var/log/syslog

4. Configure Cloud Storage (Optional):
   - See BACKUP_SYSTEM.md for cloud setup
   - Upload backups: python3 backend/backup_cli.py upload <snapshot-id>

5. Documentation:
   - Backup System: BACKUP_SYSTEM.md
   - Scheduling Guide: BACKUP_SCHEDULING_GUIDE.md
   - Quick Start: BACKUP_QUICK_START.md

EOF
    
    echo "For more details, see the documentation:"
    echo "  - $PROJECT_ROOT/BACKUP_SYSTEM.md"
    echo "  - $PROJECT_ROOT/BACKUP_SCHEDULING_GUIDE.md"
}

# Main execution
main() {
    print_header "HLaS Backup Scheduler Setup Assistant"
    
    echo "This script will help you configure automated backups."
    echo "Supports cron scheduling and/or systemd timers."
    echo ""
    
    # Check requirements
    check_requirements
    
    # Setup environment
    setup_environment
    
    # Choose scheduling method
    echo ""
    print_header "Scheduling Method"
    
    METHOD=$(prompt_choice "How would you like to schedule backups?" \
        "Cron (traditional, works on all Linux)" \
        "Systemd timers (modern, recommended)" \
        "Both (maximum redundancy)")
    
    case "$METHOD" in
        "Cron (traditional, works on all Linux)")
            setup_cron
            ;;
        "Systemd timers (modern, recommended)")
            setup_systemd
            ;;
        "Both (maximum redundancy)")
            setup_cron
            echo ""
            setup_systemd
            ;;
    esac
    
    # Verify
    verify_setup
    
    # Test
    test_backup
    
    # Next steps
    show_next_steps
    
    print_success "Setup complete!"
}

# Run main
main
