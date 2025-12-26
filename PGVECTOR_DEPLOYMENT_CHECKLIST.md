# pgvector 向量数据库集成 - 部署检查清单

## 📋 部署前检查

使用此清单确保所有准备工作已完成。

### 1. 环境准备 ✅

- [ ] Python 环境已配置（建议 Python 3.8+）
- [ ] PostgreSQL 已安装（版本 12+）
- [ ] pgvector 扩展可用（或在迁移脚本中安装）
- [ ] Gemini API Key 已获取并配置

### 2. 依赖安装 ✅

```bash
cd backend
pip install -r requirements.txt
```

检查项：
- [ ] `pgvector==0.2.4` 已安装
- [ ] `google-genai` 已安装（或相关 Gemini SDK）
- [ ] `sqlalchemy` 已安装
- [ ] 其他依赖已安装

### 3. 环境变量配置 ✅

检查 `.env` 文件：

```env
# 必需
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:password@host:port/database

# 可选（日志配置）
LOG_LEVEL=INFO
```

检查项：
- [ ] `GEMINI_API_KEY` 已配置且有效
- [ ] `DATABASE_URL` 已配置且可连接
- [ ] 数据库权限正确（可创建表和扩展）

### 4. 数据库迁移 ✅

```bash
cd backend
python migrate_add_pgvector.py
```

检查项：
- [ ] pgvector 扩展安装成功
- [ ] 4个向量表创建成功：
  - [ ] `chapter_embeddings`
  - [ ] `character_embeddings`
  - [ ] `world_setting_embeddings`
  - [ ] `foreshadowing_embeddings`
- [ ] HNSW 索引创建成功
- [ ] 没有错误信息

### 5. 功能测试 ✅

```bash
cd backend
python test_vector_features.py
```

检查项：
- [ ] 向量生成测试通过
- [ ] 文本分块测试通过
- [ ] 数据库连接测试通过
- [ ] pgvector扩展检查通过
- [ ] 向量表检查通过
- [ ] 服务初始化测试通过

### 6. API调用测试 ✅

```bash
cd backend
python test_embedding_simple.py
```

检查项：
- [ ] Gemini Embedding API 调用成功
- [ ] 向量维度正确（768）
- [ ] 没有API错误

### 7. 日志配置 ✅

在应用启动文件中添加：

```python
from config_logging import setup_logging
import logging

setup_logging(level=logging.INFO)  # 或 logging.DEBUG
```

检查项：
- [ ] 日志配置已添加
- [ ] 日志级别设置合理
- [ ] 日志输出正常

### 8. 代码集成 ✅

检查项：
- [ ] 已查看 `api_integration_example.py` 了解集成方式
- [ ] 已规划API集成位置
- [ ] 已考虑后台任务处理向量存储
- [ ] 已考虑错误处理策略

### 9. 性能考虑 ✅

检查项：
- [ ] 向量存储使用后台任务（不阻塞主流程）
- [ ] 检索操作有合理的超时设置
- [ ] 考虑了向量生成的API调用频率限制
- [ ] 数据库连接池配置合理

### 10. 监控和日志 ✅

检查项：
- [ ] 日志记录已启用
- [ ] 关键操作有日志输出
- [ ] 错误日志会被记录
- [ ] 性能日志可用于分析

## 🚀 部署步骤

### 步骤1：运行数据库迁移

```bash
cd backend
python migrate_add_pgvector.py
```

### 步骤2：运行测试

```bash
python test_vector_features.py
python test_embedding_simple.py
```

### 步骤3：配置日志

在 `main.py` 或 `run.py` 中添加：

```python
from config_logging import setup_logging
import logging
setup_logging(level=logging.INFO)
```

### 步骤4：集成到API（逐步进行）

1. 先集成向量存储（章节创建/更新时）
2. 再集成智能上下文（AI生成时）
3. 最后添加新的API端点（如果需要）

### 步骤5：验证功能

- 创建一个测试章节
- 验证向量是否正确存储
- 测试相似度检索
- 测试智能上下文推荐

## ⚠️ 常见问题排查

### 问题1：迁移脚本失败

**症状**：pgvector扩展未安装

**解决**：
```bash
# 在PostgreSQL服务器上
sudo apt-get install postgresql-14-pgvector  # 根据版本调整
# 或在迁移脚本中自动安装
```

### 问题2：向量生成失败

**症状**：API调用错误

**解决**：
1. 检查 API Key 是否正确
2. 检查 API 调用方式是否符合最新文档
3. 运行 `test_embedding_simple.py` 验证

### 问题3：数据库连接失败

**症状**：连接错误

**解决**：
1. 检查 `DATABASE_URL` 格式
2. 验证数据库服务正在运行
3. 检查防火墙和网络设置

### 问题4：性能问题

**症状**：向量生成很慢

**解决**：
1. 确保使用后台任务
2. 检查网络延迟
3. 考虑批量处理优化
4. 监控API调用频率

## 📊 部署后验证

### 功能验证

- [ ] 章节创建后向量正确存储
- [ ] 相似度检索返回正确结果
- [ ] 智能上下文推荐工作正常
- [ ] 一致性检查功能正常
- [ ] 伏笔匹配功能正常

### 性能验证

- [ ] 向量生成时间合理（< 3秒）
- [ ] 检索速度合理（< 1秒）
- [ ] 数据库查询性能正常
- [ ] 没有明显的内存泄漏

### 日志验证

- [ ] 关键操作有日志记录
- [ ] 错误信息被正确记录
- [ ] 日志级别设置合理
- [ ] 日志文件正常写入

## 🎯 下一步

部署完成后：

1. **监控运行**：观察日志，检查是否有错误
2. **性能调优**：根据实际使用调整阈值和参数
3. **用户反馈**：收集用户反馈，优化功能
4. **扩展功能**：根据需要添加可选功能（Redis缓存等）

## 📚 相关文档

- **快速开始**：`PGVECTOR_QUICK_START.md`
- **使用指南**：`PGVECTOR_README.md`
- **测试指南**：`TEST_VECTOR_FEATURES.md`
- **功能清单**：`PGVECTOR_ALL_FEATURES.md`


