param(
    [int]$BackendPort = 5050,
    [int]$FrontendPort = 8080
)

$ErrorActionPreference = 'Stop'

function Stop-ProcessTree {
    param(
        [Parameter(Mandatory = $true)]
        [int]$ProcessId
    )

    try {
        & taskkill /PID $ProcessId /T /F *> $null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

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
    if (-not $process) {
        Remove-Item -Path $PidFile -ErrorAction SilentlyContinue
        return $false
    }

    $stopped = Stop-ProcessTree -ProcessId $pidValue
    Start-Sleep -Milliseconds 200
    $stillRunning = Get-Process -Id $pidValue -ErrorAction SilentlyContinue

    Remove-Item -Path $PidFile -ErrorAction SilentlyContinue
    return ($stopped -and (-not $stillRunning))
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
    $stoppedAny = $false
    foreach ($owningProcessId in $owningProcessIds) {
        if (Stop-ProcessTree -ProcessId $owningProcessId) {
            $stoppedAny = $true
        }
    }

    return $stoppedAny
}

function Stop-ByCommandFilter {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$MustContain
    )

    $processes = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue
    if (-not $processes) {
        return $false
    }

    $matched = $processes | Where-Object {
        $commandLine = $_.CommandLine
        if (-not $commandLine) {
            return $false
        }

        foreach ($fragment in $MustContain) {
            if ($commandLine -notmatch [regex]::Escape($fragment)) {
                return $false
            }
        }

        return $true
    }

    if (-not $matched) {
        return $false
    }

    $stoppedAny = $false
    foreach ($process in $matched) {
        if ($process.ProcessId -and (Stop-ProcessTree -ProcessId $process.ProcessId)) {
            $stoppedAny = $true
        }
    }

    return $stoppedAny
}

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPidFile = Join-Path $rootDir '.backend.pid'
$frontendPidFile = Join-Path $rootDir '.frontend.pid'

$backendStopped =
    (Stop-ByPidFile -PidFile $backendPidFile) -or
    (Stop-ByPort -Port $BackendPort) -or
    (Stop-ByCommandFilter -MustContain @('\backend', 'import app'))

$frontendStopped =
    (Stop-ByPidFile -PidFile $frontendPidFile) -or
    (Stop-ByPort -Port $FrontendPort) -or
    (Stop-ByCommandFilter -MustContain @('vue-cli-service', '\frontend'))

if ($backendStopped -or $frontendStopped) {
    Write-Output 'Servers Stopped'
}
else {
    Write-Output 'No Running Servers Found'
}
