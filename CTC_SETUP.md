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
cp .env.ctc.example .env.ctc
cp deploy/caddy/Caddyfile.ctc.example deploy/caddy/Caddyfile.ctc
```

Copy the required database values from `.env.prod` into `.env.ctc`. Configure the CTC WordPress URL there. If the temporary site gate is required, add its bcrypt hash only to the ignored `Caddyfile.ctc` file.

### 3. Deploy with ctc-production Branch

```bash
cd /opt/hlas
git fetch origin
git checkout ctc-production
git pull origin ctc-production

./hlas_build.sh --target ctc-production --directory /opt/hlas \
  --env-file .env.ctc \
  --clubs-config clubs.config.ctc.json \
  --caddyfile deploy/caddy/Caddyfile.ctc \
  --health-host cambridgetroutclub.org \
  --allow-http-401
```

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
