#!/bin/bash

# 完整部署脚本 - 部署前后端到远程服务器
# 使用方法: ./deploy.sh

set -e

# 配置
SERVER="root@66.154.108.62"
SERVER_PORT="22"
REMOTE_APP_DIR="/opt/novawrite-ai"
REMOTE_FRONTEND_DIR="/var/www/novawrite-ai"
BACKEND_DIR="backend"
FRONTEND_DIR="novawrite-ai---professional-novel-assistant"

echo "🚀 开始完整部署流程..."

# 检查是否在项目根目录
if [ ! -d "$BACKEND_DIR" ] || [ ! -d "$FRONTEND_DIR" ]; then
  echo "❌ 错误：请在项目根目录执行此脚本"
  exit 1
fi

# 1. 构建前端
echo ""
echo "📦 [1/5] 正在构建前端..."
cd "$FRONTEND_DIR"

# 设置生产环境API地址（如果未设置）
if [ -z "$VITE_API_BASE_URL" ]; then
  export VITE_API_BASE_URL="http://66.154.108.62"
fi

npm install --production=false
npm run build

if [ ! -d "dist" ]; then
  echo "❌ 前端构建失败：找不到 dist 目录"
  exit 1
fi

echo "✅ 前端构建完成"
cd ..

# 2. 打包后端
echo ""
echo "📦 [2/5] 正在打包后端..."
BACKEND_PACKAGE="backend-$(date +%Y%m%d-%H%M%S).tar.gz"
tar --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='.git' \
    -czf "$BACKEND_PACKAGE" -C "$BACKEND_DIR" .

echo "✅ 后端打包完成: $BACKEND_PACKAGE"

# 3. 打包前端
echo ""
echo "📦 [3/5] 正在打包前端..."
FRONTEND_PACKAGE="frontend-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$FRONTEND_PACKAGE" -C "$FRONTEND_DIR/dist" .

echo "✅ 前端打包完成: $FRONTEND_PACKAGE"

# 4. 上传到服务器
echo ""
echo "📤 [4/5] 正在上传到服务器..."
scp -P "$SERVER_PORT" "$BACKEND_PACKAGE" "$SERVER:/tmp/"
scp -P "$SERVER_PORT" "$FRONTEND_PACKAGE" "$SERVER:/tmp/"

echo "✅ 上传完成"

# 5. 在服务器上部署
echo ""
echo "🔧 [5/5] 正在服务器上部署..."
ssh -p "$SERVER_PORT" "$SERVER" << ENDSSH
set -e

echo "🔧 开始服务器端部署..."

# 创建目录结构
mkdir -p $REMOTE_APP_DIR
mkdir -p $REMOTE_FRONTEND_DIR
mkdir -p $REMOTE_APP_DIR/backend
mkdir -p $REMOTE_APP_DIR/logs

# 备份旧版本（如果存在）
if [ -d "$REMOTE_APP_DIR/backend" ] && [ "\$(ls -A $REMOTE_APP_DIR/backend 2>/dev/null)" ]; then
  echo "📦 备份旧后端..."
  BACKEND_BACKUP="$REMOTE_APP_DIR/backend-backup-\$(date +%Y%m%d-%H%M%S)"
  mv $REMOTE_APP_DIR/backend/* "$BACKEND_BACKUP" 2>/dev/null || true
fi

if [ -d "$REMOTE_FRONTEND_DIR/current" ]; then
  echo "📦 备份旧前端..."
  FRONTEND_BACKUP="$REMOTE_FRONTEND_DIR/backup-\$(date +%Y%m%d-%H%M%S)"
  mv $REMOTE_FRONTEND_DIR/current "$FRONTEND_BACKUP"
fi

# 部署后端
echo "📦 部署后端..."
LATEST_BACKEND=\$(ls -t /tmp/backend-*.tar.gz | head -1)
tar -xzf "\$LATEST_BACKEND" -C $REMOTE_APP_DIR/backend

# 部署前端
echo "📦 部署前端..."
mkdir -p $REMOTE_FRONTEND_DIR/current
LATEST_FRONTEND=\$(ls -t /tmp/frontend-*.tar.gz | head -1)
tar -xzf "\$LATEST_FRONTEND" -C $REMOTE_FRONTEND_DIR/current

# 设置权限
chown -R www-data:www-data $REMOTE_FRONTEND_DIR/current
chmod -R 755 $REMOTE_FRONTEND_DIR/current

# 清理临时文件
rm -f /tmp/backend-*.tar.gz /tmp/frontend-*.tar.gz

echo "✅ 文件部署完成"

# 安装Python依赖（如果虚拟环境不存在）
if [ ! -d "$REMOTE_APP_DIR/venv" ]; then
  echo "📦 创建Python虚拟环境..."
  python3 -m venv $REMOTE_APP_DIR/venv
fi

echo "📦 安装/更新Python依赖..."
$REMOTE_APP_DIR/venv/bin/pip install --upgrade pip
$REMOTE_APP_DIR/venv/bin/pip install -r $REMOTE_APP_DIR/backend/requirements.txt

# 重启后端服务
if systemctl is-active --quiet novawrite-backend; then
  echo "🔄 重启后端服务..."
  systemctl restart novawrite-backend
else
  echo "⚠️  后端服务未运行，请手动启动: systemctl start novawrite-backend"
fi

# 重启Nginx
if command -v nginx &> /dev/null; then
  echo "🔄 重启Nginx..."
  systemctl reload nginx || service nginx reload
fi

echo ""
echo "✅ 部署完成！"
ENDSSH

# 6. 清理本地临时文件
rm -f "$BACKEND_PACKAGE" "$FRONTEND_PACKAGE"

echo ""
echo "🎉 部署完成！"
echo ""
echo "📝 访问地址:"
echo "  前端: http://66.154.108.62"
echo "  API: http://66.154.108.62/api"
echo "  API文档: http://66.154.108.62/api/docs"
echo ""
echo "⚠️  注意事项:"
echo "1. 确保服务器上已配置 .env 文件（数据库、SECRET_KEY等）"
echo "2. 确保数据库已初始化: ssh $SERVER 'cd $REMOTE_APP_DIR/backend && source ../venv/bin/activate && python init_db.py'"
echo "3. 检查服务状态: ssh $SERVER 'systemctl status novawrite-backend nginx'"
echo ""

