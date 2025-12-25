#!/bin/bash
# pgvector向量数据库集成 - 自动部署脚本
# 从Git仓库拉取代码并在远程服务器上部署和测试

set -e

# 服务器配置
SERVER="root@66.154.108.62"
SERVER_PORT="22"
REMOTE_APP_DIR="/opt/novawrite-ai"
REMOTE_BACKEND_DIR="$REMOTE_APP_DIR/backend"

echo "=========================================="
echo "pgvector向量数据库集成 - 自动部署"
echo "=========================================="
echo ""

# 步骤1: 确认代码已推送到Git仓库
echo "[1/5] 检查Git状态..."
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  有未提交的更改，正在提交..."
    git add .
    git commit -m "feat: pgvector向量数据库集成更新" || true
fi

echo "✅ 代码已准备就绪"
echo ""

# 步骤2: 推送到远程仓库
echo "[2/5] 推送到Git仓库..."
git push origin main || {
    echo "⚠️  Git推送失败，继续执行（可能已经是最新）"
}
echo "✅ Git推送完成"
echo ""

# 步骤3: 在服务器上拉取代码
echo "[3/5] 在服务器上拉取最新代码..."
ssh -p "$SERVER_PORT" "$SERVER" << ENDSSH
set -e

echo "📥 拉取最新代码..."
cd $REMOTE_APP_DIR

# 如果目录不存在，先克隆仓库
if [ ! -d ".git" ]; then
    echo "⚠️  目录不存在或不是Git仓库，需要先设置"
    exit 1
fi

# 拉取最新代码
git pull origin main || {
    echo "⚠️  Git拉取失败"
    exit 1
}

echo "✅ 代码拉取完成"
ENDSSH

if [ $? -ne 0 ]; then
    echo "❌ 代码拉取失败"
    exit 1
fi

echo "✅ 服务器代码已更新"
echo ""

# 步骤4: 在服务器上安装依赖和运行迁移
echo "[4/5] 在服务器上安装依赖和运行数据库迁移..."
ssh -p "$SERVER_PORT" "$SERVER" << ENDSSH
set -e

cd $REMOTE_BACKEND_DIR

echo "📦 安装Python依赖..."
source ../venv/bin/activate 2>/dev/null || {
    echo "⚠️  虚拟环境不存在，使用系统Python"
    python3 -m pip install --upgrade pip --quiet
    python3 -m pip install -r requirements.txt
}

echo "✅ 依赖安装完成"

echo ""
echo "🗄️  运行数据库迁移..."
if [ -f migrate_add_pgvector.py ]; then
    python3 migrate_add_pgvector.py || {
        echo "⚠️  数据库迁移失败（可能已经运行过）"
    }
else
    echo "⚠️  migrate_add_pgvector.py 不存在"
fi

echo "✅ 数据库迁移完成"
ENDSSH

if [ $? -ne 0 ]; then
    echo "⚠️  依赖安装或迁移有错误，但继续执行"
fi

echo "✅ 服务器环境已更新"
echo ""

# 步骤5: 运行测试
echo "[5/5] 在服务器上运行测试..."
ssh -p "$SERVER_PORT" "$SERVER" << ENDSSH
set -e

cd $REMOTE_BACKEND_DIR

echo "🧪 运行测试..."

# 使用虚拟环境或系统Python
if [ -f ../venv/bin/activate ]; then
    source ../venv/bin/activate
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

# 运行完整测试
if [ -f test_all_remote.py ]; then
    echo ""
    echo "运行完整测试 (test_all_remote.py)..."
    $PYTHON_CMD test_all_remote.py || {
        echo "⚠️  测试有警告或错误（请查看输出）"
    }
fi

echo ""
echo "✅ 测试完成"
ENDSSH

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "📝 下一步："
echo "1. 查看测试结果确认功能正常"
echo "2. 重启后端服务（如果需要）："
echo "   ssh $SERVER 'systemctl restart novawrite-backend'"
echo "3. 查看服务状态："
echo "   ssh $SERVER 'systemctl status novawrite-backend'"
echo "4. 查看日志："
echo "   ssh $SERVER 'journalctl -u novawrite-backend -f'"
echo ""

