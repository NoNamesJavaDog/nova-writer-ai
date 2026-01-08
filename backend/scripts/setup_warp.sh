#!/bin/bash
# Cloudflare WARP 配置脚本
# 用于在服务器上配置 WARP 以绕过 Gemini API 的地理位置限制

set -e

echo "🚀 开始配置 Cloudflare WARP..."

# 检查 WARP 是否已安装
if ! command -v warp-cli &> /dev/null; then
    echo "❌ WARP CLI 未安装，请先安装 Cloudflare WARP"
    exit 1
fi

# 接受服务条款并注册（如果尚未注册）
echo "📝 接受服务条款并注册 WARP..."
warp-cli --accept-tos registration new || echo "⚠️  注册可能已完成，继续..."

# 设置代理模式
echo "🔧 配置代理模式..."
warp-cli --accept-tos mode proxy || echo "⚠️  代理模式可能已设置"

# 连接 WARP
echo "🔌 连接 WARP..."
warp-cli --accept-tos connect || echo "⚠️  连接可能已建立"

# 等待连接建立
sleep 3

# 检查状态
echo "📊 WARP 状态："
warp-cli --accept-tos status

# 检查代理端口
echo ""
echo "🔍 检查代理端口..."
if ss -tlnp | grep -q "127.0.0.1:40000"; then
    echo "✅ WARP HTTP 代理已在端口 40000 上运行"
else
    echo "⚠️  警告：未检测到端口 40000 上的代理服务"
    echo "   请检查 WARP 配置：warp-cli settings list"
fi

# 测试代理连接
echo ""
echo "🧪 测试代理连接..."
if curl -s --proxy http://127.0.0.1:40000 https://www.cloudflare.com/cdn-cgi/trace/ | grep -q "warp=on"; then
    echo "✅ WARP 代理工作正常"
else
    echo "⚠️  警告：WARP 代理测试未通过，但可能仍然可用"
fi

echo ""
echo "✅ WARP 配置完成！"
echo "   代理地址: http://127.0.0.1:40000"
echo "   请在 .env 文件中设置: GEMINI_PROXY=http://127.0.0.1:40000"
