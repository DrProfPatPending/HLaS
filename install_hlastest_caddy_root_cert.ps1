param(
    [string]$CertPath = ".\hlastest-caddy-root.crt",
    [ValidateSet('LocalMachine', 'CurrentUser')]
    [string]$StoreScope = 'LocalMachine',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

function Test-IsAdministrator {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Path -LiteralPath $CertPath)) {
    throw "Certificate file not found: $CertPath"
}

if ($StoreScope -eq 'LocalMachine' -and -not (Test-IsAdministrator)) {
    throw "LocalMachine store requires Administrator PowerShell. Re-run as admin or use -StoreScope CurrentUser."
}

$resolvedCertPath = (Resolve-Path -LiteralPath $CertPath).Path
$certificate = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($resolvedCertPath)

$targetStorePath = "Cert:\$StoreScope\Root"

Write-Host "Certificate subject: $($certificate.Subject)"
Write-Host "Certificate thumbprint: $($certificate.Thumbprint)"
Write-Host "Target store: $targetStorePath"

$existing = Get-ChildItem -Path $targetStorePath | Where-Object { $_.Thumbprint -eq $certificate.Thumbprint }
if ($existing -and -not $Force) {
    Write-Host "Certificate already trusted in $targetStorePath"
    exit 0
}

if ($existing -and $Force) {
    $existing | Remove-Item -Force
}

Import-Certificate -FilePath $resolvedCertPath -CertStoreLocation $targetStorePath | Out-Null

$verified = Get-ChildItem -Path $targetStorePath | Where-Object { $_.Thumbprint -eq $certificate.Thumbprint }
if (-not $verified) {
    throw "Import command completed but certificate not found in target store."
}

Write-Host ""
Write-Host "Certificate installed successfully."
Write-Host "Thumbprint: $($certificate.Thumbprint)"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1) Fully close and reopen Microsoft Edge."
Write-Host "2) Browse to https://hlastest/admin"
Write-Host "3) If warning persists, verify you are using the same host present in the cert (hlastest or server IP)."
