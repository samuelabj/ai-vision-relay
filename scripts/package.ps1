$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd-HHmm"
$packageName = "AiVisionRelay_Package_$timestamp"
$distDir = Join-Path $PSScriptRoot "..\dist"
$tempDir = Join-Path $distDir $packageName
$zipFile = Join-Path $distDir "$packageName.zip"

# Create clean dist directory
if (Test-Path $distDir) { Remove-Item $distDir -Recurse -Force }
New-Item -ItemType Directory -Path $tempDir | Out-Null

Write-Host "Boxing up AI-Vision-Relay..." -ForegroundColor Cyan

# Define items to copy (Root relative)
$filesToCopy = @(
    "src",
    "scripts",
    "server.py",
    "requirements.txt",
    "README.md",
    "README.md",
    ".env.example"
)

# Copy items
foreach ($item in $filesToCopy) {
    $sourcePath = Join-Path $PSScriptRoot "..\$item"
    if (Test-Path $sourcePath) {
        Write-Host "Copying $item..."
        Copy-Item -Path $sourcePath -Destination $tempDir -Recurse
    }
    else {
        Write-Warning "Item not found: $item (Skipping)"
    }
}

# Clean up unnecessary files (pycache, pyc, etc.) to keep package small
Write-Host "Cleaning up __pycache__ and *.pyc files..."
Get-ChildItem -Path $tempDir -Include "__pycache__" -Recurse -Directory -Force | Remove-Item -Recurse -Force
Get-ChildItem -Path $tempDir -Include "*.pyc", "*.pyo", "*.pyd" -Recurse -File -Force | Remove-Item -Force

Write-Host "Zipping package to $zipFile..."
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipFile

# Cleanup Temp
Remove-Item $tempDir -Recurse -Force

Write-Host "Package created successfully: $zipFile" -ForegroundColor Green
Write-Host "You can verify the contents and then copy this zip to your target machine."
