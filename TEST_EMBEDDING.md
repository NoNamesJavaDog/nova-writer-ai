# 向量嵌入服务测试指南

## 📋 测试步骤

### 方式1：直接在 backend 目录运行（推荐）

```bash
cd terol/backend
python test_embedding.py
```

### 方式2：使用 Python 模块方式

```bash
cd terol
python -m backend.test_embedding
```

### 方式3：在 Python 交互式环境中测试

```python
import sys
import os
sys.path.insert(0, 'terol/backend')

from services.embedding_service import EmbeddingService
from config import GEMINI_API_KEY

# 测试向量生成
service = EmbeddingService()
embedding = service.generate_embedding("测试文本")
print(f"向量维度: {len(embedding)}")
```

## ⚠️ 前置条件

1. **已安装依赖**
   ```bash
   cd terol/backend
   pip install -r requirements.txt
   ```

2. **已配置环境变量**
   - 确保 `.env` 文件中包含 `GEMINI_API_KEY`

3. **数据库（可选）**
   - 如果要测试数据库连接，需要先运行迁移脚本：
   ```bash
   python migrate_add_pgvector.py
   ```

## 🐛 常见问题

### 问题1：ModuleNotFoundError: No module named 'services'

**原因**：Python 路径配置不正确

**解决**：确保在 `backend` 目录下运行，或使用方式2

### 问题2：GEMINI_API_KEY 未配置

**原因**：环境变量未设置

**解决**：检查 `.env` 文件是否存在且包含 `GEMINI_API_KEY`

### 问题3：embed_content 方法不存在

**原因**：Google Gemini API 的调用方式可能不同

**解决**：需要查看实际的 `google-genai` 库文档，调整 API 调用方式

## 📝 测试内容

测试脚本会执行以下测试：

1. **向量生成测试**
   - 测试 `generate_embedding()` 方法
   - 验证向量维度是否正确（应该是 768）

2. **文本分块测试**
   - 测试 `_split_into_chunks()` 方法
   - 验证文本能否正确分割

3. **数据库连接测试**（可选）
   - 检查 pgvector 扩展是否安装
   - 检查向量表是否创建

## 🔍 预期输出

```
============================================================
🧪 pgvector 向量嵌入服务测试
============================================================
🧪 测试向量生成功能...
📋 API Key 已配置: True
✅ EmbeddingService 初始化成功
📦 使用模型: models/text-embedding-004
📏 向量维度: 768

🔍 测试文本: 这是一个测试文本，用于验证向量生成功能。
⏳ 正在生成向量...
✅ 向量生成成功！
📊 向量维度: 768
...

🧪 测试文本分块功能...
...

📊 测试结果汇总
============================================================
向量生成: ✅ 通过
文本分块: ✅ 通过
数据库连接: ✅ 通过（如果配置了数据库）

🎉 所有测试通过！
```


