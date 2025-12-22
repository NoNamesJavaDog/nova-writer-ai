# 本地部署脚本 - 提交代码并部署到服务器
param(
    [string]$Message = "Update code",
    [string]$Server = "root@66.154.108.62",
    [switch]$SkipPush = $false,
    [switch]$SkipDeploy = $false
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 开始部署流程..." -ForegroundColor Cyan

# 1. 提交代码到 Git
if (-not $SkipPush) {
    Write-Host "`n📝 步骤 1/3: 提交代码到 Git..." -ForegroundColor Yellow
    
    $gitDir = "C:\software\terol\terol"
    if (-not (Test-Path $gitDir)) {
        Write-Host "❌ 错误: 找不到项目目录 $gitDir" -ForegroundColor Red
        exit 1
    }
    
    Push-Location $gitDir
    
    try {
        # 检查是否有更改
        $status = git status --porcelain 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️ Git 命令失败，请确保已安装 Git 并添加到 PATH" -ForegroundColor Yellow
            Write-Host "请手动执行以下命令：" -ForegroundColor Yellow
            Write-Host "  cd $gitDir" -ForegroundColor White
            Write-Host "  git add ." -ForegroundColor White
            Write-Host "  git commit -m `"$Message`"" -ForegroundColor White
            Write-Host "  git push origin main" -ForegroundColor White
            $SkipPush = $true
        } elseif ($status) {
            Write-Host "发现更改，正在提交..." -ForegroundColor Cyan
            git add .
            git commit -m $Message
            if ($LASTEXITCODE -eq 0) {
                git push origin main
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✅ 代码已推送到远程仓库" -ForegroundColor Green
                } else {
                    Write-Host "❌ 推送失败，请检查网络连接和 SSH 配置" -ForegroundColor Red
                    exit 1
                }
            } else {
                Write-Host "❌ 提交失败" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "ℹ️ 没有需要提交的更改" -ForegroundColor Gray
        }
    } finally {
        Pop-Location
    }
} else {
    Write-Host "`n⏭️ 跳过 Git 提交步骤" -ForegroundColor Gray
}

# 2. 在服务器上拉取并部署
if (-not $SkipDeploy) {
    Write-Host "`n📦 步骤 2/3: 在服务器上拉取代码并部署..." -ForegroundColor Yellow
    
    # 构建 SSH 命令
    $sshCommand = "cd /opt/novawrite-ai && git pull origin main && ./deploy-from-repo.sh"
    
    Write-Host "正在连接到服务器并执行部署..." -ForegroundColor Cyan
    Write-Host "服务器: $Server" -ForegroundColor Gray
    
    ssh $Server $sshCommand
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 部署完成！" -ForegroundColor Green
    } else {
        Write-Host "❌ 部署失败，请检查服务器连接和脚本执行情况" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "`n⏭️ 跳过服务器部署步骤" -ForegroundColor Gray
}

Write-Host "`n🎉 部署流程完成！" -ForegroundColor Green
Write-Host "`n如果 Git 命令失败，请手动执行 Git 操作，然后运行：" -ForegroundColor Yellow
Write-Host "  .\deploy.ps1 -SkipPush -Message `"dummy`"" -ForegroundColor White
