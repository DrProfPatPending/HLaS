param(
    [string]$ComposeFile = "docker-compose.prod.yml",
    [string]$EnvFile = ".env.prod"
)

$ErrorActionPreference = 'Stop'

$rootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $rootDir

if (-not (Test-Path $ComposeFile)) {
    throw "Compose file not found: $ComposeFile"
}
if (-not (Test-Path $EnvFile)) {
    throw "Env file not found: $EnvFile"
}

Write-Host "Building backend/frontend images..."
docker compose --env-file $EnvFile -f $ComposeFile build backend frontend

Write-Host "Pushing backend/frontend images..."
docker compose --env-file $EnvFile -f $ComposeFile push backend frontend

Write-Host "Publish complete."
