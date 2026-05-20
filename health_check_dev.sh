#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILES=(-f docker-compose.prod.yml -f docker-compose.dev.yml)
REQUIRED_SERVICES=(backend frontend caddy postgres wordpress-db wordpress wordpress-web)
LOG_SERVICES=(backend frontend caddy postgres wordpress-web)

red() { printf '\033[0;31m%s\033[0m\n' "$1"; }
green() { printf '\033[0;32m%s\033[0m\n' "$1"; }
yellow() { printf '\033[1;33m%s\033[0m\n' "$1"; }

dc() {
  docker compose --env-file .env.dev "${COMPOSE_FILES[@]}" "$@"
}

check_http_code() {
  local description="$1"
  local url="$2"
  local expected_codes="$3"
  local curl_args=()

  if [[ "$url" == https://hlastest* ]]; then
    curl_args+=(--insecure --resolve hlastest:443:127.0.0.1)
  fi

  local code
  if (( ${#curl_args[@]} )); then
    code="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' "${curl_args[@]}" "$url" || true)"
  else
    code="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' "$url" || true)"
  fi

  if [[ " $expected_codes " == *" $code "* ]]; then
    green "✓ ${description}: ${code}"
    return 0
  fi

  red "✗ ${description}: ${code} (expected: ${expected_codes})"
  return 1
}

failures=0

echo "== Dev stack health check (prod + dev overlay) =="
echo

echo "[1/3] Compose status"
if ! dc ps; then
  red "✗ Unable to read compose status"
  exit 1
fi

echo
running_services="$(dc ps --services --filter status=running || true)"
for service in "${REQUIRED_SERVICES[@]}"; do
  if grep -qx "$service" <<<"$running_services"; then
    green "✓ Service running: $service"
  else
    red "✗ Service not running: $service"
    failures=$((failures + 1))
  fi
done

echo
echo "[2/3] Recent logs (last 10m)"
if ! dc logs --since=10m --tail=120 "${LOG_SERVICES[@]}"; then
  yellow "! Could not fetch one or more service logs"
fi

echo
echo "[3/3] Smoke checks"
if ! check_http_code "Gateway HTTP" "http://localhost" "200 301 302 307 308"; then
  failures=$((failures + 1))
fi
if ! check_http_code "Gateway HTTPS" "https://hlastest" "200"; then
  failures=$((failures + 1))
fi
if ! check_http_code "Backend direct /clubs" "http://localhost:5050/clubs" "200"; then
  failures=$((failures + 1))
fi
if ! check_http_code "Backend via Caddy /clubs" "https://hlastest/clubs" "200"; then
  failures=$((failures + 1))
fi

echo
if [[ "$failures" -gt 0 ]]; then
  red "Health check completed with ${failures} issue(s)."
  exit 1
fi

green "Health check passed with no issues."
