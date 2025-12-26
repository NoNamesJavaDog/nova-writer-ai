# pgvector快速部署指南

## 🚀 在远程服务器上快速部署

由于代码已经通过Git管理，我们需要先提交并推送代码，然后在服务器上拉取。

### 步骤1: 提交代码到Git仓库（在本地执行）

```bash
# 进入项目目录（需要确认正确的git仓库位置）
cd /path/to/terol  # 或者 cd terol（根据实际git仓库位置）

# 添加所有新文件
git add .

# 提交
git commit -m "feat: 完成pgvector向量数据库集成 - 所有35个任务已完成"

# 推送到远程仓库
git push origin main
```

### 步骤2: 在服务器上拉取代码并部署

#### 方式1: 使用SSH命令（推荐）

```bash
# 1. 拉取最新代码
ssh root@66.154.108.62 -p 22 "cd /opt/novawrite-ai && git pull origin main"

# 2. 安装新依赖
ssh root@66.154.108.62 -p 22 "cd /opt/novawrite-ai/backend && source ../venv/bin/activate && pip install -r requirements.txt"

# 3. 运行数据库迁移
ssh root@66.154.108.62 -p 22 "cd /opt/novawrite-ai/backend && source ../venv/bin/activate && python migrate_add_pgvector.py"

# 4. 运行测试
ssh root@66.154.108.62 -p 22 "cd /opt/novawrite-ai/backend && source ../venv/bin/activate && python test_all_remote.py"

# 5. 重启服务（如果需要）
ssh root@66.154.108.62 -p 22 "systemctl restart novawrite-backend"
```

#### 方式2: SSH登录后执行

```bash
# SSH登录服务器
ssh root@66.154.108.62 -p 22

# 在服务器上执行
cd /opt/novawrite-ai
git pull origin main

cd backend
source ../venv/bin/activate
pip install -r requirements.txt
python migrate_add_pgvector.py
python test_all_remote.py

# 重启服务
systemctl restart novawrite-backend
```

### 步骤3: 验证部署

```bash
# 查看服务状态
ssh root@66.154.108.62 -p 22 "systemctl status novawrite-backend"

# 查看日志
ssh root@66.154.108.62 -p 22 "journalctl -u novawrite-backend -n 50"
```

## 📋 关键文件

部署后，服务器上应该有这些新文件：

- `backend/migrate_add_pgvector.py` - 数据库迁移脚本
- `backend/services/` - 所有服务文件
- `backend/config_threshold.py` - 阈值配置
- `backend/config_logging.py` - 日志配置
- `backend/test_*.py` - 所有测试脚本
- `backend/deploy_and_test.sh` - 部署测试脚本

## ⚠️ 注意事项

1. **数据库迁移**：首次运行需要执行 `migrate_add_pgvector.py`
2. **依赖安装**：需要安装 `pgvector` 和 `redis`（可选）
3. **环境变量**：确保 `.env` 中有 `GEMINI_API_KEY`
4. **PostgreSQL扩展**：需要在数据库中安装 `pgvector` 扩展

## 🔍 故障排除

如果遇到问题，检查：

1. **代码是否已推送**：`git log` 查看最新提交
2. **服务器是否拉取成功**：`ls -la /opt/novawrite-ai/backend/services/`
3. **依赖是否安装**：`pip list | grep pgvector`
4. **数据库扩展**：`psql -c "SELECT * FROM pg_extension WHERE extname='vector';"`


