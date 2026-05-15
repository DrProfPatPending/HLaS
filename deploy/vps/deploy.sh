#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.prod}"

require_env_vars() {
  local env_file="$1"
  shift

  local var_name value
  for var_name in "$@"; do
    value="$(grep -E "^${var_name}=" "$env_file" | tail -n1 | cut -d'=' -f2-)"
    if [[ -z "${value:-}" ]]; then
      echo "Required environment variable '$var_name' is missing or empty in $env_file" >&2
      exit 1
    fi
  done
}

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Env file not found: $ENV_FILE" >&2
  exit 1
fi

require_env_vars "$ENV_FILE" \
  WORDPRESS_DB_HOST \
  WORDPRESS_DB_NAME \
  WORDPRESS_DB_ROOT_PASSWORD \
  WORDPRESS_DB_USER \
  WORDPRESS_DB_PASSWORD

echo "Pulling latest images..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" pull

echo "Starting stack..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --remove-orphans

echo "Pruning dangling images..."
docker image prune -f >/dev/null

echo "Current status:"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps
