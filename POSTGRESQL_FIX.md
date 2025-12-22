# PostgreSQL 初始化问题解决方案

## 问题描述

错误信息：`ERROR: Data directory /var/lib/pgsql/data is not empty!`

这表示 PostgreSQL 数据目录已经存在且不为空，可能已经初始化过了。

## 解决方案

### 方案一：检查 PostgreSQL 是否已正常运行（推荐）

```powershell
# 使用诊断脚本
.\fix-postgresql.ps1
```

如果 PostgreSQL 已经运行，可以直接跳过初始化步骤，继续配置数据库。

### 方案二：启动 PostgreSQL 服务

```bash
ssh root@66.154.108.62 -p 22

# 尝试启动 PostgreSQL
systemctl start postgresql
systemctl status postgresql

# 如果启动成功，测试连接
sudo -u postgres psql -c "SELECT version();"
```

### 方案三：如果需要重新初始化（谨慎！会删除现有数据）

```bash
ssh root@66.154.108.62 -p 22

# 停止 PostgreSQL
systemctl stop postgresql

# 备份现有数据（如果有重要数据）
mv /var/lib/pgsql/data /var/lib/pgsql/data.backup.$(date +%Y%m%d)

# 重新初始化
postgresql-setup --initdb
# 或
postgresql-setup initdb

# 启动服务
systemctl start postgresql
```

## 继续部署流程

如果 PostgreSQL 已经正常运行，可以继续以下步骤：

### 1. 创建数据库用户和数据库

```bash
ssh root@66.154.108.62 -p 22

# 进入 PostgreSQL
sudo -u postgres psql

# 创建用户和数据库
CREATE USER novawrite_user WITH PASSWORD 'your_strong_password';
CREATE DATABASE novawrite_ai OWNER novawrite_user;
\q

# 测试连接
psql -U novawrite_user -d novawrite_ai -h localhost
# 输入密码后应该能连接，输入 \q 退出
```

### 2. 配置后端 .env 文件

```bash
cd /opt/novawrite-ai/backend
cp config.example.env .env
nano .env
```

在 `.env` 文件中设置：
```env
DATABASE_URL=postgresql://novawrite_user:your_strong_password@localhost:5432/novawrite_ai
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://66.154.108.62
ENVIRONMENT=production
DEBUG=false
```

### 3. 继续部署

```powershell
# 在本地执行
.\deploy.ps1
```

### 4. 初始化数据库

```bash
ssh root@66.154.108.62 -p 22
cd /opt/novawrite-ai/backend
source ../venv/bin/activate
python init_db.py
```

## 常见问题

### Q: 如何检查 PostgreSQL 是否运行？

```bash
systemctl status postgresql
# 或
ps aux | grep postgres
```

### Q: 如何查看 PostgreSQL 日志？

```bash
# CentOS/RHEL
tail -f /var/lib/pgsql/data/pg_log/postgresql-*.log

# Ubuntu/Debian
tail -f /var/log/postgresql/postgresql-*.log
```

### Q: 如何重置 PostgreSQL 密码？

```bash
sudo -u postgres psql
ALTER USER postgres PASSWORD 'new_password';
\q
```

## 下一步

如果 PostgreSQL 已经正常运行，请继续执行：
1. 创建数据库用户和数据库（见上面）
2. 配置 .env 文件
3. 运行部署脚本
4. 初始化数据库表


