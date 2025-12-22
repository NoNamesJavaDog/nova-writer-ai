# 部署后配置指南

## ✅ 部署已完成！

代码已经成功上传到服务器。现在需要完成以下配置：

## 步骤 1: 修复文件权限

```bash
ssh root@66.154.108.62 -p 22

# 检查 web 服务器用户
id nginx 2>/dev/null && echo "nginx user exists" || echo "nginx user not found"
id apache 2>/dev/null && echo "apache user exists" || echo "apache user not found"

# 根据实际情况设置权限（假设是 nginx 用户）
chown -R nginx:nginx /var/www/novawrite-ai/current
chmod -R 755 /var/www/novawrite-ai/current
```

## 步骤 2: 配置数据库

```bash
# 确保 PostgreSQL 运行
systemctl start postgresql
systemctl status postgresql

# 创建数据库用户和数据库
sudo -u postgres psql
```

在 PostgreSQL 中执行：
```sql
CREATE USER novawrite_user WITH PASSWORD 'your_strong_password_here';
CREATE DATABASE novawrite_ai OWNER novawrite_user;
\q
```

测试连接：
```bash
psql -U novawrite_user -d novawrite_ai -h localhost
# 输入密码后应该能连接，输入 \q 退出
```

## 步骤 3: 配置后端环境变量

```bash
cd /opt/novawrite-ai/backend

# 如果 .env 不存在，从示例创建
cp config.example.env .env

# 编辑配置文件
nano .env
```

在 `.env` 文件中设置：
```env
DATABASE_URL=postgresql://novawrite_user:your_strong_password_here@localhost:5432/novawrite_ai
SECRET_KEY=your-very-strong-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://66.154.108.62
ENVIRONMENT=production
DEBUG=false
```

生成安全的 SECRET_KEY：
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 步骤 4: 初始化数据库

```bash
cd /opt/novawrite-ai/backend
source ../venv/bin/activate
python init_db.py
```

## 步骤 5: 启动服务

```bash
# 启动后端服务
systemctl start novawrite-backend
systemctl enable novawrite-backend

# 检查服务状态
systemctl status novawrite-backend
systemctl status nginx

# 查看日志（如果有问题）
journalctl -u novawrite-backend -f
tail -f /opt/novawrite-ai/logs/backend.log
```

## 步骤 6: 测试访问

- 前端: http://66.154.108.62
- API: http://66.154.108.62/api
- API 文档: http://66.154.108.62/api/docs

## 快速命令汇总

```bash
# SSH 登录
ssh root@66.154.108.62 -p 22

# 创建数据库（在 psql 中）
CREATE USER novawrite_user WITH PASSWORD 'password';
CREATE DATABASE novawrite_ai OWNER novawrite_user;

# 配置环境变量
cd /opt/novawrite-ai/backend
nano .env

# 初始化数据库
source ../venv/bin/activate
python init_db.py

# 启动服务
systemctl start novawrite-backend
systemctl enable novawrite-backend

# 检查状态
systemctl status novawrite-backend nginx
```

## 故障排查

### 后端服务无法启动

```bash
# 查看日志
journalctl -u novawrite-backend -n 50
tail -f /opt/novawrite-ai/logs/backend.error.log

# 检查环境变量
cd /opt/novawrite-ai/backend
cat .env

# 测试数据库连接
source ../venv/bin/activate
python -c "from database import engine; engine.connect()"
```

### Nginx 502 错误

```bash
# 检查后端是否运行
systemctl status novawrite-backend
curl http://127.0.0.1:8000/api

# 检查 Nginx 配置
nginx -t
tail -f /var/log/nginx/novawrite-ai-error.log
```

### 权限问题

```bash
# 检查 web 服务器用户
id nginx
id apache
id www-data

# 设置正确的权限
chown -R nginx:nginx /var/www/novawrite-ai/current
# 或
chown -R apache:apache /var/www/novawrite-ai/current
```


