# 替代方法：不依赖脚本文件执行，直接内联脚本内容
# 使用方法: .\setup-server-alt.ps1
# 或者使用: Get-Content deploy-setup.sh | ssh root@66.154.108.62 -p 22 bash

$ErrorActionPreference = "Stop"

$SERVER = "root@66.154.108.62"
$SERVER_PORT = "22"
$SETUP_SCRIPT_PATH = "deploy-setup.sh"

Write-Host "🚀 开始设置服务器环境..." -ForegroundColor Green

# 检查脚本文件是否存在
if (-not (Test-Path $SETUP_SCRIPT_PATH)) {
    Write-Host "❌ 错误：找不到 $SETUP_SCRIPT_PATH 文件" -ForegroundColor Red
    Write-Host "请确保在项目根目录执行此脚本" -ForegroundColor Yellow
    exit 1
}

# 方法：使用 Get-Content 管道并转换换行符（Windows CRLF -> Linux LF）
Write-Host "📤 上传并执行初始化脚本..." -ForegroundColor Yellow

# 读取文件内容并替换 Windows 换行符为 Unix 换行符
$scriptContent = Get-Content -Path $SETUP_SCRIPT_PATH -Raw -Encoding UTF8
$scriptContent = $scriptContent -replace "`r`n", "`n" -replace "`r", "`n"

# 通过 SSH 执行
$scriptContent | ssh -p $SERVER_PORT $SERVER bash

Write-Host ""
Write-Host "⚠️  注意：如果看到 'apt-get: command not found' 错误，说明服务器可能不是 Ubuntu/Debian 系统" -ForegroundColor Yellow
Write-Host "   请运行 .\check-server.ps1 检查服务器系统类型，或查看 TROUBLESHOOTING_DEPLOY.md" -ForegroundColor Yellow
Write-Host ""
Write-Host "✅ 脚本执行完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📝 下一步操作：" -ForegroundColor Cyan
Write-Host "1. 检查服务器环境是否完整（可选）: .\check-server.ps1"
Write-Host "2. 配置数据库和 .env 文件（SSH登录服务器）"
Write-Host "3. 运行部署脚本: .\deploy.ps1"
Write-Host ""

