"""
Backup and snapshot management for HLaS system.

Supports:
- PostgreSQL database snapshots
- File system backups (logos, photos, documents, configs)
- Cloud storage integration (S3-compatible)
- Snapshot metadata tracking
"""

import os
import json
import sqlite3
import tarfile
import gzip
import subprocess
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger('hlas.backup')


class BackupManager:
    """Manages database and filesystem backups with cloud storage support."""

    def __init__(self, backup_base_dir: str = '/data/backups'):
        """
        Initialize backup manager.
        
        Args:
            backup_base_dir: Base directory for storing backups
        """
        self.backup_base_dir = Path(backup_base_dir)
        self.backup_base_dir.mkdir(parents=True, exist_ok=True)
        
        self.snapshots_dir = self.backup_base_dir / 'snapshots'
        self.snapshots_dir.mkdir(exist_ok=True)
        
        self.metadata_db = self.backup_base_dir / 'snapshots.db'
        self._init_metadata_db()

    def _init_metadata_db(self):
        """Initialize SQLite metadata database."""
        conn = sqlite3.connect(str(self.metadata_db))
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS snapshots (
                id TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                snapshot_type TEXT NOT NULL,
                size_bytes INTEGER,
                status TEXT DEFAULT 'success',
                description TEXT,
                db_version VARCHAR(20),
                file_count INTEGER,
                cloud_uploaded BOOLEAN DEFAULT 0,
                cloud_bucket TEXT,
                cloud_key TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS cloud_configs (
                id TEXT PRIMARY KEY,
                provider TEXT,
                bucket TEXT,
                region TEXT,
                access_key TEXT,
                secret_key TEXT,
                endpoint_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def create_database_snapshot(
        self,
        db_connection_uri: str,
        description: str = None,
        compress: bool = True
    ) -> Tuple[str, str]:
        """
        Create a PostgreSQL database snapshot using pg_dump.
        
        Args:
            db_connection_uri: PostgreSQL connection URI
            description: Optional snapshot description
            compress: Whether to compress the dump
            
        Returns:
            Tuple of (snapshot_id, snapshot_path)
        """
        timestamp = datetime.utcnow().isoformat().replace(':', '-')
        snapshot_id = f"db-{timestamp}"
        
        dump_file = self.snapshots_dir / f"{snapshot_id}.sql"
        
        try:
            # Extract connection details from URI
            # Format: postgresql://user:password@host:port/database
            cmd = ['pg_dump', '-Fc', '--no-owner', '--clean', db_connection_uri]
            
            logger.info(f"Creating database snapshot: {snapshot_id}")
            
            with open(dump_file, 'wb') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=False)
                if result.returncode != 0:
                    raise RuntimeError(f"pg_dump failed: {result.stderr.decode()}")
            
            # Compress if requested
            snapshot_path = dump_file
            if compress:
                compressed = dump_file.with_name(f"{dump_file.name}.gz")
                with open(dump_file, 'rb') as f_in:
                    with gzip.open(compressed, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                dump_file.unlink()
                snapshot_path = compressed
            
            size_bytes = snapshot_path.stat().st_size
            
            # Record metadata
            self._record_snapshot(
                snapshot_id=snapshot_id,
                snapshot_type='database',
                size_bytes=size_bytes,
                description=description,
                file_count=1
            )
            
            logger.info(f"Database snapshot created: {snapshot_id} ({size_bytes} bytes)")
            return snapshot_id, str(snapshot_path)
            
        except Exception as e:
            logger.error(f"Failed to create database snapshot: {e}")
            raise

    def create_filesystem_snapshot(
        self,
        source_dirs: List[str],
        description: str = None,
        compress: bool = True
    ) -> Tuple[str, str]:
        """
        Create a filesystem snapshot (tarball) from specified directories.
        
        Args:
            source_dirs: List of directories to include
            description: Optional snapshot description
            compress: Whether to compress the tarball
            
        Returns:
            Tuple of (snapshot_id, snapshot_path)
        """
        timestamp = datetime.utcnow().isoformat().replace(':', '-')
        snapshot_id = f"fs-{timestamp}"
        
        tar_path = self.snapshots_dir / f"{snapshot_id}.tar"
        if compress:
            tar_path = tar_path.with_name(f"{tar_path.name}.gz")
        
        try:
            logger.info(f"Creating filesystem snapshot: {snapshot_id}")
            
            file_count = 0
            mode = 'w:gz' if compress else 'w'
            
            with tarfile.open(str(tar_path), mode) as tar:
                for source_dir in source_dirs:
                    source_path = Path(source_dir)
                    if source_path.exists():
                        logger.info(f"Adding {source_dir} to snapshot")
                        for file in source_path.rglob('*'):
                            if file.is_file():
                                arcname = file.relative_to(source_path.parent)
                                tar.add(file, arcname=arcname)
                                file_count += 1
            
            size_bytes = tar_path.stat().st_size
            
            self._record_snapshot(
                snapshot_id=snapshot_id,
                snapshot_type='filesystem',
                size_bytes=size_bytes,
                description=description,
                file_count=file_count
            )
            
            logger.info(f"Filesystem snapshot created: {snapshot_id} ({size_bytes} bytes, {file_count} files)")
            return snapshot_id, str(tar_path)
            
        except Exception as e:
            logger.error(f"Failed to create filesystem snapshot: {e}")
            raise

    def create_full_snapshot(
        self,
        db_connection_uri: str,
        source_dirs: List[str],
        description: str = None,
        compress: bool = True
    ) -> str:
        """
        Create a complete snapshot (database + filesystem).
        
        Args:
            db_connection_uri: PostgreSQL connection URI
            source_dirs: List of directories to backup
            description: Optional snapshot description
            compress: Whether to compress
            
        Returns:
            Snapshot ID
        """
        timestamp = datetime.utcnow().isoformat().replace(':', '-')
        snapshot_id = f"full-{timestamp}"
        
        snapshot_dir = self.snapshots_dir / snapshot_id
        snapshot_dir.mkdir(exist_ok=True)
        
        try:
            logger.info(f"Creating full snapshot: {snapshot_id}")
            
            # Create database dump
            db_dump = snapshot_dir / 'database.sql.gz'
            cmd = ['pg_dump', '-Fc', '--no-owner', '--clean', db_connection_uri]
            with open(db_dump, 'wb') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=False)
                if result.returncode != 0:
                    raise RuntimeError(f"pg_dump failed: {result.stderr.decode()}")
            
            # Create filesystem tarball
            fs_tar = snapshot_dir / 'filesystem.tar.gz'
            file_count = 0
            with tarfile.open(str(fs_tar), 'w:gz') as tar:
                for source_dir in source_dirs:
                    source_path = Path(source_dir)
                    if source_path.exists():
                        for file in source_path.rglob('*'):
                            if file.is_file():
                                arcname = file.relative_to(source_path.parent)
                                tar.add(file, arcname=arcname)
                                file_count += 1
            
            # Create manifest
            manifest = {
                'snapshot_id': snapshot_id,
                'created_at': timestamp,
                'description': description,
                'database': {
                    'file': 'database.sql.gz',
                    'size_bytes': db_dump.stat().st_size
                },
                'filesystem': {
                    'file': 'filesystem.tar.gz',
                    'size_bytes': fs_tar.stat().st_size,
                    'file_count': file_count,
                    'dirs': source_dirs
                }
            }
            
            manifest_file = snapshot_dir / 'manifest.json'
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            total_size = db_dump.stat().st_size + fs_tar.stat().st_size
            
            self._record_snapshot(
                snapshot_id=snapshot_id,
                snapshot_type='full',
                size_bytes=total_size,
                description=description,
                file_count=file_count + 1
            )
            
            logger.info(f"Full snapshot created: {snapshot_id} ({total_size} bytes)")
            return snapshot_id
            
        except Exception as e:
            logger.error(f"Failed to create full snapshot: {e}")
            # Clean up partial snapshot
            shutil.rmtree(snapshot_dir, ignore_errors=True)
            raise

    def _record_snapshot(
        self,
        snapshot_id: str,
        snapshot_type: str,
        size_bytes: int,
        description: str = None,
        file_count: int = 0
    ):
        """Record snapshot metadata in database."""
        conn = sqlite3.connect(str(self.metadata_db))
        c = conn.cursor()
        c.execute('''
            INSERT INTO snapshots 
            (id, snapshot_type, size_bytes, description, file_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (snapshot_id, snapshot_type, size_bytes, description, file_count))
        conn.commit()
        conn.close()

    def list_snapshots(
        self,
        snapshot_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        List available snapshots.
        
        Args:
            snapshot_type: Filter by type (database, filesystem, full)
            limit: Maximum number of results
            
        Returns:
            List of snapshot metadata dicts
        """
        conn = sqlite3.connect(str(self.metadata_db))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = 'SELECT * FROM snapshots'
        params = []
        
        if snapshot_type:
            query += ' WHERE snapshot_type = ?'
            params.append(snapshot_type)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        c.execute(query, params)
        snapshots = [dict(row) for row in c.fetchall()]
        conn.close()
        
        return snapshots

    def get_snapshot_info(self, snapshot_id: str) -> Optional[Dict]:
        """Get metadata for a specific snapshot."""
        conn = sqlite3.connect(str(self.metadata_db))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM snapshots WHERE id = ?', (snapshot_id,))
        row = c.fetchone()
        conn.close()
        
        return dict(row) if row else None

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot and its files.
        
        Args:
            snapshot_id: Snapshot ID to delete
            
        Returns:
            True if successful
        """
        try:
            # Remove files
            for item in self.snapshots_dir.iterdir():
                if snapshot_id in item.name:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            
            # Remove metadata
            conn = sqlite3.connect(str(self.metadata_db))
            c = conn.cursor()
            c.execute('DELETE FROM snapshots WHERE id = ?', (snapshot_id,))
            conn.commit()
            conn.close()
            
            logger.info(f"Snapshot deleted: {snapshot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete snapshot: {e}")
            return False

    def cleanup_old_snapshots(self, days: int = 30, max_snapshots: int = None):
        """
        Delete snapshots older than specified days or keep only max_snapshots.
        
        Args:
            days: Delete snapshots older than this many days
            max_snapshots: Keep only this many most recent snapshots
        """
        snapshots = self.list_snapshots(limit=1000)
        now = datetime.utcnow()
        deleted_count = 0
        
        for snapshot in snapshots:
            created_at = datetime.fromisoformat(snapshot['created_at'].replace('Z', '+00:00'))
            age_days = (now - created_at).days
            
            if age_days > days:
                if self.delete_snapshot(snapshot['id']):
                    deleted_count += 1
        
        if max_snapshots:
            snapshots = self.list_snapshots(limit=1000)
            if len(snapshots) > max_snapshots:
                for snapshot in snapshots[max_snapshots:]:
                    if self.delete_snapshot(snapshot['id']):
                        deleted_count += 1
        
        logger.info(f"Cleanup completed: {deleted_count} snapshots deleted")
        return deleted_count


class CloudBackupUploader:
    """Handles uploading snapshots to cloud storage (S3-compatible)."""

    def __init__(
        self,
        bucket: str,
        region: str = 'us-east-1',
        access_key: str = None,
        secret_key: str = None,
        endpoint_url: str = None
    ):
        """
        Initialize cloud uploader.
        
        Args:
            bucket: S3 bucket name
            region: AWS region
            access_key: AWS access key (or set via AWS_ACCESS_KEY_ID env var)
            secret_key: AWS secret key (or set via AWS_SECRET_ACCESS_KEY env var)
            endpoint_url: Custom endpoint (for MinIO, DigitalOcean Spaces, etc.)
        """
        import boto3
        
        self.bucket = bucket
        
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        if endpoint_url:
            self.s3_client = session.client('s3', endpoint_url=endpoint_url)
        else:
            self.s3_client = session.client('s3')

    def upload_snapshot(
        self,
        snapshot_path: str,
        snapshot_id: str,
        object_key: str = None
    ) -> str:
        """
        Upload snapshot file(s) to S3.
        
        Args:
            snapshot_path: Local path to snapshot file or directory
            snapshot_id: Snapshot ID for reference
            object_key: Custom S3 object key (auto-generated if not provided)
            
        Returns:
            S3 object URL
        """
        import os
        
        snapshot_path = Path(snapshot_path)
        
        if object_key is None:
            object_key = f"snapshots/{snapshot_id}/"
        
        try:
            if snapshot_path.is_dir():
                # Upload directory contents
                for file in snapshot_path.rglob('*'):
                    if file.is_file():
                        relative = file.relative_to(snapshot_path.parent)
                        key = f"{object_key}{relative}"
                        self.s3_client.upload_file(
                            str(file),
                            self.bucket,
                            key
                        )
                        logger.info(f"Uploaded {key}")
            else:
                # Upload single file
                if not object_key.endswith('/'):
                    key = object_key
                else:
                    key = f"{object_key}{snapshot_path.name}"
                
                self.s3_client.upload_file(
                    str(snapshot_path),
                    self.bucket,
                    key
                )
                logger.info(f"Uploaded {key}")
            
            url = f"s3://{self.bucket}/{object_key}"
            logger.info(f"Snapshot uploaded to: {url}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to upload snapshot to S3: {e}")
            raise

    def download_snapshot(
        self,
        object_key: str,
        local_path: str
    ) -> str:
        """
        Download snapshot from S3.
        
        Args:
            object_key: S3 object key
            local_path: Local destination path
            
        Returns:
            Local file path
        """
        try:
            self.s3_client.download_file(
                self.bucket,
                object_key,
                local_path
            )
            logger.info(f"Downloaded {object_key} to {local_path}")
            return local_path
        except Exception as e:
            logger.error(f"Failed to download from S3: {e}")
            raise

    def list_snapshots_in_bucket(
        self,
        prefix: str = 'snapshots/'
    ) -> List[Dict]:
        """List all snapshots in bucket."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            
            snapshots = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    snapshots.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat()
                    })
            
            return snapshots
        except Exception as e:
            logger.error(f"Failed to list snapshots: {e}")
            return []
