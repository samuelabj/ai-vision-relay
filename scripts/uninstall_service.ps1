# SpeciesNet AI Proxy Service Uninstaller

$ServiceName = "BlueIrisAiProxy"

# Check for NSSM
$NssmPath = Join-Path $PSScriptRoot "nssm.exe"
if (-not (Test-Path $NssmPath)) {
    # Fallback to checking PATH
    if (Get-Command "nssm.exe" -ErrorAction SilentlyContinue) {
        $NssmPath = "nssm.exe"
    }
    else {
        Write-Error "NSSM.exe not found in scripts folder or PATH."
        exit 1
    }
}

Write-Host "Stopping $ServiceName Service..."
& $NssmPath stop $ServiceName

Write-Host "Removing $ServiceName Service..."
& $NssmPath remove $ServiceName confirm

Write-Host "Service removed successfully."
