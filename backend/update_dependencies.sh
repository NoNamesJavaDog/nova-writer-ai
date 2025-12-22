#!/bin/bash
# 更新 Python 依赖包的脚本
# 使用方法: ./update_dependencies.sh

echo "=========================================="
echo "  更新 Python 依赖包"
echo "=========================================="
echo ""

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 已激活虚拟环境"
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
    echo "✅ 已激活虚拟环境"
else
    echo "❌ 未找到虚拟环境"
    exit 1
fi

# 备份当前依赖
echo ""
echo "[1/4] 备份当前依赖..."
cp requirements.txt requirements.txt.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ 已备份到 requirements.txt.backup.*"

# 检查过期包
echo ""
echo "[2/4] 检查过期包..."
pip list --outdated

# 升级 pip
echo ""
echo "[3/4] 升级 pip..."
pip install --upgrade pip

# 更新依赖包
echo ""
echo "[4/4] 更新依赖包..."
pip install --upgrade -r requirements.txt

echo ""
echo "=========================================="
echo "  ✅ 依赖包更新完成！"
echo "=========================================="
echo ""
echo "建议："
echo "  1. 运行测试确保功能正常"
echo "  2. 查看 requirements.txt.backup.* 了解变更"
echo "  3. 如有问题，可以恢复备份: cp requirements.txt.backup.* requirements.txt"
echo ""


