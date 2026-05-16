#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/.env.prod}"
COMPOSE_FILE="${COMPOSE_FILE:-$SCRIPT_DIR/docker-compose.prod.yml}"
LOG_WINDOW="${LOG_WINDOW:-15m}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "✗ Missing env file: $ENV_FILE"
  exit 1
fi

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "✗ Missing compose file: $COMPOSE_FILE"
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "✗ docker is required"
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "✗ curl is required"
  exit 1
fi

compose() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

read_env_var() {
  local key="$1"
  awk -F= -v k="$key" '$1==k { sub(/^[[:space:]]+/,"",$2); print $2 }' "$ENV_FILE" | tail -n1
}

DOMAIN="$(read_env_var DOMAIN)"
POSTGRES_USER="$(read_env_var POSTGRES_USER)"
WORDPRESS_DOMAIN="$(read_env_var WORDPRESS_DOMAIN)"

DOMAIN="${DOMAIN:-cambridgetroutclub.org}"
POSTGRES_USER="${POSTGRES_USER:-hlas}"
WORDPRESS_DOMAIN="${WORDPRESS_DOMAIN:-wordpress.$DOMAIN}"

required_services=(postgres backend frontend wordpress-db wordpress wordpress-web caddy)
failures=()
warnings=()

check_status() {
  local title="$1"
  shift
  if "$@"; then
    echo "✓ $title"
  else
    echo "✗ $title"
    failures+=("$title")
  fi
}

check_http_code() {
  local title="$1"
  local expected_regex="$2"
  local url="$3"
  local host="$4"

  local code
  if [[ -n "$host" ]]; then
    code="$(curl --connect-timeout 5 --max-time 12 -sS -o /dev/null -w "%{http_code}" --resolve "$host:443:127.0.0.1" "$url" || true)"
  else
    code="$(curl --connect-timeout 5 --max-time 12 -sS -o /dev/null -w "%{http_code}" "$url" || true)"
  fi

  if [[ "$code" =~ $expected_regex ]]; then
    echo "✓ $title (HTTP $code)"
  else
    echo "✗ $title (HTTP $code)"
    failures+=("$title")
  fi
}

echo "=== HLaS Production Health Check ==="
echo "env file: $ENV_FILE"
echo "compose file: $COMPOSE_FILE"
echo "domain: $DOMAIN"
echo "wordpress domain: $WORDPRESS_DOMAIN"
echo "postgres user: $POSTGRES_USER"
echo

echo "--- docker compose ps ---"
if ! compose ps; then
  echo "✗ docker compose ps failed"
  exit 1
fi
echo

echo "--- service status ---"
running_services="$(compose ps --services --filter status=running)"
for service in "${required_services[@]}"; do
  check_status "service running: $service" grep -qx "$service" <<<"$running_services"
done
echo

echo "--- smoke checks ---"
check_http_code "main site via Caddy" '^2[0-9][0-9]$' "https://$DOMAIN/" "$DOMAIN"
check_http_code "api endpoint via Caddy" '^2[0-9][0-9]$' "https://$DOMAIN/api/clubs" "$DOMAIN"
check_http_code "wordpress site via Caddy" '^(2|3)[0-9][0-9]$' "https://$WORDPRESS_DOMAIN/" "$WORDPRESS_DOMAIN"
check_status "postgres readiness" compose exec -T postgres pg_isready -U "$POSTGRES_USER" >/dev/null
echo

echo "--- recent log scan ($LOG_WINDOW) ---"
log_lines="$(compose logs --since "$LOG_WINDOW" caddy backend frontend postgres wordpress wordpress-web wordpress-db 2>/dev/null | grep -Ei 'error|fatal|exception|traceback|panic' || true)"
filtered_log_lines="$(echo "$log_lines" | grep -Evi 'no OCSP stapling|Caddyfile input is not formatted|healthcheck|role "postgres" does not exist' || true)"

if [[ -n "$filtered_log_lines" ]]; then
  echo "⚠ Potentially significant errors found in recent logs:"
  echo "$filtered_log_lines" | tail -n 40
  warnings+=("recent logs contain potential errors")
else
  echo "✓ no significant errors detected in recent logs"
fi
echo

if [[ ${#warnings[@]} -gt 0 ]]; then
  echo "Warnings:"
  for warning in "${warnings[@]}"; do
    echo "- $warning"
  done
  echo
fi

if [[ ${#failures[@]} -gt 0 ]]; then
  echo "Health check FAILED"
  for failure in "${failures[@]}"; do
    echo "- $failure"
  done
  exit 1
fi

echo "Health check PASSED"
exit 0
