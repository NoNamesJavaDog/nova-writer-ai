# PowerShell 脚本：通过 SSH 在服务器上执行初始化
# 使用方法: .\setup-server.ps1

$ErrorActionPreference = "Stop"

$SERVER = "root@66.154.108.62"
$SERVER_PORT = "22"
$SETUP_SCRIPT_PATH = "deploy-setup.sh"

Write-Host "🚀 开始设置服务器环境..." -ForegroundColor Green

# 检查脚本文件是否存在
if (-not (Test-Path $SETUP_SCRIPT_PATH)) {
    Write-Host "❌ 错误：找不到 $SETUP_SCRIPT_PATH 文件" -ForegroundColor Red
    exit 1
}

# 读取脚本内容并传递给 SSH
Write-Host "📤 上传并执行初始化脚本..." -ForegroundColor Yellow
$scriptContent = Get-Content -Path $SETUP_SCRIPT_PATH -Raw -Encoding UTF8

# 通过 SSH 执行脚本
ssh -p $SERVER_PORT $SERVER "bash -s" @"
$scriptContent
"@

Write-Host ""
Write-Host "✅ 服务器环境设置完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📝 下一步操作：" -ForegroundColor Cyan
Write-Host "1. 配置数据库和 .env 文件（SSH登录服务器）"
Write-Host "2. 运行部署脚本: .\deploy.ps1"
Write-Host ""


