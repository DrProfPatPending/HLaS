#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.prod}"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Env file not found: $ENV_FILE" >&2
  exit 1
fi

echo "Pulling latest images..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" pull

echo "Starting stack..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --remove-orphans

echo "Pruning dangling images..."
docker image prune -f >/dev/null

echo "Current status:"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps
