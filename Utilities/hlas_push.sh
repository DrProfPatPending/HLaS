#!/bin/bash
# Move to the appropriate directory
cd /opt/hlas
echo "Pushing local updates back to Github"

echo "Check git status"
git status
git remote -v

# Make sure you're up to date first
echo "Get latest origin main from GitHub"
git fetch origin
git checkout main
git pull --ff-only origin main

# Create a branch for VPS deployment changes
echo "Create new branch for local deployment files"
git checkout -b vps-deploy-updates-2026-04-21

# Stage only the files you actually want to share
git add deploy/caddy/Caddyfile setup_admin_users.py bootstrap_postgres.sh hlas_build.sh hlas_push.sh pull_hlas.sh pull_hlas_v2.sh rebuild_frontend.sh rebuild_ppostgres.sh reset_user_pass.sh
git commit -m "Update VPS deployment config and admin setup script"

# Push branch to GitHub
echo "Push changes back to GitHub"
git push -u origin vps-deploy-updates-2026-04-21
