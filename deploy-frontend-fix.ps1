# 部署修复后的前端到服务器
# 使用方法: .\deploy-frontend-fix.ps1

$ErrorActionPreference = "Continue"

$SERVER = "root@66.154.108.62"
$SERVER_PORT = "22"
$FRONTEND_DIR = "novawrite-ai---professional-novel-assistant"
$REMOTE_SOURCE_DIR = "/tmp/novawrite-source"
$REMOTE_DEPLOY_DIR = "/var/www/novawrite-ai/current"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  部署修复后的前端" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查目录
if (-not (Test-Path $FRONTEND_DIR)) {
    Write-Host "❌ 错误：找不到前端目录" -ForegroundColor Red
    exit 1
}

# 1. 打包前端源代码
Write-Host "[1/4] 打包前端源代码..." -ForegroundColor Yellow
$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$SOURCE_PACKAGE = "frontend-source-$TIMESTAMP.tar.gz"

Set-Location $FRONTEND_DIR
tar -czf "../$SOURCE_PACKAGE" --exclude=node_modules --exclude=dist --exclude=.git .
Set-Location ..

if (-not (Test-Path $SOURCE_PACKAGE)) {
    Write-Host "❌ 打包失败" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 打包完成: $SOURCE_PACKAGE" -ForegroundColor Green

# 2. 上传到服务器
Write-Host ""
Write-Host "[2/4] 上传到服务器..." -ForegroundColor Yellow
scp -P $SERVER_PORT $SOURCE_PACKAGE "${SERVER}:/tmp/"

Write-Host "✅ 上传完成" -ForegroundColor Green

# 3. 在服务器上构建
Write-Host ""
Write-Host "[3/4] 在服务器上构建..." -ForegroundColor Yellow

$buildScript = @"
set -e
cd /tmp
rm -rf $REMOTE_SOURCE_DIR
mkdir -p $REMOTE_SOURCE_DIR
tar -xzf $SOURCE_PACKAGE -C $REMOTE_SOURCE_DIR
cd $REMOTE_SOURCE_DIR

echo "安装依赖..."
npm install --production=false

echo "构建前端..."
export VITE_API_BASE_URL=""
npm run build

if [ ! -d "dist" ]; then
  echo "❌ 构建失败"
  exit 1
fi

echo "✅ 构建完成"
"@

$buildScript | ssh -p $SERVER_PORT $SERVER "bash"

# 4. 部署
Write-Host ""
Write-Host "[4/4] 部署到服务器..." -ForegroundColor Yellow

$deployScript = @"
set -e

# 备份
if [ -d "$REMOTE_DEPLOY_DIR" ]; then
  BACKUP_DIR="/var/www/novawrite-ai/backup-$(date +%Y%m%d-%H%M%S)"
  mkdir -p `$BACKUP_DIR
  cp -r $REMOTE_DEPLOY_DIR/* `$BACKUP_DIR/ 2>/dev/null || true
  echo "已备份到: `$BACKUP_DIR"
fi

# 部署
mkdir -p $REMOTE_DEPLOY_DIR
cp -r /tmp/$REMOTE_SOURCE_DIR/dist/* $REMOTE_DEPLOY_DIR/

# 权限
chown -R nginx:nginx $REMOTE_DEPLOY_DIR
chmod -R 755 $REMOTE_DEPLOY_DIR

# 清理
rm -f /tmp/$SOURCE_PACKAGE
rm -rf /tmp/$REMOTE_SOURCE_DIR

echo "✅ 部署完成"
"@

$deployScript | ssh -p $SERVER_PORT $SERVER "bash"

# 清理本地文件
Remove-Item $SOURCE_PACKAGE -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access URL: http://66.154.108.62" -ForegroundColor Cyan
Write-Host ""
Write-Host "Please clear browser cache" -ForegroundColor Yellow
Write-Host ""

