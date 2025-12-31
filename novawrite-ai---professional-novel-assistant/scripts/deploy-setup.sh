#!/bin/bash

# 服务器初始化脚本
# 在服务器上运行此脚本来设置部署环境
# 使用方法: ssh root@66.154.108.62 'bash -s' < deploy-setup.sh

set -e

echo "🔧 开始设置部署环境..."

# 1. 更新系统
echo "📦 更新系统包..."
apt-get update -y

# 2. 安装nginx
if ! command -v nginx &> /dev/null; then
  echo "📦 安装nginx..."
  apt-get install -y nginx
  systemctl enable nginx
  systemctl start nginx
  echo "✅ nginx已安装"
else
  echo "✅ nginx已安装"
fi

# 3. 创建部署目录
echo "📁 创建部署目录..."
mkdir -p /var/www/novawrite-ai
chown -R www-data:www-data /var/www/novawrite-ai
chmod -R 755 /var/www/novawrite-ai

# 4. 创建nginx配置
echo "📝 配置nginx..."
cat > /etc/nginx/sites-available/novawrite-ai << 'NGINX_CONFIG'
server {
    listen 80;
    server_name 66.154.108.62;
    
    root /var/www/novawrite-ai/current;
    index index.html;
    
    access_log /var/log/nginx/novawrite-ai-access.log;
    error_log /var/log/nginx/novawrite-ai-error.log;
    
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;
    
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    client_max_body_size 10M;
}
NGINX_CONFIG

# 启用站点
ln -sf /etc/nginx/sites-available/novawrite-ai /etc/nginx/sites-enabled/

# 测试nginx配置
nginx -t

# 重启nginx
systemctl restart nginx

echo ""
echo "✅ 服务器环境设置完成！"
echo ""
echo "📝 下一步："
echo "1. 运行部署脚本: ./deploy.sh"
echo "2. 访问: http://66.154.108.62"

