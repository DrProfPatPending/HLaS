#!/bin/bash
set -euo pipefail

# Move to the appropriate directory
cd /opt/hlas
echo "Rebuilding latest HLaS from Github sources"

unset BACKEND_IMAGE FRONTEND_IMAGE DOMAIN DATABASE_URL POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB HLAS_USE_POSTGRES_READS LOG_LEVEL
echo "Pulling latest code from Git"
git checkout production
git pull origin production

# Validate and ensure production Caddyfile is in place
if [ ! -f "deploy/caddy/Caddyfile.prod" ]; then
    echo "✗ ERROR: Production Caddyfile (deploy/caddy/Caddyfile.prod) not found!"
    echo "This file should be version-controlled in git. Aborting build."
    exit 1
fi
echo "✓ Production Caddyfile configuration found"
echo "Build frontend and backend images"
docker compose --env-file .env.prod -f docker-compose.prod.yml build --no-cache backend frontend

echo "Start databases (Postgres + WordPress MySQL)"
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d postgres wordpress-db

echo "Start backend and frontend"
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d backend frontend

echo "Start WordPress services"
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d wordpress wordpress-web

echo "Start caddy"
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d caddy

echo "Check running processes"
docker compose --env-file .env.prod -f docker-compose.prod.yml ps

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

required_services=(postgres backend frontend wordpress-db wordpress wordpress-web caddy)

for service in "${required_services[@]}"; do
    if ! docker compose --env-file .env.prod -f docker-compose.prod.yml ps --services --filter "status=running" | grep -q "^${service}$"; then
        echo "✗ ERROR: Service '${service}' is not running"
        docker compose --env-file .env.prod -f docker-compose.prod.yml ps
        exit 1
    fi
done

echo "✓ All required services are running"

echo "Checking backend health endpoint"
retry_check "Backend health endpoint OK" "curl -fsS http://127.0.0.1:5050/clubs" 30 3 || exit 1

echo "Checking frontend health endpoint via caddy"
retry_check "Frontend/caddy endpoint OK" "curl -kfsS https://127.0.0.1/" 30 3 || exit 1

echo "Checking WordPress endpoint via caddy"
retry_check "WordPress endpoint OK" "curl -kfsS https://wordpress.cambridgetroutclub.org/" 30 3 || exit 1

echo "✓ Build and health checks complete"
