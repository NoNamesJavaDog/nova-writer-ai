# Cloudflare WARP 配置指南

## 问题
服务器所在地区不支持 Gemini API，需要配置 Cloudflare WARP 代理来绕过地理位置限制。

## 配置步骤

### 1. 在服务器上配置 WARP

```bash
# SSH 连接到服务器
ssh root@66.154.108.62

# 运行配置脚本
cd /opt/novawrite-ai
git pull origin main
chmod +x backend/scripts/setup_warp.sh
bash backend/scripts/setup_warp.sh
```

### 2. 手动配置（如果脚本失败）

```bash
# 接受服务条款并设置代理模式
warp-cli --accept-tos mode proxy

# 连接 WARP
warp-cli --accept-tos connect

# 等待连接建立
sleep 5

# 检查状态
warp-cli status

# 检查代理端口（应该是 40000）
ss -tlnp | grep 40000
```

### 3. 配置环境变量

在 `/opt/novawrite-ai/backend/.env` 文件中添加：

```bash
GEMINI_PROXY=http://127.0.0.1:40000
```

或者如果 WARP 使用 SOCKS5（需要转换）：

```bash
GEMINI_PROXY=socks5://127.0.0.1:40000
```

### 4. 重启后端服务

```bash
systemctl restart novawrite-backend
systemctl status novawrite-backend
```

### 5. 验证配置

```bash
# 检查 WARP 状态
warp-cli status

# 测试代理连接
curl --proxy http://127.0.0.1:40000 https://www.cloudflare.com/cdn-cgi/trace/

# 检查后端日志
journalctl -u novawrite-backend -f | grep -i "代理\|proxy\|Gemini"
```

## 故障排除

### WARP 未连接
```bash
warp-cli disconnect
warp-cli --accept-tos connect
warp-cli status
```

### 代理端口未监听
```bash
# 检查端口
ss -tlnp | grep 40000

# 如果端口不存在，尝试：
warp-cli mode proxy
warp-cli connect
```

### Python 环境变量未生效
- 确保在 `.env` 文件中设置了 `GEMINI_PROXY`
- 重启后端服务
- 检查日志中是否有 "✅ Gemini API 代理已配置" 的消息

### 仍然出现地理位置限制错误
1. 验证 WARP 是否真的在运行：`warp-cli status`
2. 测试代理是否工作：`curl --proxy http://127.0.0.1:40000 https://ipinfo.io`
3. 检查代理地址是否正确设置在 `.env` 文件中
4. 查看后端日志确认代理已加载

## 注意事项

- WARP 免费版可能不支持所有地区，如遇到问题考虑升级到 WARP+
- 如果使用 SOCKS5 代理，可能需要安装额外的库（如 `pysocks`）
- 确保防火墙允许本地代理端口（40000）
