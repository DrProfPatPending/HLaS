param(
    [int]$DelayMs = 3000,
    [int]$BackendPort = 5050,
    [int]$FrontendPort = 8080,
    [string]$BindIp = "192.168.50.57",
    [string]$BackendUrl = "",
    [string]$FrontendUrl = "",
    [switch]$TlsOff,
    [switch]$BackendTlsOff,
    [switch]$FrontendTlsOff,
    [switch]$UseBackendCertFiles,
    [string]$BackendCertFile = "",
    [string]$BackendKeyFile = ""
)

$ErrorActionPreference = 'Stop'

function Test-ServerUrl {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url
    )

    $isHttps = $Url -match '^https://'
    $curlExe = Get-Command 'curl.exe' -ErrorAction SilentlyContinue
    $previousValidationCallback = $null

    try {
        if ($curlExe) {
            $curlArgs = @('--silent', '--show-error', '--max-time', '5', '--output', 'NUL')
            if ($isHttps) {
                $curlArgs += '--insecure'
            }
            $curlArgs += $Url
            & $curlExe.Source @curlArgs | Out-Null
            return ($LASTEXITCODE -eq 0)
        }

        if ($isHttps) {
            $previousValidationCallback = [System.Net.ServicePointManager]::ServerCertificateValidationCallback
            [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
        }

        Invoke-WebRequest -Uri $Url -Method Get -UseBasicParsing -TimeoutSec 5 | Out-Null
        return $true
    }
    catch {
        if ($_.Exception -and $_.Exception.Response) {
            return $true
        }
        return $false
    }
    finally {
        if ($isHttps -and $previousValidationCallback -ne $null) {
            [System.Net.ServicePointManager]::ServerCertificateValidationCallback = $previousValidationCallback
        }
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

$backendTlsEnabledForUrls = $false
$backendTlsAdhocForRun = $true
$backendTlsCertFileForRun = ''
$backendTlsKeyFileForRun = ''

if ($backendConfig -and $backendConfig.tls -and $null -ne $backendConfig.tls.enabled) {
    $backendTlsEnabledForUrls = [bool]$backendConfig.tls.enabled
}
if ($backendConfig -and $backendConfig.tls -and $null -ne $backendConfig.tls.adhoc) {
    $backendTlsAdhocForRun = [bool]$backendConfig.tls.adhoc
}
if ($backendConfig -and $backendConfig.tls -and $backendConfig.tls.certFile) {
    $backendTlsCertFileForRun = [string]$backendConfig.tls.certFile
}
if ($backendConfig -and $backendConfig.tls -and $backendConfig.tls.keyFile) {
    $backendTlsKeyFileForRun = [string]$backendConfig.tls.keyFile
}

$frontendTlsEnabledForUrls = $false
$frontendTlsCertFileForRun = ''
$frontendTlsKeyFileForRun = ''
if ($frontendConfig -and $frontendConfig.tls -and $null -ne $frontendConfig.tls.enabled) {
    $frontendTlsEnabledForUrls = [bool]$frontendConfig.tls.enabled
}
if ($frontendConfig -and $frontendConfig.tls -and $frontendConfig.tls.certFile) {
    $frontendTlsCertFileForRun = [string]$frontendConfig.tls.certFile
}
if ($frontendConfig -and $frontendConfig.tls -and $frontendConfig.tls.keyFile) {
    $frontendTlsKeyFileForRun = [string]$frontendConfig.tls.keyFile
}

if ($TlsOff) {
    $backendTlsEnabledForUrls = $false
    $frontendTlsEnabledForUrls = $false
}
if ($BackendTlsOff) {
    $backendTlsEnabledForUrls = $false
}
if ($FrontendTlsOff) {
    $frontendTlsEnabledForUrls = $false
}

if ($UseBackendCertFiles) {
    $backendTlsEnabledForUrls = $true
    $backendTlsAdhocForRun = $false
    if ($BackendCertFile) {
        $backendTlsCertFileForRun = $BackendCertFile
    }
    if ($BackendKeyFile) {
        $backendTlsKeyFileForRun = $BackendKeyFile
    }
}

$hasTlsSwitchOverride = $TlsOff -or $BackendTlsOff -or $FrontendTlsOff -or $UseBackendCertFiles

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
    if (-not $hasTlsSwitchOverride -and $backendConfig -and $backendConfig.server -and $backendConfig.server.url) {
        $BackendUrl = "$(($backendConfig.server.url).TrimEnd('/'))/members"
    }
    else {
        $backendProtocol = if ($backendTlsEnabledForUrls) { 'https' } else { 'http' }
        $BackendUrl = "${backendProtocol}://${BindIp}:$BackendPort/members"
    }
}
if (-not $FrontendUrl) {
    if (-not $hasTlsSwitchOverride -and $frontendConfig -and $frontendConfig.server -and $frontendConfig.server.url) {
        $FrontendUrl = "$(($frontendConfig.server.url).TrimEnd('/'))/"
    }
    else {
        $frontendProtocol = if ($frontendTlsEnabledForUrls) { 'https' } else { 'http' }
        $FrontendUrl = "${frontendProtocol}://${BindIp}:$FrontendPort/"
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

$backendSslContextPy = 'None'
$backendTlsEnabled = $false
$backendTlsAdhoc = $true
$backendTlsCertFile = ''
$backendTlsKeyFile = ''

$backendTlsEnabled = $backendTlsEnabledForUrls
$backendTlsAdhoc = $backendTlsAdhocForRun
$backendTlsCertFile = $backendTlsCertFileForRun
$backendTlsKeyFile = $backendTlsKeyFileForRun

if ($backendTlsEnabled) {
    if ($backendTlsAdhoc) {
        $backendSslContextPy = "'adhoc'"
    }
    elseif ($backendTlsCertFile -and $backendTlsKeyFile) {
        $certPath = if ([System.IO.Path]::IsPathRooted($backendTlsCertFile)) { $backendTlsCertFile } else { Join-Path $backendDir $backendTlsCertFile }
        $keyPath = if ([System.IO.Path]::IsPathRooted($backendTlsKeyFile)) { $backendTlsKeyFile } else { Join-Path $backendDir $backendTlsKeyFile }
        $certPath = [System.IO.Path]::GetFullPath($certPath)
        $keyPath = [System.IO.Path]::GetFullPath($keyPath)

        if (-not (Test-Path $certPath)) {
            throw "Backend TLS certificate not found: $certPath"
        }
        if (-not (Test-Path $keyPath)) {
            throw "Backend TLS key not found: $keyPath"
        }

        $certPathPy = $certPath.Replace('\', '/').Replace("'", "\\'")
        $keyPathPy = $keyPath.Replace('\', '/').Replace("'", "\\'")
        $backendSslContextPy = "('$certPathPy', '$keyPathPy')"
    }
    else {
        throw 'Backend TLS is enabled but tls.certFile/tls.keyFile are not configured and tls.adhoc is false.'
    }
}

$backendRunCode = "import app; app.configure_logging(); app.app.run(host='$BindIp', port=$BackendPort, debug=$debugPyValue, use_reloader=$reloaderPyValue, ssl_context=$backendSslContextPy)"
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

$configuredBackendUrl = if ($backendTlsEnabled) { "https://${BindIp}:$BackendPort" } else { "http://${BindIp}:$BackendPort" }
if (-not $hasTlsSwitchOverride -and $frontendConfig -and $frontendConfig.api -and $frontendConfig.api.backendUrl) {
    $configuredBackendUrl = [string]$frontendConfig.api.backendUrl
}
$env:VUE_APP_BACKEND_URL = $configuredBackendUrl
$env:VUE_APP_TLS_ENABLED = if ($frontendTlsEnabledForUrls) { 'true' } else { 'false' }
$env:VUE_APP_TLS_CERT_FILE = $frontendTlsCertFileForRun
$env:VUE_APP_TLS_KEY_FILE = $frontendTlsKeyFileForRun
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
