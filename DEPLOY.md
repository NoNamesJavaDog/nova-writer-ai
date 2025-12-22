# 完整部署指南

## 服务器信息
- 地址: `66.154.108.62`
- 端口: `22`
- 用户: `root`

## 快速部署

### 首次部署（设置服务器环境）

**Linux/Mac:**
```bash
# 在项目根目录执行
ssh root@66.154.108.62 -p 22 'bash -s' < deploy-setup.sh
```

**Windows PowerShell:**
```powershell
# 方法1: 使用专用 PowerShell 脚本（推荐）
.\setup-server.ps1

# 方法2: 直接传递脚本内容
Get-Content deploy-setup.sh | ssh root@66.154.108.62 -p 22 bash
```

此脚本会自动：
- 更新系统包
- 安装 Python3、PostgreSQL、Nginx
- 创建目录结构
- 配置 Nginx 反向代理
- 创建 systemd 服务

### 配置数据库和环境变量

1. **SSH 登录服务器**：
```bash
ssh root@66.154.108.62 -p 22
```

2. **配置 PostgreSQL 数据库**：
```bash
# 进入 PostgreSQL
sudo -u postgres psql

# 创建数据库用户和数据库
CREATE USER novawrite_user WITH PASSWORD 'your_strong_password';
CREATE DATABASE novawrite_ai OWNER novawrite_user;
\q
```

3. **配置后端环境变量**：
```bash
cd /opt/novawrite-ai/backend
cp config.example.env .env
nano .env  # 或使用 vim
```

编辑 `.env` 文件，设置：
```env
DATABASE_URL=postgresql://novawrite_user:your_strong_password@localhost:5432/novawrite_ai
SECRET_KEY=your-very-strong-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://66.154.108.62,http://localhost:3000
ENVIRONMENT=production
DEBUG=false
```

生成安全的 SECRET_KEY：
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

4. **配置前端环境变量**（部署时会自动处理）：
前端构建时需要通过环境变量设置 API 地址：
```bash
# 在本地构建前设置（或使用 .env.local）
export VITE_API_BASE_URL=http://66.154.108.62
```

### 部署应用

在项目根目录执行：
```bash
chmod +x deploy.sh
./deploy.sh
```

此脚本会自动：
- 构建前端
- 打包前后端代码
- 上传到服务器
- 解压并部署
- 安装 Python 依赖
- 重启服务

### 初始化数据库

首次部署后需要初始化数据库：
```bash
ssh root@66.154.108.62 -p 22
cd /opt/novawrite-ai/backend
source ../venv/bin/activate
python init_db.py
```

### 启动服务

```bash
# 启动后端服务
systemctl start novawrite-backend
systemctl enable novawrite-backend  # 设置开机自启

# 检查状态
systemctl status novawrite-backend
systemctl status nginx
```

## 服务器目录结构

```
/opt/novawrite-ai/
├── backend/              # 后端代码
│   ├── .env             # 环境变量（需要手动创建）
│   ├── main.py
│   └── ...
├── venv/                 # Python 虚拟环境
└── logs/                 # 日志文件
    ├── backend.log
    └── backend.error.log

/var/www/novawrite-ai/
└── current/              # 前端静态文件
```

## 访问地址

- 前端应用: http://66.154.108.62
- API 接口: http://66.154.108.62/api
- API 文档: http://66.154.108.62/api/docs
- OpenAPI JSON: http://66.154.108.62/openapi.json

## 常用命令

### 服务管理

```bash
# 查看后端服务状态
systemctl status novawrite-backend

# 启动/停止/重启后端服务
systemctl start novawrite-backend
systemctl stop novawrite-backend
systemctl restart novawrite-backend

# 查看日志
journalctl -u novawrite-backend -f
tail -f /opt/novawrite-ai/logs/backend.log
tail -f /opt/novawrite-ai/logs/backend.error.log

# Nginx 相关
systemctl status nginx
nginx -t  # 测试配置
systemctl reload nginx
tail -f /var/log/nginx/novawrite-ai-error.log
```

### 数据库管理

```bash
# 连接数据库
sudo -u postgres psql -d novawrite_ai

# 备份数据库
sudo -u postgres pg_dump novawrite_ai > backup_$(date +%Y%m%d).sql

# 恢复数据库
sudo -u postgres psql novawrite_ai < backup_20240101.sql
```

### 更新部署

只需重新运行部署脚本：
```bash
./deploy.sh
```

## 故障排查

### 后端服务无法启动

1. 检查日志：
```bash
journalctl -u novawrite-backend -n 50
tail -f /opt/novawrite-ai/logs/backend.error.log
```

2. 检查环境变量配置：
```bash
cd /opt/novawrite-ai/backend
cat .env
```

3. 检查数据库连接：
```bash
cd /opt/novawrite-ai/backend
source ../venv/bin/activate
python -c "from database import engine; engine.connect()"
```

### Nginx 502 错误

1. 检查后端服务是否运行：
```bash
systemctl status novawrite-backend
curl http://127.0.0.1:8000/api
```

2. 检查 Nginx 配置：
```bash
nginx -t
```

3. 查看 Nginx 错误日志：
```bash
tail -f /var/log/nginx/novawrite-ai-error.log
```

### 前端无法访问 API

1. 检查前端构建时的 API 地址配置
2. 检查浏览器控制台的网络请求
3. 检查 CORS 配置（`config.py` 中的 `CORS_ORIGINS`）

### 数据库连接失败

1. 检查 PostgreSQL 是否运行：
```bash
systemctl status postgresql
```

2. 测试数据库连接：
```bash
sudo -u postgres psql -d novawrite_ai -U novawrite_user
```

3. 检查 `.env` 文件中的 `DATABASE_URL`

## 安全建议

1. **修改默认密码**：更改数据库用户密码和 SECRET_KEY
2. **配置防火墙**：只开放必要端口（80, 443, 22）
3. **使用 HTTPS**：配置 SSL 证书（Let's Encrypt）
4. **定期备份**：设置数据库自动备份
5. **更新系统**：定期更新系统和依赖包
6. **限制 SSH 访问**：使用密钥认证，禁用密码登录

## HTTPS 配置（可选）

使用 Let's Encrypt 配置 HTTPS：

```bash
# 安装 certbot
apt-get install -y certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d your-domain.com

# 自动续期
certbot renew --dry-run
```

## 性能优化

1. **增加后端 workers**：
编辑 `/etc/systemd/system/novawrite-backend.service`：
```ini
ExecStart=/opt/novawrite-ai/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
```

2. **启用 Nginx 缓存**（在 nginx 配置中添加）
3. **配置数据库连接池**（在 `database.py` 中）
4. **使用 CDN** 加速静态资源

