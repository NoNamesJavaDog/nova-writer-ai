#!/bin/bash

# 设置颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================"
echo "🛑 停止 NovaWrite AI 本地服务"
echo "========================================"
echo ""

# 停止 AI 微服务
if [ -f "logs/ai-service.pid" ]; then
    PID=$(cat logs/ai-service.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "停止 AI 微服务 (PID: $PID)..."
        kill $PID
        echo -e "${GREEN}✅ AI 微服务已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  AI 微服务未运行${NC}"
    fi
    rm logs/ai-service.pid
else
    echo -e "${YELLOW}⚠️  未找到 AI 微服务 PID 文件${NC}"
fi

echo ""

# 停止主应用
if [ -f "logs/backend.pid" ]; then
    PID=$(cat logs/backend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "停止主应用 (PID: $PID)..."
        kill $PID
        echo -e "${GREEN}✅ 主应用已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  主应用未运行${NC}"
    fi
    rm logs/backend.pid
else
    echo -e "${YELLOW}⚠️  未找到主应用 PID 文件${NC}"
fi

echo ""
echo "🎉 所有服务已停止"
