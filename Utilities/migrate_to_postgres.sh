#!/bin/bash

set -e

echo "=== HLaS PostgreSQL Migration Script ==="
echo ""

# Check if backup exists
if [ ! -f /tmp/hlas_dump.sql ]; then
    echo "ERROR: Database backup not found at /tmp/hlas_dump.sql"
    exit 1
fi

echo "[1/5] Stopping Docker containers..."
docker compose -f docker-compose.prod.yml down || true

echo "[2/5] Removing old postgres volume..."
docker volume rm hlas_postgres_data || true

echo "[3/5] Starting only postgres container..."
docker compose -f docker-compose.prod.yml up -d postgres

echo "[4/5] Waiting for postgres to be ready..."
for i in {1..30}; do
    if docker compose -f docker-compose.prod.yml exec -T postgres pg_isready -U hlas >/dev/null 2>&1; then
        echo "PostgreSQL is ready!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

echo "[5/5] Restoring database dump..."
cat /tmp/hlas_dump.sql | docker compose -f docker-compose.prod.yml exec -T postgres psql -U hlas -d hlas

echo ""
echo "=== Migration complete! ==="
echo "Starting all containers..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "Waiting for all services to be healthy..."
for i in {1..120}; do
    check=$(docker compose -f docker-compose.prod.yml ps --services --status running 2>/dev/null | wc -l)
    if [ "$check" -eq 4 ]; then
        echo "All services ready!"
        break
    fi
    echo "Waiting... ($i/120)"
    sleep 2
done

echo ""
echo "=== Migration and startup complete! ==="
echo "Run: docker compose -f docker-compose.prod.yml logs -f"
echo "to monitor the services."
