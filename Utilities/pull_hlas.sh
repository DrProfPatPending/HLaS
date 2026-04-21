#!/bin/bash
# Move to the appropriate directory
cd /opt/hlas
echo "Pulling latest code from Git"
git pull
echo "Shut down existing containers..."
docker compose --env-file .env.prod -f docker-compose.prod.yml -f docker-compose.smoke.yml down
echo "Rebuild down existing containers..."
docker compose --env-file .env.prod -f docker-compose.prod.yml -f docker-compose.smoke.yml build --no-cache backend
echo "Boot new containers..."
docker compose --env-file .env.prod -f docker-compose.prod.yml -f docker-compose.smoke.yml up -d
echo "Check container logs..."
docker compose --env-file .env.prod -f docker-compose.prod.yml -f docker-compose.smoke.yml logs --tail=120 backend
echo "Check backend is accessible..."
curl -sS http://127.0.0.1:8080/api/clubs
