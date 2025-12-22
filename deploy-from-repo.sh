#!/bin/bash
set -e

echo "🚀 开始从代码库自动部署..."
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"

REPO_DIR="/opt/novawrite-ai"
BACKEND_DIR="$REPO_DIR/backend"
FRONTEND_DIR="$REPO_DIR/novawrite-ai---professional-novel-assistant"
VENV_DIR="/opt/novawrite-ai/venv"
WEB_DIR="/var/www/novawrite-ai/current"

# 检查代码库目录
if [ ! -d "$REPO_DIR" ]; then
  echo "❌ 错误: 代码库目录不存在: $REPO_DIR"
  echo "请先运行 setup-server-repo.sh 设置代码库"
  exit 1
fi

cd "$REPO_DIR"

# 1. 更新后端依赖
echo ""
echo "📦 步骤 1/5: 更新后端依赖..."
if [ -d "$VENV_DIR" ]; then
  source "$VENV_DIR/bin/activate"
  cd "$BACKEND_DIR"
  
  # 检查 requirements.txt 是否存在
  if [ ! -f "requirements.txt" ]; then
    echo "⚠️ 警告: requirements.txt 不存在，跳过依赖更新"
  else
    pip install --upgrade pip -q
    pip install -r requirements.txt
    echo "✅ 后端依赖更新完成"
  fi
else
  echo "⚠️ 警告: 虚拟环境不存在: $VENV_DIR"
  echo "如果这是首次部署，请先运行初始化脚本"
fi

# 2. 重启后端服务
echo ""
echo "🔄 步骤 2/5: 重启后端服务..."
if systemctl is-active --quiet novawrite-backend; then
  systemctl restart novawrite-backend
  sleep 3
  if systemctl is-active --quiet novawrite-backend; then
    echo "✅ 后端服务重启成功"
    systemctl status novawrite-backend --no-pager -l | head -5
  else
    echo "❌ 后端服务启动失败"
    systemctl status novawrite-backend --no-pager -l
    exit 1
  fi
else
  echo "⚠️ 后端服务未运行，尝试启动..."
  systemctl start novawrite-backend || echo "⚠️ 启动失败，请检查服务配置"
fi

# 3. 构建前端
echo ""
echo "📦 步骤 3/5: 构建前端..."
if [ -d "$FRONTEND_DIR" ]; then
  cd "$FRONTEND_DIR"
  if command -v npm &> /dev/null; then
    echo "安装前端依赖..."
    npm install --silent
    echo "构建前端..."
    npm run build
    if [ $? -eq 0 ]; then
      echo "✅ 前端构建完成"
    else
      echo "❌ 前端构建失败"
      exit 1
    fi
  else
    echo "⚠️ npm 未安装，跳过前端构建"
    echo "请安装 Node.js 和 npm"
  fi
else
  echo "⚠️ 前端目录不存在: $FRONTEND_DIR"
fi

# 4. 复制前端构建文件到 web 目录
echo ""
echo "📁 步骤 4/5: 部署前端文件..."
if [ -d "$FRONTEND_DIR/dist" ]; then
  mkdir -p "$WEB_DIR"
  
  # 备份当前版本（可选）
  if [ -d "$WEB_DIR" ] && [ "$(ls -A $WEB_DIR)" ]; then
    BACKUP_DIR="/var/www/novawrite-ai/backup.$(date +%Y%m%d_%H%M%S)"
    echo "备份当前版本到 $BACKUP_DIR"
    cp -r "$WEB_DIR" "$BACKUP_DIR" 2>/dev/null || true
  fi
  
  # 清空并复制新文件
  rm -rf "$WEB_DIR"/*
  cp -r "$FRONTEND_DIR/dist"/* "$WEB_DIR/"
  chown -R www-data:www-data "$WEB_DIR"
  chmod -R 755 "$WEB_DIR"
  echo "✅ 前端文件已部署到 $WEB_DIR"
else
  echo "⚠️ 前端构建目录不存在: $FRONTEND_DIR/dist"
fi

# 5. 重载 Nginx
echo ""
echo "🔄 步骤 5/5: 重载 Nginx..."
if nginx -t 2>/dev/null; then
  systemctl reload nginx
  echo "✅ Nginx 已重载"
else
  echo "⚠️ Nginx 配置检查失败，跳过重载"
  nginx -t
fi

echo ""
echo "🎉 部署完成！"
echo "部署时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "检查服务状态："
systemctl is-active novawrite-backend && echo "✅ 后端服务运行中" || echo "❌ 后端服务未运行"
systemctl is-active nginx && echo "✅ Nginx 运行中" || echo "❌ Nginx 未运行"

