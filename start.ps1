param(
    [int]$DelayMs = 3000,
    [int]$BackendPort = 5050,
    [int]$FrontendPort = 8080,
    [string]$BackendUrl = "",
    [string]$FrontendUrl = ""
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
        if ($_.Exception -and $_.Exception.Response) {
            return $true
        }
        return $false
    }
}

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $rootDir 'backend'
$frontendDir = Join-Path $rootDir 'frontend'
$backendPidFile = Join-Path $rootDir '.backend.pid'
$frontendPidFile = Join-Path $rootDir '.frontend.pid'

$pythonCandidates = @(
    (Join-Path $rootDir '.venv\Scripts\python.exe'),
    (Join-Path (Split-Path -Parent $rootDir) '.venv\Scripts\python.exe')
)

$pythonExe = $null
foreach ($candidate in $pythonCandidates) {
    if (Test-Path $candidate) {
        $pythonExe = $candidate
        break
    }
}

if (-not $pythonExe) {
    $pythonExe = 'python'
}

$npmCmd = 'npm.cmd'
if (-not (Get-Command $npmCmd -ErrorAction SilentlyContinue)) {
    $npmCmd = 'npm'
}

if (-not $BackendUrl) {
    $BackendUrl = "http://127.0.0.1:$BackendPort/members"
}
if (-not $FrontendUrl) {
    $FrontendUrl = "http://127.0.0.1:$FrontendPort/"
}

$backendRunCode = "import app; app.configure_logging(); app.app.run(host='127.0.0.1', port=$BackendPort, debug=False, use_reloader=False)"
$backendProcess = Start-Process -FilePath $pythonExe -ArgumentList @('-c', ('"' + $backendRunCode + '"')) -WorkingDirectory $backendDir -PassThru
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

$frontendProcess = Start-Process -FilePath $npmCmd -ArgumentList @('run', 'serve', '--', '--port', "$FrontendPort") -WorkingDirectory $frontendDir -PassThru
$frontendProcess.Id | Set-Content -Path $frontendPidFile
Start-Sleep -Milliseconds $DelayMs

if (Test-ServerUrl -Url $FrontendUrl) {
    Write-Output 'Server Running'
}
else {
    Write-Output 'Server Not Running'
    exit 1
}
