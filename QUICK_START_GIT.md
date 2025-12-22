# Git 代码库快速开始指南

## 代码库地址

```
git@codeup.aliyun.com:694907d19889c08d4ad2be2e/nova-ai.git
```

## 本地设置（首次）

在 Git Bash 或命令行中执行：

```bash
cd C:\software\terol\terol

# 1. 初始化 Git（如果还没有）
git init

# 2. 添加远程仓库
git remote add origin git@codeup.aliyun.com:694907d19889c08d4ad2be2e/nova-ai.git

# 3. 添加所有文件
git add .

# 4. 提交
git commit -m "Initial commit: NovaWrite AI"

# 5. 推送到远程
git branch -M main
git push -u origin main
```

## 日常使用

### 提交并推送代码

```bash
cd C:\software\terol\terol
git add .
git commit -m "你的提交信息"
git push origin main
```

### 在服务器上拉取并部署

```bash
ssh root@66.154.108.62
cd /opt/novawrite-ai
git pull origin main
./deploy-from-repo.sh
```

### 一键部署（本地执行，需要 Git 在 PATH 中）

使用 PowerShell 脚本：
```powershell
cd C:\software\terol\terol
.\deploy.ps1 -Message "你的提交信息"
```

## 服务器首次设置

```bash
ssh root@66.154.108.62

# 克隆代码库
cd /opt
git clone git@codeup.aliyun.com:694907d19889c08d4ad2be2e/nova-ai.git novawrite-ai

# 进入目录
cd novawrite-ai

# 设置脚本权限
chmod +x deploy-from-repo.sh

# 配置环境变量
cd backend
cp config.example.env .env
nano .env  # 编辑配置文件

# 首次部署（需要先配置好环境）
./deploy-from-repo.sh
```

## 常见问题

### Git 命令未找到

确保 Git 已安装并添加到系统 PATH：
- 下载安装：https://git-scm.com/download/win
- 或在 Git Bash 中执行命令

### SSH 连接失败

检查 SSH 密钥配置：
```bash
ssh -T git@codeup.aliyun.com
```

如果提示权限被拒绝，请检查 SSH 公钥是否已添加到代码库。

### 服务器部署失败

检查：
1. 代码库目录是否存在：`ls -la /opt/novawrite-ai`
2. 脚本是否有执行权限：`chmod +x /opt/novawrite-ai/deploy-from-repo.sh`
3. 服务状态：`systemctl status novawrite-backend`

## 详细文档

- `GIT_SETUP.md` - 详细设置指南
- `DEPLOYMENT_WORKFLOW.md` - 完整部署流程
- `DEPLOY.md` - 服务器部署详细说明


