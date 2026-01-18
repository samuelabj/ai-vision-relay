$ErrorActionPreference = "Stop"

Write-Host "=== AI-Vision-Relay Setup ===" -ForegroundColor Cyan

# 1. Check for Python
try {
    $pythonOutput = python --version 2>&1 | Out-String
    Write-Host "Found Python: $pythonOutput" -ForegroundColor Green
    
    # Parse version (using -match on a single string ensures $matches is populated)
    # The regex needs to handle potential whitespace trimming
    if ($pythonOutput.Trim() -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        
        # Enforce strict compatibility: 3.10 <= Version < 3.13
        if ($major -eq 3 -and ($minor -ge 10 -and $minor -le 12)) {
            Write-Host "Version compatibility verified." -ForegroundColor Green
        }
        else {
            Write-Error "Unsupported Python version: $major.$minor"
            Write-Error "SpeciesNet requires Python 3.10, 3.11, or 3.12."
            Write-Error "Python 3.13+ is NOT yet supported."
            exit 1
        }
    }
    else {
        Write-Warning "Could not parse Python version from output: '$pythonOutput'"
        Write-Warning "Proceeding with caution..."
    }
}
catch {
    Write-Error "Python is not installed or not in PATH. Please install Python 3.10, 3.11, or 3.12 before running setup."
    exit 1
}

# 2. Check/Create Virtual Environment
$venvPath = Join-Path $PSScriptRoot "..\.venv"
if (Test-Path $venvPath) {
    Write-Host "Virtual environment already exists at $venvPath"
}
else {
    Write-Host "Creating virtual environment..."
    python -m venv $venvPath
    Write-Host "Virtual environment created." -ForegroundColor Green
}

# 3. Install Dependencies
Write-Host "Installing dependencies..."
$pipExec = Join-Path $venvPath "Scripts\pip.exe"
if (-not (Test-Path $pipExec)) {
    Write-Error "pip not found in venv. Creation might have failed."
    exit 1
}

$reqFile = Join-Path $PSScriptRoot "..\requirements.txt"
& $pipExec install --upgrade pip
& $pipExec install -r $reqFile

Write-Host "Dependencies installed successfully." -ForegroundColor Green

# 3b. Force install PyTorch with CUDA support (Fix for Windows)
Write-Host "Enforcing PyTorch CUDA installation..." -ForegroundColor Cyan
& $pipExec install torch torchvision --upgrade --force-reinstall --index-url https://download.pytorch.org/whl/cu118

# 4. Verify GPU Availability
# 4. Verify GPU Availability
Write-Host "Verifying GPU availability..."
$pythonExec = Join-Path $venvPath "Scripts\python.exe"
& $pythonExec -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to verify CUDA availability."
}

# 5. Prompt for Service Installation
$response = Read-Host "Do you want to install/update the Windows Service now? (y/n)"
if ($response -eq 'y') {
    $installScript = Join-Path $PSScriptRoot "install_service.ps1"
    Write-Host "Running service installer..."
    & $installScript
}
else {
    Write-Host "Service installation skipped."
    Write-Host "You can run 'scripts\install_service.ps1' later to install the service." -ForegroundColor Yellow
}

Write-Host "Setup complete!" -ForegroundColor Cyan
