# Run complete setup on server
# Usage: .\run-complete-setup.ps1

$SERVER = "root@66.154.108.62"
$SERVER_PORT = "22"
$SETUP_SCRIPT = "complete-setup.sh"

Write-Host "Running complete setup on server..." -ForegroundColor Green

# Check if script exists
if (-not (Test-Path $SETUP_SCRIPT)) {
    Write-Host "Error: $SETUP_SCRIPT not found" -ForegroundColor Red
    exit 1
}

# Read script content and convert line endings
$scriptContent = Get-Content -Path $SETUP_SCRIPT -Raw -Encoding UTF8
$scriptContent = $scriptContent -replace "`r`n", "`n" -replace "`r", "`n"

# Upload and execute
Write-Host "Uploading setup script..." -ForegroundColor Yellow
$scriptContent | ssh -p $SERVER_PORT $SERVER "cat > /tmp/complete-setup.sh && chmod +x /tmp/complete-setup.sh && bash /tmp/complete-setup.sh && rm -f /tmp/complete-setup.sh"

Write-Host ""
Write-Host "Setup completed!" -ForegroundColor Green


