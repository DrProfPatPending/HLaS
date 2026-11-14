#!/bin/bash
set -euo pipefail

TARGET="${TARGET:-development}"
DIRECTORY="${DIRECTORY:-/opt/hlas}"
VERBOSE=0
USE_REMOTE=1
NO_CACHE=1
RUN_CLEAN=0
SKIP_HEALTH=0
APP_ONLY=0
ALLOW_HTTP_401=0
LOG_FILE=""
ENV_FILE_OVERRIDE=""
CADDYFILE_OVERRIDE=""
HEALTH_HOST_OVERRIDE=""
CLUBS_CONFIG_FILE_OVERRIDE=""
INITIAL_PWD="$(pwd)"

if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    echo "✗ ERROR: Neither 'python' nor 'python3' was found in PATH" >&2
    exit 1
fi

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
  -t, --target <target>     Deployment target/branch (default: development)
                            Examples: production, ctc-production, ctc-dev, development, main
  -d, --directory <dir>     Deployment directory (default: /opt/hlas)
                            Example: /opt/hlas
    -l, --local               Build from local working tree (skip git reset)
    -r, --remote              Build from origin/<target> (default)
  -f, --full                Full rebuild: pass --no-cache to docker build (default)
  -Q, --quick               Quick rebuild: use Docker layer cache (faster for dev)
  -c, --clean               Run 'docker system prune -f' after successful build
    -C                        Alias for --noclean (disable Docker prune step)
      --noclean, --no-clean Disable Docker prune step (default)
  -n, --nohealth            Skip post-start health checks
      --app-only            Rebuild/restart only backend and frontend (no dependencies)
      --allow-http-401      Accept HTTP 401 from the public site health check
      --env-file <file>     Compose environment file (overrides target default)
      --caddyfile <file>    Caddyfile to mount (overrides target default)
      --health-host <host>  Hostname used for the HTTPS health check
      --clubs-config <file> Club configuration file mounted into the backend
      --log-file <file>      Write full build output to a file
  -q, --quiet               Suppress command output (default)
    -V                        Alias for --quiet (no verbose output)
  -v, --verbose             Show command output
      --noverbose,
      --no-verbose          Suppress command output (same as --quiet)
  -h, --help                Show this help message

Examples:
  $0
  $0 --target development --directory /opt/hlas
    $0 --target development --directory /opt/hlas --local
  $0 -t production -v
    $0 -t production -v -V
    $0 --target production --verbose --noverbose
  $0 --target development --quick --local  # fast dev rebuild using cache
  $0 --target production --clean           # deploy and prune dangling images
    $0 -t production --clean -C              # -C disables clean (last flag wins)
    $0 --target production --clean --noclean # last flag wins (no prune)
    $0 --target production --quiet --log-file /tmp/hlas-build.log
    $0 --target ctc-production --allow-http-401
    $0 --target ctc-dev --directory . --local --quick --app-only
EOF
}

while (($#)); do
    case "$1" in
        -t|--target)
            if [ $# -lt 2 ]; then
                echo "✗ ERROR: Missing value for $1" >&2
                exit 1
            fi
            TARGET="$2"
            shift 2
            ;;
        -d|--directory)
            if [ $# -lt 2 ]; then
                echo "✗ ERROR: Missing value for $1" >&2
                exit 1
            fi
            DIRECTORY="$2"
            shift 2
            ;;
        -f|--full)
            NO_CACHE=1
            shift
            ;;
        -Q|--quick)
            NO_CACHE=0
            shift
            ;;
        -c|--clean)
            RUN_CLEAN=1
            shift
            ;;
        -C|--noclean|--no-clean)
            RUN_CLEAN=0
            shift
            ;;
        -n|--nohealth)
            SKIP_HEALTH=1
            shift
            ;;
        --app-only)
            APP_ONLY=1
            shift
            ;;
        --allow-http-401)
            ALLOW_HTTP_401=1
            shift
            ;;
        --env-file)
            if [ $# -lt 2 ]; then
                echo "✗ ERROR: Missing value for $1" >&2
                exit 1
            fi
            ENV_FILE_OVERRIDE="$2"
            shift 2
            ;;
        --caddyfile)
            if [ $# -lt 2 ]; then
                echo "✗ ERROR: Missing value for $1" >&2
                exit 1
            fi
            CADDYFILE_OVERRIDE="$2"
            shift 2
            ;;
        --health-host)
            if [ $# -lt 2 ]; then
                echo "✗ ERROR: Missing value for $1" >&2
                exit 1
            fi
            HEALTH_HOST_OVERRIDE="$2"
            shift 2
            ;;
        --clubs-config)
            if [ $# -lt 2 ]; then
                echo "✗ ERROR: Missing value for $1" >&2
                exit 1
            fi
            CLUBS_CONFIG_FILE_OVERRIDE="$2"
            shift 2
            ;;
        --log-file)
            if [ $# -lt 2 ]; then
                echo "✗ ERROR: Missing value for $1" >&2
                exit 1
            fi
            LOG_FILE="$2"
            shift 2
            ;;
        -l|--local)
            USE_REMOTE=0
            shift
            ;;
        -r|--remote)
            USE_REMOTE=1
            shift
            ;;
        -q|-V|--quiet)
            VERBOSE=0
            shift
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        --noverbose|--no-verbose)
            VERBOSE=0
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "✗ ERROR: Unknown option '$1'" >&2
            usage
            exit 1
            ;;
    esac
done

if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    echo "✗ ERROR: Neither 'python' nor 'python3' was found in PATH" >&2
    exit 1
fi

if [ -n "$LOG_FILE" ] && [ "${LOG_FILE#/}" = "$LOG_FILE" ]; then
    LOG_FILE="$INITIAL_PWD/$LOG_FILE"
fi

if [ -n "$LOG_FILE" ]; then
    LOG_DIR="$(dirname "$LOG_FILE")"
    if ! mkdir -p "$LOG_DIR"; then
        echo "✗ ERROR: Could not create log directory '$LOG_DIR'" >&2
        exit 1
    fi
    : >"$LOG_FILE"
fi

log() {
    printf '%s\n' "$1"
    if [ -n "$LOG_FILE" ]; then
        printf '%s\n' "$1" >>"$LOG_FILE"
    fi
}

log_err() {
    printf '%s\n' "$1" >&2
    if [ -n "$LOG_FILE" ]; then
        printf '%s\n' "$1" >>"$LOG_FILE"
    fi
}
run_step() {
    local description="$1"
    shift

    log "$description"
    if [ -n "$LOG_FILE" ] && [ "$VERBOSE" -eq 1 ]; then
        "$@" \
            > >(tee -a "$LOG_FILE") \
            2> >(tee -a "$LOG_FILE" >&2)
    elif [ -n "$LOG_FILE" ]; then
        "$@" >>"$LOG_FILE" 2>&1
    elif [ "$VERBOSE" -eq 1 ]; then
        "$@"
    else
        "$@" >/dev/null 2>&1
    fi
}

require_env_vars() {
    local env_file="$1"
    shift

    local var_name value
    for var_name in "$@"; do
        value="$(grep -E "^${var_name}=" "$env_file" | tail -n1 | cut -d'=' -f2-)"
        if [ -z "${value:-}" ]; then
            log_err "✗ ERROR: Required environment variable '${var_name}' is missing or empty in ${env_file}"
            exit 1
        fi
    done
}

if [ ! -d "$DIRECTORY" ]; then
    log_err "✗ ERROR: Directory '$DIRECTORY' not found"
    exit 1
fi

cd "$DIRECTORY"
log "Rebuilding latest HLaS from Github sources (directory: $DIRECTORY, target: $TARGET)"

unset BACKEND_IMAGE FRONTEND_IMAGE DOMAIN DATABASE_URL POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB HLAS_USE_POSTGRES_READS LOG_LEVEL

DEFAULT_CLUBS_CONFIG_FILE="backend/clubs.config.json"

case "$TARGET" in
    production|prod)
        BRANCH_NAME="production"
        ENV_FILE=".env.prod"
        COMPOSE_FILES=("-f" "docker-compose.prod.yml")
        CADDYFILE="deploy/caddy/Caddyfile.prod"
        HEALTH_HOST="anglerconnect.cloud"
        ;;
    ctc-production)
        BRANCH_NAME="ctc-production"
        ENV_FILE=".env.ctc"
        COMPOSE_FILES=("-f" "docker-compose.prod.yml")
        CADDYFILE="deploy/caddy/Caddyfile.ctc"
        HEALTH_HOST="cambridgetroutclub.org"
        DEFAULT_CLUBS_CONFIG_FILE="clubs.config.ctc.json"
        ;;
    ctc-dev)
        BRANCH_NAME="ctc-dev"
        ENV_FILE="/dev/null"
        COMPOSE_FILES=("--project-name" "ctc-dev" "-f" "docker-compose.ctc-dev.yml")
        CADDYFILE="deploy/caddy/Caddyfile.ctc-dev"
        HEALTH_HOST="hlastest"
        DEFAULT_CLUBS_CONFIG_FILE="deploy/clubs.config.ctc-dev.json"
        if [ -n "$ENV_FILE_OVERRIDE$CADDYFILE_OVERRIDE$CLUBS_CONFIG_FILE_OVERRIDE" ]; then
            log_err "✗ ERROR: ctc-dev uses fixed isolated configuration; --env-file, --caddyfile and --clubs-config are not supported"
            exit 1
        fi
        ;;
    development|dev)
        BRANCH_NAME="development"
        ENV_FILE=".env.dev"
        COMPOSE_FILES=("-f" "docker-compose.prod.yml" "-f" "docker-compose.dev.yml")
        CADDYFILE="deploy/caddy/Caddyfile.dev"
        HEALTH_HOST="hlastest"
        ;;
    main)
        BRANCH_NAME="main"
        ENV_FILE=".env.dev"
        COMPOSE_FILES=("-f" "docker-compose.prod.yml" "-f" "docker-compose.dev.yml")
        CADDYFILE="deploy/caddy/Caddyfile.dev"
        HEALTH_HOST="hlastest"
        ;;
    *)
        BRANCH_NAME="$TARGET"
        ENV_FILE=".env.dev"
        COMPOSE_FILES=("-f" "docker-compose.prod.yml" "-f" "docker-compose.dev.yml")
        CADDYFILE="deploy/caddy/Caddyfile.dev"
        HEALTH_HOST="hlastest"
        ;;
esac

if [ -n "$ENV_FILE_OVERRIDE" ]; then
    ENV_FILE="$ENV_FILE_OVERRIDE"
fi
if [ -n "$CADDYFILE_OVERRIDE" ]; then
    CADDYFILE="$CADDYFILE_OVERRIDE"
fi
if [ -n "$HEALTH_HOST_OVERRIDE" ]; then
    HEALTH_HOST="$HEALTH_HOST_OVERRIDE"
fi
CLUBS_CONFIG_FILE="${CLUBS_CONFIG_FILE_OVERRIDE:-$DEFAULT_CLUBS_CONFIG_FILE}"

if [ "${CADDYFILE#/}" = "$CADDYFILE" ]; then
    CADDYFILE="$PWD/$CADDYFILE"
fi
if [ "${CLUBS_CONFIG_FILE#/}" = "$CLUBS_CONFIG_FILE" ]; then
    CLUBS_CONFIG_FILE="$PWD/$CLUBS_CONFIG_FILE"
fi

compose() {
    HLAS_ENV_FILE="$ENV_FILE" \
    HLAS_CADDYFILE="$CADDYFILE" \
    HLAS_CLUBS_CONFIG_FILE="$CLUBS_CONFIG_FILE" \
        docker compose --env-file "$ENV_FILE" "${COMPOSE_FILES[@]}" "$@"
}

if [ "$TARGET" != "ctc-dev" ]; then
    if [ ! -f "$ENV_FILE" ]; then
        log_err "✗ ERROR: Environment file '$ENV_FILE' not found"
        exit 1
    fi

    require_env_vars "$ENV_FILE" \
        WORDPRESS_DB_HOST \
        WORDPRESS_DB_NAME \
        WORDPRESS_DB_ROOT_PASSWORD \
        WORDPRESS_DB_USER \
        WORDPRESS_DB_PASSWORD
fi

if [ "$USE_REMOTE" -eq 1 ]; then
    log "Pulling latest code from Git (branch: $BRANCH_NAME)"
    run_step "  Checking out branch '$BRANCH_NAME'..." git checkout "$BRANCH_NAME"
    run_step "  Fetching from origin..." git fetch origin
    run_step "  Resetting to origin/$BRANCH_NAME..." git reset --hard "origin/$BRANCH_NAME"
else
    log "Using local working tree (no git checkout/fetch/reset)"
fi

if [ ! -f "$CADDYFILE" ]; then
    log_err "✗ ERROR: Caddyfile ($CADDYFILE) not found!"
    log_err "This file should be version-controlled in git. Aborting build."
    exit 1
fi
log "✓ Caddyfile configuration found: $CADDYFILE"

if [ ! -f "$CLUBS_CONFIG_FILE" ]; then
    log_err "✗ ERROR: Club configuration file ($CLUBS_CONFIG_FILE) not found!"
    exit 1
fi
log "✓ Club configuration found: $CLUBS_CONFIG_FILE"

if [ "$TARGET" = "ctc-dev" ] && [ ! -s "deploy/.ctc-dev-postgres-password" ]; then
    log_err "✗ ERROR: ctc-dev requires the existing non-empty deploy/.ctc-dev-postgres-password secret"
    exit 1
fi

if [ "$APP_ONLY" -eq 1 ]; then
    log "Checking app-only deployment prerequisites"
    postgres_id="$(compose ps --status running -q postgres)"
    if [ -z "$postgres_id" ] || [ "$(docker inspect --format '{{.State.Health.Status}}' "$postgres_id")" != "healthy" ]; then
        log_err "✗ ERROR: App-only deployment requires an already running, healthy PostgreSQL service"
        exit 1
    fi
    if [[ "$TARGET" = "ctc-production" || "$TARGET" = "ctc-dev" ]]; then
        if ! compose config --format json | "$PYTHON_BIN" -c '
import json, sys
config = json.load(sys.stdin)
flag = config["services"]["backend"]["environment"].get("HLAS_SYNC_FILES_ON_STARTUP", "")
sys.exit(0 if str(flag).strip().lower() == "false" else 1)
'; then
            log_err "✗ ERROR: CTC app-only deployment requires HLAS_SYNC_FILES_ON_STARTUP=false"
            exit 1
        fi
    fi
fi

log "Validating club source manifest"
if make -n clubs-check >/dev/null 2>&1; then
    run_step "  Running make clubs-check..." make clubs-check
elif [ -f "backend/build_clubs_config.py" ]; then
    run_step "  Running $PYTHON_BIN backend/build_clubs_config.py --check..." "$PYTHON_BIN" backend/build_clubs_config.py --check
else
    log "⚠ clubs-check skipped: split config tooling is not present on branch '$BRANCH_NAME'"
fi

log "Build frontend and backend images"
if [ "$NO_CACHE" -eq 1 ]; then
    log "  (--no-cache: full rebuild, ignoring Docker layer cache)"
    run_step "  Building backend and frontend images..." compose build --no-cache backend frontend
else
    log "  (--quick: using Docker layer cache for faster rebuild)"
    run_step "  Building backend and frontend images..." compose build backend frontend
fi

if [ "$APP_ONLY" -eq 1 ]; then
    log "Start backend and frontend without recreating dependencies"
    run_step "  Starting backend..." compose up -d --no-deps --wait --wait-timeout 120 backend
    run_step "  Starting frontend..." compose up -d --no-deps --wait --wait-timeout 120 frontend
else
    if [ "$TARGET" = "ctc-dev" ]; then
        log "Start isolated development PostgreSQL"
        run_step "  Starting postgres..." compose up -d postgres
    else
        log "Start databases (Postgres + WordPress MySQL)"
        run_step "  Starting postgres and wordpress-db..." compose up -d postgres wordpress-db
    fi

    log "Start backend and frontend"
    run_step "  Starting backend and frontend..." compose up -d backend frontend

    if [ "$TARGET" != "ctc-dev" ]; then
        log "Start WordPress services"
        run_step "  Starting wordpress and wordpress-web..." compose up -d wordpress wordpress-web
    fi

    log "Start caddy"
    run_step "  Starting caddy..." compose up -d caddy
fi

run_step "  Checking running processes..." compose ps

log "Running post-start health checks"

retry_check() {
    local description="$1"
    local attempts="$2"
    local delay_seconds="$3"
    shift 3

    local i
    for ((i=1; i<=attempts; i++)); do
        if "$@" >/dev/null 2>&1; then
            log "✓ ${description}"
            return 0
        fi
        if [ "$i" -lt "$attempts" ]; then
            sleep "$delay_seconds"
        fi
    done

    log_err "✗ ERROR: ${description} failed after ${attempts} attempts"
    return 1
}

frontend_health_check() {
    local status
    status="$(curl --connect-timeout 5 --max-time 10 -ksS -o /dev/null -w '%{http_code}' \
        --resolve "${HEALTH_HOST}:443:127.0.0.1" "https://${HEALTH_HOST}/")" || return 1

    if [[ "$status" =~ ^[23][0-9][0-9]$ ]]; then
        return 0
    fi
    [[ "$ALLOW_HTTP_401" -eq 1 && "$status" = "401" ]]
}

if [ "$SKIP_HEALTH" -eq 1 ]; then
    log "⚠ Health checks skipped (--nohealth)"
else
    if [ "$TARGET" = "ctc-dev" ]; then
        required_services=(postgres backend frontend caddy)
    else
        required_services=(postgres backend frontend wordpress-db wordpress wordpress-web caddy)
    fi

    for service in "${required_services[@]}"; do
        if ! compose ps --services --filter "status=running" | grep -q "^${service}$"; then
            log_err "✗ ERROR: Service '${service}' is not running"
            run_step "  Current service status..." compose ps
            exit 1
        fi
    done

    log "✓ All required services are running"

    log "Checking backend health endpoint"
    if [ "$TARGET" = "ctc-dev" ]; then
        retry_check "Backend health endpoint OK" 30 3 compose exec -T backend python -c \
            "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5050/clubs', timeout=5)" || exit 1
    else
        retry_check "Backend health endpoint OK" 30 3 curl --connect-timeout 5 --max-time 10 -fsS http://127.0.0.1:5050/clubs || exit 1
    fi

    log "Checking frontend health endpoint via caddy"
    retry_check "Frontend/caddy endpoint OK" 30 3 frontend_health_check || exit 1

    if [ "$TARGET" != "ctc-dev" ]; then
        log "Checking WordPress/Nginx health endpoint"
        retry_check "WordPress/Nginx endpoint OK" 30 3 compose exec -T wordpress-web wget -q -O - http://127.0.0.1/healthz || exit 1
    fi
fi

log "✓ Build complete"

if [ "$RUN_CLEAN" -eq 1 ]; then
    log "Pruning unused Docker objects (docker system prune -f)..."
    run_step "  Removing dangling images and unused resources..." docker system prune -f
    log "✓ Docker system clean complete"
fi
