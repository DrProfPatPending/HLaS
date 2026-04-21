#!/bin/bash
# Make the switch between binary dump - use pg_restore and ASCII dump - use psql...
#
set IMPORT="binary"

echo "Move to build directory..."
cd /opt/hlas
echo "Shut down the existing applications..."
docker compose --env-file .env.prod -f docker-compose.prod.yml stop backend frontend caddy
echo "Bring up just postgres..."
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d postgres

echo "Drop any existing database stubs..."
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T postgres \
  psql -U hlas -d postgres -c "DROP DATABASE IF EXISTS hlas;"
echo "Create new empty database..."
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T postgres \
  psql -U hlas -d postgres -c "CREATE DATABASE hlas OWNER hlas;"

if [[ $IMPORT = "binary" ]] 
then
    echo "Importing binary database dump..."
    docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T postgres \
      pg_restore -U hlas -d hlas --clean --if-exists --no-owner --no-privileges < /tmp/hlas_bootstrap.dump
  else
    echo "Importing ASCII database dump..."
    docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T postgres \
      psql -U hlas -d hlas < /tmp/hlas_bootstrap.sql
fi

echo "Rebuild all applications..."
docker compose --env-file .env.prod -f docker-compose.prod.yml -f docker-compose.smoke.yml up -d
echo "Check frontend and backend..."
curl -sS http://127.0.0.1:8080/api/clubs
