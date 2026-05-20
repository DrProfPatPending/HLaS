#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$SCRIPT_DIR/docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/.env.prod}"
PROJECT_NAME="${PROJECT_NAME:-}"
BACKUP_DIR=""
FORCE=false

usage() {
    cat <<'EOF'
Usage:
  ./restore_wordpress.sh --backup-dir <path> [options]

Restores WordPress from a backup folder created by backup_wordpress.sh:
  1) imports wordpress_db.sql.gz (or wordpress_db.sql)
  2) restores wp-content.tar.gz

Options:
  --backup-dir <path>     Backup directory to restore from (required)
  --compose-file <path>   Docker compose file (default: ./docker-compose.prod.yml)
  --env-file <path>       Env file used by compose (default: ./.env.prod)
  --project-name <name>   Optional compose project name
  --force                 Skip confirmation prompt
  -h, --help              Show this help

Examples:
  ./restore_wordpress.sh --backup-dir ./backups/wordpress/wp_backup_20260519_120000
  ./restore_wordpress.sh --backup-dir /data/backups/wp_backup_20260519_120000 --force
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --compose-file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --project-name)
            PROJECT_NAME="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            exit 1
            ;;
    esac
done

if [[ -z "$BACKUP_DIR" ]]; then
    echo "ERROR: --backup-dir is required" >&2
    usage
    exit 1
fi

if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "ERROR: Compose file not found: $COMPOSE_FILE" >&2
    exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: Env file not found: $ENV_FILE" >&2
    exit 1
fi

if [[ ! -d "$BACKUP_DIR" ]]; then
    echo "ERROR: Backup directory not found: $BACKUP_DIR" >&2
    exit 1
fi

DB_GZ="$BACKUP_DIR/wordpress_db.sql.gz"
DB_SQL="$BACKUP_DIR/wordpress_db.sql"
CONTENT_TAR="$BACKUP_DIR/wp-content.tar.gz"
CHECKSUMS="$BACKUP_DIR/SHA256SUMS"

if [[ ! -f "$DB_GZ" && ! -f "$DB_SQL" ]]; then
    echo "ERROR: Missing database dump. Expected wordpress_db.sql.gz or wordpress_db.sql in $BACKUP_DIR" >&2
    exit 1
fi

if [[ ! -f "$CONTENT_TAR" ]]; then
    echo "ERROR: Missing content archive: $CONTENT_TAR" >&2
    exit 1
fi

compose_args=(--env-file "$ENV_FILE" -f "$COMPOSE_FILE")
if [[ -n "$PROJECT_NAME" ]]; then
    compose_args+=(--project-name "$PROJECT_NAME")
fi

if [[ -f "$CHECKSUMS" ]]; then
    echo "Verifying backup checksums..."
    (
        cd "$BACKUP_DIR"
        sha256sum -c SHA256SUMS
    )
fi

echo "Ensuring WordPress services are running..."
docker compose "${compose_args[@]}" up -d wordpress-db wordpress

echo
echo "WARNING: This will overwrite current WordPress database and wp-content."
echo "Backup source: $BACKUP_DIR"

if [[ "$FORCE" != true ]]; then
    read -r -p "Proceed with restore? (y/N): " CONFIRM
    if [[ "${CONFIRM:-}" != "y" && "${CONFIRM:-}" != "Y" ]]; then
        echo "Restore cancelled"
        exit 0
    fi
fi

echo "Step 1/2: Restoring WordPress MySQL database..."
if [[ -f "$DB_GZ" ]]; then
    gunzip -c "$DB_GZ" | docker compose "${compose_args[@]}" exec -T wordpress-db sh -lc 'exec mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"'
else
    cat "$DB_SQL" | docker compose "${compose_args[@]}" exec -T wordpress-db sh -lc 'exec mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"'
fi

echo "Step 2/2: Restoring wp-content..."
RESTORE_MARKER="pre_restore_$(date +%Y%m%d_%H%M%S)"
docker compose "${compose_args[@]}" exec -T wordpress sh -lc "if [ -d /var/www/html/wp-content ]; then mv /var/www/html/wp-content /var/www/html/wp-content.${RESTORE_MARKER}; fi"
cat "$CONTENT_TAR" | docker compose "${compose_args[@]}" exec -T wordpress sh -lc 'tar -xzf - -C /var/www/html'

echo "Restore complete"
echo "- Previous wp-content moved to: /var/www/html/wp-content.${RESTORE_MARKER} (inside wordpress container)"
