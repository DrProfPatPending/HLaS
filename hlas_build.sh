#!/bin/bash
set -euo pipefail

TARGET="${TARGET:-production}"
DIRECTORY="${DIRECTORY:-/opt/hlas}"
VERBOSE=0
USE_REMOTE=1
NO_CACHE=1
RUN_CLEAN=0
SKIP_HEALTH=0

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
  -t, --target <target>     Deployment target/branch (default: production)
                            Examples: production, development, main
  -d, --directory <dir>     Deployment directory (default: /opt/hlas)
                            Example: /opt/HLaS
    -l, --local               Build from local working tree (skip git reset)
    -r, --remote              Build from origin/<target> (default)
  -f, --full                Full rebuild: pass --no-cache to docker build (default)
  -Q, --quick               Quick rebuild: use Docker layer cache (faster for dev)
  -c, --clean               Run 'docker system prune -f' after successful build
  -n, --nohealth            Skip post-start health checks
  -q, --quiet               Suppress command output (default)
  -v, --verbose             Show command output
  -h, --help                Show this help message

Examples:
  $0
  $0 --target development --directory /opt/HLaS
    $0 --target development --directory /opt/HLaS --local
  $0 -t production -v
  $0 --target development --quick --local  # fast dev rebuild using cache
  $0 --target production --clean           # deploy and prune dangling images
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
        -n|--nohealth)
            SKIP_HEALTH=1
            shift
            ;;
        -l|--local)
            USE_REMOTE=0
            shift
            ;;
        -r|--remote)
            USE_REMOTE=1
            shift
            ;;
        -q|--quiet)
            VERBOSE=0
            shift
            ;;
        -v|--verbose)
            VERBOSE=1
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

run_step() {
    local description="$1"
    shift

    echo "$description"
    if [ "$VERBOSE" -eq 1 ]; then
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
            echo "✗ ERROR: Required environment variable '${var_name}' is missing or empty in ${env_file}" >&2
            exit 1
        fi
    done
}

if [ ! -d "$DIRECTORY" ]; then
    echo "✗ ERROR: Directory '$DIRECTORY' not found" >&2
    exit 1
fi

cd "$DIRECTORY"
echo "Rebuilding latest HLaS from Github sources (directory: $DIRECTORY, target: $TARGET)"

unset BACKEND_IMAGE FRONTEND_IMAGE DOMAIN DATABASE_URL POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB HLAS_USE_POSTGRES_READS LOG_LEVEL

case "$TARGET" in
    production|prod)
        BRANCH_NAME="production"
        ENV_FILE=".env.prod"
        COMPOSE_FILES=("-f" "docker-compose.prod.yml")
        CADDYFILE="deploy/caddy/Caddyfile.prod"
        HEALTH_HOST="cambridgetroutclub.org"
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

compose() {
    docker compose --env-file "$ENV_FILE" "${COMPOSE_FILES[@]}" "$@"
}

if [ ! -f "$ENV_FILE" ]; then
    echo "✗ ERROR: Environment file '$ENV_FILE' not found" >&2
    exit 1
fi

require_env_vars "$ENV_FILE" \
    WORDPRESS_DB_HOST \
    WORDPRESS_DB_NAME \
    WORDPRESS_DB_ROOT_PASSWORD \
    WORDPRESS_DB_USER \
    WORDPRESS_DB_PASSWORD

if [ "$USE_REMOTE" -eq 1 ]; then
    echo "Pulling latest code from Git (branch: $BRANCH_NAME)"
    run_step "  Checking out branch '$BRANCH_NAME'..." git checkout "$BRANCH_NAME"
    run_step "  Fetching from origin..." git fetch origin
    run_step "  Resetting to origin/$BRANCH_NAME..." git reset --hard "origin/$BRANCH_NAME"
else
    echo "Using local working tree (no git checkout/fetch/reset)"
fi

if [ ! -f "$CADDYFILE" ]; then
    echo "✗ ERROR: Caddyfile ($CADDYFILE) not found!"
    echo "This file should be version-controlled in git. Aborting build."
    exit 1
fi
echo "✓ Caddyfile configuration found: $CADDYFILE"

echo "Validating club source manifest"
if make -n clubs-check >/dev/null 2>&1; then
    run_step "  Running make clubs-check..." make clubs-check
elif [ -f "backend/build_clubs_config.py" ]; then
    run_step "  Running $PYTHON_BIN backend/build_clubs_config.py --check..." "$PYTHON_BIN" backend/build_clubs_config.py --check
else
    echo "⚠ clubs-check skipped: split config tooling is not present on branch '$BRANCH_NAME'"
fi

echo "Build frontend and backend images"
if [ "$NO_CACHE" -eq 1 ]; then
    echo "  (--no-cache: full rebuild, ignoring Docker layer cache)"
    run_step "  Building backend and frontend images..." compose build --no-cache backend frontend
else
    echo "  (--quick: using Docker layer cache for faster rebuild)"
    run_step "  Building backend and frontend images..." compose build backend frontend
fi

echo "Start databases (Postgres + WordPress MySQL)"
run_step "  Starting postgres and wordpress-db..." compose up -d postgres wordpress-db

echo "Start backend and frontend"
run_step "  Starting backend and frontend..." compose up -d backend frontend

echo "Start WordPress services"
run_step "  Starting wordpress and wordpress-web..." compose up -d wordpress wordpress-web

echo "Start caddy"
run_step "  Starting caddy..." compose up -d caddy

echo "Check running processes"
compose ps

echo "Running post-start health checks"

retry_check() {
    local description="$1"
    local command="$2"
    local attempts="${3:-30}"
    local delay_seconds="${4:-3}"

    local i
    for ((i=1; i<=attempts; i++)); do
        if eval "$command" >/dev/null 2>&1; then
            echo "✓ ${description}"
            return 0
        fi
        if [ "$i" -lt "$attempts" ]; then
            sleep "$delay_seconds"
        fi
    done

    echo "✗ ERROR: ${description} failed after ${attempts} attempts"
    return 1
}

if [ "$SKIP_HEALTH" -eq 1 ]; then
    echo "⚠ Health checks skipped (--nohealth)"
else
    required_services=(postgres backend frontend wordpress-db wordpress wordpress-web caddy)

    for service in "${required_services[@]}"; do
        if ! compose ps --services --filter "status=running" | grep -q "^${service}$"; then
            echo "✗ ERROR: Service '${service}' is not running"
            compose ps
            exit 1
        fi
    done

    echo "✓ All required services are running"

    echo "Checking backend health endpoint"
    retry_check "Backend health endpoint OK" "curl --connect-timeout 5 --max-time 10 -fsS http://127.0.0.1:5050/clubs" 30 3 || exit 1

    echo "Checking frontend health endpoint via caddy"
    retry_check "Frontend/caddy endpoint OK" "curl --connect-timeout 5 --max-time 10 -kfsS --resolve ${HEALTH_HOST}:443:127.0.0.1 https://${HEALTH_HOST}/" 30 3 || exit 1

    echo "Checking WordPress/Nginx health endpoint"
    retry_check "WordPress/Nginx endpoint OK" "compose exec -T wordpress-web wget -q -O - http://127.0.0.1/healthz" 30 3 || exit 1
fi

echo "✓ Build complete"

if [ "$RUN_CLEAN" -eq 1 ]; then
    echo "Pruning unused Docker objects (docker system prune -f)..."
    run_step "  Removing dangling images and unused resources..." docker system prune -f
    echo "✓ Docker system clean complete"
fi
