# 快速测试向量嵌入服务

## 🚀 快速开始

### 步骤1：确保环境配置

```bash
# 进入 backend 目录
cd terol/backend

# 安装/更新依赖
pip install -r requirements.txt

# 确保 .env 文件中有 GEMINI_API_KEY
```

### 步骤2：运行简化测试

```bash
# 测试 Gemini API 调用方式
python test_embedding_simple.py
```

这个测试会：
- 验证 API Key 是否配置
- 尝试不同的 API 调用方式
- 输出可用的方法和属性

### 步骤3：根据测试结果调整代码

如果测试失败，需要：

1. **查看实际的 API 调用方式**
   - 运行 `test_embedding_simple.py` 查看输出
   - 根据输出调整 `embedding_service.py` 中的 `generate_embedding()` 方法

2. **确认模型名称**
   - 如果 `text-embedding-004` 不可用，可能需要使用其他模型
   - 或者使用 Vertex AI 的 embedding 服务

## 🔍 常见问题排查

### 问题1：API 方法不存在

**现象**：`AttributeError: 'Models' object has no attribute 'embed_content'`

**解决**：
- 检查 `google-genai` 库版本
- 查看最新文档，确认正确的调用方式
- 可能需要使用 `client.models.embed()` 或其他方法

### 问题2：模型名称错误

**现象**：模型不存在或不可用

**解决**：
- 确认正确的模型名称
- 检查 API 权限
- 可能需要使用 Vertex AI 而不是 Gemini API

### 问题3：向量维度不匹配

**现象**：返回的向量维度不是 768

**解决**：
- 检查实际返回的向量维度
- 更新 `embedding_service.py` 中的 `self.dimension`
- 更新数据库表定义中的向量维度

## 📝 下一步

测试成功后，可以：

1. **运行完整测试**：`python test_embedding.py`
2. **测试数据库集成**：运行迁移脚本并测试向量存储
3. **集成到现有 API**：开始阶段3的实施

## 💡 提示

如果 Gemini Embedding API 不可用，可以考虑：

1. **使用 Vertex AI Embedding**
   ```python
   from google.cloud import aiplatform
   aiplatform.init(project="your-project", location="us-central1")
   # 使用 text-embedding-004
   ```

2. **使用 OpenAI Embedding**（如果已配置）
   ```python
   from openai import OpenAI
   client = OpenAI()
   response = client.embeddings.create(
       model="text-embedding-3-small",
       input=text
   )
   embedding = response.data[0].embedding
   ```

3. **使用开源模型**（需要本地部署）
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
   embedding = model.encode(text)
   ```

