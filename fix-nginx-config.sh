#!/bin/bash
# Fix Nginx configuration

echo "Fixing Nginx configuration..."

cat > /etc/nginx/conf.d/novawrite-ai.conf << 'NGINX_CONFIG'
server {
    listen 80;
    server_name 66.154.108.62;
    
    client_max_body_size 20M;
    
    # 前端静态文件
    location / {
        root /var/www/novawrite-ai/current;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # 静态资源缓存
        location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # 后端API代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # API文档
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_set_header Host $host;
    }
    
    access_log /var/log/nginx/novawrite-ai-access.log;
    error_log /var/log/nginx/novawrite-ai-error.log;
    
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json application/javascript;
    
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
NGINX_CONFIG

# Test configuration
echo "Testing Nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
  echo "Configuration is valid, reloading Nginx..."
  systemctl reload nginx
  sleep 2
  
  echo ""
  echo "Testing local connection..."
  curl -I http://127.0.0.1 2>&1 | head -5
  
  echo ""
  echo "Nginx configuration fixed!"
else
  echo "Configuration test failed!"
  exit 1
fi


