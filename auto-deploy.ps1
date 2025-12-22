# 自动部署脚本 - 完整流程
# 使用方法: .\auto-deploy.ps1

$ErrorActionPreference = "Continue"  # 改为 Continue 以便继续执行

$SERVER = "root@66.154.108.62"
$SERVER_PORT = "22"
$REMOTE_APP_DIR = "/opt/novawrite-ai"
$REMOTE_FRONTEND_DIR = "/var/www/novawrite-ai"
$BACKEND_DIR = "backend"
$FRONTEND_DIR = "novawrite-ai---professional-novel-assistant"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NovaWrite AI 自动部署脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查目录
if (-not (Test-Path $BACKEND_DIR) -or -not (Test-Path $FRONTEND_DIR)) {
    Write-Host "❌ 错误：请在项目根目录执行此脚本" -ForegroundColor Red
    Write-Host "当前目录: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

# 1. 构建前端
Write-Host "[1/6] 构建前端..." -ForegroundColor Yellow
Set-Location $FRONTEND_DIR

# 检查 npm
$npmPath = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npmPath) {
    Write-Host "⚠️  npm 未找到，尝试查找 Node.js..." -ForegroundColor Yellow
    $nodePath = Get-Command node -ErrorAction SilentlyContinue
    if (-not $nodePath) {
        Write-Host "❌ 未找到 Node.js 和 npm，请先安装 Node.js" -ForegroundColor Red
        Write-Host "   下载地址: https://nodejs.org/" -ForegroundColor Yellow
        Set-Location ..
        exit 1
    }
}

# 设置环境变量
$env:VITE_API_BASE_URL = "http://66.154.108.62"

# 安装依赖（如果需要）
if (-not (Test-Path "node_modules")) {
    Write-Host "   安装前端依赖..." -ForegroundColor Gray
    npm install
}

# 构建
Write-Host "   构建前端应用..." -ForegroundColor Gray
npm run build

if (-not (Test-Path "dist")) {
    Write-Host "❌ 前端构建失败" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host "✅ 前端构建完成" -ForegroundColor Green
Set-Location ..

# 2. 打包后端
Write-Host ""
Write-Host "[2/6] 打包后端..." -ForegroundColor Yellow
$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$BACKEND_PACKAGE = "backend-$TIMESTAMP.tar.gz"

Set-Location $BACKEND_DIR
tar -czf "../$BACKEND_PACKAGE" --exclude=__pycache__ --exclude=*.pyc --exclude=.env --exclude=.git * 2>$null
Set-Location ..

if (-not (Test-Path $BACKEND_PACKAGE)) {
    Write-Host "❌ 后端打包失败" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 后端打包完成: $BACKEND_PACKAGE" -ForegroundColor Green

# 3. 打包前端
Write-Host ""
Write-Host "[3/6] 打包前端..." -ForegroundColor Yellow
$FRONTEND_PACKAGE = "frontend-$TIMESTAMP.tar.gz"

Set-Location "$FRONTEND_DIR\dist"
tar -czf "..\..\$FRONTEND_PACKAGE" * 2>$null
Set-Location ..\..

if (-not (Test-Path $FRONTEND_PACKAGE)) {
    Write-Host "❌ 前端打包失败" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 前端打包完成: $FRONTEND_PACKAGE" -ForegroundColor Green

# 4. 上传到服务器
Write-Host ""
Write-Host "[4/6] 上传到服务器..." -ForegroundColor Yellow
scp -P $SERVER_PORT $BACKEND_PACKAGE "${SERVER}:/tmp/"
scp -P $SERVER_PORT $FRONTEND_PACKAGE "${SERVER}:/tmp/"

Write-Host "✅ 上传完成" -ForegroundColor Green

# 5. 在服务器上部署
Write-Host ""
Write-Host "[5/6] 在服务器上部署..." -ForegroundColor Yellow

# 使用独立的部署脚本文件
$deployScriptFile = "deploy-remote.sh"
if (-not (Test-Path $deployScriptFile)) {
    Write-Host "❌ 错误：找不到 $deployScriptFile" -ForegroundColor Red
    exit 1
}

# 上传部署脚本
scp -P $SERVER_PORT $deployScriptFile "${SERVER}:/tmp/"
$remoteScript = "/tmp/$deployScriptFile"

# 执行部署脚本
$sshCommand = "chmod +x $remoteScript; bash $remoteScript; rm -f $remoteScript"
ssh -p $SERVER_PORT $SERVER $sshCommand

Write-Host "✅ 服务器部署完成" -ForegroundColor Green

# 6. 清理本地文件
Write-Host ""
Write-Host "[6/6] 清理临时文件..." -ForegroundColor Yellow
Remove-Item -Force $BACKEND_PACKAGE -ErrorAction SilentlyContinue
Remove-Item -Force $FRONTEND_PACKAGE -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🎉 部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "访问地址:" -ForegroundColor Cyan
Write-Host "  前端: http://66.154.108.62" -ForegroundColor White
Write-Host "  API: http://66.154.108.62/api" -ForegroundColor White
Write-Host "  API文档: http://66.154.108.62/api/docs" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  重要提示:" -ForegroundColor Yellow
Write-Host "1. 确保服务器上已配置 .env 文件（数据库、SECRET_KEY等）" -ForegroundColor White
Write-Host "2. 如果首次部署，需要初始化数据库:" -ForegroundColor White
$initDbCmd = "ssh $SERVER -p $SERVER_PORT 'cd $REMOTE_APP_DIR/backend; source ../venv/bin/activate; python init_db.py'"
Write-Host "   $initDbCmd" -ForegroundColor Gray
Write-Host "3. 启动后端服务:" -ForegroundColor White
$startCmd = "ssh $SERVER -p $SERVER_PORT 'systemctl start novawrite-backend; systemctl enable novawrite-backend'"
Write-Host "   $startCmd" -ForegroundColor Gray
Write-Host "4. 检查服务状态:" -ForegroundColor White
$statusCmd = "ssh $SERVER -p $SERVER_PORT 'systemctl status novawrite-backend nginx'"
Write-Host "   $statusCmd" -ForegroundColor Gray
Write-Host ""

