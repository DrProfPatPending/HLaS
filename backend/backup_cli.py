#!/usr/bin/env python3
"""
HLaS Backup Management CLI

Usage:
    python backup_cli.py create-db [--compress] [--description="..."]
    python backup_cli.py create-fs [--compress] [--description="..." --dirs="..."]
    python backup_cli.py create-full [--compress] [--description="..."]
    python backup_cli.py list [--type=database|filesystem|full]
    python backup_cli.py info <snapshot-id>
    python backup_cli.py delete <snapshot-id>
    python backup_cli.py cleanup [--days=30 --max=10]
    python backup_cli.py upload <snapshot-id> [--bucket=... --key=...]
    python backup_cli.py schedule --interval=daily|weekly --type=full
    python backup_cli.py status
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime
import json

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backup import BackupManager, CloudBackupUploader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('hlas.backup.cli')


def get_backup_manager():
    """Initialize backup manager from environment."""
    backup_dir = os.getenv('HLAS_BACKUP_DIR', '/data/backups')
    return BackupManager(backup_dir)


def cmd_create_db(args):
    """Create database snapshot."""
    logger.info("Creating database snapshot...")
    
    db_uri = os.getenv('DATABASE_URL')
    if not db_uri:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    try:
        manager = get_backup_manager()
        snapshot_id, path = manager.create_database_snapshot(
            db_connection_uri=db_uri,
            description=args.description,
            compress=args.compress
        )
        print(f"✓ Database snapshot created: {snapshot_id}")
        print(f"  Path: {path}")
        return True
    except Exception as e:
        logger.error(f"Failed: {e}")
        return False


def cmd_create_fs(args):
    """Create filesystem snapshot."""
    logger.info("Creating filesystem snapshot...")
    
    dirs = args.dirs.split(',') if args.dirs else ['/data', '/app/club_logos']
    
    try:
        manager = get_backup_manager()
        snapshot_id, path = manager.create_filesystem_snapshot(
            source_dirs=dirs,
            description=args.description,
            compress=args.compress
        )
        print(f"✓ Filesystem snapshot created: {snapshot_id}")
        print(f"  Path: {path}")
        return True
    except Exception as e:
        logger.error(f"Failed: {e}")
        return False


def cmd_create_full(args):
    """Create full snapshot."""
    logger.info("Creating full snapshot...")
    
    db_uri = os.getenv('DATABASE_URL')
    if not db_uri:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    dirs = args.dirs.split(',') if args.dirs else ['/data', '/app/club_logos']
    
    try:
        manager = get_backup_manager()
        snapshot_id = manager.create_full_snapshot(
            db_connection_uri=db_uri,
            source_dirs=dirs,
            description=args.description,
            compress=args.compress
        )
        print(f"✓ Full snapshot created: {snapshot_id}")
        return True
    except Exception as e:
        logger.error(f"Failed: {e}")
        return False


def cmd_list(args):
    """List snapshots."""
    try:
        manager = get_backup_manager()
        snapshots = manager.list_snapshots(
            snapshot_type=args.type,
            limit=args.limit
        )
        
        if not snapshots:
            print("No snapshots found")
            return True
        
        print(f"\n{'ID':<30} {'Type':<12} {'Size (MB)':<12} {'Created':<20} {'Description':<30}")
        print("-" * 110)
        
        for s in snapshots:
            size_mb = s['size_bytes'] / (1024 * 1024) if s['size_bytes'] else 0
            created = s['created_at'][:19] if s['created_at'] else 'N/A'
            desc = s['description'][:27] if s['description'] else ''
            
            print(f"{s['id']:<30} {s['snapshot_type']:<12} {size_mb:>10.1f}  {created:<20} {desc:<30}")
        
        print(f"\nTotal: {len(snapshots)} snapshots")
        return True
        
    except Exception as e:
        logger.error(f"Failed: {e}")
        return False


def cmd_info(args):
    """Show snapshot info."""
    try:
        manager = get_backup_manager()
        info = manager.get_snapshot_info(args.snapshot_id)
        
        if not info:
            print(f"Snapshot not found: {args.snapshot_id}")
            return False
        
        print(f"\nSnapshot: {info['id']}")
        print(f"Type: {info['snapshot_type']}")
        print(f"Created: {info['created_at']}")
        print(f"Size: {info['size_bytes'] / (1024*1024):.1f} MB")
        print(f"Files: {info['file_count']}")
        print(f"Status: {info['status']}")
        if info['description']:
            print(f"Description: {info['description']}")
        if info['cloud_uploaded']:
            print(f"Cloud bucket: {info['cloud_bucket']}")
            print(f"Cloud key: {info['cloud_key']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed: {e}")
        return False


def cmd_delete(args):
    """Delete snapshot."""
    if not args.force:
        confirm = input(f"Delete snapshot {args.snapshot_id}? (y/N): ")
        if confirm.lower() != 'y':
            print("Cancelled")
            return True
    
    try:
        manager = get_backup_manager()
        if manager.delete_snapshot(args.snapshot_id):
            print(f"✓ Snapshot deleted: {args.snapshot_id}")
            return True
        else:
            print(f"✗ Failed to delete snapshot")
            return False
    except Exception as e:
        logger.error(f"Failed: {e}")
        return False


def cmd_cleanup(args):
    """Cleanup old snapshots."""
    logger.info(f"Cleaning up snapshots older than {args.days} days...")
    
    try:
        manager = get_backup_manager()
        deleted = manager.cleanup_old_snapshots(
            days=args.days,
            max_snapshots=args.max
        )
        print(f"✓ {deleted} snapshots deleted")
        return True
    except Exception as e:
        logger.error(f"Failed: {e}")
        return False


def cmd_upload(args):
    """Upload snapshot to cloud storage."""
    bucket = args.bucket or os.getenv('BACKUP_CLOUD_BUCKET')
    if not bucket:
        logger.error("Bucket not specified and BACKUP_CLOUD_BUCKET not set")
        return False
    
    try:
        import boto3
    except ImportError:
        logger.error("boto3 not installed. Install with: pip install boto3")
        return False
    
    try:
        uploader = CloudBackupUploader(
            bucket=bucket,
            region=os.getenv('BACKUP_CLOUD_REGION', 'us-east-1'),
            access_key=os.getenv('AWS_ACCESS_KEY_ID'),
            secret_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            endpoint_url=os.getenv('BACKUP_CLOUD_ENDPOINT')
        )
        
        manager = get_backup_manager()
        snapshot_info = manager.get_snapshot_info(args.snapshot_id)
        
        if not snapshot_info:
            logger.error(f"Snapshot not found: {args.snapshot_id}")
            return False
        
        # Find snapshot files
        snapshot_dir = manager.snapshots_dir
        snapshot_files = list(snapshot_dir.glob(f"{args.snapshot_id}*"))
        
        if not snapshot_files:
            logger.error("Snapshot files not found")
            return False
        
        urls = []
        for filepath in snapshot_files:
            object_key = args.key or f"snapshots/{args.snapshot_id}/{filepath.name}"
            url = uploader.upload_snapshot(str(filepath), args.snapshot_id, object_key)
            urls.append(url)
            print(f"✓ Uploaded: {url}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed: {e}")
        return False


def cmd_schedule(args):
    """Setup automated backup scheduling (cron)."""
    import crontab
    
    interval = args.interval or 'daily'
    backup_type = args.type or 'full'
    
    # Determine cron schedule
    schedules = {
        'hourly': '0 * * * *',
        'daily': '0 2 * * *',      # 2 AM daily
        'weekly': '0 2 * * 0',     # 2 AM Sunday
        'monthly': '0 2 1 * *',    # 2 AM 1st of month
    }
    
    cron_schedule = schedules.get(interval)
    if not cron_schedule:
        logger.error(f"Unknown interval: {interval}")
        return False
    
    try:
        cron = crontab.CronTab(user=True)
        
        # Remove existing backup jobs
        for job in cron.find_command('backup_cli.py'):
            cron.remove(job)
        
        # Get script path
        script_path = os.path.abspath(__file__)
        
        # Add new job
        job = cron.new(
            command=f'python3 {script_path} create-{backup_type} >> /var/log/hlas-backup.log 2>&1',
            comment='HLaS Automated Backup'
        )
        job.setall(cron_schedule)
        
        cron.write()
        
        print(f"✓ Backup scheduled: {interval} {backup_type} backups")
        print(f"  Cron: {cron_schedule}")
        print(f"  Log: /var/log/hlas-backup.log")
        
        return True
        
    except ImportError:
        logger.error("python-crontab not installed. Install with: pip install python-crontab")
        print("\nAlternatively, add this to your crontab manually:")
        script_path = os.path.abspath(__file__)
        print(f"{cron_schedule} python3 {script_path} create-{backup_type}")
        return False
    except Exception as e:
        logger.error(f"Failed to setup cron: {e}")
        return False


def cmd_status(args):
    """Show backup system status."""
    try:
        manager = get_backup_manager()
        snapshots = manager.list_snapshots(limit=5)
        
        print("\n=== HLaS Backup System Status ===\n")
        print(f"Backup directory: {manager.backup_base_dir}")
        
        all_snapshots = manager.list_snapshots(limit=1000)
        total_size = sum(s.get('size_bytes', 0) for s in all_snapshots)
        
        print(f"Total snapshots: {len(all_snapshots)}")
        print(f"Total size: {total_size / (1024**3):.2f} GB")
        
        if snapshots:
            print(f"\nLatest snapshots:")
            for s in snapshots:
                size_mb = s['size_bytes'] / (1024 * 1024)
                created = s['created_at'][:19]
                print(f"  {s['id']} ({size_mb:.1f} MB) - {created}")
        
        cloud_bucket = os.getenv('BACKUP_CLOUD_BUCKET')
        if cloud_bucket:
            print(f"\nCloud storage: {cloud_bucket} (region: {os.getenv('BACKUP_CLOUD_REGION', 'us-east-1')})")
        else:
            print("\nCloud storage: Not configured")
        
        print()
        return True
        
    except Exception as e:
        logger.error(f"Failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='HLaS Backup Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create commands
    create_db = subparsers.add_parser('create-db', help='Create database snapshot')
    create_db.add_argument('--compress', action='store_true', default=True)
    create_db.add_argument('--description', help='Snapshot description')
    create_db.set_defaults(func=cmd_create_db)
    
    create_fs = subparsers.add_parser('create-fs', help='Create filesystem snapshot')
    create_fs.add_argument('--compress', action='store_true', default=True)
    create_fs.add_argument('--description', help='Snapshot description')
    create_fs.add_argument('--dirs', help='Comma-separated directories (default: /data, /app/club_logos)')
    create_fs.set_defaults(func=cmd_create_fs)
    
    create_full = subparsers.add_parser('create-full', help='Create full snapshot')
    create_full.add_argument('--compress', action='store_true', default=True)
    create_full.add_argument('--description', help='Snapshot description')
    create_full.add_argument('--dirs', help='Comma-separated directories (default: /data, /app/club_logos)')
    create_full.set_defaults(func=cmd_create_full)
    
    # List command
    list_cmd = subparsers.add_parser('list', help='List snapshots')
    list_cmd.add_argument('--type', choices=['database', 'filesystem', 'full'])
    list_cmd.add_argument('--limit', type=int, default=20)
    list_cmd.set_defaults(func=cmd_list)
    
    # Info command
    info_cmd = subparsers.add_parser('info', help='Show snapshot info')
    info_cmd.add_argument('snapshot_id', help='Snapshot ID')
    info_cmd.set_defaults(func=cmd_info)
    
    # Delete command
    delete_cmd = subparsers.add_parser('delete', help='Delete snapshot')
    delete_cmd.add_argument('snapshot_id', help='Snapshot ID')
    delete_cmd.add_argument('-f', '--force', action='store_true', help='Skip confirmation')
    delete_cmd.set_defaults(func=cmd_delete)
    
    # Cleanup command
    cleanup_cmd = subparsers.add_parser('cleanup', help='Cleanup old snapshots')
    cleanup_cmd.add_argument('--days', type=int, default=30)
    cleanup_cmd.add_argument('--max', type=int, help='Keep only this many recent snapshots')
    cleanup_cmd.set_defaults(func=cmd_cleanup)
    
    # Upload command
    upload_cmd = subparsers.add_parser('upload', help='Upload snapshot to cloud')
    upload_cmd.add_argument('snapshot_id', help='Snapshot ID')
    upload_cmd.add_argument('--bucket', help='S3 bucket (or set BACKUP_CLOUD_BUCKET)')
    upload_cmd.add_argument('--key', help='Custom S3 key')
    upload_cmd.set_defaults(func=cmd_upload)
    
    # Schedule command
    schedule_cmd = subparsers.add_parser('schedule', help='Setup automated backups')
    schedule_cmd.add_argument('--interval', choices=['hourly', 'daily', 'weekly', 'monthly'], default='daily')
    schedule_cmd.add_argument('--type', choices=['db', 'fs', 'full'], default='full')
    schedule_cmd.set_defaults(func=cmd_schedule)
    
    # Status command
    status_cmd = subparsers.add_parser('status', help='Show backup status')
    status_cmd.set_defaults(func=cmd_status)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    success = args.func(args)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
