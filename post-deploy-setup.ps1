# Post-deployment setup script
# Usage: .\post-deploy-setup.ps1

$SERVER = "root@66.154.108.62"
$SERVER_PORT = "22"
$REMOTE_APP_DIR = "/opt/novawrite-ai"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Post-Deployment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This script will help you:" -ForegroundColor Yellow
Write-Host "1. Fix file permissions" -ForegroundColor White
Write-Host "2. Configure database" -ForegroundColor White
Write-Host "3. Initialize database" -ForegroundColor White
Write-Host "4. Start services" -ForegroundColor White
Write-Host ""

# Fix permissions
Write-Host "[1/4] Fixing file permissions..." -ForegroundColor Yellow
ssh -p $SERVER_PORT $SERVER @"
# Find the correct web server user
if id nginx &>/dev/null; then
  WEB_USER=nginx
elif id apache &>/dev/null; then
  WEB_USER=apache
elif id www-data &>/dev/null; then
  WEB_USER=www-data
else
  WEB_USER=root
fi

echo "Using web user: \$WEB_USER"

# Fix frontend permissions
if [ -d "/var/www/novawrite-ai/current" ]; then
  chown -R \$WEB_USER:\$WEB_USER /var/www/novawrite-ai/current
  chmod -R 755 /var/www/novawrite-ai/current
  echo "Frontend permissions fixed"
fi

# Fix backend permissions
if [ -d "/opt/novawrite-ai/backend" ]; then
  chown -R root:root /opt/novawrite-ai/backend
  chmod -R 755 /opt/novawrite-ai/backend
  echo "Backend permissions fixed"
fi
"@

Write-Host "OK: Permissions fixed" -ForegroundColor Green

# Check PostgreSQL
Write-Host ""
Write-Host "[2/4] Checking PostgreSQL..." -ForegroundColor Yellow
ssh -p $SERVER_PORT $SERVER @"
if systemctl is-active --quiet postgresql 2>/dev/null; then
  echo "PostgreSQL is running"
  sudo -u postgres psql -c "SELECT version();" 2>/dev/null && echo "PostgreSQL is accessible" || echo "PostgreSQL connection test failed"
else
  echo "PostgreSQL is not running, attempting to start..."
  systemctl start postgresql
  sleep 2
  systemctl status postgresql --no-pager -l | head -5
fi
"@

Write-Host ""
Write-Host "Please configure database manually:" -ForegroundColor Yellow
Write-Host "  ssh $SERVER -p $SERVER_PORT" -ForegroundColor White
Write-Host "  sudo -u postgres psql" -ForegroundColor Gray
Write-Host "  CREATE USER novawrite_user WITH PASSWORD 'your_password';" -ForegroundColor Gray
Write-Host "  CREATE DATABASE novawrite_ai OWNER novawrite_user;" -ForegroundColor Gray
Write-Host "  \q" -ForegroundColor Gray
Write-Host ""

# Configure .env
Write-Host "[3/4] Checking .env configuration..." -ForegroundColor Yellow
ssh -p $SERVER_PORT $SERVER @"
if [ ! -f "$REMOTE_APP_DIR/backend/.env" ]; then
  echo ".env file not found, creating from example..."
  if [ -f "$REMOTE_APP_DIR/backend/config.example.env" ]; then
    cp $REMOTE_APP_DIR/backend/config.example.env $REMOTE_APP_DIR/backend/.env
    echo ".env file created, please edit it:"
    echo "  nano $REMOTE_APP_DIR/backend/.env"
  else
    echo "config.example.env not found"
  fi
else
  echo ".env file exists"
fi
"@

Write-Host ""
Write-Host "Please configure .env file:" -ForegroundColor Yellow
Write-Host "  ssh $SERVER -p $SERVER_PORT" -ForegroundColor White
Write-Host "  cd $REMOTE_APP_DIR/backend" -ForegroundColor Gray
Write-Host "  nano .env" -ForegroundColor Gray
Write-Host ""

# Initialize database
Write-Host "[4/4] Ready to initialize database..." -ForegroundColor Yellow
Write-Host ""
Write-Host "To initialize database, run:" -ForegroundColor Yellow
Write-Host "  ssh $SERVER -p $SERVER_PORT" -ForegroundColor White
Write-Host "  cd $REMOTE_APP_DIR/backend" -ForegroundColor Gray
Write-Host "  source ../venv/bin/activate" -ForegroundColor Gray
Write-Host "  python init_db.py" -ForegroundColor Gray
Write-Host ""

Write-Host "To start services:" -ForegroundColor Yellow
Write-Host "  ssh $SERVER -p $SERVER_PORT" -ForegroundColor White
Write-Host "  systemctl start novawrite-backend" -ForegroundColor Gray
Write-Host "  systemctl enable novawrite-backend" -ForegroundColor Gray
Write-Host "  systemctl status novawrite-backend" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Guide Completed" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""


