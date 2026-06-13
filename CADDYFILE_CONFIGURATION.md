# Caddyfile Configuration Guide

## Overview

HLaS uses **environment-specific Caddyfile configurations** to ensure SSL/TLS settings remain correct across development and production deployments, even when rebasing branches.

### Language Convention

- User-facing copy and documentation in this repository should default to British English spelling (for example: recognised, localisation, authorised).
- Keep external API/library identifiers unchanged where spelling is fixed by the platform (for example: `wp_localize_script`).

## Configuration Files

### Production Configuration
**File:** `deploy/caddy/Caddyfile.prod`

```caddyfile
cambridgetroutclub.org {
    encode zstd gzip

    handle_path /api/* {
        reverse_proxy backend:5050
    }

    handle {
        reverse_proxy frontend:80
    }
}
```

**Usage:**
- Domain: `cambridgetroutclub.org` (production domain)
- TLS: Let's Encrypt certificates (automatic, via ACME)
- Deployed: Via `docker-compose.prod.yml` on VPS
- Certificate storage: `/data/caddy/certificates/acme-v02.api.letsencrypt.org-directory/cambridgetroutclub.org/`

### Development Configuration
**File:** `deploy/caddy/Caddyfile.dev`

```caddyfile
hlastest {
    tls internal

    encode zstd gzip

    handle_path /api/* {
        reverse_proxy backend:5050
    }

    handle {
        reverse_proxy frontend:80
    }
}
```

**Usage:**
- Domain: `hlastest` (local development server)
- TLS: Caddy internal CA (self-signed, requires system trust)
- Deployed: Via `docker-compose.dev.yml` override on dev/test servers
- Certificate: Stored locally at `/data/caddy/pki/authorities/local/`

### Shared Caddyfile (Main Branch)
**File:** `deploy/caddy/Caddyfile`

- **This file is NOT environment-specific** — it defaults to the dev configuration
- Used on `main` branch where development is primary
- Never edited directly; kept in sync with `Caddyfile.dev`
- Production deployments ignore this file (explicit volume mount in docker-compose)

## Docker Compose Integration

### Production Deployment
**File:** `docker-compose.prod.yml`

```yaml
caddy:
  image: caddy:2.8-alpine
  volumes:
    - ./deploy/caddy/Caddyfile.prod:/etc/caddy/Caddyfile:ro  # ← Explicit production config
    - caddy_data:/data
    - caddy_config:/config
```

The **explicit volume mount** ensures the production Caddyfile is always used, regardless of what's in the working directory.

### Development Deployment Override
**File:** `docker-compose.dev.yml`

```yaml
services:
  caddy:
    volumes:
      - ./deploy/caddy/Caddyfile.dev:/etc/caddy/Caddyfile:ro  # ← Explicit dev config
```

This override is merged when starting the dev server:
```bash
docker compose -f docker-compose.prod.yml -f docker-compose.dev.yml up -d caddy
```

## Deployment Process

### VPS Production Deployment

1. **Merge tested code into `production` branch:**
   ```bash
   git checkout production
   git merge main
   ```

2. **Run the build script:**
   ```bash
   ./hlas_build.sh
   ```

   The script:
   - Validates that `deploy/caddy/Caddyfile.prod` exists
   - Pulls the latest `production` branch
   - Builds backend and frontend
   - Starts services using `docker-compose.prod.yml`
   - Caddy automatically uses `Caddyfile.prod` via explicit volume mount

3. **Verify deployment:**
   ```bash
   docker compose ps
   docker compose logs caddy | grep -i "domains\|cert"
   curl -v https://cambridgetroutclub.org
   ```

### Build Script Validation

**File:** `hlas_build.sh`

The build script includes safety validation:

```bash
# Validate and ensure production Caddyfile is in place
if [ ! -f "deploy/caddy/Caddyfile.prod" ]; then
    echo "✗ ERROR: Production Caddyfile (deploy/caddy/Caddyfile.prod) not found!"
    echo "This file should be version-controlled in git. Aborting build."
    exit 1
fi
echo "✓ Production Caddyfile configuration found"
```

This prevents deployment if the production configuration is missing.

## Git Management

### Both Files Are Version-Controlled

```bash
git ls-files deploy/caddy/Caddyfile*
# output:
# deploy/caddy/Caddyfile
# deploy/caddy/Caddyfile.dev
# deploy/caddy/Caddyfile.prod
```

### Workflow for Changes

#### Updating Development Configuration

1. Edit `deploy/caddy/Caddyfile.dev` (dev-specific settings)
2. Sync to main `Caddyfile` for consistency:
   ```bash
   cp deploy/caddy/Caddyfile.dev deploy/caddy/Caddyfile
   ```
3. Commit both:
   ```bash
   git add deploy/caddy/Caddyfile deploy/caddy/Caddyfile.dev
   git commit -m "Update development Caddyfile configuration"
   git push origin main
   ```

#### Updating Production Configuration

1. Edit `deploy/caddy/Caddyfile.prod` (production-specific settings)
2. Commit:
   ```bash
   git add deploy/caddy/Caddyfile.prod
   git commit -m "Update production Caddyfile configuration"
   ```
3. Merge to `main` (if config should be shared):
   ```bash
   git checkout main
   git merge production
   ```

#### Domain Changes (e.g., new certificate domain)

If the production domain changes (e.g., migrating to a new domain):

1. Update `Caddyfile.prod` with the new domain
2. Clear old certificates if needed:
   ```bash
   docker exec hlas-caddy-1 rm -rf /data/caddy/certificates/acme-v02.api.letsencrypt.org-directory/
   docker exec hlas-caddy-1 caddy reload --config /etc/caddy/Caddyfile
   ```
3. Caddy will auto-request a new Let's Encrypt certificate for the new domain

## Certificate Management

### Production Certificates (Let's Encrypt)

**Location:** `/data/caddy/certificates/acme-v02.api.letsencrypt.org-directory/cambridgetroutclub.org/`

**Automatic Renewal:**
- Caddy checks certificates weekly
- Renews 30 days before expiry
- No manual intervention needed

**Verify Certificate Status:**
```bash
cd /opt/hlas
docker cp hlas-caddy-1:/data/caddy/certificates/acme-v02.api.letsencrypt.org-directory/cambridgetroutclub.org/cambridgetroutclub.org.crt /tmp/cert.crt
openssl x509 -in /tmp/cert.crt -dates -noout
openssl x509 -in /tmp/cert.crt -subject -noout
```

### Development Certificates (Internal CA)

**Location:** `/data/caddy/pki/authorities/local/`

**Installation (macOS):**
```bash
./trust_caddy_mac.sh
```

**Installation (Linux):**
Caddy automatically installs to the system trust store when running as root.

## Troubleshooting

### Issue: "Invalid SSL certificate" on production

**Check which Caddyfile is being used:**
```bash
docker exec hlas-caddy-1 ps aux | grep caddy
# Should show: caddy run --config /etc/caddy/Caddyfile

docker compose logs caddy | grep -i "domains\|cert\|error"
```

**Verify the correct file is mounted:**
```bash
docker inspect hlas-caddy-1 --format='{{json .Mounts}}' | grep Caddyfile
# Should show: "./deploy/caddy/Caddyfile.prod"
```

**If production Caddyfile is not mounted:**
1. Check `docker-compose.prod.yml` for correct volume path
2. Verify file exists: `ls -la deploy/caddy/Caddyfile.prod`
3. Restart caddy: `docker compose restart caddy`

### Issue: Git rebase overwrites Caddyfile

**Prevent accidental overwrites:**

1. The explicit docker-compose volume mount protects against this
2. Run the build script which validates the file exists
3. Don't edit the working directory `Caddyfile` — always edit `Caddyfile.prod` or `Caddyfile.dev`

### Issue: Development server shows self-signed cert warning

1. Run `./trust_caddy_mac.sh` (macOS) to install the Caddy root CA
2. Or access via `http://localhost` (not HTTPS) for testing
3. The self-signed cert is expected and secure for local development

## Best Practices

1. ✅ **Keep both Caddyfile files in git** — always commit changes
2. ✅ **Use explicit paths in docker-compose** — never assume current directory
3. ✅ **Validate in build scripts** — check files exist before deployment
4. ✅ **Document domain/TLS changes** — commit messages should explain SSL changes
5. ✅ **Test on `main` before promoting** — verify dev config works before merging to `production`
6. ❌ **Don't edit the working Caddyfile directly** — always update `Caddyfile.prod` or `Caddyfile.dev`
7. ❌ **Don't skip the build script** — run `hlas_build.sh` on VPS, not manual docker commands
8. ❌ **Don't hardcode paths** — use the explicit docker-compose volume mounts

## Reference

- [DEPLOYMENT.md](DEPLOYMENT.md) — Full deployment workflow
- [Caddy Documentation](https://caddyserver.com/docs/) — Configuration reference
- `hlas_build.sh` — Production build and validation script
- `docker-compose.prod.yml` — Production docker configuration
- `docker-compose.dev.yml` — Development docker override
