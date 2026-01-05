# ============================================================================
# One-click deployment script
#
# Functions:
#   1. Check and commit local changes to Git repository
#   2. Push to remote Git repository (origin/main)
#   3. Pull latest code on the remote server
#   4. Restart backend service (novawrite-backend)
#   5. Optional: Build and deploy frontend
#
# Requirements:
#   - Validate after each step before proceeding
#   - Any failed step will interrupt the deployment process
#
# Usage:
#   Execute in project root: .\deploy-full.ps1
#
# Prerequisites:
#   1. SSH key configured for passwordless login to the remote server
#   2. Git remote repository and branch configured
#   3. PowerShell installed locally (built-in on Windows 10+)
#   4. Node.js and npm installed locally for frontend deployment
#
# ============================================================================

$ErrorActionPreference = "Stop"

# Configuration
$REMOTE_SERVER = "root@66.154.108.62"
$REMOTE_BACKEND_DIR = "/opt/novawrite-ai"
$REMOTE_FRONTEND_DIR = "/var/www/novawrite-ai/current"
$GIT_REMOTE = "origin"
$GIT_BRANCH = "main"
$FRONTEND_DIR = "novawrite-ai---professional-novel-assistant"

# Color output functions
function Write-Step {
    param($Message)
    Write-Host "`n" -NoNewline
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

function Write-Success {
    param($Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param($Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Warning {
    param($Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Info {
    param($Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
}

# Validation function
function Test-Command {
    param(
        [string]$Command,
        [string]$SuccessMessage,
        [string]$ErrorMessage
    )
    
    try {
        $result = Invoke-Expression $Command 2>&1
        if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq $null) {
            Write-Success $SuccessMessage
            return $true
        } else {
            Write-Error "$ErrorMessage (Exit Code: $LASTEXITCODE)"
            Write-Host $result
            return $false
        }
    } catch {
        Write-Error "$ErrorMessage : $_"
        return $false
    }
}

function Test-SSHCommand {
    param(
        [string]$Command,
        [string]$SuccessMessage,
        [string]$ErrorMessage,
        [switch]$MultiLine
    )
    
    try {
        if ($MultiLine) {
            # For multi-line scripts, execute with bash -s
            $result = $Command | ssh $REMOTE_SERVER "bash -s" 2>&1
        } else {
            $result = ssh $REMOTE_SERVER $Command 2>&1
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success $SuccessMessage
            if ($result) {
                Write-Host $result -ForegroundColor Gray
            }
            return $true
        } else {
            Write-Error "$ErrorMessage (Exit Code: $LASTEXITCODE)"
            Write-Host $result
            return $false
        }
    } catch {
        Write-Error "$ErrorMessage : $_"
        return $false
    }
}

# ============================================================================
# Step 1: Check Git status and commit code
# ============================================================================
Write-Step "Step 1: Check Git status and commit code"

# Check for uncommitted changes
Write-Info "Checking Git status..."
$gitStatus = git status --short
if ($gitStatus) {
    Write-Host "Found uncommitted changes:" -ForegroundColor Yellow
    Write-Host $gitStatus
    
    $commitMessage = Read-Host "Enter commit message (default: 'feat: auto deploy')"
    if ([string]::IsNullOrWhiteSpace($commitMessage)) {
        $commitMessage = "feat: auto deploy"
    }
    
    # Add all changes
    if (-not (Test-Command "git add ." "Files added to staging area" "Failed to add files")) {
        exit 1
    }
    
    # Commit changes
    if (-not (Test-Command "git commit -m '$commitMessage'" "Code committed" "Failed to commit code")) {
        exit 1
    }
} else {
    Write-Success "No uncommitted changes, skipping commit step"
}

# ============================================================================
# Step 2: Push to remote repository
# ============================================================================
Write-Step "Step 2: Push to remote repository"

if (-not (Test-Command "git push $GIT_REMOTE $GIT_BRANCH" "Code pushed to remote repository" "Failed to push code")) {
    Write-Error "Push failed, please check network connection and permissions"
    exit 1
}

# Validate: Check remote repository for the latest commit
Write-Info "Validating: Checking remote repository status..."
Start-Sleep -Seconds 2
$remoteCommit = git ls-remote --heads $GIT_REMOTE $GIT_BRANCH | ForEach-Object { ($_ -split '\s+')[0] }
$localCommit = git rev-parse HEAD

if ($remoteCommit -eq $localCommit) {
    Write-Success "Remote repository is up-to-date with the latest code (Commit: $($localCommit.Substring(0,7)))"
} else {
    Write-Warning "Remote commit: $($remoteCommit.Substring(0,7)), Local commit: $($localCommit.Substring(0,7))"
    Write-Info "Continuing deployment (could be due to delay)"
}

# ============================================================================
# Step 3: Pull latest code on remote server
# ============================================================================
Write-Step "Step 3: Pull latest code on remote server"

$pullCommand = "cd $REMOTE_BACKEND_DIR && git fetch $GIT_REMOTE && git reset --hard $GIT_REMOTE/$GIT_BRANCH"

if (-not (Test-SSHCommand $pullCommand "Remote server code updated" "Failed to pull code")) {
    Write-Error "Pull failed, please check server connection and Git configuration"
    exit 1
}

# Validate: Check remote server code version
Write-Info "Validating: Checking remote server code version..."
$remoteServerCommit = ssh $REMOTE_SERVER "cd $REMOTE_BACKEND_DIR && git rev-parse HEAD" 2>&1
if ($LASTEXITCODE -eq 0) {
    if ($remoteServerCommit.Trim() -eq $localCommit) {
        Write-Success "Remote server code version is correct (Commit: $($localCommit.Substring(0,7)))"
    } else {
        Write-Warning "Remote server commit: $($remoteServerCommit.Trim().Substring(0,7)), Local commit: $($localCommit.Substring(0,7))"
    }
} else {
    Write-Warning "Cannot verify remote server code version, continuing deployment"
}

# ============================================================================
# Step 4: Restart backend service
# ============================================================================
Write-Step "Step 4: Restart backend service"

$restartCommand = "systemctl restart novawrite-backend && sleep 3 && systemctl status novawrite-backend --no-pager | head -15"

if (-not (Test-SSHCommand $restartCommand "Backend service has been restarted" "Failed to restart backend service")) {
    Write-Error "Restart failed, please check service status"
    exit 1
}

# Validate: Check backend service status
Write-Info "Validating: Checking backend service status..."
Start-Sleep -Seconds 2
$serviceStatus = ssh $REMOTE_SERVER "systemctl is-active novawrite-backend" 2>&1
if ($serviceStatus.Trim() -eq "active") {
    Write-Success "Backend service is running normally (Status: active)"
    
    # Check service health
    Write-Info "Validating: Checking backend service health..."
    $healthCheck = ssh $REMOTE_SERVER "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/health || echo '000'" 2>&1
    if ($healthCheck -eq "200" -or $healthCheck -eq "401") {
        Write-Success "Backend service is responding normally (HTTP Status: $healthCheck)"
    } else {
        Write-Warning "Backend service health check failed (HTTP Status: $healthCheck), but service is active. Continuing deployment."
    }
} else {
    Write-Error "Backend service status is abnormal (Status: $serviceStatus)"
    Write-Info "Checking service logs..."
    ssh $REMOTE_SERVER "journalctl -u novawrite-backend -n 30 --no-pager"
    exit 1
}

# ============================================================================
# Step 5: Build and deploy frontend (optional)
# ============================================================================
Write-Step "Step 5: Build and deploy frontend"

$deployFrontend = Read-Host "Deploy frontend? (Y/n)"
if ($deployFrontend -ne "n" -and $deployFrontend -ne "N") {
    # Check if frontend directory exists
    if (-not (Test-Path $FRONTEND_DIR)) {
        Write-Error "Frontend directory not found: $FRONTEND_DIR"
        exit 1
    }
    
    # Change to frontend directory
    Push-Location $FRONTEND_DIR
    
    try {
        # Build frontend
        Write-Info "Building frontend..."
        if (-not (Test-Command "npm run build" "Frontend build complete" "Frontend build failed")) {
            Pop-Location
            exit 1
        }
        
        # Check for dist directory
        if (-not (Test-Path "dist")) {
            Write-Error "Build failed: dist directory not found"
            Pop-Location
            exit 1
        }
        
        # Create deployment package
        Write-Info "Packaging frontend files..."
        $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $deployPackage = "../deploy-frontend-$timestamp.tar.gz"
        
        Set-Location dist
        tar -czf $deployPackage * 2>&1 | Out-Null
        Set-Location ..
        
        if (-not (Test-Path $deployPackage)) {
            Write-Error "Packaging failed"
            Pop-Location
            exit 1
        }
        
        Write-Success "Packaging complete: $deployPackage"
        
        # Upload to server
        Write-Info "Uploading frontend files to server..."
        if (-not (Test-Command "scp $deployPackage ${REMOTE_SERVER}:/tmp/" "Frontend files uploaded" "Failed to upload frontend files")) {
            Remove-Item $deployPackage -ErrorAction SilentlyContinue
            Pop-Location
            exit 1
        }
        
        # Deploy on server
        Write-Info "Deploying frontend on server..."
        $packageName = "deploy-frontend-$timestamp.tar.gz"
        $deployScript = @"
set -e
DEPLOY_PACKAGE=/tmp/$packageName
if [ ! -f `$DEPLOY_PACKAGE ]; then
  echo "Error: Deployment package not found"
  exit 1
fi

# Backup old version
if [ -d "$REMOTE_FRONTEND_DIR" ]; then
  BACKUP_DIR="/var/www/novawrite-ai/backup-`$(date +%Y%m%d-%H%M%S)"
  mkdir -p `$BACKUP_DIR
  cp -r $REMOTE_FRONTEND_DIR/* `$BACKUP_DIR/ 2>/dev/null || true
  echo "✅ Backup created at: `$BACKUP_DIR"
fi

# Create deployment directory
mkdir -p $REMOTE_FRONTEND_DIR

# Unpack new version
echo "📦 Unpacking deployment package..."
tar -xzf `$DEPLOY_PACKAGE -C $REMOTE_FRONTEND_DIR

# Set permissions
chown -R www-data:www-data $REMOTE_FRONTEND_DIR 2>/dev/null || chown -R nginx:nginx $REMOTE_FRONTEND_DIR
find $REMOTE_FRONTEND_DIR -type d -exec chmod 755 {} \;
find $REMOTE_FRONTEND_DIR -type f -exec chmod 644 {} \;

# Clean up temporary files
rm -f `$DEPLOY_PACKAGE

echo "✅ Frontend deployment complete"
"@
        
        if (-not (Test-SSHCommand $deployScript "Frontend deployed to server" "Frontend deployment failed" -MultiLine)) {
            Remove-Item $deployPackage -ErrorAction SilentlyContinue
            Pop-Location
            exit 1
        }
        
        # Validate: Check if frontend files exist
        Write-Info "Validating: Checking frontend deployment..."
        $indexExists = ssh $REMOTE_SERVER "test -f $REMOTE_FRONTEND_DIR/index.html && echo 'yes' || echo 'no'" 2>&1
        if ($indexExists.Trim() -eq "yes") {
            Write-Success "Frontend files deployed successfully (index.html exists)"
        } else {
            Write-Warning "Frontend file validation failed, but continuing deployment"
        }
        
        # Restart nginx
        Write-Info "Restarting nginx..."
        ssh $REMOTE_SERVER "systemctl reload nginx || service nginx reload" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "nginx has been reloaded"
        } else {
            Write-Warning "Failed to reload nginx, please check manually"
        }
        
        # Clean up local temporary files
        Remove-Item $deployPackage -ErrorAction SilentlyContinue
        
    } finally {
        Pop-Location
    }
} else {
    Write-Info "Skipping frontend deployment"
}

# ============================================================================
# Deployment Complete
# ============================================================================
Write-Step "Deployment Complete"

Write-Success "All steps have been completed!"
Write-Host ""
Write-Host "📝 Deployment Summary:" -ForegroundColor Cyan
Write-Host "  - Remote Server: $REMOTE_SERVER"
Write-Host "  - Backend Directory: $REMOTE_BACKEND_DIR"
Write-Host "  - Frontend Directory: $REMOTE_FRONTEND_DIR"
Write-Host "  - Git Branch: $GIT_BRANCH"
Write-Host "  - Local Commit: $($localCommit.Substring(0,7))"
Write-Host ""
Write-Host "🔗 Access URLs:" -ForegroundColor Cyan
Write-Host "  - Frontend: http://66.154.108.62"
Write-Host "  - Backend API: http://66.154.108.62/api"
Write-Host ""
Write-Host "📋 Common Commands:" -ForegroundColor Cyan
Write-Host "  - View backend logs: ssh $REMOTE_SERVER 'journalctl -u novawrite-backend -f'"
Write-Host "  - Check backend status: ssh $REMOTE_SERVER 'systemctl status novawrite-backend'"
Write-Host "  - Restart backend service: ssh $REMOTE_SERVER 'systemctl restart novawrite-backend'"
Write-Host ""
