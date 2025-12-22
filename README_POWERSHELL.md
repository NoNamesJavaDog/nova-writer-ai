# PowerShell 执行策略问题解决方案

## 问题说明

PowerShell 默认禁止执行本地脚本，这是 Windows 的安全策略。

## 解决方法

### 方法一：使用专用脚本（推荐，已处理换行符问题）

```powershell
# 临时允许执行策略
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\setup-server-alt.ps1
```

### 方法二：手动转换换行符后使用管道

```powershell
# 读取文件，转换换行符，然后通过 SSH 执行
$content = Get-Content deploy-setup.sh -Raw -Encoding UTF8
$content = $content -replace "`r`n", "`n" -replace "`r", "`n"
$content | ssh root@66.154.108.62 -p 22 bash
```

**注意：** 直接使用 `Get-Content | ssh` 会因为 Windows CRLF 换行符导致错误，需要先转换。

### 方法二：临时允许执行脚本（当前会话）

```powershell
# 仅对当前 PowerShell 会话生效
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\setup-server.ps1
```

### 方法三：允许当前用户执行脚本（推荐）

```powershell
# 允许当前用户执行本地脚本（需要管理员权限）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup-server.ps1
```

### 方法四：绕过执行策略（仅当前命令）

```powershell
# 使用 -ExecutionPolicy Bypass 参数
powershell -ExecutionPolicy Bypass -File .\setup-server.ps1
```

## 推荐的完整部署流程

### 步骤1: 设置服务器环境（无需修改执行策略）

```powershell
# 方法A: 直接使用管道（最简单）
Get-Content deploy-setup.sh | ssh root@66.154.108.62 -p 22 bash

# 方法B: 使用替代脚本
.\setup-server-alt.ps1

# 方法C: 临时允许执行策略
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\setup-server.ps1
```

### 步骤2: 配置数据库和 .env

```powershell
ssh root@66.154.108.62 -p 22
```

然后在服务器上执行：
```bash
# 创建数据库
sudo -u postgres psql
CREATE USER novawrite_user WITH PASSWORD 'your_password';
CREATE DATABASE novawrite_ai OWNER novawrite_user;
\q

# 配置环境变量
cd /opt/novawrite-ai/backend
cp config.example.env .env
nano .env
```

### 步骤3: 部署应用

```powershell
# 退出SSH后，在本地执行
exit

# 部署（deploy.ps1 也可能需要处理执行策略）
Get-Content deploy.ps1 | powershell -ExecutionPolicy Bypass
# 或者
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\deploy.ps1
```

### 步骤4: 初始化数据库并启动服务

```powershell
ssh root@66.154.108.62 -p 22
cd /opt/novawrite-ai/backend
source ../venv/bin/activate
python init_db.py
systemctl start novawrite-backend
systemctl enable novawrite-backend
```

## 查看当前执行策略

```powershell
Get-ExecutionPolicy -List
```

## 各执行策略说明

- **Restricted**（默认）：禁止所有脚本执行
- **RemoteSigned**：本地脚本可以执行，远程脚本需要签名
- **Bypass**：允许所有脚本执行（不推荐长期使用）
- **Unrestricted**：允许所有脚本执行（不推荐）

## 推荐设置

对于开发环境，推荐设置为：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

这样允许执行本地脚本，但远程脚本需要签名，既方便又相对安全。

