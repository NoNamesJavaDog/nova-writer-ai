# 向量数据库功能测试指南

## 📋 测试脚本

使用 `test_vector_features.py` 可以快速验证所有向量功能的完整性。

## 🚀 运行测试

```bash
cd backend
python test_vector_features.py
```

## ✅ 测试内容

### 1. 向量生成测试
- 验证 Gemini Embedding API 调用是否正常
- 检查向量维度是否正确（应该是768）

### 2. 文本分块测试
- 验证文本分割功能是否正常
- 检查分块逻辑是否正确

### 3. 数据库连接测试
- 验证数据库连接配置是否正确
- 检查能否正常连接数据库

### 4. pgvector扩展检查
- 验证 pgvector 扩展是否已安装
- 如果未安装，需要运行迁移脚本

### 5. 向量表检查
- 检查所有4个向量表是否存在：
  - `chapter_embeddings`
  - `character_embeddings`
  - `world_setting_embeddings`
  - `foreshadowing_embeddings`
- 如果表不存在，需要运行迁移脚本

### 6. 服务初始化测试
- 验证所有服务类能否正常初始化：
  - `EmbeddingService`
  - `ConsistencyChecker`
  - `ForeshadowingMatcher`
  - `ContentSimilarityChecker`

## 📊 测试结果

测试脚本会显示每个测试的结果：

```
=== 测试1: 向量生成 ===
✅ 向量生成成功
   维度: 768
   前5个值: [0.123, 0.456, ...]

=== 测试2: 文本分块 ===
✅ 文本分块成功
   原始文本长度: 50
   分块数量: 3

...

测试总结
============================================================
向量生成: ✅ 通过
文本分块: ✅ 通过
数据库连接: ✅ 通过
pgvector扩展: ✅ 通过
向量表检查: ✅ 通过
服务初始化: ✅ 通过

总计: 6/6 通过
🎉 所有测试通过！
```

## ⚠️ 常见问题

### 问题1: 向量生成失败
**原因**：Gemini API Key 未配置或无效

**解决**：
1. 检查 `.env` 文件中的 `GEMINI_API_KEY`
2. 确认 API Key 有效且有足够的配额

### 问题2: 数据库连接失败
**原因**：数据库配置错误

**解决**：
1. 检查 `.env` 文件中的 `DATABASE_URL`
2. 确认数据库服务正在运行
3. 验证连接字符串格式正确

### 问题3: pgvector扩展未安装
**原因**：未运行迁移脚本或扩展安装失败

**解决**：
```bash
python migrate_add_pgvector.py
```

### 问题4: 向量表不存在
**原因**：未运行迁移脚本

**解决**：
```bash
python migrate_add_pgvector.py
```

### 问题5: 服务初始化失败
**原因**：依赖缺失或导入错误

**解决**：
1. 检查是否安装了所有依赖：`pip install -r requirements.txt`
2. 检查 Python 路径配置
3. 查看详细错误信息

## 🔧 详细测试

如果需要测试特定功能，可以修改测试脚本或直接调用相关函数：

```python
from services.embedding_service import EmbeddingService

service = EmbeddingService()

# 测试向量生成
embedding = service.generate_embedding("测试文本")

# 测试文本分块
chunks = service._split_into_chunks("长文本内容...", chunk_size=500)
```

## 📈 性能测试（可选）

如果需要测试性能，可以在测试脚本中添加性能测试：

```python
import time

start = time.time()
embedding = service.generate_embedding("测试文本")
elapsed = time.time() - start
print(f"向量生成耗时: {elapsed:.2f}秒")
```

## 🎯 下一步

测试通过后，可以：

1. **运行完整测试**：`python test_embedding.py`
2. **集成到API**：参考 `api_integration_example.py`
3. **实际使用**：开始使用向量功能

## 📚 相关文档

- **设置指南**：`PGVECTOR_SETUP_GUIDE.md`
- **使用指南**：`PGVECTOR_README.md`
- **快速开始**：`PGVECTOR_QUICK_START.md`


