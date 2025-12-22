# Git 代码库设置指南

## 代码库地址

```
git@codeup.aliyun.com:694907d19889c08d4ad2be2e/nova-ai.git
```

## 本地初始化 Git 仓库（如果还没有）

由于当前 PowerShell 环境中可能没有 Git，请使用 Git Bash 或命令行执行以下步骤：

### 1. 初始化 Git 仓库

```bash
cd C:\software\terol\terol
git init
```

### 2. 添加远程仓库

```bash
git remote add origin git@codeup.aliyun.com:694907d19889c08d4ad2be2e/nova-ai.git
```

### 3. 添加所有文件

```bash
git add .
```

### 4. 提交代码

```bash
git commit -m "Initial commit: NovaWrite AI with mobile support and foreshadowing management"
```

### 5. 设置主分支

```bash
git branch -M main
```

### 6. 推送到远程仓库

```bash
git push -u origin main
```

## 后续开发流程

### 日常开发流程

1. **开发完成后，提交代码**：
   ```bash
   cd C:\software\terol\terol
   git add .
   git commit -m "描述你的更改"
   git push origin main
   ```

2. **在远程服务器上部署**：
   ```bash
   ssh root@66.154.108.62
   cd /opt/novawrite-ai
   git pull origin main
   ./deploy-from-repo.sh
   ```

## 远程服务器设置

### 1. 在服务器上克隆代码库（首次）

```bash
ssh root@66.154.108.62

# 如果 /opt/novawrite-ai 已经存在但还不是 git 仓库
cd /opt/novawrite-ai
rm -rf * .* 2>/dev/null || true  # 清空目录（谨慎操作）
git clone git@codeup.aliyun.com:694907d19889c08d4ad2be2e/nova-ai.git .

# 或者如果目录不存在
mkdir -p /opt/novawrite-ai
cd /opt/novawrite-ai
git clone git@codeup.aliyun.com:694907d19889c08d4ad2be2e/nova-ai.git .
```

### 2. 配置服务器上的部署脚本

确保 `deploy-from-repo.sh` 有执行权限：

```bash
chmod +x /opt/novawrite-ai/deploy-from-repo.sh
```

### 3. 首次部署时需要手动配置

首次部署时需要：
1. 创建 `.env` 文件（后端环境变量）
2. 初始化数据库
3. 创建 systemd 服务

详见 `DEPLOY.md`

### 4. 后续自动部署

每次代码更新后，只需在服务器上运行：

```bash
cd /opt/novawrite-ai
git pull origin main
./deploy-from-repo.sh
```

## 自动化部署（可选）

可以使用 GitHub Actions 或 GitLab CI/CD 实现自动化部署。

### 使用 SSH Action（需要配置 Secrets）

在代码库设置中添加以下 Secrets：
- `SERVER_HOST`: 服务器IP (66.154.108.62)
- `SERVER_USER`: 服务器用户 (root)
- `SERVER_SSH_KEY`: SSH 私钥

然后每次推送到 main 分支时会自动触发部署。

## 注意事项

1. **不要提交敏感信息**：
   - `.env` 文件已在 `.gitignore` 中
   - 确保不要提交 API Keys、数据库密码等

2. **服务器上的 .env 文件**：
   - 服务器上的 `.env` 文件不会被 Git 覆盖
   - 首次部署后手动创建，之后保持不变

3. **数据库迁移**：
   - 如果模型有变更，需要手动运行数据库迁移
   - 或者在部署脚本中添加自动迁移逻辑

4. **前端构建**：
   - 部署脚本会自动构建前端
   - 确保服务器上安装了 Node.js 和 npm

## 快速部署命令

**本地提交并推送**：
```bash
cd C:\software\terol\terol
git add .
git commit -m "your message"
git push origin main
```

**服务器端拉取并部署**：
```bash
ssh root@66.154.108.62 "cd /opt/novawrite-ai && git pull origin main && ./deploy-from-repo.sh"
```


