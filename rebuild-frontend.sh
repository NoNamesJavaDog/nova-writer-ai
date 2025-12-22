#!/bin/bash
# Rebuild frontend with correct API configuration

cd /opt/novawrite-ai
FRONTEND_SOURCE="/tmp/novawrite-frontend-source"

echo "Downloading frontend source..."
# 这里需要从本地上传，或者直接在服务器上修改
# 暂时先检查是否有构建好的 dist

if [ -d "$FRONTEND_SOURCE" ]; then
  cd "$FRONTEND_SOURCE/novawrite-ai---professional-novel-assistant"
  
  # 修改 apiService.ts 使用相对路径
  sed -i "s|const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';|const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';|g" services/apiService.ts
  
  # 构建
  export VITE_API_BASE_URL=""
  npm run build
  
  # 部署
  if [ -d "dist" ]; then
    cp -r dist/* /var/www/novawrite-ai/current/
    echo "Frontend deployed"
  fi
else
  echo "Frontend source not found at $FRONTEND_SOURCE"
  echo "Please upload and rebuild from local machine"
fi


