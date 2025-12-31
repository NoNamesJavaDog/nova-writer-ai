# PowerShell 部署脚本
# 部署到远程服务器 root@66.154.108.62

$ErrorActionPreference = "Stop"

$SERVER = "root@66.154.108.62"
$REMOTE_DIR = "/var/www/novawrite-ai"
$LOCAL_BUILD_DIR = "dist"

Write-Host "🚀 开始部署流程..." -ForegroundColor Green

# 1. 构建项目
Write-Host "📦 正在构建项目..." -ForegroundColor Yellow
npm run build

if (-not (Test-Path $LOCAL_BUILD_DIR)) {
    Write-Host "❌ 构建失败：找不到 dist 目录" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 构建完成" -ForegroundColor Green

# 2. 创建临时部署包
Write-Host "📦 正在打包..." -ForegroundColor Yellow
$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$DEPLOY_PACKAGE = "deploy-$TIMESTAMP.tar.gz"

# 使用 tar 命令打包（Windows 10+ 支持）
Set-Location $LOCAL_BUILD_DIR
tar -czf "../$DEPLOY_PACKAGE" *
Set-Location ..

Write-Host "✅ 打包完成: $DEPLOY_PACKAGE" -ForegroundColor Green

# 3. 上传到服务器
Write-Host "📤 正在上传到服务器..." -ForegroundColor Yellow
scp $DEPLOY_PACKAGE "${SERVER}:/tmp/"

Write-Host "✅ 上传完成" -ForegroundColor Green

# 4. 在服务器上部署
Write-Host "🔧 正在服务器上部署..." -ForegroundColor Yellow

$DEPLOY_SCRIPT = @"
set -e

# 创建部署目录
mkdir -p /var/www/novawrite-ai

# 备份旧版本（如果存在）
if [ -d "/var/www/novawrite-ai/current" ]; then
  echo "📦 备份旧版本..."
  BACKUP_DIR="/var/www/novawrite-ai/backup-$(date +%Y%m%d-%H%M%S)"
  mv /var/www/novawrite-ai/current `$BACKUP_DIR
  echo "✅ 已备份到: `$BACKUP_DIR"
fi

# 创建新版本目录
NEW_DIR="/var/www/novawrite-ai/current"
mkdir -p `$NEW_DIR

# 解压新版本
LATEST_PACKAGE=`$(ls -t /tmp/deploy-*.tar.gz | head -1)
echo "📦 解压: `$LATEST_PACKAGE"
tar -xzf `$LATEST_PACKAGE -C `$NEW_DIR

# 设置权限
chown -R www-data:www-data `$NEW_DIR
chmod -R 755 `$NEW_DIR

# 清理临时文件
rm -f /tmp/deploy-*.tar.gz

echo "✅ 部署完成"

# 重启nginx（如果存在）
if command -v nginx &> /dev/null; then
  echo "🔄 重启nginx..."
  systemctl reload nginx || service nginx reload
  echo "✅ nginx已重启"
fi
"@

# 执行部署脚本
echo $DEPLOY_SCRIPT | ssh $SERVER bash

# 5. 清理本地临时文件
Remove-Item $DEPLOY_PACKAGE -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "🎉 部署完成！" -ForegroundColor Green
Write-Host "📝 访问地址: http://66.154.108.62" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  注意：" -ForegroundColor Yellow
Write-Host "1. 确保服务器上已安装并配置nginx"
Write-Host "2. 确保nginx配置指向: $REMOTE_DIR/current"
Write-Host "3. 如需配置HTTPS，请使用Let's Encrypt"

