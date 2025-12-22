# 部署工作流程

## 概述

本项目使用 Git 代码库进行版本管理，支持自动化的部署流程。

**代码库地址**: `git@codeup.aliyun.com:694907d19889c08d4ad2be2e/nova-ai.git`

## 部署架构

```
本地开发 → Git 提交 → 代码库 → 服务器拉取 → 自动构建部署
```

## 快速开始

### 本地首次设置

1. **初始化 Git 仓库**（如果还没有）：
   ```bash
   cd C:\software\terol\terol
   git init
   git remote add origin git@codeup.aliyun.com:694907d19889c08d4ad2be2e/nova-ai.git
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git push -u origin main
   ```

### 服务器首次设置

1. **克隆代码库**：
   ```bash
   ssh root@66.154.108.62
   cd /opt
   git clone git@codeup.aliyun.com:694907d19889c08d4ad2be2e/nova-ai.git novawrite-ai
   cd novawrite-ai
   chmod +x deploy-from-repo.sh setup-server-repo.sh
   ```

2. **配置环境变量**：
   ```bash
   cd /opt/novawrite-ai/backend
   cp config.example.env .env
   # 编辑 .env 文件，填入实际配置
   nano .env
   ```

3. **初始化服务**（如果需要）：
   - 创建虚拟环境
   - 安装依赖
   - 初始化数据库
   - 配置 systemd 服务
   - 配置 Nginx

详见 `DEPLOY.md`

## 日常部署流程

### 方式一：使用 PowerShell 脚本（推荐）

```powershell
cd C:\software\terol\terol
.\deploy.ps1 -Message "描述你的更改"
```

这会自动：
1. 提交代码到 Git
2. 推送到远程仓库
3. 在服务器上拉取代码
4. 执行自动部署

### 方式二：手动操作

**本地**：
```bash
cd C:\software\terol\terol
git add .
git commit -m "描述你的更改"
git push origin main
```

**服务器**：
```bash
ssh root@66.154.108.62
cd /opt/novawrite-ai
git pull origin main
./deploy-from-repo.sh
```

### 方式三：一行命令（本地执行）

```powershell
# 仅推送代码
cd C:\software\terol\terol; git add .; git commit -m "更新"; git push origin main

# 推送并部署（需要配置 SSH）
ssh root@66.154.108.62 "cd /opt/novawrite-ai && git pull origin main && ./deploy-from-repo.sh"
```

## 部署脚本说明

### deploy-from-repo.sh

服务器端自动部署脚本，执行以下步骤：

1. **更新后端依赖**：在虚拟环境中更新 Python 包
2. **重启后端服务**：重启 novawrite-backend systemd 服务
3. **构建前端**：运行 `npm install` 和 `npm run build`
4. **部署前端文件**：复制构建产物到 web 目录
5. **重载 Nginx**：重载 Nginx 配置

**位置**: `/opt/novawrite-ai/deploy-from-repo.sh`

**执行权限**: 
```bash
chmod +x /opt/novawrite-ai/deploy-from-repo.sh
```

### deploy.ps1

本地一键部署脚本，可以：
- 自动提交代码到 Git
- 推送到远程仓库
- 连接到服务器执行部署

**使用方法**:
```powershell
.\deploy.ps1 -Message "提交信息"
.\deploy.ps1 -SkipPush        # 跳过 Git 操作，只部署
.\deploy.ps1 -SkipDeploy      # 只推送到 Git，不部署
```

## 自动化部署（可选）

### GitHub Actions / GitLab CI/CD

可以使用 CI/CD 实现自动部署。示例配置见 `.github/workflows/deploy.yml`。

需要配置的 Secrets：
- `SERVER_HOST`: 服务器 IP
- `SERVER_USER`: SSH 用户名
- `SERVER_SSH_KEY`: SSH 私钥

### Webhook 自动部署

在服务器上设置 webhook 监听器，当代码库有推送时自动触发部署。

## 回滚部署

如果需要回滚到之前的版本：

```bash
ssh root@66.154.108.62
cd /opt/novawrite-ai

# 查看提交历史
git log --oneline -10

# 回滚到指定提交
git checkout <commit-hash>
./deploy-from-repo.sh

# 或者回滚到上一个版本
git checkout HEAD~1
./deploy-from-repo.sh
```

前端文件有自动备份，位于 `/var/www/novawrite-ai/backup.*`。

## 故障排查

### Git 操作失败

1. **检查 SSH 密钥配置**：
   ```bash
   ssh -T git@codeup.aliyun.com
   ```

2. **检查远程仓库配置**：
   ```bash
   git remote -v
   ```

### 部署脚本失败

1. **检查脚本权限**：
   ```bash
   ls -l /opt/novawrite-ai/deploy-from-repo.sh
   chmod +x /opt/novawrite-ai/deploy-from-repo.sh
   ```

2. **手动执行脚本查看详细错误**：
   ```bash
   bash -x /opt/novawrite-ai/deploy-from-repo.sh
   ```

3. **检查服务状态**：
   ```bash
   systemctl status novawrite-backend
   systemctl status nginx
   ```

### 前端构建失败

1. **检查 Node.js 和 npm**：
   ```bash
   node --version
   npm --version
   ```

2. **清理并重新安装依赖**：
   ```bash
   cd /opt/novawrite-ai/novawrite-ai---professional-novel-assistant
   rm -rf node_modules package-lock.json
   npm install
   ```

### 后端服务启动失败

1. **查看服务日志**：
   ```bash
   journalctl -u novawrite-backend -n 50
   ```

2. **检查环境变量**：
   ```bash
   cat /opt/novawrite-ai/backend/.env
   ```

3. **手动测试后端**：
   ```bash
   source /opt/novawrite-ai/venv/bin/activate
   cd /opt/novawrite-ai/backend
   python main.py
   ```

## 最佳实践

1. **提交前测试**：在本地测试代码后再提交
2. **清晰的提交信息**：使用描述性的 commit message
3. **小步提交**：频繁提交，每次提交包含一个完整的功能或修复
4. **分支管理**：开发新功能时使用分支，测试通过后再合并到 main
5. **部署前备份**：重要更新前备份数据库和配置文件
6. **监控服务**：部署后检查服务状态和日志

## 相关文档

- `GIT_SETUP.md` - Git 代码库设置详细指南
- `DEPLOY.md` - 手动部署详细说明
- `README.md` - 项目总体说明


