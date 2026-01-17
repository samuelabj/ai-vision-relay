# SpeciesNet AI Proxy Service Installer

$ServiceName = "BlueIrisAiProxy"
$PythonPath = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe" # Use local venv
$ScriptPath = Join-Path $PSScriptRoot "..\server.py"
$AppDirectory = Join-Path $PSScriptRoot ".."

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

Write-Host "Installing $ServiceName Service..."
& $NssmPath install $ServiceName $PythonPath "\"$ScriptPath\""
& $NssmPath set $ServiceName AppDirectory $AppDirectory
& $NssmPath set $ServiceName Description "SpeciesNet AI Proxy for Blue Iris"
& $NssmPath set $ServiceName AppStdout ("$AppDirectory\service.log")
& $NssmPath set $ServiceName AppStderr ("$AppDirectory\service.log")
& $NssmPath set $ServiceName AppRotateFiles 1
& $NssmPath set $ServiceName AppRotateOnline 1
& $NssmPath set $ServiceName AppRotateSeconds 86400
& $NssmPath set $ServiceName AppRotateBytes 5242880

Write-Host "Service installed successfully."
Write-Host "You can start it with: nssm start $ServiceName"
