# HLaS Backup Systemd Timer Examples
#
# This file shows different timer configurations for various backup scenarios.
# Choose the one that matches your needs and adapt to your environment.

# ============================================================================
# SCENARIO 1: Daily Full Backup
# ============================================================================
# Best for: Most deployments, simple recovery, local storage
# Schedule: Daily at 2 AM
# Type: Full backup (database + filesystem)
# Retention: 7 most recent snapshots

# File: /etc/systemd/system/hlas-backup-daily.timer
[Timer]
OnCalendar=*-*-* 02:00:00
RandomizedDelaySec=5m
Persistent=true

# ============================================================================
# SCENARIO 2: Hourly Database Backup
# ============================================================================
# Best for: High-availability setups, frequent changes
# Schedule: Every hour (:00)
# Type: Database only (faster, smaller)
# Retention: Keep 14 recent hourly backups

[Timer]
OnCalendar=*-*-* *:00:00
RandomizedDelaySec=2m
Persistent=true

# ============================================================================
# SCENARIO 3: Multiple Backups (Recommended for Production)
# ============================================================================
# Best for: Production environments, hybrid approach
# Includes:
#   - Hourly database backups during business hours
#   - Daily full backup at 2 AM
#   - Weekly cloud upload on Sundays

# Option A: Database backup timer (hourly, 8 AM - 6 PM)
[Timer]
OnCalendar=*-*-* 08,09,10,11,12,13,14,15,16,17,18:00:00
RandomizedDelaySec=2m
Persistent=true

# Option B: Full backup timer (daily 2 AM)
[Timer]
OnCalendar=*-*-* 02:00:00
RandomizedDelaySec=5m
Persistent=true

# Option C: Cloud upload timer (weekly Sunday 4 AM)
[Timer]
OnCalendar=Sun *-*-* 04:00:00
RandomizedDelaySec=10m
Persistent=true

# ============================================================================
# SCENARIO 4: More Frequent Backups (High-Volume Deployments)
# ============================================================================
# Best for: Large databases, mission-critical
# Schedule: Every 6 hours
# Type: Full snapshot
# Retention: 28 snapshots (7 days)

[Timer]
OnCalendar=*-*-* 00,06,12,18:00:00
RandomizedDelaySec=3m
Persistent=true

# ============================================================================
# SCENARIO 5: Multiple File Backups (Development/Testing)
# ============================================================================
# Best for: Testing backup/restore procedures
# Schedule: Every 4 hours during business hours
# Type: Filesystem only
# Retention: Many recent backups (testing recovery)

[Timer]
OnCalendar=*-*-* 08,12,16,20:00:00
RandomizedDelaySec=1m
Persistent=true

# ============================================================================
# SCENARIO 6: Off-Peak Heavy Backup (Large Systems)
# ============================================================================
# Best for: Large deployments with limited offpeak windows
# Backup window: Nightly (11 PM), early morning (2 AM, 5 AM)
# Retention: Full monthly + weekly + multiple daily

[Timer]
OnCalendar=*-*-* 23:00:00  # 11 PM - Primary full backup
RandomizedDelaySec=5m
Persistent=true

[Timer]
OnCalendar=*-*-* 05:00:00  # 5 AM - Secondary full backup
RandomizedDelaySec=5m
Persistent=true

# ============================================================================
# MANAGEMENT NOTES
# ============================================================================
#
# Systemd Timer Format (OnCalendar):
#   Dow Year-Month-Day Hour:Minute:Second
#
# Examples:
#   *-*-* 02:00:00              Every day at 2 AM
#   *-*-* 02,08,14,20:00:00     Every 6 hours (2,8,14,20:00)
#   Mon *-*-* 02:00:00          Every Monday at 2 AM
#   *-*-01 02:00:00             1st of month at 2 AM
#   Sun *-*-* 04:00:00          Every Sunday at 4 AM
#
# Randomization:
#   RandomizedDelaySec=5m        Start within random 5m window
#   Helps avoid resource spikes with multiple timers
#
# Persistence:
#   Persistent=true              Run missed execution if system was off
#   Accuracy=1m                  Timer accuracy
#
# Deployment:
#   1. Copy service/timer to /etc/systemd/system/
#   2. Adjust DATABASE_URL and paths
#   3. systemctl daemon-reload
#   4. systemctl enable hlas-backup.timer
#   5. systemctl start hlas-backup.timer
#   6. systemctl list-timers
#   7. journalctl -u hlas-backup -f
#
# ============================================================================
