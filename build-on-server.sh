#!/bin/bash
# Build frontend on server

set -e

FRONTEND_SOURCE="/tmp/novawrite-frontend"
BUILD_DIR="/tmp/novawrite-build"
DEPLOY_DIR="/var/www/novawrite-ai/current"

echo "========================================"
echo "  在服务器上构建前端"
echo "========================================"
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
  echo "❌ 未找到 Node.js，正在安装..."
  
  # 检测系统类型并安装 Node.js
  if [ -f /etc/redhat-release ]; then
    # CentOS/RHEL
    curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
    yum install -y nodejs
  elif [ -f /etc/debian_version ]; then
    # Debian/Ubuntu
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
  else
    echo "❌ 无法自动安装 Node.js，请手动安装"
    exit 1
  fi
fi

echo "✅ Node.js 版本: $(node --version)"
echo "✅ npm 版本: $(npm --version)"
echo ""

# 检查是否有源代码
if [ ! -f "/tmp/App.tsx" ]; then
  echo "⚠️  未找到源代码文件，尝试从 Git 或其他位置获取"
  echo "   或者需要手动上传源代码"
  exit 1
fi

# 创建临时构建目录
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# 如果源代码目录存在，使用它
if [ -d "$FRONTEND_SOURCE" ]; then
  echo "📦 复制源代码..."
  cp -r "$FRONTEND_SOURCE"/* .
else
  echo "⚠️  源代码目录不存在，需要手动上传完整源代码"
  echo "   或者使用已构建的 dist 目录"
  exit 1
fi

# 复制修复后的 App.tsx
if [ -f "/tmp/App.tsx" ]; then
  echo "📝 应用修复后的 App.tsx..."
  cp /tmp/App.tsx ./App.tsx
fi

# 安装依赖
echo ""
echo "📦 安装依赖..."
npm install --production=false

# 构建
echo ""
echo "🔨 构建前端..."
export VITE_API_BASE_URL=""
npm run build

if [ ! -d "dist" ]; then
  echo "❌ 构建失败：找不到 dist 目录"
  exit 1
fi

# 备份当前版本
if [ -d "$DEPLOY_DIR" ]; then
  BACKUP_DIR="/var/www/novawrite-ai/backup-$(date +%Y%m%d-%H%M%S)"
  echo ""
  echo "💾 备份当前版本到: $BACKUP_DIR"
  mkdir -p "$BACKUP_DIR"
  cp -r "$DEPLOY_DIR"/* "$BACKUP_DIR/" 2>/dev/null || true
fi

# 部署
echo ""
echo "🚀 部署新版本..."
mkdir -p "$DEPLOY_DIR"
cp -r dist/* "$DEPLOY_DIR/"

# 设置权限
chown -R nginx:nginx "$DEPLOY_DIR"
chmod -R 755 "$DEPLOY_DIR"

echo ""
echo "✅ 构建和部署完成！"
echo ""
echo "访问地址: http://66.154.108.62"
echo ""


