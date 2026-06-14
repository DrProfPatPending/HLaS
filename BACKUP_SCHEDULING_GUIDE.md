# HLaS Backup Scheduling Guide

This guide explains how to set up automated backup scheduling on Linux servers using either **cron** (traditional) or **systemd timers** (modern approach).

### Language Convention

- User-facing copy and documentation in this repository should default to British English spelling (for example: recognised, localisation, authorised).
- Keep external API/library identifiers unchanged where spelling is fixed by the platform (for example: `wp_localize_script`).

## Quick Summary

| Method | Best For | Complexity | Reliability |
|--------|----------|-----------|------------|
| **Cron** | Simple setups, all Linux | Low | Good |
| **Systemd Timers** | Modern Linux, complex needs | Medium | Excellent |

**Recommendation:** Use **systemd timers** if available (CentOS 7+, Ubuntu 15.04+, Debian 8+).

---

## Option 1: Cron-Based Scheduling (Traditional)

### Quick Start

```bash
# Setup daily backups at 2 AM
cd /opt/hlas/backend
export DATABASE_URL="postgresql://hlas:password@localhost:5432/hlas"
chmod +x schedule_backups_cron.sh
./schedule_backups_cron.sh daily

# Verify
./schedule_backups_cron.sh list

# View logs
tail -f /var/log/hlas-backup.log
```

### Available Presets

```bash
# Daily full backup (recommended for most)
./schedule_backups_cron.sh daily
# Runs at: 2 AM daily
# What: Full backup + cleanup

# Hourly database backup (high-frequency)
./schedule_backups_cron.sh hourly
# Runs at: Every hour
# What: Database only + cleanup

# Weekly + daily (hybrid)
./schedule_backups_cron.sh weekly
# Runs at: Daily 2 AM + Extra backup Sunday 1 AM
# What: Balanced approach

# Remove all backup crons
./schedule_backups_cron.sh remove

# View current schedule
./schedule_backups_cron.sh list
```

### Manual Cron Setup

If you prefer to set up cron manually:

```bash
# Edit crontab
crontab -e

# Add these lines:

# Daily full backup at 2 AM
0 2 * * * python3 /opt/hlas/backend/backup_cli.py create-full --description="Daily backup" >> /var/log/hlas-backup.log 2>&1

# Cleanup old backups at 3 AM
0 3 * * * python3 /opt/hlas/backend/backup_cli.py cleanup --days=30 --max=7 >> /var/log/hlas-backup.log 2>&1

# Hourly database backup (optional, for high-frequency needs)
0 * * * * python3 /opt/hlas/backend/backup_cli.py create-db --description="Hourly db backup" >> /var/log/hlas-backup.log 2>&1

# Weekly cloud upload (optional, if configured)
0 4 * * 0 python3 /opt/hlas/backend/backup_cli.py upload $(ls -t /data/backups/snapshots/ | head -1) >> /var/log/hlas-backup.log 2>&1
```

### Cron Schedule Format

```
minute hour day month weekday command
0      2    *   *     *       python3 backup_cli.py create-full

# Common patterns:
0 2 * * *           Every day at 2 AM
0 2 * * 0           Every Sunday at 2 AM (weekday 0)
0 2 1 * *           1st of month at 2 AM
0 */6 * * *         Every 6 hours
0 0,12 * * *        At noon and midnight
*/30 * * * *        Every 30 minutes
```

### Verify Cron Setup

```bash
# View scheduled crons
crontab -l

# Monitor cron logs (if available)
sudo grep CRON /var/log/syslog          # Debian/Ubuntu
sudo grep CRON /var/log/messages        # CentOS/RHEL

# Manually test a backup
python3 /opt/hlas/backend/backup_cli.py create-full

# View backup logs
tail -f /var/log/hlas-backup.log
```

---

## Option 2: Systemd Timers (Recommended for Modern Linux)

### Requirements

- Linux with systemd (CentOS 7+, Ubuntu 15.04+, Debian 8+)
- System admin access (`sudo`)
- systemd version 217 or later

### Quick Start

```bash
# 1. Copy service and timer files
sudo cp /opt/hlas/backend/hlas-backup.service /etc/systemd/system/
sudo cp /opt/hlas/backend/hlas-backup.timer /etc/systemd/system/

# 2. Ensure /opt/hlas/.env.prod contains the production DATABASE_URL
#    The service sources that file at runtime, so you do not need to edit
#    the unit file for credentials.

# 3. Reload systemd
sudo systemctl daemon-reload

# 4. Enable and start timer
sudo systemctl enable hlas-backup.timer
sudo systemctl start hlas-backup.timer

# 5. Verify
sudo systemctl status hlas-backup.timer
sudo systemctl list-timers hlas-backup.timer
```

### Verify and Monitor

```bash
# Check timer is running
sudo systemctl status hlas-backup.timer

# List all timers
sudo systemctl list-timers hlas-backup.timer

# View last execution result
sudo systemctl status hlas-backup.service

# Follow live logs
sudo journalctl -u hlas-backup -f

# View logs from specific date
sudo journalctl -u hlas-backup --since "2026-01-15 00:00:00"

# Count successful backups
sudo journalctl -u hlas-backup | grep -c "✓"
```

### Customizing the Schedule

The default timer schedules daily backup at 2 AM. To change:

```bash
# Stop the timer
sudo systemctl stop hlas-backup.timer

# Edit the timer
sudo systemctl edit hlas-backup.timer

# Change OnCalendar line, e.g.:
# OnCalendar=*-*-* 02:00:00         # Every day at 2 AM
# OnCalendar=*-*-* 02,14:00:00      # At 2 AM and 2 PM daily
# OnCalendar=Sun *-*-* 02:00:00    # Weekly on Sunday at 2 AM

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart hlas-backup.timer

# Verify
sudo systemctl list-timers hlas-backup.timer
```

### Schedule Format (OnCalendar)

```
Dow Year-Month-Day Hour:Minute:Second
*   *-*-*          *:*:*              # Every second
*   *-*-*          *:*:00             # Every minute
*   *-*-*          *:00:00            # Every hour
*   *-*-*          02:00:00           # Daily at 2 AM
*   *-*-*          02,14:00:00        # Twice daily (2 AM, 2 PM)
*   *-*-*          08,12,16,20:00:00  # Every 6 hours
Mon *-*-*          02:00:00           # Every Monday at 2 AM
*   *-*-01         02:00:00           # 1st of month at 2 AM
Sun *-*-*          04:00:00           # Every Sunday at 4 AM
```

### Common Systemd Timer Scenarios

**Scenario 1: Daily at 2 AM** (default, recommended)
```ini
[Timer]
OnCalendar=*-*-* 02:00:00
```

**Scenario 2: Three times daily (2 AM, 2 PM, 8 PM)**
```ini
[Timer]
OnCalendar=*-*-* 02,14,20:00:00
```

**Scenario 3: Every 6 hours**
```ini
[Timer]
OnCalendar=*-*-* 00,06,12,18:00:00
```

**Scenario 4: Weekdays at 2 AM, Weekends at Midnight**
```ini
[Timer]
OnCalendar=Mon-Fri *-*-* 02:00:00
OnCalendar=Sat,Sun *-*-* 00:00:00
```

**Scenario 5: Weekly on Sunday at 3 AM**
```ini
[Timer]
OnCalendar=Sun *-*-* 03:00:00
```

**Scenario 6: Monthly on 1st at 2 AM**
```ini
[Timer]
OnCalendar=*-*-01 02:00:00
```

### Troubleshooting Systemd Timers

**Timer not running?**
```bash
# Check if enabled
sudo systemctl is-enabled hlas-backup.timer

# Enable it
sudo systemctl enable hlas-backup.timer
sudo systemctl start hlas-backup.timer
```

**Service failing?**
```bash
# Check logs for errors
sudo journalctl -u hlas-backup -n 50

# Test manually
sudo systemctl start hlas-backup.service

# Check service file syntax
sudo systemd-analyze verify /etc/systemd/system/hlas-backup.service
```

**Permission issues?**
```bash
# Ensure service runs as root (can access data directories)
# Check Service file:
grep "^User=" /etc/systemd/system/hlas-backup.service

# If needed, fix permissions
sudo chown root:root /etc/systemd/system/hlas-backup.*
sudo chmod 644 /etc/systemd/system/hlas-backup.*
sudo systemctl daemon-reload
```

**Database connection failing?**
```bash
# Verify the deployment DATABASE_URL source
grep DATABASE_URL /opt/hlas/.env.prod

# The host backup service connects via the published Docker port
grep -n '^ *- "5433:5432"' /opt/hlas/docker-compose.prod.yml

# Test connection manually
export DATABASE_URL="postgresql://..."
python3 /opt/hlas/backend/backup_cli.py status
```

---

## Choosing Between Cron and Systemd

### Use Cron If:
- ✓ Simple, straightforward backup (daily/weekly)
- ✓ Server is older (pre-2015 Linux)
- ✓ Don't need log aggregation
- ✓ Prefer simple text-based config

### Use Systemd Timers If:
- ✓ Modern Linux server (2015+)
- ✓ Need robust scheduling and error handling
- ✓ Want integrated logging (journalctl)
- ✓ Multiple backup scenarios
- ✓ Managing many services
- ✓ Need to run missed backups if system was offline

---

## Complete Example: Production Setup

### Setup both cron AND systemd for redundancy

```bash
# Step 1: Enable systemd timer (primary)
sudo cp /opt/hlas/backend/hlas-backup.service /etc/systemd/system/
sudo cp /opt/hlas/backend/hlas-backup.timer /etc/systemd/system/
# Ensure /opt/hlas/.env.prod contains the production credentials
# The service will translate those into a host-reachable URL using 127.0.0.1:5433
sudo systemctl enable hlas-backup.timer
sudo systemctl start hlas-backup.timer

# Step 2: Setup cron as fallback (only if you want a second scheduler)
export DATABASE_URL="postgresql://..."
cd /opt/hlas/backend
./schedule_backups_cron.sh daily

# Step 3: Monitor both
sudo systemctl list-timers hlas-backup.timer
crontab -l | grep backup_cli

# Step 4: View combined logs
sudo journalctl -u hlas-backup -f &
tail -f /var/log/hlas-backup.log &
```

---

## Email Notifications on Failure

### With Systemd

Create `/opt/hlas/backend/backup-failure-handler.sh`:

```bash
#!/bin/bash
EMAIL="admin@example.com"
SUBJECT="HLaS Backup Failed"

# If service failed
if [ "$SERVICE_RESULT" != "success" ]; then
    MESSAGE=$(journalctl -u hlas-backup -n 20)
    echo "$MESSAGE" | mail -s "$SUBJECT" "$EMAIL"
fi
```

Add to service file:
```ini
[Service]
OnFailure=backup-failure-email@%i.service
```

### With Cron

Add to crontab:

```bash
# Check backup from last 24 hours
0 6 * * * bash << 'EOF'
LAST_BACKUP=$(ls -t /data/backups/snapshots/ | head -1)
LAST_TIME=$(stat -c %Y /data/backups/snapshots/$LAST_BACKUP)
NOW=$(date +%s)
IF [ $((NOW - LAST_TIME)) -gt 86400 ]; then
    echo "Backup is more than 24 hours old" | \
    mail -s "HLaS Backup Alert" admin@example.com
fi
EOF
```

---

## References

- **Backup System**: See `BACKUP_SYSTEM.md`
- **CLI Reference**: `python3 backup_cli.py --help`
- **Systemd Documentation**: `man systemd.timer`, `man systemd.service`
- **Cron Documentation**: `man crontab`, `man 5 crontab`

---

## Getting Help

```bash
# Test backup manually
python3 /opt/hlas/backend/backup_cli.py status

# Check system status
python3 /opt/hlas/backend/backup_cli.py list

# View detailed logs
tail -100 /var/log/hlas-backup.log

# Report issues with:
journalctl -u hlas-backup > /tmp/backup-logs.txt
crontab -l > /tmp/crontab.txt
```
