#!/bin/bash
# Move to the appropriate directory
cd /opt/hlas
echo "Rebuilding latest HLaS from Github sources"

unset BACKEND_IMAGE FRONTEND_IMAGE DOMAIN DATABASE_URL POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB HLAS_USE_POSTGRES_READS LOG_LEVEL
echo "Pulling latest code from Git"
git checkout main
git pull origin main
echo "Build frontend and backend"
docker compose --env-file .env.prod -f docker-compose.prod.yml build --no-cache backend frontend
echo "Start postgres"
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d postgres
echo "Start backend"
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d backend
echo "Start frontend and caddy"
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d frontend caddy
echo "Check running processes"
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
