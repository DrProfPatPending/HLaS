"""
API endpoints for backup and snapshot management.

Requires: backup.create, backup.download, backup.restore
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from functools import wraps
from pathlib import Path

logger = logging.getLogger('hlas.api.backup')


def create_backup_routes(app, get_principal_context, require_permission):
    """Register backup API routes."""
    
    bp = Blueprint('backup', __name__, url_prefix='/admin/backups')
    
    # Import inside function to avoid circular imports
    from backup import BackupManager, CloudBackupUploader
    import os
    
    # Initialize backup manager
    backup_dir = os.getenv('HLAS_BACKUP_DIR', '/data/backups')
    backup_manager = BackupManager(backup_dir)
    
    def require_backup_permission(permission: str):
        """Decorator to check backup permissions."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                auth_error = require_permission(f'backup.{permission}')
                if auth_error:
                    return auth_error
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    # ============================================================================
    # Snapshot Management Endpoints
    # ============================================================================
    
    @bp.route('/snapshots', methods=['GET'])
    @require_backup_permission('read')
    def list_snapshots():
        """
        List available snapshots.
        
        Query Parameters:
        - type: Filter by snapshot type (database, filesystem, full)
        - limit: Maximum results (default: 50)
        """
        try:
            snapshot_type = request.args.get('type')
            limit = int(request.args.get('limit', 50))
            
            snapshots = backup_manager.list_snapshots(
                snapshot_type=snapshot_type,
                limit=limit
            )
            
            return jsonify({
                'success': True,
                'count': len(snapshots),
                'snapshots': snapshots
            }), 200
            
        except Exception as e:
            logger.error(f"Failed to list snapshots: {e}")
            return jsonify({'error': str(e)}), 500
    
    @bp.route('/snapshots/<snapshot_id>', methods=['GET'])
    @require_backup_permission('read')
    def get_snapshot_info(snapshot_id):
        """Get metadata for a specific snapshot."""
        try:
            info = backup_manager.get_snapshot_info(snapshot_id)
            
            if not info:
                return jsonify({'error': 'Snapshot not found'}), 404
            
            return jsonify({
                'success': True,
                'snapshot': info
            }), 200
            
        except Exception as e:
            logger.error(f"Failed to get snapshot info: {e}")
            return jsonify({'error': str(e)}), 500
    
    @bp.route('/snapshots/<snapshot_id>', methods=['DELETE'])
    @require_backup_permission('delete')
    def delete_snapshot(snapshot_id):
        """Delete a snapshot."""
        try:
            if backup_manager.delete_snapshot(snapshot_id):
                return jsonify({
                    'success': True,
                    'message': f'Snapshot {snapshot_id} deleted'
                }), 200
            else:
                return jsonify({'error': 'Failed to delete snapshot'}), 500
                
        except Exception as e:
            logger.error(f"Failed to delete snapshot: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # Create Snapshots
    # ============================================================================
    
    @bp.route('/snapshots/create/database', methods=['POST'])
    @require_backup_permission('create')
    def create_db_snapshot():
        """
        Create a database snapshot.
        
        Request Body:
        {
            "description": "Optional description",
            "compress": true
        }
        """
        try:
            data = request.get_json() or {}
            
            db_uri = os.getenv('DATABASE_URL')
            if not db_uri:
                return jsonify({'error': 'DATABASE_URL not configured'}), 500
            
            snapshot_id, snapshot_path = backup_manager.create_database_snapshot(
                db_connection_uri=db_uri,
                description=data.get('description'),
                compress=data.get('compress', True)
            )
            
            return jsonify({
                'success': True,
                'snapshot_id': snapshot_id,
                'path': snapshot_path,
                'message': 'Database snapshot created'
            }), 201
            
        except Exception as e:
            logger.error(f"Failed to create database snapshot: {e}")
            return jsonify({'error': str(e)}), 500
    
    @bp.route('/snapshots/create/filesystem', methods=['POST'])
    @require_backup_permission('create')
    def create_fs_snapshot():
        """
        Create a filesystem snapshot.
        
        Request Body:
        {
            "directories": ["/data", "/app/club_logos"],
            "description": "Optional description",
            "compress": true
        }
        """
        try:
            data = request.get_json() or {}
            directories = data.get('directories', ['/data', '/app/club_logos'])
            
            # Validate paths
            for d in directories:
                if not os.path.exists(d):
                    logger.warning(f"Directory does not exist: {d}")
            
            snapshot_id, snapshot_path = backup_manager.create_filesystem_snapshot(
                source_dirs=directories,
                description=data.get('description'),
                compress=data.get('compress', True)
            )
            
            return jsonify({
                'success': True,
                'snapshot_id': snapshot_id,
                'path': snapshot_path,
                'message': 'Filesystem snapshot created'
            }), 201
            
        except Exception as e:
            logger.error(f"Failed to create filesystem snapshot: {e}")
            return jsonify({'error': str(e)}), 500
    
    @bp.route('/snapshots/create/full', methods=['POST'])
    @require_backup_permission('create')
    def create_full_snapshot():
        """
        Create a complete snapshot (database + filesystem).
        
        Request Body:
        {
            "directories": ["/data", "/app/club_logos"],
            "description": "Optional description",
            "compress": true
        }
        """
        try:
            data = request.get_json() or {}
            directories = data.get('directories', ['/data', '/app/club_logos'])
            
            db_uri = os.getenv('DATABASE_URL')
            if not db_uri:
                return jsonify({'error': 'DATABASE_URL not configured'}), 500
            
            snapshot_id = backup_manager.create_full_snapshot(
                db_connection_uri=db_uri,
                source_dirs=directories,
                description=data.get('description'),
                compress=data.get('compress', True)
            )
            
            return jsonify({
                'success': True,
                'snapshot_id': snapshot_id,
                'message': 'Full snapshot created'
            }), 201
            
        except Exception as e:
            logger.error(f"Failed to create full snapshot: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # Cleanup
    # ============================================================================
    
    @bp.route('/cleanup', methods=['POST'])
    @require_backup_permission('create')
    def cleanup_old_snapshots():
        """
        Delete old snapshots based on retention policy.
        
        Request Body:
        {
            "days": 30,
            "max_snapshots": 10
        }
        """
        try:
            data = request.get_json() or {}
            days = int(data.get('days', 30))
            max_snapshots = data.get('max_snapshots')
            
            deleted_count = backup_manager.cleanup_old_snapshots(
                days=days,
                max_snapshots=max_snapshots
            )
            
            return jsonify({
                'success': True,
                'deleted_count': deleted_count,
                'message': f'{deleted_count} snapshots deleted'
            }), 200
            
        except Exception as e:
            logger.error(f"Failed to cleanup snapshots: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # Cloud Storage Integration
    # ============================================================================
    
    @bp.route('/cloud/config', methods=['POST'])
    @require_backup_permission('create')
    def configure_cloud_storage():
        """
        Configure cloud storage for backup uploads.
        
        Request Body:
        {
            "provider": "aws" | "minio" | "digitalocean",
            "bucket": "my-bucket",
            "region": "us-east-1",
            "access_key": "...",
            "secret_key": "...",
            "endpoint_url": "https://minio.example.com" (optional, for MinIO/custom)
        }
        """
        try:
            data = request.get_json() or {}
            
            required = ['bucket', 'access_key', 'secret_key']
            if not all(k in data for k in required):
                return jsonify({'error': 'Missing required fields'}), 400
            
            # For now, store config in environment (could be database)
            # In production, encrypt and store in secure vault
            os.environ['BACKUP_CLOUD_BUCKET'] = data['bucket']
            os.environ['BACKUP_CLOUD_REGION'] = data.get('region', 'us-east-1')
            os.environ['AWS_ACCESS_KEY_ID'] = data['access_key']
            os.environ['AWS_SECRET_ACCESS_KEY'] = data['secret_key']
            
            if 'endpoint_url' in data:
                os.environ['BACKUP_CLOUD_ENDPOINT'] = data['endpoint_url']
            
            return jsonify({
                'success': True,
                'message': 'Cloud storage configured'
            }), 200
            
        except Exception as e:
            logger.error(f"Failed to configure cloud storage: {e}")
            return jsonify({'error': str(e)}), 500
    
    @bp.route('/snapshots/<snapshot_id>/upload', methods=['POST'])
    @require_backup_permission('create')
    def upload_snapshot_to_cloud(snapshot_id):
        """
        Upload a snapshot to cloud storage.
        
        Request Body:
        {
            "object_key": "optional-custom-key"
        }
        """
        try:
            bucket = os.getenv('BACKUP_CLOUD_BUCKET')
            if not bucket:
                return jsonify({'error': 'Cloud storage not configured'}), 400
            
            # Try to import boto3
            try:
                import boto3
            except ImportError:
                return jsonify({'error': 'boto3 not installed. Install with: pip install boto3'}), 500
            
            data = request.get_json() or {}
            
            # Find snapshot files
            snapshot_info = backup_manager.get_snapshot_info(snapshot_id)
            if not snapshot_info:
                return jsonify({'error': 'Snapshot not found'}), 404
            
            uploader = CloudBackupUploader(
                bucket=bucket,
                region=os.getenv('BACKUP_CLOUD_REGION', 'us-east-1'),
                access_key=os.getenv('AWS_ACCESS_KEY_ID'),
                secret_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                endpoint_url=os.getenv('BACKUP_CLOUD_ENDPOINT')
            )
            
            # Find snapshot files
            snapshot_dir = backup_manager.snapshots_dir
            snapshot_files = list(snapshot_dir.glob(f"{snapshot_id}*"))
            
            if not snapshot_files:
                return jsonify({'error': 'Snapshot files not found'}), 404
            
            urls = []
            for filepath in snapshot_files:
                object_key = data.get('object_key', f"snapshots/{snapshot_id}/{filepath.name}")
                url = uploader.upload_snapshot(str(filepath), snapshot_id, object_key)
                urls.append(url)
            
            return jsonify({
                'success': True,
                'snapshot_id': snapshot_id,
                'urls': urls,
                'message': 'Snapshot uploaded to cloud storage'
            }), 200
            
        except Exception as e:
            logger.error(f"Failed to upload snapshot: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # Download
    # ============================================================================
    
    @bp.route('/snapshots/<snapshot_id>/download', methods=['GET'])
    @require_backup_permission('download')
    def download_snapshot(snapshot_id):
        """Download a snapshot file."""
        try:
            snapshot_dir = backup_manager.snapshots_dir
            
            # Find the snapshot file
            candidates = list(snapshot_dir.glob(f"{snapshot_id}*"))
            if not candidates:
                return jsonify({'error': 'Snapshot not found'}), 404
            
            # For full snapshots, create a temporary tar
            if candidates[0].is_dir():
                import tempfile
                temp_tar = Path(tempfile.gettempdir()) / f"{snapshot_id}.tar.gz"
                
                import tarfile
                with tarfile.open(str(temp_tar), 'w:gz') as tar:
                    for file in candidates[0].rglob('*'):
                        if file.is_file():
                            tar.add(file, arcname=file.relative_to(candidates[0].parent))
                
                return send_file(
                    str(temp_tar),
                    as_attachment=True,
                    download_name=f"{snapshot_id}.tar.gz"
                )
            else:
                return send_file(
                    str(candidates[0]),
                    as_attachment=True,
                    download_name=candidates[0].name
                )
            
        except Exception as e:
            logger.error(f"Failed to download snapshot: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # Status/Info
    # ============================================================================
    
    @bp.route('/status', methods=['GET'])
    @require_backup_permission('read')
    def backup_status():
        """Get backup system status."""
        try:
            snapshots = backup_manager.list_snapshots(limit=10)
            
            total_size = sum(s.get('size_bytes', 0) for s in snapshots)
            
            return jsonify({
                'success': True,
                'backup_dir': str(backup_manager.backup_base_dir),
                'total_snapshots': len(backup_manager.list_snapshots(limit=1000)),
                'recent_snapshots': len(snapshots),
                'total_size_bytes': total_size,
                'latest_snapshot': snapshots[0] if snapshots else None
            }), 200
            
        except Exception as e:
            logger.error(f"Failed to get backup status: {e}")
            return jsonify({'error': str(e)}), 500
    
    app.register_blueprint(bp)
    logger.info("Backup routes registered")
