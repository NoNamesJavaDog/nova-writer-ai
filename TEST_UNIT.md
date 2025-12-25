# 单元测试指南

## 📋 测试脚本

使用 `test_unit.py` 进行单元测试。

## 🚀 运行测试

```bash
cd backend
python test_unit.py
```

或者使用unittest：

```bash
python -m unittest test_unit
```

## ✅ 测试内容

### 1. EmbeddingService测试
- 文本分块功能
- 空文本处理
- 分块大小验证

### 2. ConsistencyChecker测试
- 服务初始化
- 基本功能验证

### 3. ForeshadowingMatcher测试
- 服务初始化
- 基本功能验证

### 4. ContentSimilarityChecker测试
- 服务初始化
- 基本功能验证

### 5. VectorHelper测试
- 函数导入
- 单例模式验证

## 📊 测试覆盖

当前测试覆盖：
- ✅ 服务初始化
- ✅ 基本功能验证
- ✅ 边界情况处理
- ⏳ API调用（需要mock）
- ⏳ 数据库操作（需要mock）

## 🔧 扩展测试

可以添加更多测试：

```python
class TestEmbeddingService(unittest.TestCase):
    def test_generate_embedding_with_mock(self):
        """使用mock测试向量生成"""
        with patch('services.embedding_service.client') as mock_client:
            mock_client.models.embed_content.return_value = Mock(embedding=[0.1] * 768)
            
            embedding = self.service.generate_embedding("测试文本")
            self.assertEqual(len(embedding), 768)
```

## ⚠️ 注意事项

1. **不需要数据库**：当前测试不依赖数据库
2. **不需要API调用**：当前测试不调用实际API
3. **可以扩展**：可以根据需要添加更多测试

## 📚 相关文档

- **性能测试**：`TEST_PERFORMANCE.md`
- **功能测试**：`TEST_VECTOR_FEATURES.md`

