#!/bin/bash
# 依赖安装脚本（Linux/Mac）

echo "=========================================="
echo "安装 pgvector 向量数据库依赖"
echo "=========================================="

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

echo "✅ Python3 已安装: $(python3 --version)"

# 升级pip
echo ""
echo "升级 pip..."
python3 -m pip install --upgrade pip

# 安装依赖
echo ""
echo "安装依赖包..."
python3 -m pip install -r requirements.txt

# 验证安装
echo ""
echo "验证安装..."
python3 -c "
import sys
missing = []

try:
    import redis
    print('✅ redis')
except ImportError:
    print('⚠️  redis (可选)')
    missing.append('redis')

try:
    import sqlalchemy
    print('✅ sqlalchemy')
except ImportError:
    print('❌ sqlalchemy')
    missing.append('sqlalchemy')

try:
    import pgvector
    print('✅ pgvector')
except ImportError:
    print('❌ pgvector')
    missing.append('pgvector')

try:
    import google.genai
    print('✅ google-genai')
except ImportError:
    print('❌ google-genai')
    missing.append('google-genai')

if missing:
    print(f'\n⚠️  缺少依赖: {missing}')
    sys.exit(1)
else:
    print('\n✅ 所有依赖已安装')
"

echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="

