# 快速部署指南

## 一键部署步骤

### 1. 首次部署（仅需执行一次）

**Linux/Mac:**
```bash
# 在项目根目录执行，设置服务器环境
ssh root@66.154.108.62 -p 22 'bash -s' < deploy-setup.sh
```

**Windows PowerShell:**
```powershell
# 方法1: 使用脚本（推荐，已处理换行符问题）
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\setup-server-alt.ps1

# 方法2: 手动转换换行符后使用管道
$content = Get-Content deploy-setup.sh -Raw -Encoding UTF8
$content = $content -replace "`r`n", "`n" -replace "`r", "`n"
$content | ssh root@66.154.108.62 -p 22 bash
```

**注意：** 
- 如果遇到执行策略错误，需要先执行：`Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process`
- 直接使用 `Get-Content | ssh` 会因为 Windows CRLF 换行符导致错误，需要先转换
- 详细说明请查看 `README_POWERSHELL.md`

### 2. 配置数据库（SSH登录服务器后执行）

```bash
ssh root@66.154.108.62 -p 22

# 创建数据库用户和数据库
sudo -u postgres psql
CREATE USER novawrite_user WITH PASSWORD 'your_strong_password_here';
CREATE DATABASE novawrite_ai OWNER novawrite_user;
\q

# 配置后端环境变量
cd /opt/novawrite-ai/backend
cp config.example.env .env
nano .env  # 编辑配置文件
```

在 `.env` 文件中设置：
```env
DATABASE_URL=postgresql://novawrite_user:your_strong_password_here@localhost:5432/novawrite_ai
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
CORS_ORIGINS=http://66.154.108.62
ENVIRONMENT=production
DEBUG=false
```

### 3. 部署应用

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**Windows (PowerShell):**
```powershell
.\deploy.ps1
```

### 4. 初始化数据库（首次部署需要）

```bash
ssh root@66.154.108.62 -p 22
cd /opt/novawrite-ai/backend
source ../venv/bin/activate
python init_db.py
```

### 5. 启动服务

```bash
systemctl start novawrite-backend
systemctl enable novawrite-backend  # 开机自启
systemctl status novawrite-backend  # 检查状态
```

### 6. 访问应用

- 前端: http://66.154.108.62
- API: http://66.154.108.62/api
- API文档: http://66.154.108.62/api/docs

## 后续更新

只需重新运行部署脚本：
```bash
./deploy.sh  # Linux/Mac
# 或
.\deploy.ps1  # Windows
```

## 常用命令

```bash
# 查看服务状态
systemctl status novawrite-backend
systemctl status nginx

# 查看日志
journalctl -u novawrite-backend -f
tail -f /opt/novawrite-ai/logs/backend.log

# 重启服务
systemctl restart novawrite-backend
systemctl restart nginx

# 测试API
curl http://66.154.108.62/api
```

