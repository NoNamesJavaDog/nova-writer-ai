# 从 Git 代码库部署到服务器

## 当前状态

✅ 本地代码已推送到远程仓库：`git@codeup.aliyun.com:694907d19889c08d4ad2be2e/nova-ai.git`  
✅ 服务器上 Git 仓库已初始化  
⚠️ 服务器上 SSH 连接代码库需要配置

## 方法一：在服务器上配置 SSH 密钥（推荐）

### 1. 在服务器上生成 SSH 密钥（如果还没有）

```bash
ssh root@66.154.108.62

# 生成 SSH 密钥
ssh-keygen -t rsa -b 4096 -C "server@novawrite"
# 按 Enter 使用默认路径，可以设置密码或留空

# 查看公钥
cat ~/.ssh/id_rsa.pub
```

### 2. 将公钥添加到代码库

1. 复制上面显示的 SSH 公钥内容
2. 登录到代码库网页（codeup.aliyun.com）
3. 进入项目设置 → SSH 公钥
4. 添加新的 SSH 公钥

### 3. 测试 SSH 连接

```bash
ssh -T git@codeup.aliyun.com
# 输入 yes 确认主机密钥
```

### 4. 拉取代码并部署

```bash
cd /opt/novawrite-ai

# 备份现有 .env 文件
if [ -f backend/.env ]; then
  cp backend/.env /tmp/novawrite-env-backup.env
fi

# 拉取代码
git fetch origin main
git reset --hard origin/main
git branch -M main

# 恢复 .env 文件
if [ -f /tmp/novawrite-env-backup.env ]; then
  mkdir -p backend
  cp /tmp/novawrite-env-backup.env backend/.env
fi

# 设置权限并部署
chmod +x deploy-from-repo.sh
./deploy-from-repo.sh
```

## 方法二：使用 HTTPS 方式（如果代码库支持）

如果代码库支持 HTTPS 访问，可以使用访问令牌：

```bash
ssh root@66.154.108.62
cd /opt/novawrite-ai

# 更改远程地址为 HTTPS
git remote set-url origin https://codeup.aliyun.com/694907d19889c08d4ad2be2e/nova-ai.git

# 拉取代码（会提示输入用户名和密码/访问令牌）
git fetch origin main
git reset --hard origin/main
git branch -M main

# 恢复 .env 并部署
if [ -f /tmp/novawrite-env-backup.env ]; then
  cp /tmp/novawrite-env-backup.env backend/.env
fi
chmod +x deploy-from-repo.sh
./deploy-from-repo.sh
```

## 方法三：使用 SCP 直接复制（临时方案）

如果 SSH 配置有问题，可以临时使用 SCP 直接复制代码：

```bash
# 在本地打包代码
cd C:\software\terol\terol
tar -czf /tmp/novawrite-code.tar.gz --exclude='.git' --exclude='node_modules' --exclude='venv' --exclude='__pycache__' --exclude='dist' --exclude='*.tar.gz' .

# 复制到服务器
scp /tmp/novawrite-code.tar.gz root@66.154.108.62:/tmp/

# 在服务器上解压
ssh root@66.154.108.62 "cd /opt/novawrite-ai && tar -xzf /tmp/novawrite-code.tar.gz && chmod +x deploy-from-repo.sh && ./deploy-from-repo.sh"
```

## 快速部署脚本

在服务器上配置好 SSH 后，可以使用以下脚本：

```bash
#!/bin/bash
# /opt/novawrite-ai/deploy-from-git.sh

cd /opt/novawrite-ai

# 备份 .env
[ -f backend/.env ] && cp backend/.env /tmp/novawrite-env-backup.env

# 拉取代码
git fetch origin main
git reset --hard origin/main
git branch -M main 2>/dev/null

# 恢复 .env
[ -f /tmp/novawrite-env-backup.env ] && cp /tmp/novawrite-env-backup.env backend/.env

# 部署
chmod +x deploy-from-repo.sh
./deploy-from-repo.sh
```

保存为 `/opt/novawrite-ai/deploy-from-git.sh`，然后：

```bash
chmod +x /opt/novawrite-ai/deploy-from-git.sh
/opt/novawrite-ai/deploy-from-git.sh
```

## 验证部署

部署完成后，检查服务状态：

```bash
# 检查后端服务
systemctl status novawrite-backend

# 检查后端健康状态
curl http://localhost:8000/api/health

# 检查前端文件
ls -la /var/www/novawrite-ai/current/

# 检查 Nginx
systemctl status nginx
nginx -t
```

## 后续更新流程

配置好 SSH 后，以后更新代码只需：

**本地**：
```bash
cd C:\software\terol\terol
git add .
git commit -m "更新描述"
git push origin main
```

**服务器**：
```bash
ssh root@66.154.108.62
cd /opt/novawrite-ai
./deploy-from-git.sh
```

或使用一键脚本：
```bash
cd C:\software\terol\terol
.\deploy.ps1 -Message "更新描述"
```

