#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$SCRIPT_DIR/docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/.env.prod}"
OUTPUT_ROOT="${OUTPUT_ROOT:-$SCRIPT_DIR/backups/wordpress}"
PROJECT_NAME="${PROJECT_NAME:-}"

usage() {
    cat <<'EOF'
Usage:
  ./backup_wordpress.sh [options]

Creates a timestamped WordPress backup with:
  1) MySQL dump from wordpress-db
  2) wp-content archive from wordpress

Options:
  --compose-file <path>   Docker compose file (default: ./docker-compose.prod.yml)
  --env-file <path>       Env file used by compose (default: ./.env.prod)
  --output-root <path>    Backup root directory (default: ./backups/wordpress)
  --project-name <name>   Optional compose project name
  -h, --help              Show this help

Examples:
  ./backup_wordpress.sh
  ./backup_wordpress.sh --output-root /data/backups/wordpress
  ./backup_wordpress.sh --compose-file docker-compose.prod.yml --env-file .env.prod
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --compose-file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --output-root)
            OUTPUT_ROOT="$2"
            shift 2
            ;;
        --project-name)
            PROJECT_NAME="$2"
            shift 2
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

if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "ERROR: Compose file not found: $COMPOSE_FILE" >&2
    exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: Env file not found: $ENV_FILE" >&2
    exit 1
fi

compose_args=(--env-file "$ENV_FILE" -f "$COMPOSE_FILE")
if [[ -n "$PROJECT_NAME" ]]; then
    compose_args+=(--project-name "$PROJECT_NAME")
fi

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DEST_DIR="$OUTPUT_ROOT/wp_backup_$TIMESTAMP"
DB_SQL="$DEST_DIR/wordpress_db.sql"
DB_GZ="$DEST_DIR/wordpress_db.sql.gz"
CONTENT_TAR="$DEST_DIR/wp-content.tar.gz"
META_FILE="$DEST_DIR/backup_meta.txt"

mkdir -p "$DEST_DIR"

echo "Creating WordPress backup in: $DEST_DIR"

echo "Step 1/3: Exporting WordPress MySQL database..."
docker compose "${compose_args[@]}" exec -T wordpress-db sh -lc 'exec mysqldump -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' > "$DB_SQL"
gzip -f "$DB_SQL"

echo "Step 2/3: Archiving wp-content..."
docker compose "${compose_args[@]}" exec -T wordpress sh -lc 'tar -czf - -C /var/www/html wp-content' > "$CONTENT_TAR"

echo "Step 3/3: Writing metadata and checksums..."
{
    echo "timestamp=$TIMESTAMP"
    echo "compose_file=$COMPOSE_FILE"
    echo "env_file=$ENV_FILE"
    echo "backup_dir=$DEST_DIR"
} > "$META_FILE"

(
    cd "$DEST_DIR"
    sha256sum "$(basename "$DB_GZ")" "$(basename "$CONTENT_TAR")" > SHA256SUMS
)

echo "Backup complete"
echo "- Database dump: $DB_GZ"
echo "- Content archive: $CONTENT_TAR"
echo "- Metadata: $META_FILE"
echo "- Checksums: $DEST_DIR/SHA256SUMS"
