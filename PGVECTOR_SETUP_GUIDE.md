# pgvector 向量数据库集成 - 设置指南

## 📋 前提条件

1. PostgreSQL 12+ 数据库
2. Python 3.8+
3. Google Gemini API Key（已配置）

## 🚀 快速开始

### 步骤1：安装 pgvector 扩展（在 PostgreSQL 服务器上）

```bash
# 在 PostgreSQL 服务器上执行
sudo apt-get install postgresql-14-pgvector  # 根据你的 PostgreSQL 版本调整

# 或者使用源码编译安装
# 参考：https://github.com/pgvector/pgvector
```

**重要**：如果是在远程服务器上，需要 SSH 登录到数据库服务器执行上述命令。

### 步骤2：运行数据库迁移

```bash
cd backend
python migrate_add_pgvector.py
```

这将创建：
- pgvector 扩展
- chapter_embeddings 表
- character_embeddings 表
- world_setting_embeddings 表
- foreshadowing_embeddings 表
- 所有必要的索引

### 步骤3：安装 Python 依赖

```bash
cd backend
pip install -r requirements.txt
```

新增的依赖：
- `pgvector==0.2.4`

### 步骤4：确认 Gemini Embedding API

目前代码中使用的是 `models/text-embedding-004`。如果你需要使用 `gemini-embedding-001`，需要：

1. 确认该模型在 Google Gemini API 中可用
2. 修改 `backend/services/embedding_service.py` 中的 `self.model` 值

**注意**：根据当前信息，Google 可能没有 `gemini-embedding-001` 模型。建议使用：
- `text-embedding-004`（Gemini Embedding 模型，推荐）
- 或者使用 Vertex AI 的 embedding 服务

## 🔧 配置检查

确认 `.env` 文件中已配置：
```env
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:password@host:port/database
```

## ✅ 验证安装

运行以下 Python 脚本验证：

```python
from backend.services.embedding_service import EmbeddingService

# 测试向量生成
service = EmbeddingService()
embedding = service.generate_embedding("测试文本")
print(f"向量维度: {len(embedding)}")  # 应该是 768
```

## ⚠️ 注意事项

1. **向量维度**：`text-embedding-004` 的维度是 768，数据库表中已正确设置
2. **索引性能**：HNSW 索引在数据量大时性能更好，但创建时间较长
3. **API 调用**：向量生成会调用 Gemini API，注意 API 配额限制
4. **异步处理**：建议向量生成和存储使用异步任务，避免阻塞主流程

## 🐛 故障排除

### 错误：extension "vector" does not exist
- **原因**：pgvector 扩展未安装
- **解决**：在 PostgreSQL 服务器上安装 pgvector 扩展

### 错误：无法生成向量
- **原因**：Gemini API Key 配置错误或模型名称不正确
- **解决**：检查 `.env` 文件和模型名称

### 错误：向量维度不匹配
- **原因**：API 返回的向量维度与数据库表定义不一致
- **解决**：检查 `embedding_service.py` 中的 `self.dimension` 值


