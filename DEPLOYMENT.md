# HLaS Production Deployment (Docker + VPS)

This bundle deploys HLaS with three containers:

- `backend`: Flask API served by Gunicorn
- `frontend`: Vue production build served by Nginx
- `caddy`: reverse proxy + TLS (Let's Encrypt)

## 1) Prerequisites

- A Linux VPS (Ubuntu recommended)
- DNS `A` record pointing your domain to the VPS IP
- Docker Engine + Compose plugin on VPS
- A container registry (GHCR or Docker Hub)

## 2) Files in this bundle

- `backend/Dockerfile`
- `frontend/Dockerfile`
- `docker-compose.prod.yml`
- `deploy/caddy/Caddyfile`
- `deploy/nginx/frontend.conf`
- `deploy/local/publish.ps1`
- `deploy/vps/deploy.sh`
- `deploy/vps/bootstrap-ubuntu.sh`
- `.env.prod.example`

## 3) Build and push images (local machine)

1. Copy `.env.prod.example` to `.env.prod` and set values.
2. Login to your registry (example GHCR):
   ```powershell
   echo <YOUR_GITHUB_TOKEN> | docker login ghcr.io -u <YOUR_GITHUB_USERNAME> --password-stdin
   ```
3. Build and push images:
   ```powershell
   .\deploy\local\publish.ps1 -EnvFile .env.prod
   ```

## 4) Prepare VPS

### Option A: Bootstrap Docker automatically (Ubuntu)

```bash
sudo bash deploy/vps/bootstrap-ubuntu.sh
```

### Option B: Existing Docker install

Skip bootstrap if Docker + Compose are already installed.

## 5) Copy deployment files to VPS

Copy the repo (or at least these files) to the VPS, e.g. `/opt/hlas`.

Required on VPS:

- `docker-compose.prod.yml`
- `deploy/caddy/Caddyfile`
- `deploy/vps/deploy.sh`
- `.env.prod` (with real values)

## 6) Deploy on VPS

```bash
cd /opt/hlas
chmod +x deploy/vps/deploy.sh
./deploy/vps/deploy.sh
```

This script:

- pulls newest images
- runs `docker compose up -d --remove-orphans`
- prunes dangling images
- prints service status

## 7) Data persistence

Backend data is persisted in Docker volume `hlas_data` via `HLAS_DATA_DIR=/data`.
This includes:

- club databases (`*.db`)
- `clubs.config.json`
- `server.config.json`
- `club_logos/`
- `ID_photos/`

## 8) Routing and TLS

- Public HTTPS endpoint is served by Caddy
- `/api/*` is forwarded to backend and stripped to backend routes
- all other paths are forwarded to frontend
- Caddy issues and renews certs automatically for `DOMAIN`

## 9) Update workflow

1. Build + push new images (`publish.ps1`)
2. SSH into VPS and run:
   ```bash
   cd /opt/hlas
   ./deploy/vps/deploy.sh
   ```

## 10) Troubleshooting

- Service status:
  ```bash
  docker compose --env-file .env.prod -f docker-compose.prod.yml ps
  ```
- Logs:
  ```bash
  docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f caddy frontend backend
  ```
- Verify DNS: `DOMAIN` must resolve to VPS public IP
- Ensure firewall allows ports `80` and `443`
