#!/bin/bash
# Run backend Python scripts in the Docker container
# This ensures compatibility across different host environments (macOS, Linux, etc.)
#
# Usage:
#   ./run_backend_script.sh <script_name> [args...]
#   ./run_backend_script.sh sync_beats_postgres_to_json.py
#   ./run_backend_script.sh import_club_logos_to_postgres.py -q
#   ./run_backend_script.sh backup_cli.py --help

set -e

# Default container name (override with HLAS_BACKEND_CONTAINER env var)
CONTAINER_NAME="${HLAS_BACKEND_CONTAINER:-hlas-backend-1}"

# Check if script name provided
if [ -z "$1" ]; then
    echo "Usage: $0 <script_name> [args...]"
    echo ""
    echo "Examples:"
    echo "  $0 sync_beats_postgres_to_json.py"
    echo "  $0 import_club_logos_to_postgres.py -v"
    echo "  $0 backup_cli.py --help"
    echo ""
    echo "Available scripts:"
    docker exec "$CONTAINER_NAME" ls -1 /app/*.py 2>/dev/null | grep -E "^[^/]+\.py$" | sed 's/^/  /'
    exit 1
fi

SCRIPT_NAME="$1"
shift  # Consume the script name argument

# Check if container is running
if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}\$"; then
    echo "❌ Error: Container '$CONTAINER_NAME' is not running"
    echo ""
    echo "Available containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep hlas
    exit 1
fi

# Check if script exists in container
if ! docker exec "$CONTAINER_NAME" [ -f "/app/$SCRIPT_NAME" ]; then
    echo "❌ Error: Script '$SCRIPT_NAME' not found in container"
    echo ""
    echo "Available scripts:"
    docker exec "$CONTAINER_NAME" ls -1 /app/*.py 2>/dev/null | sed 's/^/  /'
    exit 1
fi

# Run the script in the container with any additional arguments
echo "🐳 Running: python3 /app/$SCRIPT_NAME $@"
echo ""
docker exec "$CONTAINER_NAME" python3 "/app/$SCRIPT_NAME" "$@"
