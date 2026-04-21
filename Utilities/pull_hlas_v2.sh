#!/bin/bash
# Move to the appropriate directory
cd /opt/hlas
echo "Pulling latest code from Git"
git pull

# rebuild backend image with fixed migration
echo "Rebuild Docker containers"
docker compose --env-file .env.prod -f docker-compose.prod.yml -f docker-compose.smoke.yml build --no-cache backend

# restart stack
echo "Restart Docker container stack"
docker compose --env-file .env.prod -f docker-compose.prod.yml -f docker-compose.smoke.yml up -d

# verify backend migration/startup
echo "Verify backend migration"
docker compose --env-file .env.prod -f docker-compose.prod.yml -f docker-compose.smoke.yml logs --tail=150 backend

# verify app endpoint
echo "Verify App endpoint"
curl -sS http://127.0.0.1:8080/api/clubs
