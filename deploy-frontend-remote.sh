#!/bin/bash
# Deploy frontend to server

REMOTE_FRONTEND_DIR="/var/www/novawrite-ai"
FRONTEND_PACKAGE="$1"

if [ -z "$FRONTEND_PACKAGE" ]; then
  echo "Usage: $0 <frontend-package.tar.gz>"
  exit 1
fi

# 备份当前版本
if [ -d "$REMOTE_FRONTEND_DIR/current" ]; then
  BACKUP_DIR="$REMOTE_FRONTEND_DIR/backup-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$BACKUP_DIR"
  cp -r "$REMOTE_FRONTEND_DIR/current"/* "$BACKUP_DIR/" 2>/dev/null || true
  echo "已备份到: $BACKUP_DIR"
fi

# 解压新版本
mkdir -p "$REMOTE_FRONTEND_DIR/current"
tar -xzf "/tmp/$FRONTEND_PACKAGE" -C "$REMOTE_FRONTEND_DIR/current"

# 设置权限
chown -R nginx:nginx "$REMOTE_FRONTEND_DIR/current"
chmod -R 755 "$REMOTE_FRONTEND_DIR/current"

# 清理
rm -f "/tmp/$FRONTEND_PACKAGE"

echo "✅ 前端部署完成"


