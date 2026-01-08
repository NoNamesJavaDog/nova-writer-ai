# Gemini API 代理配置指南

## 问题说明

Gemini API 对某些地区或数据中心的 IP 地址有访问限制。即使服务器位于美国，某些托管服务商的 IP 也可能被限制访问。

错误信息：
```
400 FAILED_PRECONDITION. {'error': {'code': 400, 'message': 'User location is not supported for the API use.', 'status': 'FAILED_PRECONDITION'}}
```

## 解决方案

配置 HTTP 代理以绕过地区限制。

### 1. 选择代理服务

推荐的代理服务选项：

#### 选项 A: 公共代理服务
- **Bright Data** (https://brightdata.com/)
- **Smartproxy** (https://smartproxy.com/)
- **Oxylabs** (https://oxylabs.io/)

#### 选项 B: 自建代理
- 在支持的地区（如美国西海岸、欧洲）部署一个简单的 HTTP 代理服务器
- 使用 Squid、Tinyproxy 或 Nginx 作为代理

#### 选项 C: Cloudflare Workers
- 创建一个 Cloudflare Worker 作为代理中转
- 免费且可靠

### 2. 配置代理

在服务器的 `.env` 文件中添加以下配置：

```bash
# Gemini API 代理配置
GEMINI_PROXY=http://proxy-host:proxy-port

# 如果代理需要认证，使用以下格式：
# GEMINI_PROXY=http://username:password@proxy-host:proxy-port
```

示例：
```bash
# 使用本地代理
GEMINI_PROXY=http://localhost:8888

# 使用远程代理
GEMINI_PROXY=http://proxy.example.com:3128

# 使用带认证的代理
GEMINI_PROXY=http://user:pass@proxy.example.com:3128
```

### 3. 重启服务

配置完成后，重启后端服务：

```bash
systemctl restart novawrite-backend
```

### 4. 验证配置

检查服务日志，应该看到代理配置成功的消息：

```bash
journalctl -u novawrite-backend -f
```

预期输出：
```
✅ Gemini API 代理已配置: http://proxy-host:port
```

### 5. 测试 API 调用

在服务器上运行测试脚本：

```bash
cd /opt/novawrite-ai/backend
source /opt/novawrite-ai/venv/bin/activate
python3 -c "
import os
import sys
sys.path.insert(0, '/opt/novawrite-ai/backend')
from dotenv import load_dotenv
load_dotenv()
from google import genai

api_key = os.getenv('GEMINI_API_KEY')
proxy = os.getenv('GEMINI_PROXY')

if proxy:
    os.environ['HTTP_PROXY'] = proxy
    os.environ['HTTPS_PROXY'] = proxy
    print(f'使用代理: {proxy}')

try:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents='Hello, test'
    )
    print('✅ API 调用成功')
    print(f'响应: {response.text[:100]}')
except Exception as e:
    print(f'❌ API 调用失败: {e}')
"
```

## 简易自建代理方案

### 使用 Squid 代理（Linux）

1. 安装 Squid：
```bash
# Ubuntu/Debian
apt-get update && apt-get install -y squid

# CentOS/RHEL
yum install -y squid
```

2. 配置 Squid (`/etc/squid/squid.conf`)：
```
http_port 3128
acl allowed_ips src all
http_access allow allowed_ips
forwarded_for off
```

3. 启动 Squid：
```bash
systemctl start squid
systemctl enable squid
```

4. 在 NovaWrite 服务器的 `.env` 中配置：
```bash
GEMINI_PROXY=http://squid-server-ip:3128
```

## 故障排查

### 问题 1: 代理连接失败
- 检查代理服务器是否可访问：`curl -x http://proxy:port https://www.google.com`
- 检查防火墙规则
- 验证代理认证信息

### 问题 2: 仍然提示地区限制
- 确认代理服务器位于支持的地区
- 尝试使用不同的代理服务器
- 检查代理是否正常工作

### 问题 3: 代理配置未生效
- 重启 novawrite-backend 服务
- 检查 .env 文件格式是否正确
- 查看服务日志确认代理配置已加载

## 安全建议

1. 使用 HTTPS 代理（如果可用）
2. 不要在日志中输出代理认证信息
3. 定期轮换代理认证凭证
4. 使用私有代理服务器而非公共代理

## 支持的代理协议

- HTTP 代理：`http://host:port`
- HTTPS 代理：`https://host:port`
- 带认证的代理：`http://user:pass@host:port`
- SOCKS 代理：目前不支持，需要使用 HTTP/HTTPS 代理

## 更多信息

如果问题持续存在，请检查：
1. Gemini API 配额和限制
2. API Key 是否有效
3. 服务器网络连接
4. 代理服务器状态
