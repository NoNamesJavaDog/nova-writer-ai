# Simplified deployment - uses existing build if available
# Usage: .\deploy-simple.ps1

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

# Step 1: Build frontend (if needed)
Write-Host "[1/6] Checking frontend build..." -ForegroundColor Yellow
Set-Location $FRONTEND_DIR

$needBuild = $false
if (-not (Test-Path "dist")) {
    Write-Host "  dist directory not found, need to build" -ForegroundColor Yellow
    $needBuild = $true
} else {
    $distFiles = Get-ChildItem -Path "dist" -Recurse -File
    if ($distFiles.Count -eq 0) {
        Write-Host "  dist directory is empty, need to build" -ForegroundColor Yellow
        $needBuild = $true
    }
}

if ($needBuild) {
    $npmPath = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npmPath) {
        Write-Host "Error: npm not found. Please install Node.js or use existing dist folder" -ForegroundColor Red
        Write-Host "  Download: https://nodejs.org/" -ForegroundColor Yellow
        Set-Location ..
        exit 1
    }
    
    $env:VITE_API_BASE_URL = "http://66.154.108.62"
    
    if (-not (Test-Path "node_modules")) {
        Write-Host "  Installing dependencies..." -ForegroundColor Gray
        npm install
    }
    
    Write-Host "  Building application..." -ForegroundColor Gray
    npm run build
}

if (-not (Test-Path "dist")) {
    Write-Host "Error: Frontend build failed or dist not found" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host "OK: Frontend ready" -ForegroundColor Green
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

Write-Host "OK: Backend packaged" -ForegroundColor Green

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

Write-Host "OK: Frontend packaged" -ForegroundColor Green

# Step 4: Upload to server
Write-Host ""
Write-Host "[4/6] Uploading to server..." -ForegroundColor Yellow
scp -P $SERVER_PORT $BACKEND_PACKAGE "${SERVER}:/tmp/"
scp -P $SERVER_PORT $FRONTEND_PACKAGE "${SERVER}:/tmp/"

Write-Host "OK: Upload completed" -ForegroundColor Green

# Step 5: Deploy on server
Write-Host ""
Write-Host "[5/6] Deploying on server..." -ForegroundColor Yellow

$deployScriptFile = "deploy-remote.sh"
if (-not (Test-Path $deployScriptFile)) {
    Write-Host "Error: $deployScriptFile not found" -ForegroundColor Red
    exit 1
}

scp -P $SERVER_PORT $deployScriptFile "${SERVER}:/tmp/"
$remoteScript = "/tmp/$deployScriptFile"

$cmd1 = "chmod +x $remoteScript"
$cmd2 = "bash $remoteScript"
$cmd3 = "rm -f $remoteScript"
ssh -p $SERVER_PORT $SERVER "$cmd1; $cmd2; $cmd3"

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
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Configure database and .env file on server" -ForegroundColor White
Write-Host "2. Initialize database: ssh $SERVER -p $SERVER_PORT" -ForegroundColor White
Write-Host "3. Start service: systemctl start novawrite-backend" -ForegroundColor White
Write-Host ""
Write-Host "Access: http://66.154.108.62" -ForegroundColor Cyan
Write-Host ""


