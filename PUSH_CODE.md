# 推送代码到远程仓库

## 当前状态

✅ 代码已成功提交到本地 Git 仓库
✅ 远程仓库已配置：`git@codeup.aliyun.com:694907d19889c08d4ad2be2e/nova-ai.git`
✅ 提交信息：Initial commit: NovaWrite AI with mobile support and foreshadowing management

## 推送代码

由于 SSH 主机密钥验证问题，请使用以下方法之一：

### 方法一：使用 Git Bash（推荐）

1. 打开 **Git Bash**
2. 执行以下命令：

```bash
cd /c/software/terol/terol
git push -u origin main
```

如果首次连接，会提示确认主机密钥，输入 `yes` 确认。

### 方法二：在 PowerShell 中手动接受主机密钥

在 PowerShell 中执行：

```powershell
# 添加主机密钥到 known_hosts
$knownHostsPath = "$env:USERPROFILE\.ssh\known_hosts"
$hostKey = "codeup.aliyun.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC..."
# 需要先通过 ssh 连接一次来获取主机密钥

# 或者使用 Git Bash 执行一次 SSH 连接
# ssh -T git@codeup.aliyun.com
# 输入 yes 确认

# 然后执行推送
cd C:\software\terol\terol
& "C:\Program Files\Git\bin\git.exe" push -u origin main
```

### 方法三：使用 HTTPS（如果配置了访问令牌）

如果代码库支持 HTTPS 访问：

```bash
cd C:\software\terol\terol
git remote set-url origin https://codeup.aliyun.com/694907d19889c08d4ad2be2e/nova-ai.git
git push -u origin main
```

需要输入用户名和密码/访问令牌。

## 验证推送结果

推送成功后，可以验证：

```bash
git log --oneline -1
git remote -v
git branch -vv
```

或者访问代码库网页查看代码是否已上传。

## 后续操作

推送成功后，后续开发流程：

1. **本地开发并提交**：
   ```bash
   git add .
   git commit -m "描述你的更改"
   git push origin main
   ```

2. **在服务器上拉取并部署**：
   ```bash
   ssh root@66.154.108.62
   cd /opt/novawrite-ai
   git pull origin main
   ./deploy-from-repo.sh
   ```

## 常见问题

### SSH 密钥问题

如果遇到权限问题，检查 SSH 密钥：

```bash
# 测试 SSH 连接
ssh -T git@codeup.aliyun.com

# 检查 SSH 密钥
ls -la ~/.ssh/id_rsa*

# 如果没有密钥，生成新的
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
# 然后将 ~/.ssh/id_rsa.pub 的内容添加到代码库的 SSH 密钥设置中
```

### 推送被拒绝

如果推送被拒绝，可能是因为远程仓库已有代码：

```bash
# 先拉取远程代码
git pull origin main --allow-unrelated-histories

# 解决冲突后
git push origin main
```

