param(
    [int]$DelayMs = 3000,
    [int]$BackendPort = 5050,
    [int]$FrontendPort = 8080,
    [string]$BindIp = "192.168.50.57",
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
$backendConfigPath = Join-Path $backendDir 'server.config.json'
$frontendConfigPath = Join-Path $frontendDir 'server.config.json'

$backendConfig = $null
if (Test-Path $backendConfigPath) {
    try {
        $backendConfig = Get-Content -Path $backendConfigPath -Raw | ConvertFrom-Json
    }
    catch {
        Write-Warning "Unable to parse backend/server.config.json. Using script defaults."
    }
}

$frontendConfig = $null
if (Test-Path $frontendConfigPath) {
    try {
        $frontendConfig = Get-Content -Path $frontendConfigPath -Raw | ConvertFrom-Json
    }
    catch {
        Write-Warning "Unable to parse frontend/server.config.json. Using script defaults."
    }
}

if (-not $PSBoundParameters.ContainsKey('DelayMs')) {
    if ($frontendConfig -and $frontendConfig.startup -and $frontendConfig.startup.delayMs -ne $null) {
        $DelayMs = [int]$frontendConfig.startup.delayMs
    }
    elseif ($backendConfig -and $backendConfig.startup -and $backendConfig.startup.delayMs -ne $null) {
        $DelayMs = [int]$backendConfig.startup.delayMs
    }
}

if (-not $PSBoundParameters.ContainsKey('BackendPort') -and $backendConfig -and $backendConfig.server -and $backendConfig.server.port -ne $null) {
    $BackendPort = [int]$backendConfig.server.port
}

if (-not $PSBoundParameters.ContainsKey('FrontendPort') -and $frontendConfig -and $frontendConfig.server -and $frontendConfig.server.port -ne $null) {
    $FrontendPort = [int]$frontendConfig.server.port
}

if (-not $PSBoundParameters.ContainsKey('BindIp')) {
    if ($frontendConfig -and $frontendConfig.server -and $frontendConfig.server.host) {
        $BindIp = [string]$frontendConfig.server.host
    }
    elseif ($backendConfig -and $backendConfig.server -and $backendConfig.server.host) {
        $BindIp = [string]$backendConfig.server.host
    }
}

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
    if ($backendConfig -and $backendConfig.server -and $backendConfig.server.url) {
        $BackendUrl = "$(($backendConfig.server.url).TrimEnd('/'))/members"
    }
    else {
        $BackendUrl = "http://${BindIp}:$BackendPort/members"
    }
}
if (-not $FrontendUrl) {
    if ($frontendConfig -and $frontendConfig.server -and $frontendConfig.server.url) {
        $FrontendUrl = "$(($frontendConfig.server.url).TrimEnd('/'))/"
    }
    else {
        $FrontendUrl = "http://${BindIp}:$FrontendPort/"
    }
}

$backendDebug = $false
if ($backendConfig -and $backendConfig.runtime -and $backendConfig.runtime.debug -ne $null) {
    $backendDebug = [bool]$backendConfig.runtime.debug
}

$backendUseReloader = $false
if ($backendConfig -and $backendConfig.runtime -and $backendConfig.runtime.useReloader -ne $null) {
    $backendUseReloader = [bool]$backendConfig.runtime.useReloader
}

$debugPyValue = if ($backendDebug) { 'True' } else { 'False' }
$reloaderPyValue = if ($backendUseReloader) { 'True' } else { 'False' }

$backendRunCode = "import app; app.configure_logging(); app.app.run(host='$BindIp', port=$BackendPort, debug=$debugPyValue, use_reloader=$reloaderPyValue)"
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

$configuredBackendUrl = "http://${BindIp}:$BackendPort"
if ($frontendConfig -and $frontendConfig.api -and $frontendConfig.api.backendUrl) {
    $configuredBackendUrl = [string]$frontendConfig.api.backendUrl
}
$env:VUE_APP_BACKEND_URL = $configuredBackendUrl
$frontendProcess = Start-Process -FilePath $npmCmd -ArgumentList @('run', 'serve', '--', '--host', "$BindIp", '--port', "$FrontendPort") -WorkingDirectory $frontendDir -PassThru
$frontendProcess.Id | Set-Content -Path $frontendPidFile
Start-Sleep -Milliseconds $DelayMs

if (Test-ServerUrl -Url $FrontendUrl) {
    Write-Output 'Server Running'
}
else {
    Write-Output 'Server Not Running'
    exit 1
}
