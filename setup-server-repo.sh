#!/bin/bash
# 在服务器上首次设置代码库
set -e

echo "🔧 设置服务器代码库..."

REPO_DIR="/opt/novawrite-ai"
REPO_URL="git@codeup.aliyun.com:694907d19889c08d4ad2be2e/nova-ai.git"

# 检查目录是否存在
if [ -d "$REPO_DIR" ]; then
    echo "⚠️ 目录 $REPO_DIR 已存在"
    read -p "是否清空并重新克隆？(y/N): " confirm
    if [[ $confirm == [yY] ]]; then
        echo "📁 备份现有目录..."
        BACKUP_DIR="${REPO_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
        mv "$REPO_DIR" "$BACKUP_DIR"
        echo "✅ 已备份到 $BACKUP_DIR"
    else
        echo "❌ 操作取消"
        exit 1
    fi
fi

# 创建目录
mkdir -p "$REPO_DIR"
cd "$REPO_DIR"

# 克隆代码库
echo "📥 克隆代码库..."
git clone "$REPO_URL" .

# 设置部署脚本权限
chmod +x deploy-from-repo.sh

echo "✅ 代码库设置完成！"
echo ""
echo "下一步："
echo "1. 配置后端环境变量: cp backend/config.example.env backend/.env"
echo "2. 编辑 backend/.env 文件，填入实际配置"
echo "3. 运行初始化脚本（如果需要）"
echo "4. 运行部署脚本: ./deploy-from-repo.sh"


