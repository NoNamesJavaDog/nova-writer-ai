#!/bin/bash

# 服务器初始化脚本 - 设置完整的部署环境
# 使用方法: ssh root@66.154.108.62 -p 22 'bash -s' < deploy-setup.sh

set -e

echo "🔧 开始设置服务器部署环境..."

# 1. 更新系统
echo ""
echo "📦 [1/7] 更新系统包..."

# 检测系统类型
if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu 系统
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get upgrade -y
elif [ -f /etc/redhat-release ]; then
    # CentOS/RHEL 系统
    if command -v dnf &> /dev/null; then
        dnf update -y
    else
        yum update -y
    fi
else
    echo "⚠️  警告：未知的系统类型，跳过系统更新"
fi

# 2. 安装基础工具
echo ""
echo "📦 [2/7] 安装基础工具..."
if [ -f /etc/debian_version ]; then
    apt-get install -y curl wget git build-essential python3 python3-pip python3-venv
elif [ -f /etc/redhat-release ]; then
    if command -v dnf &> /dev/null; then
        dnf install -y curl wget git gcc python3 python3-pip
        python3 -m pip install --upgrade pip
    else
        yum install -y curl wget git gcc python3 python3-pip
        python3 -m pip install --upgrade pip
    fi
fi

# 3. 安装PostgreSQL
echo ""
echo "📦 [3/7] 安装PostgreSQL..."
if ! command -v psql &> /dev/null; then
  if [ -f /etc/debian_version ]; then
    apt-get install -y postgresql postgresql-contrib
    systemctl enable postgresql
    systemctl start postgresql
  elif [ -f /etc/redhat-release ]; then
    if command -v dnf &> /dev/null; then
      dnf install -y postgresql-server postgresql
      # 只在数据目录不存在时初始化
      if [ ! -d "/var/lib/pgsql/data" ] || [ -z "$(ls -A /var/lib/pgsql/data 2>/dev/null)" ]; then
        postgresql-setup --initdb
      else
        echo "⚠️  PostgreSQL数据目录已存在，跳过初始化"
      fi
    else
      yum install -y postgresql-server postgresql
      # 只在数据目录不存在时初始化
      if [ ! -d "/var/lib/pgsql/data" ] || [ -z "$(ls -A /var/lib/pgsql/data 2>/dev/null)" ]; then
        postgresql-setup initdb
      else
        echo "⚠️  PostgreSQL数据目录已存在，跳过初始化"
      fi
    fi
    systemctl enable postgresql
    systemctl start postgresql
  fi
  echo "✅ PostgreSQL已安装"
else
  echo "✅ PostgreSQL已安装"
  # 确保服务已启动
  systemctl start postgresql 2>/dev/null || true
fi

# 4. 安装Nginx
echo ""
echo "📦 [4/7] 安装Nginx..."
if ! command -v nginx &> /dev/null; then
  if [ -f /etc/debian_version ]; then
    apt-get install -y nginx
  elif [ -f /etc/redhat-release ]; then
    if command -v dnf &> /dev/null; then
      dnf install -y nginx
    else
      yum install -y nginx
    fi
  fi
  systemctl enable nginx
  systemctl start nginx
  echo "✅ Nginx已安装"
else
  echo "✅ Nginx已安装"
fi

# 5. 创建目录结构
echo ""
echo "📁 [5/7] 创建目录结构..."
REMOTE_APP_DIR="/opt/novawrite-ai"
REMOTE_FRONTEND_DIR="/var/www/novawrite-ai"

mkdir -p $REMOTE_APP_DIR
mkdir -p $REMOTE_APP_DIR/backend
mkdir -p $REMOTE_APP_DIR/logs
mkdir -p $REMOTE_FRONTEND_DIR
mkdir -p /etc/nginx/sites-available
mkdir -p /etc/nginx/sites-enabled

chown -R www-data:www-data $REMOTE_FRONTEND_DIR

# 6. 配置Nginx
echo ""
echo "📝 [6/7] 配置Nginx..."
cat > /etc/nginx/sites-available/novawrite-ai << 'NGINX_CONFIG'
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

# 启用站点
ln -sf /etc/nginx/sites-available/novawrite-ai /etc/nginx/sites-enabled/

# 移除默认配置（如果存在）
rm -f /etc/nginx/sites-enabled/default

# 测试nginx配置
nginx -t

# 重启nginx
systemctl restart nginx

echo "✅ Nginx配置完成"

# 7. 创建systemd服务文件
echo ""
echo "📝 [7/7] 创建systemd服务..."

cat > /etc/systemd/system/novawrite-backend.service << 'SERVICE_CONFIG'
[Unit]
Description=NovaWrite AI Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/novawrite-ai/backend
Environment="PATH=/opt/novawrite-ai/venv/bin"
ExecStart=/opt/novawrite-ai/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=10
StandardOutput=append:/opt/novawrite-ai/logs/backend.log
StandardError=append:/opt/novawrite-ai/logs/backend.error.log

[Install]
WantedBy=multi-user.target
SERVICE_CONFIG

# 重新加载systemd
systemctl daemon-reload

echo "✅ Systemd服务配置完成"

# 设置PostgreSQL数据库（可选提示）
echo ""
echo "📝 数据库配置提示:"
echo "   1. 创建数据库用户和数据库:"
echo "      sudo -u postgres psql"
echo "      CREATE USER novawrite_user WITH PASSWORD 'your_password';"
echo "      CREATE DATABASE novawrite_ai OWNER novawrite_user;"
echo "      \\q"
echo ""
echo "   2. 在 $REMOTE_APP_DIR/backend/.env 中配置:"
echo "      DATABASE_URL=postgresql://novawrite_user:your_password@localhost:5432/novawrite_ai"
echo "      SECRET_KEY=your-secret-key-here"
echo ""

echo ""
echo "✅ 服务器环境设置完成！"
echo ""
echo "📝 下一步："
echo "1. 配置数据库和 .env 文件"
echo "2. 运行部署脚本: ./deploy.sh"
echo "3. 初始化数据库: ssh $SERVER 'cd $REMOTE_APP_DIR/backend && source ../venv/bin/activate && python init_db.py'"
echo "4. 启动服务: systemctl start novawrite-backend"
echo "5. 访问: http://66.154.108.62"
echo ""

