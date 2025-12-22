# PowerShell 部署脚本 - 部署安全更新到远程服务器
# 使用方法: .\deploy-security-updates.ps1

$ErrorActionPreference = "Stop"

# 配置
$SERVER = "root@66.154.108.62"
$SERVER_PORT = "22"
$REMOTE_APP_DIR = "/opt/novawrite-ai"
$REMOTE_FRONTEND_DIR = "/var/www/novawrite-ai"
$BACKEND_DIR = "backend"
$FRONTEND_DIR = "novawrite-ai---professional-novel-assistant"

Write-Host "🚀 开始部署安全更新..." -ForegroundColor Green

# 检查是否在项目根目录
if (-not (Test-Path $BACKEND_DIR) -or -not (Test-Path $FRONTEND_DIR)) {
    Write-Host "❌ 错误：请在项目根目录执行此脚本" -ForegroundColor Red
    exit 1
}

# 1. 打包后端
Write-Host ""
Write-Host "📦 [1/3] 正在打包后端..." -ForegroundColor Yellow
$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$BACKEND_PACKAGE = "backend-$TIMESTAMP.tar.gz"

Set-Location $BACKEND_DIR
tar -czf "../$BACKEND_PACKAGE" --exclude=__pycache__ --exclude=*.pyc --exclude=.env --exclude=.git *
Set-Location ..

if (-not (Test-Path $BACKEND_PACKAGE)) {
    Write-Host "❌ 后端打包失败" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 后端打包完成: $BACKEND_PACKAGE" -ForegroundColor Green

# 2. 打包前端源代码（用于在服务器上构建）
Write-Host ""
Write-Host "📦 [2/3] 正在打包前端源代码..." -ForegroundColor Yellow
$FRONTEND_SRC_PACKAGE = "frontend-src-$TIMESTAMP.tar.gz"

Set-Location $FRONTEND_DIR
tar -czf "../$FRONTEND_SRC_PACKAGE" --exclude=node_modules --exclude=dist --exclude=.git --exclude=.env.local *
Set-Location ..

if (-not (Test-Path $FRONTEND_SRC_PACKAGE)) {
    Write-Host "❌ 前端源代码打包失败" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 前端源代码打包完成: $FRONTEND_SRC_PACKAGE" -ForegroundColor Green

# 3. 上传到服务器
Write-Host ""
Write-Host "📤 [3/3] 正在上传到服务器..." -ForegroundColor Yellow
scp -P $SERVER_PORT $BACKEND_PACKAGE "${SERVER}:/tmp/"
scp -P $SERVER_PORT $FRONTEND_SRC_PACKAGE "${SERVER}:/tmp/"

Write-Host "✅ 上传完成" -ForegroundColor Green

# 4. 在服务器上部署
Write-Host ""
Write-Host "🔧 正在服务器上部署..." -ForegroundColor Yellow

$DEPLOY_SCRIPT = @"
set -e

echo "🔧 开始服务器端部署..."

# 创建目录结构
mkdir -p $REMOTE_APP_DIR
mkdir -p $REMOTE_FRONTEND_DIR
mkdir -p $REMOTE_APP_DIR/backend
mkdir -p $REMOTE_APP_DIR/logs

# 备份旧版本
if [ -d "$REMOTE_APP_DIR/backend" ] && [ "\$(ls -A $REMOTE_APP_DIR/backend 2>/dev/null)" ]; then
  echo "📦 备份旧后端..."
  BACKEND_BACKUP="$REMOTE_APP_DIR/backend-backup-\$(date +%Y%m%d-%H%M%S)"
  mkdir -p "\$BACKEND_BACKUP"
  cp -r $REMOTE_APP_DIR/backend/* "\$BACKEND_BACKUP/" 2>/dev/null || true
fi

# 部署后端
echo "📦 部署后端..."
LATEST_BACKEND=\$(ls -t /tmp/backend-*.tar.gz | head -1)
tar -xzf "\$LATEST_BACKEND" -C $REMOTE_APP_DIR/backend

# 备份旧前端
if [ -d "$REMOTE_FRONTEND_DIR/current" ]; then
  echo "📦 备份旧前端..."
  FRONTEND_BACKUP="$REMOTE_FRONTEND_DIR/backup-\$(date +%Y%m%d-%H%M%S)"
  mv $REMOTE_FRONTEND_DIR/current "\$FRONTEND_BACKUP"
fi

# 构建和部署前端
echo "📦 构建前端..."
FRONTEND_BUILD_DIR="/tmp/frontend-build-\$(date +%Y%m%d-%H%M%S)"
mkdir -p "\$FRONTEND_BUILD_DIR"

LATEST_FRONTEND_SRC=\$(ls -t /tmp/frontend-src-*.tar.gz | head -1)
tar -xzf "\$LATEST_FRONTEND_SRC" -C "\$FRONTEND_BUILD_DIR"

cd "\$FRONTEND_BUILD_DIR"
if [ -d "$(basename $FRONTEND_DIR)" ]; then
  cd "$(basename $FRONTEND_DIR)"
fi

# 安装依赖
echo "  📦 安装前端依赖..."
npm install --production=false

# 构建
echo "  🔨 构建前端应用..."
npm run build

# 部署构建结果
echo "  📦 部署前端构建结果..."
mkdir -p $REMOTE_FRONTEND_DIR/current
cp -r dist/* $REMOTE_FRONTEND_DIR/current/

# 设置权限
chown -R www-data:www-data $REMOTE_FRONTEND_DIR/current
chmod -R 755 $REMOTE_FRONTEND_DIR/current

# 清理临时文件
rm -rf "\$FRONTEND_BUILD_DIR"
rm -f /tmp/backend-*.tar.gz /tmp/frontend-src-*.tar.gz

echo "✅ 文件部署完成"

# 安装Python依赖
if [ ! -d "$REMOTE_APP_DIR/venv" ]; then
  echo "📦 创建Python虚拟环境..."
  python3 -m venv $REMOTE_APP_DIR/venv
fi

echo "📦 安装/更新Python依赖..."
$REMOTE_APP_DIR/venv/bin/pip install --upgrade pip --quiet
$REMOTE_APP_DIR/venv/bin/pip install -r $REMOTE_APP_DIR/backend/requirements.txt --quiet

# 重启后端服务
if systemctl is-active --quiet novawrite-backend 2>/dev/null; then
  echo "🔄 重启后端服务..."
  systemctl restart novawrite-backend
  sleep 2
  systemctl status novawrite-backend --no-pager -l || true
else
  echo "⚠️  后端服务未运行，请手动启动: systemctl start novawrite-backend"
fi

# 重启Nginx
if command -v nginx &> /dev/null; then
  echo "🔄 重启Nginx..."
  systemctl reload nginx 2>/dev/null || service nginx reload 2>/dev/null || true
fi

echo ""
echo "✅ 部署完成！"
echo ""
echo "📝 更新内容："
echo "  - 请求速率限制"
echo "  - 安全响应头"
echo "  - 刷新令牌机制"
echo "  - 改进的错误处理"
"@

# 将脚本保存到临时文件并上传
$TEMP_SCRIPT = "deploy-remote-temp.sh"
$DEPLOY_SCRIPT | Out-File -FilePath $TEMP_SCRIPT -Encoding utf8 -NoNewline
scp -P $SERVER_PORT $TEMP_SCRIPT "${SERVER}:/tmp/$TEMP_SCRIPT"
Remove-Item $TEMP_SCRIPT

# 执行部署脚本
ssh -p $SERVER_PORT $SERVER "chmod +x /tmp/$TEMP_SCRIPT; bash /tmp/$TEMP_SCRIPT; rm -f /tmp/$TEMP_SCRIPT"

# 5. 清理本地临时文件
Remove-Item -Force $BACKEND_PACKAGE -ErrorAction SilentlyContinue
Remove-Item -Force $FRONTEND_SRC_PACKAGE -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "🎉 部署完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📝 访问地址:" -ForegroundColor Cyan
Write-Host "  前端: http://66.154.108.62"
Write-Host "  API: http://66.154.108.62/api"
Write-Host "  API文档: http://66.154.108.62/api/docs"
Write-Host ""
Write-Host "✅ 安全更新已部署:" -ForegroundColor Green
Write-Host "  - 请求速率限制" -ForegroundColor White
Write-Host "  - 安全响应头" -ForegroundColor White
Write-Host "  - 刷新令牌机制" -ForegroundColor White
Write-Host "  - 改进的错误处理" -ForegroundColor White
Write-Host ""
Write-Host "注意事项:" -ForegroundColor Yellow
Write-Host "1. 检查服务状态: ssh $SERVER systemctl status novawrite-backend nginx" -ForegroundColor White
Write-Host "2. 查看服务日志: ssh $SERVER journalctl -u novawrite-backend -n 50" -ForegroundColor White
Write-Host ""

