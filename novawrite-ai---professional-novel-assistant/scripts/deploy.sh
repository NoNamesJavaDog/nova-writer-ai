#!/bin/bash

# 部署脚本 - 部署到远程服务器
# 使用方法: ./deploy.sh

set -e

# 配置
SERVER="root@66.154.108.62"
REMOTE_DIR="/var/www/novawrite-ai"
LOCAL_BUILD_DIR="dist"

echo "🚀 开始部署流程..."

# 1. 构建项目
echo "📦 正在构建项目..."
npm run build

if [ ! -d "$LOCAL_BUILD_DIR" ]; then
  echo "❌ 构建失败：找不到 dist 目录"
  exit 1
fi

echo "✅ 构建完成"

# 2. 创建临时部署包
echo "📦 正在打包..."
DEPLOY_PACKAGE="deploy-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$DEPLOY_PACKAGE" -C "$LOCAL_BUILD_DIR" .

echo "✅ 打包完成: $DEPLOY_PACKAGE"

# 3. 上传到服务器
echo "📤 正在上传到服务器..."
scp "$DEPLOY_PACKAGE" "$SERVER:/tmp/"

echo "✅ 上传完成"

# 4. 在服务器上部署
echo "🔧 正在服务器上部署..."
ssh "$SERVER" << 'ENDSSH'
  set -e
  
  # 创建部署目录
  mkdir -p /var/www/novawrite-ai
  
  # 备份旧版本（如果存在）
  if [ -d "/var/www/novawrite-ai/current" ]; then
    echo "📦 备份旧版本..."
    BACKUP_DIR="/var/www/novawrite-ai/backup-$(date +%Y%m%d-%H%M%S)"
    mv /var/www/novawrite-ai/current "$BACKUP_DIR"
    echo "✅ 已备份到: $BACKUP_DIR"
  fi
  
  # 创建新版本目录
  NEW_DIR="/var/www/novawrite-ai/current"
  mkdir -p "$NEW_DIR"
  
  # 解压新版本
  LATEST_PACKAGE=$(ls -t /tmp/deploy-*.tar.gz | head -1)
  echo "📦 解压: $LATEST_PACKAGE"
  tar -xzf "$LATEST_PACKAGE" -C "$NEW_DIR"
  
  # 设置权限
  chown -R www-data:www-data "$NEW_DIR"
  chmod -R 755 "$NEW_DIR"
  
  # 清理临时文件
  rm -f /tmp/deploy-*.tar.gz
  
  echo "✅ 部署完成"
  
  # 重启nginx（如果存在）
  if command -v nginx &> /dev/null; then
    echo "🔄 重启nginx..."
    systemctl reload nginx || service nginx reload
    echo "✅ nginx已重启"
  fi
ENDSSH

# 5. 清理本地临时文件
rm -f "$DEPLOY_PACKAGE"

echo ""
echo "🎉 部署完成！"
echo "📝 访问地址: http://66.154.108.62"
echo ""
echo "⚠️  注意："
echo "1. 确保服务器上已安装并配置nginx"
echo "2. 确保nginx配置指向: $REMOTE_DIR/current"
echo "3. 如需配置HTTPS，请使用Let's Encrypt"

