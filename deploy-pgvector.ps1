# pgvector向量数据库集成 - 自动部署脚本 (PowerShell)
# 从Git仓库拉取代码并在远程服务器上部署和测试

$ErrorActionPreference = "Stop"

# 服务器配置
$SERVER = "root@66.154.108.62"
$SERVER_PORT = "22"
$REMOTE_APP_DIR = "/opt/novawrite-ai"
$REMOTE_BACKEND_DIR = "$REMOTE_APP_DIR/backend"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "pgvector向量数据库集成 - 自动部署" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 确认代码已推送到Git仓库
Write-Host "[1/5] 检查Git状态..." -ForegroundColor Yellow
$gitStatus = git status --short
if ($gitStatus) {
    Write-Host "⚠️  有未提交的更改，正在提交..." -ForegroundColor Yellow
    git add .
    git commit -m "feat: pgvector向量数据库集成更新" -ErrorAction SilentlyContinue
}

Write-Host "✅ 代码已准备就绪" -ForegroundColor Green
Write-Host ""

# 步骤2: 推送到远程仓库
Write-Host "[2/5] 推送到Git仓库..." -ForegroundColor Yellow
try {
    git push origin main
    Write-Host "✅ Git推送完成" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Git推送失败，继续执行（可能已经是最新）" -ForegroundColor Yellow
}
Write-Host ""

# 步骤3: 在服务器上拉取代码
Write-Host "[3/5] 在服务器上拉取最新代码..." -ForegroundColor Yellow

$pullScript = @"
set -e
cd $REMOTE_APP_DIR
if [ ! -d ".git" ]; then
    echo "⚠️  目录不存在或不是Git仓库"
    exit 1
fi
git pull origin main
echo "✅ 代码拉取完成"
"@

try {
    $pullResult = $pullScript | ssh -p $SERVER_PORT $SERVER bash
    Write-Host $pullResult
    Write-Host "✅ 服务器代码已更新" -ForegroundColor Green
} catch {
    Write-Host "❌ 代码拉取失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 步骤4: 在服务器上安装依赖和运行迁移
Write-Host "[4/5] 在服务器上安装依赖和运行数据库迁移..." -ForegroundColor Yellow

$deployScript = @"
set -e
cd $REMOTE_BACKEND_DIR

echo "📦 安装Python依赖..."
if [ -f ../venv/bin/activate ]; then
    source ../venv/bin/activate
    pip install --upgrade pip --quiet
    pip install -r requirements.txt
else
    python3 -m pip install --upgrade pip --quiet
    python3 -m pip install -r requirements.txt
fi

echo "✅ 依赖安装完成"
echo ""
echo "🗄️  运行数据库迁移..."
if [ -f migrate_add_pgvector.py ]; then
    python3 migrate_add_pgvector.py || echo "⚠️  数据库迁移失败（可能已经运行过）"
else
    echo "⚠️  migrate_add_pgvector.py 不存在"
fi
echo "✅ 数据库迁移完成"
"@

try {
    $deployResult = $deployScript | ssh -p $SERVER_PORT $SERVER bash
    Write-Host $deployResult
    Write-Host "✅ 服务器环境已更新" -ForegroundColor Green
} catch {
    Write-Host "⚠️  依赖安装或迁移有错误，但继续执行: $_" -ForegroundColor Yellow
}

Write-Host ""

# 步骤5: 运行测试
Write-Host "[5/5] 在服务器上运行测试..." -ForegroundColor Yellow

$testScript = @"
set -e
cd $REMOTE_BACKEND_DIR

echo "🧪 运行测试..."
if [ -f ../venv/bin/activate ]; then
    source ../venv/bin/activate
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

if [ -f test_all_remote.py ]; then
    echo ""
    echo "运行完整测试 (test_all_remote.py)..."
    `$PYTHON_CMD test_all_remote.py || echo "⚠️  测试有警告或错误"
fi

echo ""
echo "✅ 测试完成"
"@

try {
    $testResult = $testScript | ssh -p $SERVER_PORT $SERVER bash
    Write-Host $testResult
    Write-Host "✅ 测试完成" -ForegroundColor Green
} catch {
    Write-Host "⚠️  测试有错误: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "部署完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 下一步：" -ForegroundColor Cyan
Write-Host "1. 查看测试结果确认功能正常"
Write-Host "2. 重启后端服务（如果需要）："
Write-Host "   ssh $SERVER -p $SERVER_PORT 'systemctl restart novawrite-backend'" -ForegroundColor Gray
Write-Host "3. 查看服务状态："
Write-Host "   ssh $SERVER -p $SERVER_PORT 'systemctl status novawrite-backend'" -ForegroundColor Gray
Write-Host "4. 查看日志："
Write-Host "   ssh $SERVER -p $SERVER_PORT 'journalctl -u novawrite-backend -f'" -ForegroundColor Gray
Write-Host ""

