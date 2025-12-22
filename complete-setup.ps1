# Complete post-deployment setup
# Usage: .\complete-setup.ps1

$SERVER = "root@66.154.108.62"
$SERVER_PORT = "22"
$REMOTE_APP_DIR = "/opt/novawrite-ai"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Complete Post-Deployment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Fix permissions
Write-Host "[1/5] Fixing file permissions..." -ForegroundColor Yellow
ssh -p $SERVER_PORT $SERVER @"
# Find web server user
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
chown -R root:root /opt/novawrite-ai/backend
chmod -R 755 /opt/novawrite-ai/backend
echo "Backend permissions fixed"
"@

Write-Host "OK: Permissions fixed" -ForegroundColor Green

# Step 2: Start PostgreSQL and create database
Write-Host ""
Write-Host "[2/5] Setting up database..." -ForegroundColor Yellow

# Generate random password
$dbPassword = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 16 | ForEach-Object {[char]$_})
$dbUser = "novawrite_user"
$dbName = "novawrite_ai"

Write-Host "  Starting PostgreSQL..." -ForegroundColor Gray
ssh -p $SERVER_PORT $SERVER "systemctl start postgresql; systemctl enable postgresql"

Write-Host "  Creating database user and database..." -ForegroundColor Gray
ssh -p $SERVER_PORT $SERVER @"
sudo -u postgres psql << EOF
-- Check if user exists
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$dbUser') THEN
    CREATE USER $dbUser WITH PASSWORD '$dbPassword';
  END IF;
END
\$\$;

-- Check if database exists
SELECT 'CREATE DATABASE $dbName OWNER $dbUser' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$dbName')\gexec

\q
EOF

echo "Database user and database created"
echo "Database password: $dbPassword"
"@

Write-Host "OK: Database created" -ForegroundColor Green
Write-Host "  Database user: $dbUser" -ForegroundColor Gray
Write-Host "  Database name: $dbName" -ForegroundColor Gray
Write-Host "  Database password: $dbPassword" -ForegroundColor Gray
Write-Host "  (Please save this password!)" -ForegroundColor Yellow

# Step 3: Configure .env file
Write-Host ""
Write-Host "[3/5] Configuring .env file..." -ForegroundColor Yellow

# Generate SECRET_KEY
$secretKey = -join ((48..57) + (65..90) + (97..122) + (45,95) | Get-Random -Count 32 | ForEach-Object {[char]$_})

ssh -p $SERVER_PORT $SERVER @"
cd $REMOTE_APP_DIR/backend

# Create .env if not exists
if [ ! -f .env ]; then
  if [ -f config.example.env ]; then
    cp config.example.env .env
  else
    cat > .env << 'ENVFILE'
DATABASE_URL=postgresql://$dbUser:$dbPassword@localhost:5432/$dbName
SECRET_KEY=$secretKey
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://66.154.108.62
ENVIRONMENT=production
DEBUG=false
ENVFILE
  fi
fi

# Update .env with correct values
sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql://$dbUser:$dbPassword@localhost:5432/$dbName|g" .env
sed -i "s|SECRET_KEY=.*|SECRET_KEY=$secretKey|g" .env
sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=http://66.154.108.62|g" .env
sed -i "s|ENVIRONMENT=.*|ENVIRONMENT=production|g" .env
sed -i "s|DEBUG=.*|DEBUG=false|g" .env

echo ".env file configured"
cat .env | grep -v "PASSWORD\|SECRET_KEY" | head -5
"@

Write-Host "OK: .env file configured" -ForegroundColor Green

# Step 4: Initialize database
Write-Host ""
Write-Host "[4/5] Initializing database..." -ForegroundColor Yellow

ssh -p $SERVER_PORT $SERVER @"
cd $REMOTE_APP_DIR/backend
source ../venv/bin/activate

# Initialize database
python init_db.py

echo "Database initialized"
"@

Write-Host "OK: Database initialized" -ForegroundColor Green

# Step 5: Start services
Write-Host ""
Write-Host "[5/5] Starting services..." -ForegroundColor Yellow

ssh -p $SERVER_PORT $SERVER @"
# Start backend service
systemctl start novawrite-backend
systemctl enable novawrite-backend

# Check service status
echo "Backend service status:"
systemctl is-active novawrite-backend && echo "  Running" || echo "  Not running"

# Reload Nginx
if command -v nginx &>/dev/null; then
  systemctl reload nginx 2>/dev/null || service nginx reload 2>/dev/null || true
  echo "Nginx reloaded"
fi

# Show service status
echo ""
echo "Service status:"
systemctl status novawrite-backend --no-pager -l | head -10
"@

Write-Host "OK: Services started" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Cyan
Write-Host "  Frontend: http://66.154.108.62" -ForegroundColor White
Write-Host "  API: http://66.154.108.62/api" -ForegroundColor White
Write-Host "  API Docs: http://66.154.108.62/api/docs" -ForegroundColor White
Write-Host ""
Write-Host "Database Information:" -ForegroundColor Yellow
Write-Host "  User: $dbUser" -ForegroundColor White
Write-Host "  Database: $dbName" -ForegroundColor White
Write-Host "  Password: $dbPassword" -ForegroundColor White
Write-Host "  (Please save this password!)" -ForegroundColor Yellow
Write-Host ""
Write-Host "To check service status:" -ForegroundColor Cyan
Write-Host "  ssh $SERVER -p $SERVER_PORT 'systemctl status novawrite-backend nginx'" -ForegroundColor Gray
Write-Host ""


