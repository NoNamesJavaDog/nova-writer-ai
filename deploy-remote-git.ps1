# 从 Git 代码库部署到远程服务器
param(
    [string]$Server = "root@66.154.108.62"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 开始从 Git 代码库部署到服务器..." -ForegroundColor Cyan
Write-Host "服务器: $Server" -ForegroundColor Gray

# 步骤1: 初始化 Git 仓库并拉取代码
Write-Host "`n📦 步骤 1/4: 初始化 Git 仓库并拉取代码..." -ForegroundColor Yellow

$initScript = @"
cd /opt/novawrite-ai

# 备份 .env 文件
if [ -f backend/.env ]; then
  cp backend/.env /tmp/novawrite-env-backup.env
  echo 'Backed up .env file'
fi

# 初始化 Git
if [ ! -d .git ]; then
  git init
  git remote add origin git@codeup.aliyun.com:694907d19889c08d4ad2be2e/nova-ai.git 2>/dev/null || git remote set-url origin git@codeup.aliyun.com:694907d19889c08d4ad2be2e/nova-ai.git
fi

# 拉取代码
git fetch origin main 2>&1
git reset --hard origin/main 2>&1 || git pull origin main --allow-unrelated-histories 2>&1
git branch -M main 2>/dev/null

echo 'Code pulled successfully'
"@

ssh $Server $initScript

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 代码拉取失败" -ForegroundColor Red
    Write-Host "可能是 SSH 密钥问题，请在服务器上手动执行：" -ForegroundColor Yellow
    Write-Host "  ssh-keygen -t rsa" -ForegroundColor White
    Write-Host "  然后将 ~/.ssh/id_rsa.pub 添加到代码库的 SSH 密钥中" -ForegroundColor White
    exit 1
}

Write-Host "✅ 代码拉取成功" -ForegroundColor Green

# 步骤2: 恢复 .env 文件
Write-Host "`n📝 步骤 2/4: 恢复配置文件..." -ForegroundColor Yellow

$restoreScript = @"
cd /opt/novawrite-ai
if [ -f /tmp/novawrite-env-backup.env ]; then
  mkdir -p backend
  cp /tmp/novawrite-env-backup.env backend/.env
  echo 'Restored .env file'
else
  echo 'No .env backup found'
fi
"@

ssh $Server $restoreScript
Write-Host "✅ 配置文件已恢复" -ForegroundColor Green

# 步骤3: 设置脚本权限
Write-Host "`n🔧 步骤 3/4: 设置脚本权限..." -ForegroundColor Yellow

$chmodScript = @"
cd /opt/novawrite-ai
chmod +x deploy-from-repo.sh 2>/dev/null || true
chmod +x setup-server-repo.sh 2>/dev/null || true
ls -la deploy-from-repo.sh 2>/dev/null || echo 'deploy-from-repo.sh not found'
"@

ssh $Server $chmodScript
Write-Host "✅ 权限设置完成" -ForegroundColor Green

# 步骤4: 执行部署脚本
Write-Host "`n🚀 步骤 4/4: 执行部署脚本..." -ForegroundColor Yellow

$deployScript = @"
cd /opt/novawrite-ai
if [ -f deploy-from-repo.sh ]; then
  bash deploy-from-repo.sh
else
  echo 'Deploy script not found, checking files...'
  ls -la *.sh 2>/dev/null || echo 'No shell scripts found'
fi
"@

ssh $Server $deployScript

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ 部署成功完成！" -ForegroundColor Green
} else {
    Write-Host "`n❌ 部署过程中出现错误，请检查上面的输出" -ForegroundColor Red
    exit 1
}

Write-Host "`n🎉 所有步骤完成！" -ForegroundColor Green

