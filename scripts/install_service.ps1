# SpeciesNet AI Proxy Service Installer

# Check for Administrator privileges
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "You do not have Administrator rights to this machine. Log on as an Administrator and re-run this script."
    exit 1
}

$SERVICE_NAME = "AiVisionRelay"
$PYTHON_EXEC = Resolve-Path "$PSScriptRoot\..\.venv\Scripts\python.exe" | Select-Object -ExpandProperty Path
$APP_PATH = Resolve-Path "$PSScriptRoot\..\server.py" | Select-Object -ExpandProperty Path
$APP_DIR = Resolve-Path "$PSScriptRoot\.." | Select-Object -ExpandProperty Path

Write-Host "Installing Service: $SERVICE_NAME"
Write-Host "Python Executable: $PYTHON_EXEC"
Write-Host "Application Path: $APP_PATH"
Write-Host "Application Directory: $APP_DIR"

if (-not (Test-Path $PYTHON_EXEC)) {
    Write-Error "Python executable not found. Please create the venv first."
    exit 1
}

# Check for admin
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "You must run this script as Administrator to install the service."
    exit 1
}

# NSSM Install
# Ensure nssm is in path or provide full path. Assuming nssm is available or in scripts folder.
$NSSM = "$PSScriptRoot\nssm.exe"
if (-not (Test-Path $NSSM)) {
    # Fallback to system path nssm
    $NSSM = "nssm"
}

# Stop if exists
& $NSSM stop $SERVICE_NAME
& $NSSM remove $SERVICE_NAME confirm

# Install
# Command: python.exe server.py
# Use quotes around paths to handle spaces
& $NSSM install $SERVICE_NAME "$PYTHON_EXEC" "$APP_PATH"
& $NSSM set $SERVICE_NAME AppDirectory "$APP_DIR"
& $NSSM set $SERVICE_NAME Description "AI Vision Relay - Smart Proxy for Blue Iris"
& $NSSM set $SERVICE_NAME AppStdout "$APP_DIR\service.log"
& $NSSM set $SERVICE_NAME AppStderr "$APP_DIR\service.log"
& $NSSM set $SERVICE_NAME AppRotateFiles 1
& $NSSM set $SERVICE_NAME AppRotateOnline 1
& $NSSM set $SERVICE_NAME AppRotateSeconds 86400
& $NSSM set $SERVICE_NAME AppRotateBytes 5242880

Write-Host "Service installed. Starting..."
& $NSSM start $SERVICE_NAME
Write-Host "Done. Check service.log for output."
Write-Host "--- Service Configuration ---"
& $NSSM get $SERVICE_NAME Application
& $NSSM get $SERVICE_NAME AppParameters
& $NSSM get $SERVICE_NAME AppDirectory
Write-Host "-----------------------------"
