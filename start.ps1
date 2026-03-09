param(
    [int]$DelayMs = 3000,
    [string]$BackendUrl = "http://127.0.0.1:5000/members",
    [string]$FrontendUrl = "http://127.0.0.1:8080/"
)

$ErrorActionPreference = 'Stop'

function Test-ServerUrl {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url
    )

    try {
        Invoke-WebRequest -Uri $Url -Method Get -UseBasicParsing -TimeoutSec 5 | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $rootDir 'backend'
$frontendDir = Join-Path $rootDir 'frontend'
$backendPidFile = Join-Path $rootDir '.backend.pid'
$frontendPidFile = Join-Path $rootDir '.frontend.pid'

$pythonExe = Join-Path $rootDir '.venv\Scripts\python.exe'
if (-not (Test-Path $pythonExe)) {
    $pythonExe = 'python'
}

$npmCmd = 'npm.cmd'
if (-not (Get-Command $npmCmd -ErrorAction SilentlyContinue)) {
    $npmCmd = 'npm'
}

$backendProcess = Start-Process -FilePath $pythonExe -ArgumentList @('app.py') -WorkingDirectory $backendDir -PassThru
$backendProcess.Id | Set-Content -Path $backendPidFile
Start-Sleep -Milliseconds $DelayMs

if (Test-ServerUrl -Url $BackendUrl) {
    Write-Output 'Backend Running'
}
else {
    Write-Output 'Server Not Running'
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force
    }
    exit 1
}

$frontendProcess = Start-Process -FilePath $npmCmd -ArgumentList @('run', 'serve') -WorkingDirectory $frontendDir -PassThru
$frontendProcess.Id | Set-Content -Path $frontendPidFile
Start-Sleep -Milliseconds $DelayMs

if (Test-ServerUrl -Url $FrontendUrl) {
    Write-Output 'Server Running'
}
else {
    Write-Output 'Server Not Running'
    exit 1
}
