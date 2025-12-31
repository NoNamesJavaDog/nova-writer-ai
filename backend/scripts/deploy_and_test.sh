#!/bin/bash
# pgvector 向量数据库集成 - 完整部署和测试脚本
# 在远程服务器上运行此脚本来部署和测试所有功能

set -e  # 遇到错误立即退出

echo "=========================================="
echo "pgvector 向量数据库集成 - 部署和测试"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✅ $1 已安装${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 未安装${NC}"
        return 1
    fi
}

# 步骤1: 检查前置要求
echo "=========================================="
echo "步骤1: 检查前置要求"
echo "=========================================="

# 检查Python
if ! check_command python3; then
    echo -e "${RED}请先安装Python 3.8+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "   Python版本: $PYTHON_VERSION"

# 检查pip
if ! check_command pip3; then
    echo -e "${YELLOW}尝试使用 python3 -m pip...${NC}"
    pip_cmd="python3 -m pip"
else
    pip_cmd="pip3"
fi

# 检查PostgreSQL
if ! check_command psql; then
    echo -e "${YELLOW}⚠️  psql未找到，请确保PostgreSQL已安装${NC}"
fi

# 检查Redis（可选）
if check_command redis-cli; then
    echo -e "${GREEN}✅ Redis已安装（可选）${NC}"
else
    echo -e "${YELLOW}⚠️  Redis未安装（可选，缓存功能将被禁用）${NC}"
fi

echo ""

# 步骤2: 检查环境变量
echo "=========================================="
echo "步骤2: 检查环境变量"
echo "=========================================="

if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env 文件不存在${NC}"
    echo "请创建 .env 文件并配置以下变量："
    echo "  GEMINI_API_KEY=your_api_key"
    echo "  DATABASE_URL=postgresql://user:password@host:port/database"
    echo ""
    read -p "是否继续？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env 文件存在${NC}"
    
    # 检查必要的环境变量
    source .env 2>/dev/null || true
    
    if [ -z "$GEMINI_API_KEY" ]; then
        echo -e "${YELLOW}⚠️  GEMINI_API_KEY 未设置${NC}"
    else
        echo -e "${GREEN}✅ GEMINI_API_KEY 已设置${NC}"
    fi
    
    if [ -z "$DATABASE_URL" ]; then
        echo -e "${YELLOW}⚠️  DATABASE_URL 未设置${NC}"
    else
        echo -e "${GREEN}✅ DATABASE_URL 已设置${NC}"
    fi
fi

echo ""

# 步骤3: 安装依赖
echo "=========================================="
echo "步骤3: 安装Python依赖"
echo "=========================================="

echo "升级pip..."
$pip_cmd install --upgrade pip --quiet

echo "安装依赖包..."
$pip_cmd install -r requirements.txt

echo -e "${GREEN}✅ 依赖安装完成${NC}"
echo ""

# 步骤4: 验证依赖安装
echo "=========================================="
echo "步骤4: 验证依赖安装"
echo "=========================================="

python3 << EOF
import sys
missing = []

try:
    import redis
    print("✅ redis")
except ImportError:
    print("⚠️  redis (可选)")
    missing.append('redis')

try:
    import sqlalchemy
    print(f"✅ sqlalchemy ({sqlalchemy.__version__})")
except ImportError:
    print("❌ sqlalchemy")
    missing.append('sqlalchemy')
    sys.exit(1)

try:
    import pgvector
    print("✅ pgvector")
except ImportError:
    print("❌ pgvector")
    missing.append('pgvector')
    sys.exit(1)

try:
    import google.genai
    print("✅ google-genai")
except ImportError:
    print("❌ google-genai")
    missing.append('google-genai')
    sys.exit(1)

if 'redis' in missing:
    print("\n⚠️  Redis未安装，缓存功能将被禁用")
else:
    print("\n✅ 所有依赖已安装")
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}依赖验证失败，请检查错误信息${NC}"
    exit 1
fi

echo ""

# 步骤5: 运行数据库迁移
echo "=========================================="
echo "步骤5: 运行数据库迁移"
echo "=========================================="

if [ -f migrate_add_pgvector.py ]; then
    echo "运行数据库迁移脚本..."
    python3 migrate_add_pgvector.py
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 数据库迁移完成${NC}"
    else
        echo -e "${RED}❌ 数据库迁移失败${NC}"
        echo "请检查数据库连接和权限"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  migrate_add_pgvector.py 不存在，跳过迁移${NC}"
fi

echo ""

# 步骤6: 运行测试
echo "=========================================="
echo "步骤6: 运行测试"
echo "=========================================="

# 6.1 完整测试
echo "6.1 运行完整测试 (test_all_remote.py)..."
if [ -f test_all_remote.py ]; then
    python3 test_all_remote.py
    test_result=$?
    
    if [ $test_result -eq 0 ]; then
        echo -e "${GREEN}✅ 完整测试通过${NC}"
    else
        echo -e "${YELLOW}⚠️  完整测试有警告或错误（请查看输出）${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  test_all_remote.py 不存在${NC}"
fi

echo ""

# 6.2 功能测试
echo "6.2 运行功能测试 (test_vector_features.py)..."
if [ -f test_vector_features.py ]; then
    python3 test_vector_features.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 功能测试通过${NC}"
    else
        echo -e "${YELLOW}⚠️  功能测试有警告或错误${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  test_vector_features.py 不存在${NC}"
fi

echo ""

# 6.3 API测试
echo "6.3 运行API测试 (test_embedding_simple.py)..."
if [ -f test_embedding_simple.py ]; then
    python3 test_embedding_simple.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ API测试通过${NC}"
    else
        echo -e "${YELLOW}⚠️  API测试有警告或错误${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  test_embedding_simple.py 不存在${NC}"
fi

echo ""

# 6.4 单元测试
echo "6.4 运行单元测试 (test_unit.py)..."
if [ -f test_unit.py ]; then
    python3 test_unit.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 单元测试通过${NC}"
    else
        echo -e "${YELLOW}⚠️  单元测试有警告或错误${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  test_unit.py 不存在${NC}"
fi

echo ""

# 总结
echo "=========================================="
echo "部署和测试总结"
echo "=========================================="
echo -e "${GREEN}✅ 部署完成！${NC}"
echo ""
echo "下一步："
echo "1. 查看测试结果，确保所有测试通过"
echo "2. 查看使用文档: PGVECTOR_README.md"
echo "3. 集成到API: 参考 api_integration_example.py"
echo "4. 开始使用向量数据库功能！"
echo ""
echo "=========================================="


