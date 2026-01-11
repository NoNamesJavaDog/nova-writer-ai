#!/bin/bash

# 设置颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "🚀 NovaWrite AI - 本地启动脚本"
echo "========================================"
echo ""

# 检查是否在项目根目录
if [ ! -d "backend" ]; then
    echo -e "${RED}❌ 错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 错误: 未安装 Python3${NC}"
    exit 1
fi

echo ""
echo "📋 步骤 1/5: 检查环境配置"
echo "========================================"

# 检查后端 .env
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠️  警告: backend/.env 不存在，复制模板...${NC}"
    cp backend/.env.example backend/.env
    echo ""
    echo "📝 请编辑 backend/.env 文件，设置以下配置:"
    echo "   - GEMINI_API_KEY（必填）"
    echo "   - DATABASE_URL（如果不是默认值）"
    echo ""
    read -p "按 Enter 继续..."
fi

# 检查微服务 .env
if [ ! -f "nova-ai-service/.env" ]; then
    echo -e "${YELLOW}⚠️  警告: nova-ai-service/.env 不存在，复制模板...${NC}"
    cp nova-ai-service/.env.example nova-ai-service/.env
    echo ""
    echo "📝 请编辑 nova-ai-service/.env 文件，设置 GEMINI_API_KEY"
    echo ""
    read -p "按 Enter 继续..."
fi

echo -e "${GREEN}✅ 环境配置检查完成${NC}"
echo ""

echo "📋 步骤 2/5: 初始化数据库"
echo "========================================"
cd backend
python3 ../scripts/init_local_db.py
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ 数据库初始化失败！${NC}"
    echo "💡 请检查:"
    echo "   1. PostgreSQL 是否正在运行"
    echo "   2. DATABASE_URL 配置是否正确"
    echo "   3. 数据库用户是否有创建表的权限"
    cd ..
    exit 1
fi
cd ..

echo ""
echo -e "${GREEN}✅ 数据库初始化完成${NC}"
echo ""

echo "📋 步骤 3/5: 启动 AI 微服务 (端口 8001)"
echo "========================================"
cd nova-ai-service

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
pip install -r requirements.txt -q

# 后台启动微服务
nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload > ../logs/ai-service.log 2>&1 &
AI_SERVICE_PID=$!
echo $AI_SERVICE_PID > ../logs/ai-service.pid
echo -e "${GREEN}✅ AI 微服务已启动 (PID: $AI_SERVICE_PID)${NC}"

deactivate
cd ..

echo "⏳ 等待 AI 微服务启动 (15秒)..."
sleep 15

echo ""
echo "📋 步骤 4/5: 启动主应用后端 (端口 8000)"
echo "========================================"
cd backend

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
pip install -r requirements.txt -q

# 后台启动主应用
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid
echo -e "${GREEN}✅ 主应用已启动 (PID: $BACKEND_PID)${NC}"

deactivate
cd ..

echo "⏳ 等待主应用启动 (10秒)..."
sleep 10

echo ""
echo "📋 步骤 5/5: 验证服务状态"
echo "========================================"
echo ""

# 创建 logs 目录
mkdir -p logs

echo "🔍 检查 AI 微服务 (http://localhost:8001)..."
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ AI 微服务运行正常${NC}"
else
    echo -e "${YELLOW}⚠️  AI 微服务可能还未完全启动，请稍等片刻${NC}"
fi

echo ""
echo "🔍 检查主应用 (http://localhost:8000)..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 主应用运行正常${NC}"
else
    echo -e "${YELLOW}⚠️  主应用可能还未完全启动，请稍等片刻${NC}"
fi

echo ""
echo "========================================"
echo "🎉 启动完成！"
echo "========================================"
echo ""
echo "📡 服务访问地址:"
echo "   AI 微服务:  http://localhost:8001"
echo "   API 文档:   http://localhost:8001/docs"
echo "   主应用:     http://localhost:8000"
echo "   主应用文档: http://localhost:8000/docs"
echo ""
echo "📝 日志文件:"
echo "   AI 微服务:  logs/ai-service.log"
echo "   主应用:     logs/backend.log"
echo ""
echo "🛑 停止服务:"
echo "   ./scripts/stop_local.sh"
echo ""
echo "💡 提示:"
echo "   - 查看 AI 微服务日志: tail -f logs/ai-service.log"
echo "   - 查看主应用日志: tail -f logs/backend.log"
echo ""
