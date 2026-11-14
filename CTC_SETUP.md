# CTC-Production Branch Setup Guide

## Overview

The `ctc-production` branch is a specialized deployment for Cambridge Trout Club (CTC) running on the production VPS (`cambridgetroutclub.org`).

This branch:
- Receives universal application updates from `main`
- Keeps live `.env.ctc`, `clubs.config.ctc.json`, and `deploy/caddy/Caddyfile.ctc` files outside Git
- Retains only CTC-specific content and presentation changes in the branch

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

Set `HLAS_SYNC_FILES_ON_STARTUP=false` in `.env.ctc` to prevent the backend's
first-request hooks from replacing PostgreSQL beats and syncing filesystem logos
and backgrounds. The default is `true` for compatibility; the setting only
works with a backend image containing this startup control. Disabling these
hooks does not disable migrations or other database writes.

For an application-only update when PostgreSQL and the other services are
already running, add `--app-only`. This rebuilds and restarts only the backend
and frontend, waits for each to become healthy, and requires a healthy
PostgreSQL service and the CTC startup-sync opt-out.

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
