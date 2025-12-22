# 快速重新部署前端（仅前端）
# 使用方法: .\quick-redeploy-frontend.ps1

$ErrorActionPreference = "Continue"

$SERVER = "root@66.154.108.62"
$SERVER_PORT = "22"
$FRONTEND_DIR = "novawrite-ai---professional-novel-assistant"
$REMOTE_FRONTEND_DIR = "/var/www/novawrite-ai"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  快速重新部署前端" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查目录
if (-not (Test-Path $FRONTEND_DIR)) {
    Write-Host "❌ 错误：找不到前端目录" -ForegroundColor Red
    exit 1
}

# 1. 构建前端
Write-Host "[1/3] 构建前端..." -ForegroundColor Yellow
Set-Location $FRONTEND_DIR

# 检查 npm
$npmPath = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npmPath) {
    Write-Host "❌ 错误：未找到 npm，请先安装 Node.js" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# 设置环境变量（使用相对路径）
$env:VITE_API_BASE_URL = ""

Write-Host "  使用 API 基础 URL: 相对路径" -ForegroundColor Gray

# 构建
Write-Host "  正在构建..." -ForegroundColor Gray
npm run build

if (-not (Test-Path "dist")) {
    Write-Host "❌ 前端构建失败" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host "✅ 前端构建完成" -ForegroundColor Green
Set-Location ..

# 2. 打包前端
Write-Host ""
Write-Host "[2/3] 打包前端..." -ForegroundColor Yellow
$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$FRONTEND_PACKAGE = "frontend-$TIMESTAMP.tar.gz"

tar -czf $FRONTEND_PACKAGE -C "$FRONTEND_DIR/dist" .

if (-not (Test-Path $FRONTEND_PACKAGE)) {
    Write-Host "❌ 打包失败" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 打包完成: $FRONTEND_PACKAGE" -ForegroundColor Green

# 3. 上传并部署
Write-Host ""
Write-Host "[3/3] 上传并部署..." -ForegroundColor Yellow

# 上传
Write-Host "  上传到服务器..." -ForegroundColor Gray
scp -P $SERVER_PORT $FRONTEND_PACKAGE "${SERVER}:/tmp/"

# 部署
Write-Host "  部署到服务器..." -ForegroundColor Gray

# 上传部署脚本
scp -P $SERVER_PORT deploy-frontend-remote.sh "${SERVER}:/tmp/"

# 执行部署
ssh -p $SERVER_PORT $SERVER "chmod +x /tmp/deploy-frontend-remote.sh; /tmp/deploy-frontend-remote.sh $FRONTEND_PACKAGE; rm -f /tmp/deploy-frontend-remote.sh"

# 清理本地打包文件
Remove-Item $FRONTEND_PACKAGE -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "访问地址: http://66.154.108.62" -ForegroundColor Cyan
Write-Host ""
Write-Host "如果仍有错误，请清除浏览器缓存后重试" -ForegroundColor Yellow
Write-Host ""

