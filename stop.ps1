param(
    [int]$BackendPort = 5000,
    [int]$FrontendPort = 8080
)

$ErrorActionPreference = 'Stop'

function Stop-ByPidFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PidFile
    )

    if (-not (Test-Path $PidFile)) {
        return $false
    }

    $content = Get-Content -Path $PidFile -ErrorAction SilentlyContinue
    if (-not $content) {
        Remove-Item -Path $PidFile -ErrorAction SilentlyContinue
        return $false
    }

    $pidValue = 0
    if (-not [int]::TryParse($content[0], [ref]$pidValue)) {
        Remove-Item -Path $PidFile -ErrorAction SilentlyContinue
        return $false
    }

    $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
    }

    Remove-Item -Path $PidFile -ErrorAction SilentlyContinue
    return $true
}

function Stop-ByPort {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $connections) {
        return $false
    }

    $owningProcessIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($owningProcessId in $owningProcessIds) {
        Stop-Process -Id $owningProcessId -Force -ErrorAction SilentlyContinue
    }

    return $true
}

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPidFile = Join-Path $rootDir '.backend.pid'
$frontendPidFile = Join-Path $rootDir '.frontend.pid'

$backendStopped = (Stop-ByPidFile -PidFile $backendPidFile) -or (Stop-ByPort -Port $BackendPort)
$frontendStopped = (Stop-ByPidFile -PidFile $frontendPidFile) -or (Stop-ByPort -Port $FrontendPort)

if ($backendStopped -or $frontendStopped) {
    Write-Output 'Servers Stopped'
}
else {
    Write-Output 'No Running Servers Found'
}
