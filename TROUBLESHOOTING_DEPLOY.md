# 部署故障排查

## apt-get: command not found

如果遇到 `apt-get: command not found` 错误，说明服务器可能不是 Ubuntu/Debian 系统。

### 解决方法

#### 1. 检查服务器系统类型

```powershell
# 使用检查脚本
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\check-server.ps1

# 或手动检查
ssh root@66.154.108.62 -p 22 "cat /etc/os-release"
```

#### 2. 根据系统类型手动安装

**如果是 CentOS/RHEL 系统：**

```bash
ssh root@66.154.108.62 -p 22

# 安装基础工具
yum install -y curl wget git gcc python3 python3-pip
# 或使用 dnf（CentOS 8+）
# dnf install -y curl wget git gcc python3 python3-pip

# 安装 PostgreSQL
yum install -y postgresql-server postgresql
postgresql-setup initdb
systemctl enable postgresql
systemctl start postgresql

# 安装 Nginx
yum install -y nginx
systemctl enable nginx
systemctl start nginx
```

#### 3. 使用更新后的脚本

我已经更新了 `deploy-setup.sh` 脚本，现在支持自动检测系统类型。重新运行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\setup-server-alt.ps1
```

## 其他常见问题

### Python3 未安装

```bash
# Ubuntu/Debian
apt-get install -y python3 python3-pip python3-venv

# CentOS/RHEL
yum install -y python3 python3-pip
# 或
dnf install -y python3 python3-pip
```

### PostgreSQL 连接失败

1. 检查 PostgreSQL 是否运行：
```bash
systemctl status postgresql
```

2. 检查 PostgreSQL 配置：
```bash
sudo -u postgres psql -c "SHOW config_file;"
```

3. 如果无法连接，检查 `/var/lib/pgsql/data/pg_hba.conf` 配置

### Nginx 配置错误

1. 测试配置：
```bash
nginx -t
```

2. 查看错误日志：
```bash
tail -f /var/log/nginx/error.log
```

3. 检查端口是否被占用：
```bash
netstat -tulpn | grep :80
```

## 手动完成服务器设置

如果自动脚本失败，可以手动完成设置：

### 1. 创建目录结构

```bash
mkdir -p /opt/novawrite-ai
mkdir -p /opt/novawrite-ai/backend
mkdir -p /opt/novawrite-ai/logs
mkdir -p /var/www/novawrite-ai
```

### 2. 配置 Nginx

创建 `/etc/nginx/sites-available/novawrite-ai`，内容参考 `deploy-setup.sh` 中的配置。

### 3. 创建 systemd 服务

创建 `/etc/systemd/system/novawrite-backend.service`，内容参考 `deploy-setup.sh` 中的配置。

### 4. 重新加载 systemd

```bash
systemctl daemon-reload
```

## 获取帮助

如果问题仍未解决，请提供：
1. 服务器系统信息：`cat /etc/os-release`
2. 错误日志
3. 具体出错步骤


