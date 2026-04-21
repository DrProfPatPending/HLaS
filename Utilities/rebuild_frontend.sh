#!/bin/bash
# Move to the appropriate directory
cd /opt/hlas

#
echo "Pull latest version from Git"
git pull origin main

echo "Rebuild frontend with no cache"
docker compose --env-file .env.prod -f docker-compose.prod.yml build --no-cache frontend

echo "Restart frontend with caddy"
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d frontend caddy

echo "Rebuild complete..."

