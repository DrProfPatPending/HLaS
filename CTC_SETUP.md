# CTC-Production Branch Setup Guide

## Overview

The `ctc-production` branch is a specialized deployment for Cambridge Trout Club (CTC) running on the production VPS (`cambridgetroutclub.org`).

This branch:
- Derives from `production` but maintains a separate config
- Uses an external `clubs.config.ctc.json` file to specify only CTC
- Can be rebased/merged from `development` without conflicts (code updates on core only)
- Allows CTC-specific theme and configuration customizations

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

### 2. Configure Environment Variable

Set `HLAS_CLUBS_CONFIG_PATH` in your deployment environment:

**Option A: In `.env.ctc` (recommended)**
```bash
cp .env.ctc.example .env.ctc
nano .env.ctc
# Ensure HLAS_CLUBS_CONFIG_PATH=/opt/hlas/clubs.config.ctc.json
```

Then use during deployment:
```bash
./hlas_build.sh --target ctc-production --directory /opt/hlas --env-file .env.ctc
```

**Option B: In docker-compose override**
Add to `docker-compose.prod.yml` or a `docker-compose.ctc.yml` override:
```yaml
services:
  backend:
    environment:
      HLAS_CLUBS_CONFIG_PATH: /opt/hlas/clubs.config.ctc.json
```

### 3. Deploy with ctc-production Branch

```bash
cd /opt/hlas
git fetch origin
git checkout ctc-production
git pull origin ctc-production

# Standard build script (will use HLAS_CLUBS_CONFIG_PATH if set)
./hlas_build.sh --target ctc-production --directory /opt/hlas
```

---

## Merging Core Updates

When you want to merge updates from `development` into `ctc-production`:

```bash
git checkout ctc-production
git fetch origin
git merge --no-edit origin/development
# Resolve any conflicts (should be rare if config is external)
git push origin ctc-production
```

Since club config is external (env var), core code updates will merge cleanly.

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

Keep per-environment config in `.env.ctc` (VPS-only, not committed) or external config files referenced by env vars.

---

## Troubleshooting

**"Could not open clubs.config.ctc.json"**
- Verify `HLAS_CLUBS_CONFIG_PATH` is set and the file exists
- Check file permissions: `ls -la /opt/hlas/clubs.config.ctc.json`

**Old clubs appearing after merge from development**
- This shouldn't happen if using external config (env var)
- If you see it, check that `HLAS_CLUBS_CONFIG_PATH` environment variable is being passed to the container
- Verify the external config file is up-to-date

**Cannot merge from development**
- Use `git merge --no-edit origin/development` to accept incoming changes
- Manually resolve any conflicts in `.gitignore` or `.env` files if they exist

---

## Branch Maintenance

Keep `ctc-production` aligned with core updates:

```bash
# Monthly or as needed:
git checkout ctc-production
git merge --no-edit origin/production  # Always in sync with main production
```

Or periodically rebase on top of newer `production`:
```bash
git rebase origin/production  # if you want a linear history
```

---

## Reverting to Multi-Club

If you later want to revert to a full multi-club setup:

```bash
git checkout production
# Or switch back to development if you want all branches aligned
```

The `ctc-production` branch will remain available in git history for reference.
