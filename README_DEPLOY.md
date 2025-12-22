# 部署说明 - Windows PowerShell 用户

## PowerShell 兼容性说明

由于 Windows PowerShell 不支持 `<` 重定向操作符，请使用以下方式：

## 方法一：使用专用 PowerShell 脚本（推荐）

```powershell
# 1. 设置服务器环境
.\setup-server.ps1

# 2. 部署应用
.\deploy.ps1
```

## 方法二：使用 Get-Content 管道

```powershell
# 设置服务器环境
Get-Content deploy-setup.sh | ssh root@66.154.108.62 -p 22 bash

# 部署应用
.\deploy.ps1
```

## 方法三：使用 Git Bash 或 WSL

如果在 Windows 上安装了 Git Bash 或 WSL，可以直接使用 Linux 命令：

```bash
# Git Bash
ssh root@66.154.108.62 -p 22 'bash -s' < deploy-setup.sh
./deploy.sh

# WSL
wsl
ssh root@66.154.108.62 -p 22 'bash -s' < deploy-setup.sh
./deploy.sh
```

## 完整部署流程

### 1. 首次部署

```powershell
# 步骤1: 设置服务器环境
.\setup-server.ps1

# 步骤2: SSH登录服务器配置数据库
ssh root@66.154.108.62 -p 22

# 在服务器上执行:
sudo -u postgres psql
CREATE USER novawrite_user WITH PASSWORD 'your_password';
CREATE DATABASE novawrite_ai OWNER novawrite_user;
\q

cd /opt/novawrite-ai/backend
cp config.example.env .env
nano .env  # 编辑配置

# 步骤3: 部署应用
exit  # 退出SSH，回到本地
.\deploy.ps1

# 步骤4: 初始化数据库
ssh root@66.154.108.62 -p 22
cd /opt/novawrite-ai/backend
source ../venv/bin/activate
python init_db.py
systemctl start novawrite-backend
systemctl enable novawrite-backend
```

### 2. 后续更新

```powershell
# 只需运行部署脚本
.\deploy.ps1
```

## 注意事项

1. **SSH 连接**：确保已配置 SSH 密钥或密码认证
2. **防火墙**：确保服务器开放 22 端口（SSH）
3. **权限**：PowerShell 可能需要设置执行策略：
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```


