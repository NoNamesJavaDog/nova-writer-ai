#!/bin/bash
# Fix firewall and Nginx configuration

echo "Fixing firewall and Nginx..."

# Open port 80 in firewall
if command -v firewall-cmd &>/dev/null; then
  echo "Opening port 80 in firewalld..."
  firewall-cmd --permanent --add-service=http
  firewall-cmd --permanent --add-port=80/tcp
  firewall-cmd --reload
  echo "Firewall configured"
elif command -v iptables &>/dev/null; then
  echo "Opening port 80 in iptables..."
  iptables -I INPUT -p tcp --dport 80 -j ACCEPT
  # Save iptables rules (varies by system)
  if command -v iptables-save &>/dev/null; then
    iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
  fi
  echo "Iptables configured"
fi

# Check Nginx configuration
echo ""
echo "Checking Nginx configuration..."
nginx -t

# Ensure Nginx site is enabled
if [ -f /etc/nginx/sites-available/novawrite-ai ]; then
  ln -sf /etc/nginx/sites-available/novawrite-ai /etc/nginx/sites-enabled/novawrite-ai
  echo "Nginx site enabled"
fi

# Restart Nginx
echo ""
echo "Restarting Nginx..."
systemctl restart nginx

# Check if Nginx is listening
sleep 2
echo ""
echo "Checking Nginx status..."
systemctl status nginx --no-pager | head -10

echo ""
echo "Testing local connection..."
curl -I http://127.0.0.1 2>&1 | head -5

echo ""
echo "Firewall and Nginx fixed!"


