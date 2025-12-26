# 远程服务器测试完整指南

## 🚀 快速开始

### 方式1：使用安装脚本（推荐）

#### Linux/Mac:
```bash
cd backend
chmod +x install_dependencies.sh
./install_dependencies.sh
```

#### Windows:
```powershell
cd backend
.\install_dependencies.ps1
```

### 方式2：手动安装

```bash
cd backend
pip install -r requirements.txt
```

## ✅ 测试步骤

### 1. 完整测试（推荐首次运行）

```bash
cd backend
python test_all_remote.py
```

这个脚本会：
- ✅ 检查所有依赖
- ✅ 检查环境变量
- ✅ 测试服务导入
- ✅ 测试向量生成
- ✅ 测试数据库连接
- ✅ 测试其他功能

### 2. 功能完整性测试

```bash
python test_vector_features.py
```

### 3. API调用测试

```bash
python test_embedding_simple.py
```

### 4. 单元测试

```bash
python test_unit.py
```

### 5. 性能测试

```bash
python test_performance.py
```

## 📋 前置要求

### 必需
- ✅ Python 3.8+
- ✅ PostgreSQL 12+
- ✅ Gemini API Key
- ✅ 数据库连接配置

### 可选
- ⚠️ Redis（用于缓存功能，可选）

## 🔧 配置检查

### 1. 环境变量

确保 `.env` 文件中有：
```env
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://localhost:6379/0  # 可选
```

### 2. 数据库设置

运行数据库迁移：
```bash
python migrate_add_pgvector.py
```

这会：
- 安装pgvector扩展
- 创建4个向量表
- 创建HNSW索引

## 📊 测试结果解读

### test_all_remote.py 输出示例

```
============================================================
pgvector 向量数据库集成 - 完整测试
============================================================

[1/6] 检查依赖...
  ✅ redis
  ✅ sqlalchemy
  ✅ pgvector
  ✅ google-genai
  ✅ config

[2/6] 检查环境变量...
  ✅ GEMINI_API_KEY: ********************
  ✅ DATABASE_URL 已配置

[3/6] 测试服务导入...
  ✅ EmbeddingService
  ✅ ConsistencyChecker
  ✅ ForeshadowingMatcher
  ✅ ContentSimilarityChecker
  ✅ EmbeddingCache
  ✅ BatchEmbeddingProcessor
  ✅ ThresholdConfig

[4/6] 测试向量生成...
  ✅ 向量生成成功
     维度: 768
     耗时: 1.23秒
     前5个值: [0.123, 0.456, ...]

[5/6] 测试数据库连接...
  ✅ 数据库连接成功
  ✅ pgvector扩展已安装
  ✅ chapter_embeddings 表存在
  ✅ character_embeddings 表存在
  ✅ world_setting_embeddings 表存在
  ✅ foreshadowing_embeddings 表存在

[6/6] 测试其他功能...
  ✅ 文本分块: 3 个块
  ✅ 阈值配置: chapter_similarity = 0.7
  ✅ Redis缓存已启用

============================================================
测试总结
============================================================
✅ 所有核心功能测试通过！

下一步：
1. 如果向量表不存在，运行: python migrate_add_pgvector.py
2. 运行完整测试: python test_vector_features.py
3. 运行性能测试: python test_performance.py
4. 查看使用文档: PGVECTOR_README.md
============================================================
```

## ⚠️ 常见问题

### 问题1：依赖安装失败

**解决**：
```bash
# 升级pip
python -m pip install --upgrade pip

# 单独安装问题包
pip install pgvector --no-cache-dir
pip install redis --no-cache-dir
```

### 问题2：数据库连接失败

**检查**：
1. DATABASE_URL格式是否正确
2. 数据库服务是否运行
3. 网络连接是否正常
4. 用户权限是否正确

### 问题3：pgvector扩展未安装

**解决**：
```bash
# 在PostgreSQL中执行
CREATE EXTENSION IF NOT EXISTS vector;

# 或运行迁移脚本
python migrate_add_pgvector.py
```

### 问题4：向量表不存在

**解决**：
```bash
python migrate_add_pgvector.py
```

### 问题5：Redis连接失败

**说明**：Redis是可选的，失败不影响核心功能，缓存功能会自动禁用。

## 📚 相关文档

- **使用指南**：`PGVECTOR_README.md`
- **快速开始**：`PGVECTOR_QUICK_START.md`
- **部署清单**：`PGVECTOR_DEPLOYMENT_CHECKLIST.md`


