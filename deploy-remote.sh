#!/bin/bash
set -e

REMOTE_APP_DIR="/opt/novawrite-ai"
REMOTE_FRONTEND_DIR="/var/www/novawrite-ai"

echo "Creating directories..."
mkdir -p $REMOTE_APP_DIR
mkdir -p $REMOTE_FRONTEND_DIR
mkdir -p $REMOTE_APP_DIR/backend
mkdir -p $REMOTE_APP_DIR/logs

# Backup old versions
if [ -d "$REMOTE_APP_DIR/backend" ] && [ "$(ls -A $REMOTE_APP_DIR/backend 2>/dev/null)" ]; then
  echo "Backing up old backend..."
  BACKEND_BACKUP="$REMOTE_APP_DIR/backend-backup-$(date +%Y%m%d-%H%M%S)"
  mv $REMOTE_APP_DIR/backend/* "$BACKEND_BACKUP" 2>/dev/null || true
fi

if [ -d "$REMOTE_FRONTEND_DIR/current" ]; then
  echo "Backing up old frontend..."
  FRONTEND_BACKUP="$REMOTE_FRONTEND_DIR/backup-$(date +%Y%m%d-%H%M%S)"
  mv $REMOTE_FRONTEND_DIR/current "$FRONTEND_BACKUP"
fi

# Deploy backend
echo "Deploying backend..."
LATEST_BACKEND=$(ls -t /tmp/backend-*.tar.gz | head -1)
tar -xzf "$LATEST_BACKEND" -C $REMOTE_APP_DIR/backend

# Deploy frontend
echo "Deploying frontend..."
mkdir -p $REMOTE_FRONTEND_DIR/current
LATEST_FRONTEND=$(ls -t /tmp/frontend-*.tar.gz | head -1)
tar -xzf "$LATEST_FRONTEND" -C $REMOTE_FRONTEND_DIR/current

# Set permissions
chown -R www-data:www-data $REMOTE_FRONTEND_DIR/current
chmod -R 755 $REMOTE_FRONTEND_DIR/current

# Cleanup
rm -f /tmp/backend-*.tar.gz /tmp/frontend-*.tar.gz

echo "File deployment completed"

# Install Python dependencies
if [ ! -d "$REMOTE_APP_DIR/venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv $REMOTE_APP_DIR/venv
fi

echo "Installing/updating Python dependencies..."
$REMOTE_APP_DIR/venv/bin/pip install --upgrade pip --quiet
$REMOTE_APP_DIR/venv/bin/pip install -r $REMOTE_APP_DIR/backend/requirements.txt --quiet

# Restart backend service
if systemctl is-active --quiet novawrite-backend 2>/dev/null; then
  echo "Restarting backend service..."
  systemctl restart novawrite-backend
else
  echo "Backend service not running, please start manually: systemctl start novawrite-backend"
fi

# Reload Nginx
if command -v nginx &> /dev/null; then
  echo "Reloading Nginx..."
  systemctl reload nginx 2>/dev/null || service nginx reload 2>/dev/null || true
fi

echo ""
echo "Deployment completed successfully!"


