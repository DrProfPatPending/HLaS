#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.prod}"
MODE="${1:-verify}"
EXPECTED_BRANCH="${EXPECTED_BRANCH:-main}"
EXPECTED_BACKEND_SUFFIX="${EXPECTED_BACKEND_SUFFIX:-:latest}"
EXPECTED_FRONTEND_SUFFIX="${EXPECTED_FRONTEND_SUFFIX:-:latest}"

STALE_ENV_VARS=(
  BACKEND_IMAGE
  FRONTEND_IMAGE
  DOMAIN
  DATABASE_URL
  POSTGRES_USER
  POSTGRES_PASSWORD
  POSTGRES_DB
  HLAS_USE_POSTGRES_READS
  LOG_LEVEL
)

REQUIRED_WORDPRESS_ENV_VARS=(
  WORDPRESS_DB_HOST
  WORDPRESS_DB_NAME
  WORDPRESS_DB_ROOT_PASSWORD
  WORDPRESS_DB_USER
  WORDPRESS_DB_PASSWORD
)

usage() {
  cat <<'EOF'
Usage:
  deploy/vps/verify-and-deploy.sh verify
  deploy/vps/verify-and-deploy.sh deploy

Modes:
  verify   Run production preflight checks only
  deploy   Run preflight checks, pull main, build backend/frontend, and restart the stack
EOF
}

log() {
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

run_compose() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

wait_for_service_state() {
  local service="$1"
  local expected="$2"
  local timeout_seconds="${3:-120}"
  local start_ts now_ts cid status

  start_ts="$(date +%s)"
  while true; do
    cid="$(run_compose ps -q "$service" 2>/dev/null || true)"
    if [[ -n "$cid" ]]; then
      status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$cid" 2>/dev/null || true)"
      if [[ "$status" == "$expected" ]]; then
        return 0
      fi
    fi

    now_ts="$(date +%s)"
    if (( now_ts - start_ts >= timeout_seconds )); then
      echo "Timed out waiting for service '$service' to reach state '$expected'" >&2
      run_compose ps || true
      run_compose logs --tail=80 "$service" || true
      return 1
    fi
    sleep 2
  done
}

require_file() {
  local file_path="$1"
  [[ -f "$file_path" ]] || fail "Required file not found: $file_path"
}

sanitize_shell_env() {
  for var_name in "${STALE_ENV_VARS[@]}"; do
    unset "$var_name" || true
  done
}

check_wordpress_env() {
  local var_name value

  for var_name in "${REQUIRED_WORDPRESS_ENV_VARS[@]}"; do
    value="$(grep -E "^${var_name}=" "$ENV_FILE" | tail -n1 | cut -d'=' -f2-)"
    [[ -n "${value:-}" ]] || fail "${var_name} missing or empty in ${ENV_FILE}"
  done

  log "WordPress database env vars verified"
}

check_git_branch() {
  local current_branch
  current_branch="$(git -C "$ROOT_DIR" branch --show-current)"
  [[ "$current_branch" == "$EXPECTED_BRANCH" ]] || fail "Expected branch '$EXPECTED_BRANCH' but found '$current_branch'"
  log "Git branch verified: $current_branch"
}

check_env_tags() {
  local backend_image frontend_image
  backend_image="$(grep '^BACKEND_IMAGE=' "$ENV_FILE" | head -n1 | cut -d'=' -f2-)"
  frontend_image="$(grep '^FRONTEND_IMAGE=' "$ENV_FILE" | head -n1 | cut -d'=' -f2-)"

  [[ -n "$backend_image" ]] || fail "BACKEND_IMAGE missing from $ENV_FILE"
  [[ -n "$frontend_image" ]] || fail "FRONTEND_IMAGE missing from $ENV_FILE"
  [[ "$backend_image" == *"$EXPECTED_BACKEND_SUFFIX" ]] || fail "BACKEND_IMAGE is '$backend_image' (expected suffix '$EXPECTED_BACKEND_SUFFIX')"
  [[ "$frontend_image" == *"$EXPECTED_FRONTEND_SUFFIX" ]] || fail "FRONTEND_IMAGE is '$frontend_image' (expected suffix '$EXPECTED_FRONTEND_SUFFIX')"

  log "Env image tags verified: $backend_image / $frontend_image"
}

check_compose_resolution() {
  local config_output
  config_output="$(run_compose config)"

  grep -q 'image: .*hlas-backend:latest' <<<"$config_output" || fail "Resolved backend image is not :latest"
  grep -q 'image: .*hlas-frontend:latest' <<<"$config_output" || fail "Resolved frontend image is not :latest"
  grep -q 'DATABASE_URL: postgresql+psycopg://' <<<"$config_output" || fail "Resolved DATABASE_URL is not using postgresql+psycopg://"
  grep -q 'name: hlas_postgres_data' <<<"$config_output" || fail "Resolved postgres volume is not hlas_postgres_data"
  grep -q 'external: true' <<<"$config_output" || fail "Resolved postgres volume is not marked external"

  log "Compose config resolution verified"
}

verify_backend_api() {
  if command -v curl >/dev/null 2>&1; then
    curl -fsS http://127.0.0.1:5050/clubs >/dev/null || fail "Backend /clubs endpoint did not respond successfully"
    log "Backend API check passed"
  else
    log "curl not available; skipping backend API check"
  fi
}

run_verify() {
  require_file "$COMPOSE_FILE"
  require_file "$ENV_FILE"
  sanitize_shell_env
  check_git_branch
  check_wordpress_env
  check_env_tags
  check_compose_resolution
  log "Verification complete"
}

run_deploy() {
  run_verify

  log "Pulling latest $EXPECTED_BRANCH"
  git -C "$ROOT_DIR" checkout "$EXPECTED_BRANCH"
  git -C "$ROOT_DIR" pull origin "$EXPECTED_BRANCH"

  log "Rebuilding backend and frontend images"
  run_compose build --no-cache backend frontend

  log "Starting postgres"
  run_compose up -d postgres
  wait_for_service_state postgres healthy 180

  log "Starting backend"
  run_compose up -d backend
  wait_for_service_state backend healthy 180

  log "Starting frontend and caddy"
  run_compose up -d frontend caddy
  wait_for_service_state frontend healthy 180

  log "Current compose status"
  run_compose ps

  verify_backend_api

  log "Deployment complete"
}

case "$MODE" in
  verify)
    run_verify
    ;;
  deploy)
    run_deploy
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage
    fail "Unknown mode: $MODE"
    ;;
esac
