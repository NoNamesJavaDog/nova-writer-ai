#!/bin/bash
# Create systemd service for backend

echo "Creating systemd service..."

cat > /etc/systemd/system/novawrite-backend.service << 'SERVICE_CONFIG'
[Unit]
Description=NovaWrite AI Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/novawrite-ai/backend
Environment="PATH=/opt/novawrite-ai/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/novawrite-ai/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=10
StandardOutput=append:/opt/novawrite-ai/logs/backend.log
StandardError=append:/opt/novawrite-ai/logs/backend.error.log

[Install]
WantedBy=multi-user.target
SERVICE_CONFIG

# Create logs directory
mkdir -p /opt/novawrite-ai/logs

# Reload systemd
systemctl daemon-reload

echo "Service created"
echo "Starting service..."

# Start and enable service
systemctl start novawrite-backend
systemctl enable novawrite-backend

# Check status
sleep 2
systemctl status novawrite-backend --no-pager -l | head -15

echo ""
echo "Service status:"
if systemctl is-active --quiet novawrite-backend; then
  echo "✅ Backend service is running"
else
  echo "❌ Backend service failed to start"
  echo "Check logs: journalctl -u novawrite-backend -n 50"
fi


