# pgvector向量数据库集成 - 手动部署说明

## ⚠️ 重要提示

由于本地环境路径限制，需要手动完成代码提交和部署。

## 📋 部署步骤

### 步骤1: 提交代码到Git仓库（在本地项目根目录执行）

请在你的本地项目根目录（包含.git目录的目录）执行以下命令：

```bash
# 1. 进入项目根目录（包含.git的目录）
cd /path/to/your/project  # 例如：cd C:\software\terol\terol 或实际git仓库位置

# 2. 添加所有新文件
git add .

# 3. 提交
git commit -m "feat: 完成pgvector向量数据库集成 - 所有35个任务已完成，包括Redis缓存、批量处理和阈值配置优化"

# 4. 推送到远程仓库
git push origin main
```

**确认Git仓库位置的方法**：
```bash
# 查找.git目录
find . -name ".git" -type d  # Linux/Mac
# 或
dir /s .git  # Windows CMD
# 或
Get-ChildItem -Path . -Filter ".git" -Directory -Recurse -Depth 3  # PowerShell
```

### 步骤2: 在服务器上拉取代码

代码推送成功后，在服务器上执行：

```bash
ssh root@66.154.108.62 -p 22

cd /opt/novawrite-ai
git pull origin main
```

### 步骤3: 安装依赖（服务器上）

```bash
cd /opt/novawrite-ai/backend
source ../venv/bin/activate
pip install -r requirements.txt
```

**注意**：pgvector和redis依赖已经安装过了，这一步主要是确保所有依赖都是最新的。

### 步骤4: 运行数据库迁移（服务器上）

```bash
cd /opt/novawrite-ai/backend
source ../venv/bin/activate
python migrate_add_pgvector.py
```

### 步骤5: 运行测试（服务器上）

```bash
cd /opt/novawrite-ai/backend
source ../venv/bin/activate
python test_all_remote.py
```

### 步骤6: 重启服务（服务器上）

```bash
systemctl restart novawrite-backend
systemctl status novawrite-backend
```

## 🔍 验证部署

部署完成后，验证以下内容：

```bash
# 1. 检查文件是否存在
ssh root@66.154.108.62 "ls -la /opt/novawrite-ai/backend/services/"
ssh root@66.154.108.62 "ls -la /opt/novawrite-ai/backend/migrate_add_pgvector.py"

# 2. 检查依赖
ssh root@66.154.108.62 "cd /opt/novawrite-ai/backend && source ../venv/bin/activate && pip list | grep -E 'pgvector|redis'"

# 3. 检查数据库扩展
ssh root@66.154.108.62 "cd /opt/novawrite-ai/backend && source ../venv/bin/activate && python -c 'from sqlalchemy import create_engine, text; from config import DATABASE_URL; engine = create_engine(DATABASE_URL); conn = engine.connect(); result = conn.execute(text(\"SELECT * FROM pg_extension WHERE extname='vector'\")); print(\"pgvector扩展:\", result.fetchone() is not None); conn.close()'"
```

## 📁 需要部署的新文件

### 服务文件
- `backend/services/` 目录（所有7个服务文件）

### 配置和工具
- `backend/migrate_add_pgvector.py`
- `backend/config_threshold.py`
- `backend/config_logging.py`

### 测试脚本
- `backend/test_all_remote.py`
- `backend/test_vector_features.py`
- `backend/test_embedding.py`
- `backend/test_embedding_simple.py`
- `backend/test_performance.py`
- `backend/test_unit.py`

### 部署脚本
- `backend/deploy_and_test.sh`
- `backend/deploy_and_test.ps1`
- `backend/install_dependencies.sh`
- `backend/install_dependencies.ps1`

### 集成示例
- `backend/api_integration_example.py`

## ✅ 当前状态

- ✅ 服务器依赖已安装（pgvector, redis）
- ✅ 服务器后端服务正在运行
- ⏳ 等待代码提交到Git仓库
- ⏳ 等待在服务器上拉取代码

## 💡 一键部署命令（代码提交后）

如果代码已提交并推送到Git仓库，可以使用以下命令一键完成服务器端部署：

```bash
ssh root@66.154.108.62 << 'EOF'
cd /opt/novawrite-ai
git pull origin main
cd backend
source ../venv/bin/activate
pip install -r requirements.txt
python migrate_add_pgvector.py
python test_all_remote.py
systemctl restart novawrite-backend
EOF
```

