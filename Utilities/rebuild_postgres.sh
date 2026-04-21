#!/bin/bash
# Move to the appropriate directory
cd /opt/hlas

# 1) Confirm root cause quickly
docker compose --env-file .env.prod -f docker-compose.prod.yml logs --tail=120 postgres

# 2) Tear down and delete old Postgres data volume
docker compose --env-file .env.prod -f docker-compose.prod.yml -f docker-compose.smoke.yml down
docker volume rm hlas_postgres_data || true

# 3) Start only Postgres and wait until healthy
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d postgres
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
docker compose --env-file .env.prod -f docker-compose.prod.yml logs --tail=80 postgres

# 4) Recreate DB and import your plain SQL dump
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T postgres psql -U hlas -d postgres -c "DROP DATABASE IF EXISTS hlas;"
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T postgres psql -U hlas -d postgres -c "CREATE DATABASE hlas OWNER hlas;"
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T postgres psql -U hlas -d hlas < /tmp/hlas_bootstrap.sql

# 5) Bring up app stack and verify
docker compose --env-file .env.prod -f docker-compose.prod.yml -f docker-compose.smoke.yml up -d
docker compose --env-file .env.prod -f docker-compose.prod.yml -f docker-compose.smoke.yml ps
docker compose --env-file .env.prod -f docker-compose.prod.yml -f docker-compose.smoke.yml logs --tail=120 backend
echo "Check backend is accessible..."
curl -sS http://127.0.0.1:8080/api/clubs
