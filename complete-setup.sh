#!/bin/bash
# Complete post-deployment setup script
# This script will be executed on the server

set -e

REMOTE_APP_DIR="/opt/novawrite-ai"
REMOTE_FRONTEND_DIR="/var/www/novawrite-ai"

echo "========================================"
echo "  Complete Post-Deployment Setup"
echo "========================================"
echo ""

# Step 1: Fix permissions
echo "[1/5] Fixing file permissions..."
if id nginx &>/dev/null; then
  WEB_USER=nginx
elif id apache &>/dev/null; then
  WEB_USER=apache
elif id www-data &>/dev/null; then
  WEB_USER=www-data
else
  WEB_USER=root
fi

echo "Using web user: $WEB_USER"

if [ -d "$REMOTE_FRONTEND_DIR/current" ]; then
  chown -R $WEB_USER:$WEB_USER $REMOTE_FRONTEND_DIR/current
  chmod -R 755 $REMOTE_FRONTEND_DIR/current
  echo "Frontend permissions fixed"
fi

chown -R root:root $REMOTE_APP_DIR/backend
chmod -R 755 $REMOTE_APP_DIR/backend
echo "Backend permissions fixed"
echo "OK: Permissions fixed"
echo ""

# Step 2: Start PostgreSQL
echo "[2/5] Setting up database..."
systemctl start postgresql
systemctl enable postgresql
sleep 2

# Generate random password
DB_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)
DB_USER="novawrite_user"
DB_NAME="novawrite_ai"

echo "Creating database user and database..."
sudo -u postgres psql << EOF
-- Create user if not exists
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
    CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
  ELSE
    ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
  END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

\q
EOF

echo "Database created"
echo "Database user: $DB_USER"
echo "Database name: $DB_NAME"
echo "Database password: $DB_PASSWORD"
echo "OK: Database created"
echo ""

# Step 3: Configure .env file
echo "[3/5] Configuring .env file..."

cd $REMOTE_APP_DIR/backend

# Generate SECRET_KEY
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -hex 32)

# Create or update .env
if [ ! -f .env ]; then
  if [ -f config.example.env ]; then
    cp config.example.env .env
  else
    cat > .env << ENVFILE
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
SECRET_KEY=$SECRET_KEY
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
sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME|g" .env
sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env
sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=http://66.154.108.62|g" .env
sed -i "s|ENVIRONMENT=.*|ENVIRONMENT=production|g" .env
sed -i "s|DEBUG=.*|DEBUG=false|g" .env

echo ".env file configured"
echo "OK: .env file configured"
echo ""

# Step 4: Create virtual environment and initialize database
echo "[4/5] Setting up Python environment and initializing database..."

cd $REMOTE_APP_DIR

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv venv
fi

# Install/update dependencies
echo "Installing Python dependencies..."
venv/bin/pip install --upgrade pip --quiet
venv/bin/pip install -r backend/requirements.txt --quiet

# Initialize database
echo "Initializing database..."
cd backend
source ../venv/bin/activate
python init_db.py
echo "OK: Database initialized"
echo ""

# Step 5: Start services
echo "[5/5] Starting services..."
systemctl start novawrite-backend
systemctl enable novawrite-backend

# Check service status
if systemctl is-active --quiet novawrite-backend; then
  echo "Backend service: Running"
else
  echo "Backend service: Not running (check logs)"
fi

# Reload Nginx
if command -v nginx &>/dev/null; then
  systemctl reload nginx 2>/dev/null || service nginx reload 2>/dev/null || true
  echo "Nginx reloaded"
fi

echo "OK: Services started"
echo ""

echo "========================================"
echo "  Setup Completed!"
echo "========================================"
echo ""
echo "Access URLs:"
echo "  Frontend: http://66.154.108.62"
echo "  API: http://66.154.108.62/api"
echo "  API Docs: http://66.154.108.62/api/docs"
echo ""
echo "Database Information:"
echo "  User: $DB_USER"
echo "  Database: $DB_NAME"
echo "  Password: $DB_PASSWORD"
echo ""
echo "Service Status:"
systemctl status novawrite-backend --no-pager -l | head -5
echo ""

