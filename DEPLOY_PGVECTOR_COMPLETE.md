# pgvector向量数据库集成 - 完整部署说明

## ⚠️ 当前状态

代码已准备就绪，但**需要先提交到Git仓库**，然后才能在服务器上拉取。

## 📋 部署步骤

### 步骤1: 提交代码到Git仓库（本地执行）

由于当前环境限制，需要手动执行以下步骤：

#### 1.1 找到Git仓库根目录

根据之前的信息，Git仓库地址是：
```
git@codeup.aliyun.com:694907d19889c08d4ad2be2e/nova-ai.git
```

需要找到包含 `.git` 目录的项目根目录。

#### 1.2 提交代码

```bash
# 进入项目根目录（包含.git目录的目录）
cd /path/to/your/project

# 添加所有新文件
git add .

# 提交
git commit -m "feat: 完成pgvector向量数据库集成 - 所有35个任务已完成，包括Redis缓存、批量处理和阈值配置优化"

# 推送到远程仓库
git push origin main
```

### 步骤2: 在服务器上拉取代码

```bash
# SSH登录服务器
ssh root@66.154.108.62 -p 22

# 拉取最新代码
cd /opt/novawrite-ai
git pull origin main
```

### 步骤3: 安装依赖

依赖已在服务器上安装（✅ pgvector 和 redis 已安装），如果需要重新安装：

```bash
cd /opt/novawrite-ai/backend
source ../venv/bin/activate
pip install -r requirements.txt
```

### 步骤4: 运行数据库迁移

```bash
cd /opt/novawrite-ai/backend
source ../venv/bin/activate
python migrate_add_pgvector.py
```

### 步骤5: 运行测试

```bash
cd /opt/novawrite-ai/backend
source ../venv/bin/activate
python test_all_remote.py
```

### 步骤6: 重启服务

```bash
systemctl restart novawrite-backend
systemctl status novawrite-backend
```

## 📁 需要部署的文件

### 核心服务文件（新创建）

```
backend/services/
├── __init__.py
├── embedding_service.py          # 向量嵌入服务
├── consistency_checker.py        # 一致性检查服务
├── foreshadowing_matcher.py      # 伏笔匹配服务
├── content_similarity_checker.py # 相似度检查服务
├── vector_helper.py              # 向量存储辅助
├── embedding_cache.py            # Redis缓存服务 ⭐
└── batch_embedding_processor.py  # 批量处理器 ⭐
```

### 配置和工具文件（新创建）

```
backend/
├── config_threshold.py           # 阈值配置管理 ⭐
├── config_logging.py             # 日志配置
├── migrate_add_pgvector.py       # 数据库迁移脚本
├── api_integration_example.py    # API集成示例
└── test_*.py                     # 测试脚本（6个文件）
```

### 部署脚本（新创建）

```
backend/
├── deploy_and_test.sh
├── deploy_and_test.ps1
├── install_dependencies.sh
└── install_dependencies.ps1
```

### 依赖更新

```
backend/requirements.txt  # 已添加 pgvector==0.2.4 和 redis>=4.5.0
```

## ✅ 已完成的服务器操作

1. ✅ **依赖已安装**
   - pgvector-0.4.2 已安装
   - redis-7.0.1 已安装
   - numpy-2.0.2 已安装

2. ✅ **服务器状态正常**
   - 后端服务正在运行
   - Git仓库已连接

## ⏳ 待完成的操作

1. ⏳ **提交代码到Git仓库**（需要在本地执行）
2. ⏳ **在服务器上拉取代码**
3. ⏳ **运行数据库迁移**
4. ⏳ **运行测试验证功能**
5. ⏳ **重启服务**

## 🔍 验证部署

部署完成后，检查以下内容：

```bash
# 1. 检查文件是否存在
ssh root@66.154.108.62 "ls -la /opt/novawrite-ai/backend/services/"
ssh root@66.154.108.62 "ls -la /opt/novawrite-ai/backend/migrate_add_pgvector.py"

# 2. 检查依赖
ssh root@66.154.108.62 "cd /opt/novawrite-ai/backend && source ../venv/bin/activate && pip list | grep -E 'pgvector|redis'"

# 3. 运行测试
ssh root@66.154.108.62 "cd /opt/novawrite-ai/backend && source ../venv/bin/activate && python test_all_remote.py"
```

## 📚 相关文档

- **快速部署**：`QUICK_DEPLOY_PGVECTOR.md`
- **部署指南**：`DEPLOYMENT_GUIDE.md`
- **测试指南**：`REMOTE_TEST_INSTRUCTIONS.md`

## 💡 一键部署命令（在代码提交后）

如果代码已提交到Git仓库，可以使用以下命令一键部署：

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

