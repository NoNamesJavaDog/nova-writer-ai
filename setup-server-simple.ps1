# 简化版：直接使用命令（解决换行符问题）
# 使用方法: .\setup-server-simple.ps1

$SERVER = "root@66.154.108.62"
$SERVER_PORT = "22"
$SETUP_SCRIPT_PATH = "deploy-setup.sh"

Write-Host "🚀 开始设置服务器环境..." -ForegroundColor Green

if (-not (Test-Path $SETUP_SCRIPT_PATH)) {
    Write-Host "❌ 错误：找不到 $SETUP_SCRIPT_PATH 文件" -ForegroundColor Red
    exit 1
}

Write-Host "📤 上传并执行初始化脚本..." -ForegroundColor Yellow

# 读取文件，转换为 Unix 格式，然后通过 SSH 执行
$content = Get-Content -Path $SETUP_SCRIPT_PATH -Raw -Encoding UTF8
# 替换 Windows 换行符 (CRLF) 为 Unix 换行符 (LF)
$content = $content -replace "`r`n", "`n"
$content = $content -replace "`r", "`n"

# 通过 SSH 执行
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
$bytes = $utf8NoBom.GetBytes($content)
$content = $utf8NoBom.GetString($bytes)

$content | ssh -p $SERVER_PORT $SERVER bash

Write-Host ""
Write-Host "✅ 服务器环境设置完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📝 下一步操作：" -ForegroundColor Cyan
Write-Host "1. 配置数据库和 .env 文件（SSH登录服务器）"
Write-Host "2. 运行部署脚本: .\deploy.ps1"
Write-Host ""


