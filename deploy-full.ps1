# Complete deployment script
# Usage: .\deploy-full.ps1

$ErrorActionPreference = "Continue"

$SERVER = "root@66.154.108.62"
$SERVER_PORT = "22"
$REMOTE_APP_DIR = "/opt/novawrite-ai"
$REMOTE_FRONTEND_DIR = "/var/www/novawrite-ai"
$BACKEND_DIR = "backend"
$FRONTEND_DIR = "novawrite-ai---professional-novel-assistant"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NovaWrite AI Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check directories
if (-not (Test-Path $BACKEND_DIR) -or -not (Test-Path $FRONTEND_DIR)) {
    Write-Host "Error: Please run from project root directory" -ForegroundColor Red
    exit 1
}

# Step 1: Build frontend
Write-Host "[1/6] Building frontend..." -ForegroundColor Yellow
Set-Location $FRONTEND_DIR

# Check npm
$npmPath = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npmPath) {
    Write-Host "Error: npm not found. Please install Node.js" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# Set environment variable
$env:VITE_API_BASE_URL = "http://66.154.108.62"

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "  Installing dependencies..." -ForegroundColor Gray
    npm install
}

# Build
Write-Host "  Building application..." -ForegroundColor Gray
npm run build

if (-not (Test-Path "dist")) {
    Write-Host "Error: Frontend build failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host "OK: Frontend build completed" -ForegroundColor Green
Set-Location ..

# Step 2: Package backend
Write-Host ""
Write-Host "[2/6] Packaging backend..." -ForegroundColor Yellow
$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$BACKEND_PACKAGE = "backend-$TIMESTAMP.tar.gz"

Set-Location $BACKEND_DIR
tar -czf "../$BACKEND_PACKAGE" --exclude=__pycache__ --exclude=*.pyc --exclude=.env --exclude=.git * 2>$null
Set-Location ..

if (-not (Test-Path $BACKEND_PACKAGE)) {
    Write-Host "Error: Backend packaging failed" -ForegroundColor Red
    exit 1
}

Write-Host "OK: Backend packaged: $BACKEND_PACKAGE" -ForegroundColor Green

# Step 3: Package frontend
Write-Host ""
Write-Host "[3/6] Packaging frontend..." -ForegroundColor Yellow
$FRONTEND_PACKAGE = "frontend-$TIMESTAMP.tar.gz"

Set-Location "$FRONTEND_DIR\dist"
tar -czf "..\..\$FRONTEND_PACKAGE" * 2>$null
Set-Location ..\..

if (-not (Test-Path $FRONTEND_PACKAGE)) {
    Write-Host "Error: Frontend packaging failed" -ForegroundColor Red
    exit 1
}

Write-Host "OK: Frontend packaged: $FRONTEND_PACKAGE" -ForegroundColor Green

# Step 4: Upload to server
Write-Host ""
Write-Host "[4/6] Uploading to server..." -ForegroundColor Yellow
scp -P $SERVER_PORT $BACKEND_PACKAGE "${SERVER}:/tmp/"
scp -P $SERVER_PORT $FRONTEND_PACKAGE "${SERVER}:/tmp/"

Write-Host "OK: Upload completed" -ForegroundColor Green

# Step 5: Deploy on server
Write-Host ""
Write-Host "[5/6] Deploying on server..." -ForegroundColor Yellow

# Upload and execute remote deployment script
$deployScriptFile = "deploy-remote.sh"
if (-not (Test-Path $deployScriptFile)) {
    Write-Host "Error: $deployScriptFile not found" -ForegroundColor Red
    exit 1
}

scp -P $SERVER_PORT $deployScriptFile "${SERVER}:/tmp/"
$remoteScript = "/tmp/$deployScriptFile"

# Execute deployment script
$sshCmd1 = "chmod +x $remoteScript"
$sshCmd2 = "bash $remoteScript"
$sshCmd3 = "rm -f $remoteScript"
ssh -p $SERVER_PORT $SERVER "$sshCmd1; $sshCmd2; $sshCmd3"

Write-Host "OK: Server deployment completed" -ForegroundColor Green

# Step 6: Cleanup
Write-Host ""
Write-Host "[6/6] Cleaning up..." -ForegroundColor Yellow
Remove-Item -Force $BACKEND_PACKAGE -ErrorAction SilentlyContinue
Remove-Item -Force $FRONTEND_PACKAGE -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deployment Completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Cyan
Write-Host "  Frontend: http://66.154.108.62" -ForegroundColor White
Write-Host "  API: http://66.154.108.62/api" -ForegroundColor White
Write-Host "  API Docs: http://66.154.108.62/api/docs" -ForegroundColor White
Write-Host ""
Write-Host "Important:" -ForegroundColor Yellow
Write-Host "1. Ensure .env file is configured on server" -ForegroundColor White
Write-Host "2. Initialize database if first deployment" -ForegroundColor White
Write-Host "3. Start backend service: systemctl start novawrite-backend" -ForegroundColor White
Write-Host ""


