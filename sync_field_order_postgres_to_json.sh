#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${1:-.env.prod}"
COMPOSE_FILE="${2:-docker-compose.prod.yml}"
OUTPUT_FILE="${3:-backend/field_order.json}"
CLUB_SHORT_NAME="${4:-}"

cd "$ROOT_DIR"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: Env file not found: $ENV_FILE" >&2
  exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "ERROR: Compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi

read_env_var() {
  local var_name="$1"
  local env_file="$2"
  grep -E "^${var_name}=" "$env_file" | tail -n1 | cut -d'=' -f2-
}

POSTGRES_USER="$(read_env_var POSTGRES_USER "$ENV_FILE")"
POSTGRES_DB="$(read_env_var POSTGRES_DB "$ENV_FILE")"

if [ -z "${POSTGRES_USER:-}" ] || [ -z "${POSTGRES_DB:-}" ]; then
  echo "ERROR: POSTGRES_USER and POSTGRES_DB must be present in $ENV_FILE" >&2
  exit 1
fi

if ! docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps --services --filter status=running | grep -q '^postgres$'; then
  echo "ERROR: postgres service is not running for compose file $COMPOSE_FILE with env $ENV_FILE" >&2
  exit 1
fi

TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tA -c \
  "SELECT COALESCE(cfo.config, a.value)::text
   FROM clubs c
   LEFT JOIN club_field_order cfo ON cfo.club_id = c.id
   LEFT JOIN app_settings a ON a.scope='global' AND a.key='field_order'
   WHERE ('${CLUB_SHORT_NAME}' = '' OR c.short_name='${CLUB_SHORT_NAME}')
   ORDER BY CASE WHEN '${CLUB_SHORT_NAME}' = '' THEN c.short_name ELSE '' END, c.id
   LIMIT 1;" \
  > "$TMP_FILE"

if [ ! -s "$TMP_FILE" ]; then
  if [ -n "$CLUB_SHORT_NAME" ]; then
    echo "ERROR: No field_order payload found for club '$CLUB_SHORT_NAME'" >&2
  else
    echo "ERROR: No field_order payload found (club_field_order/app_settings)" >&2
  fi
  exit 1
fi

python3 - <<'PY' "$TMP_FILE" "$OUTPUT_FILE"
import json
import sys
from pathlib import Path

src = Path(sys.argv[1])
out = Path(sys.argv[2])
raw = src.read_text(encoding='utf-8').strip()
if not raw:
    raise SystemExit("No field_order value returned from PostgreSQL")

payload = json.loads(raw)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2) + "\n", encoding='utf-8')
print(f"Synced PostgreSQL field_order to {out}")
PY

python3 -m json.tool "$OUTPUT_FILE" >/dev/null

echo "Validation OK: $OUTPUT_FILE"
