# CTC-Production Branch Setup Guide

## Overview

The `ctc-production` branch is a specialized deployment for Cambridge Trout Club (CTC) running on the production VPS (`cambridgetroutclub.org`).

This branch:
- Receives universal application updates from `main`
- Keeps live `.env.ctc`, `clubs.config.ctc.json`, and `deploy/caddy/Caddyfile.ctc` files outside Git
- Retains only CTC-specific content and presentation changes in the branch

---

## CTC Development on hlastest

Use `ctc-dev` for CTC changes, starting from the pushed production baseline.
Test there before merging into `ctc-production`; do not deploy directly from
`main` or the handover branch. Configuration and content stored in PostgreSQL
are not transferred by Git.

`docker-compose.ctc-dev.yml` is a standalone development stack, not an override
for the production Compose file. It uses separate `ctc-dev` database/application
volumes and local image tags. The backend has only an internal Docker network,
with no external egress, and PostgreSQL has no published port. WordPress data
is not cloned: Caddy retains the existing `wordpress.hlastest` route over
`hlas_default`. Only the existing development TLS data volume is shared, so
trusted development certificates continue working. Do not use this file on
production.

The stack sets `HLAS_SYNC_FILES_ON_STARTUP=false` so first-request hooks cannot
replace restored PostgreSQL beats or images with filesystem defaults. Other
deployments retain the existing default (`true`). Backup API routes are also
disabled with `ENABLE_BACKUPS=false`; no production backup schedule is copied.

Before starting:

1. Securely transfer the approved custom-format dump outside the repository.
   Verify its SHA-256, byte count and restricted permissions.
2. Generate a development-only database password once:
   ```bash
   (umask 077; test ! -e deploy/.ctc-dev-postgres-password &&
     openssl rand -hex -out deploy/.ctc-dev-postgres-password 32)
   ```
   Keep this ignored file private and do not regenerate it for an existing
   database volume.
3. Validate and build the standalone stack:
   ```bash
   docker compose -f docker-compose.ctc-dev.yml config --quiet
   docker compose -f docker-compose.ctc-dev.yml build backend frontend
   docker compose -f docker-compose.ctc-dev.yml up -d --wait postgres
   ```
4. Verify PostgreSQL is using a new `ctc-dev` volume and an empty database.
   Restore only into that database with `pg_restore --no-owner --no-acl
   --exit-on-error --single-transaction`. Before starting the backend, clear
   `host`, `username`, `password` and `from_email` in its restored
   `club_smtp_settings` table, truncate `member_sessions` and
   `member_refresh_sessions`, and review other production-specific settings.
   Do not copy production environment files or credentials.
5. Start and check `backend` and `frontend` first. Neither service publishes
   a host port; run readiness checks inside their internal Docker network.
   For example:
   ```bash
   docker compose -f docker-compose.ctc-dev.yml exec -T frontend \
     wget -q -O /dev/null http://127.0.0.1/club/CTC/
   ```
   Verify blocked backend egress before switching public development routing.
6. Only after readiness checks, stop the old development Caddy and start
   the CTC Caddy:
   ```bash
   docker compose -f docker-compose.prod.yml -f docker-compose.dev.yml stop caddy
   docker compose -f docker-compose.ctc-dev.yml up -d caddy
   ```
   Verify `https://hlastest/club/CTC/`, its enabled pages, login, and the
   `X-Robots-Tag`/robots.txt indexing restrictions. The original databases and
   other services remain untouched.

To roll back routing without deleting either stack's data:
```bash
docker compose -f docker-compose.ctc-dev.yml stop caddy
docker compose -f docker-compose.prod.yml -f docker-compose.dev.yml start caddy
```

Exchange non-sensitive progress and questions in `HANDOVER.md` on
`sync-handover`, not on the deployment branches. Fetch before updating it and
push responses without including dumps or secrets. While the stack is running,
update the handover branch without switching the deployment checkout: its
branch-specific files are bind-mounted into running containers.

---

## Initial Setup on VPS

### 1. Create External Config File

On your VPS at `/opt/hlas`, create a CTC-only clubs config:

```bash
cp clubs.config.ctc.example.json clubs.config.ctc.json
# Edit clubs.config.ctc.json as needed for your CTC instance
nano clubs.config.ctc.json
```

Alternatively, extract the `[CTC]` entries from the current `backend/clubs.config.json` and place them in `clubs.config.ctc.json`.

### 2. Create Deployment Files

```bash
cp --preserve=mode .env.prod .env.ctc
cp deploy/caddy/Caddyfile.ctc.example deploy/caddy/Caddyfile.ctc
```

Set `WORDPRESS_PUBLIC_URL=https://wordpress.cambridgetroutclub.org` in `.env.ctc`. If the temporary site gate is required, add its bcrypt hash only to the ignored `Caddyfile.ctc` file.

### 3. Deploy with ctc-production Branch

```bash
cd /opt/hlas
git fetch origin
git checkout ctc-production
git pull origin ctc-production

./hlas_build.sh --target ctc-production --directory /opt/hlas --allow-http-401
```

The target automatically selects `.env.ctc`, `clubs.config.ctc.json`, `deploy/caddy/Caddyfile.ctc`, and the CTC health-check hostname. The explicit file options remain available for exceptional deployments.

The build script defaults to fetching and resetting to the remote target branch. Use `--local --quick` only when intentionally deploying the checked-out local commit, and ensure the commit has been pushed first so a later remote deployment will retain it.

### 4. Verify the CTC Mini-Site

- Check the enabled Home, About and Contact pages at mobile and desktop widths, including navigation, direct page access and the member login form.
- Verify the public page and `/api/clubs` through Caddy, and check container health. The protected WordPress host may return HTTP 401 without credentials.
- Mini-site page settings are stored per club in PostgreSQL; Dev database settings are not deployed by Git and must be reviewed separately in the authorised Club Settings interface.

---

## Merging Core Updates

When you want to merge tested application updates into `ctc-production`:

```bash
git checkout ctc-production
git fetch origin
git merge --no-edit origin/main
git push origin ctc-production
```

The ignored live deployment files are not changed by the merge.

---

## Customizations

### Theme/Branding

Commit CTC-specific theme overrides to `ctc-production`:
- Custom CSS/styling
- Logo/image assets
- Frontend component modifications
- Feature flags (if applicable)

Example:
```bash
git add frontend/src/custom-themes/ctc-theme.css
git commit -m "style: CTC brand theme"
git push origin ctc-production
```

### Configuration Changes

Keep environment values in `.env.ctc`, club data in `clubs.config.ctc.json`, and Caddy routing/authentication in `deploy/caddy/Caddyfile.ctc`. These files are ignored and selected explicitly by `hlas_build.sh`.

---

## Troubleshooting

**"Could not open clubs.config.ctc.json"**
- Verify the `--clubs-config` path exists
- Check file permissions: `ls -la /opt/hlas/clubs.config.ctc.json`

**Old clubs appearing after merge from development**
- This shouldn't happen if using external config (env var)
- Check that the deployment command includes `--clubs-config clubs.config.ctc.json`
- Inspect the rendered backend mount with `docker compose config`

**Cannot merge from development**
- Use `git merge --no-edit origin/development` to accept incoming changes
- Manually resolve any conflicts in `.gitignore` or `.env` files if they exist

---

## Branch Maintenance

Keep `ctc-production` aligned with core updates:

```bash
# Monthly or as needed:
git checkout ctc-production
git merge --no-edit origin/main
```

---

## Reverting to Multi-Club

If you later want to revert to a full multi-club setup:

```bash
git checkout production
# Or switch back to development if you want all branches aligned
```

The `ctc-production` branch will remain available in git history for reference.
