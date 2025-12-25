# pgvector 向量数据库集成 - 部署指南

## 🚀 快速部署（一键脚本）

### Linux/Mac 服务器

```bash
cd backend
chmod +x deploy_and_test.sh
./deploy_and_test.sh
```

### Windows 服务器

```powershell
cd backend
.\deploy_and_test.ps1
```

## 📋 部署脚本功能

`deploy_and_test.sh` / `deploy_and_test.ps1` 会自动完成：

1. ✅ **检查前置要求**
   - Python 3.8+
   - pip
   - PostgreSQL客户端（可选检查）
   - Redis（可选检查）

2. ✅ **检查环境变量**
   - .env 文件
   - GEMINI_API_KEY
   - DATABASE_URL

3. ✅ **安装依赖**
   - 升级pip
   - 安装所有requirements.txt中的依赖

4. ✅ **验证依赖**
   - 检查redis, sqlalchemy, pgvector, google-genai
   - 显示安装状态

5. ✅ **运行数据库迁移**
   - 执行 migrate_add_pgvector.py
   - 创建向量表和索引

6. ✅ **运行测试**
   - test_all_remote.py - 完整测试
   - test_vector_features.py - 功能测试
   - test_embedding_simple.py - API测试
   - test_unit.py - 单元测试

## 🔧 手动部署步骤

如果自动脚本遇到问题，可以手动执行：

### 步骤1: 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 步骤2: 配置环境变量

创建或编辑 `.env` 文件：

```env
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://localhost:6379/0  # 可选
```

### 步骤3: 运行数据库迁移

```bash
python migrate_add_pgvector.py
```

### 步骤4: 运行测试

```bash
# 完整测试
python test_all_remote.py

# 功能测试
python test_vector_features.py

# API测试
python test_embedding_simple.py

# 单元测试
python test_unit.py
```

## 📊 部署检查清单

部署后，检查以下项目：

- [ ] 所有依赖已安装
- [ ] 环境变量已配置
- [ ] 数据库连接成功
- [ ] pgvector扩展已安装
- [ ] 向量表已创建
- [ ] 向量生成测试通过
- [ ] 数据库连接测试通过
- [ ] 所有服务导入成功

## ⚠️ 常见问题

### 问题1: 数据库迁移失败

**错误**: `extension "vector" does not exist`

**解决**:
```sql
-- 在PostgreSQL中执行
CREATE EXTENSION IF NOT EXISTS vector;
```

或者确保数据库用户有创建扩展的权限。

### 问题2: 依赖安装失败

**解决**:
```bash
# 升级pip
python -m pip install --upgrade pip

# 单独安装问题包
pip install pgvector --no-cache-dir
pip install redis --no-cache-dir
```

### 问题3: API调用失败

**检查**:
1. GEMINI_API_KEY是否正确
2. API Key是否有效
3. 网络连接是否正常

### 问题4: Redis连接失败

**说明**: Redis是可选的，连接失败不影响核心功能，缓存功能会自动禁用。

## 📚 部署后

部署成功后：

1. **查看文档**
   - `PGVECTOR_README.md` - 使用指南
   - `PGVECTOR_QUICK_START.md` - 快速开始

2. **集成到API**
   - 参考 `api_integration_example.py`
   - 在章节创建/更新时添加向量存储

3. **开始使用**
   - 使用智能上下文推荐
   - 使用相似度检查
   - 使用伏笔匹配

## 🎯 验证部署

运行以下命令验证部署：

```bash
cd backend
python test_all_remote.py
```

应该看到：
```
✅ 所有核心功能测试通过！
```

## 📞 需要帮助？

- 查看 `REMOTE_TEST_INSTRUCTIONS.md` 了解详细测试步骤
- 查看 `PGVECTOR_DEPLOYMENT_CHECKLIST.md` 了解部署检查清单
- 查看各测试脚本的输出了解详细错误信息

