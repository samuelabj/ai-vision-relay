# SpeciesNet AI Proxy Service Uninstaller

$SERVICE_NAME = "AiVisionRelay"

# Check for admin
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "You must run this script as Administrator to uninstall the service."
    exit 1
}

# Check for NSSM
$NSSM = "$PSScriptRoot\nssm.exe"
if (-not (Test-Path $NSSM)) {
    $NSSM = "nssm"
}

Write-Host "Uninstalling Service: $SERVICE_NAME"
& $NSSM stop $SERVICE_NAME
& $NSSM remove $SERVICE_NAME confirm
Write-Host "Done."
