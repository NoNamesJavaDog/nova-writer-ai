# pgvector 向量数据库集成 - 使用指南

## 📚 目录

1. [快速开始](#快速开始)
2. [功能概览](#功能概览)
3. [API使用](#api使用)
4. [配置说明](#配置说明)
5. [故障排除](#故障排除)

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 运行数据库迁移

```bash
python migrate_add_pgvector.py
```

这会：
- 安装 pgvector 扩展
- 创建4个向量表
- 创建必要的索引

### 3. 配置环境变量

确保 `.env` 文件中包含：
```env
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:password@host:port/database
```

### 4. 配置日志（可选）

```python
# 在 main.py 或 run.py 中
from config_logging import setup_logging
import logging

setup_logging(level=logging.INFO)  # 生产环境
# setup_logging(level=logging.DEBUG)  # 开发环境（更详细）
```

### 5. 测试

```bash
# 简单测试
python test_embedding_simple.py

# 完整测试
python test_embedding.py
```

## 🎯 功能概览

### 1. 智能去重系统

**功能**：检测语义相似的章节，避免重复内容

**使用**：
```python
from services.embedding_service import EmbeddingService

service = EmbeddingService()
similar = service.find_similar_chapters(
    db=db,
    novel_id=novel_id,
    query_text="章节内容或标题",
    similarity_threshold=0.8
)
```

### 2. 智能上下文推荐

**功能**：根据当前章节主题，推荐最相关的上下文章节

**使用**：
```python
from services.consistency_checker import ConsistencyChecker

checker = ConsistencyChecker()
context = checker.get_relevant_context_text(
    db=db,
    novel_id=novel_id,
    current_chapter_title="新章节标题",
    current_chapter_summary="章节摘要",
    max_chapters=3
)
```

### 3. 内容相似度检查

**功能**：在生成章节前检查是否与已有内容重复

**使用**：
```python
from services.content_similarity_checker import ContentSimilarityChecker

checker = ContentSimilarityChecker()
result = checker.check_before_generation(
    db=db,
    novel_id=novel_id,
    chapter_title="新章节",
    chapter_summary="摘要",
    similarity_threshold=0.8
)

if result["has_similar_content"]:
    print("警告：存在相似章节")
```

### 4. 智能伏笔匹配

**功能**：自动匹配章节内容可能解决的伏笔

**使用**：
```python
from services.foreshadowing_matcher import ForeshadowingMatcher

matcher = ForeshadowingMatcher()
result = matcher.auto_update_foreshadowing_resolution(
    db=db,
    novel_id=novel_id,
    chapter_id=chapter_id,
    chapter_content=chapter.content,
    auto_update=False  # 建议设为False，手动确认
)
```

### 5. 向量存储

**功能**：自动存储章节、角色、世界观、伏笔的向量

**使用**：
```python
from services.vector_helper import store_chapter_embedding_async

# 在后台任务中调用
store_chapter_embedding_async(
    db=db,
    chapter_id=chapter_id,
    novel_id=novel_id,
    content=chapter.content
)
```

## 📡 API使用

### 集成到现有API

参考 `api_integration_example.py` 中的完整示例。

**基本步骤**：

1. **导入模块**
```python
from services.vector_helper import store_chapter_embedding_async
from fastapi import BackgroundTasks
```

2. **在章节创建/更新时存储向量**
```python
@router.post("/volumes/{volume_id}/chapters")
async def create_chapters(
    volume_id: str,
    chapters: List[ChapterCreate],
    background_tasks: BackgroundTasks,  # 新增
    db: Session = Depends(get_db),
    ...
):
    # ... 创建章节 ...
    
    # 存储向量（后台任务）
    for chapter in created_chapters:
        if chapter.content:
            background_tasks.add_task(
                store_chapter_embedding_async,
                db=db,
                chapter_id=chapter.id,
                novel_id=volume.novel_id,
                content=chapter.content
            )
```

3. **使用智能上下文**
```python
from gemini_service import write_chapter_content_stream

stream = write_chapter_content_stream(
    # ... 原有参数 ...
    novel_id=novel.id,  # 新增
    current_chapter_id=chapter_id,  # 新增
    db_session=db  # 新增
)
```

### 新增API端点

#### 1. 相似度检查
```
POST /api/novels/{novel_id}/chapters/check-similarity
Body: {
    "content": "要检查的内容",
    "current_chapter_id": "可选",
    "threshold": 0.8
}
```

#### 2. 伏笔匹配
```
POST /api/novels/{novel_id}/foreshadowings/match-resolutions
Body: {
    "chapter_id": "章节ID",
    "auto_update": false,
    "similarity_threshold": 0.8
}
```

#### 3. 生成前检查
```
POST /api/novels/{novel_id}/chapters/check-before-generation
Body: {
    "chapter_title": "章节标题",
    "chapter_summary": "章节摘要",
    "current_chapter_id": "可选"
}
```

## ⚙️ 配置说明

### 相似度阈值

- **伏笔匹配**：0.75-0.85（推荐0.8）
- **相似度检查（生成前）**：0.8（较宽松）
- **相似度检查（生成后）**：0.85（较严格）
- **智能上下文检索**：0.6（较低，获取更多相关章节）

### 重试配置

在 `embedding_service.py` 中：
```python
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 1  # 重试延迟（秒）
```

### 日志级别

- **DEBUG**：详细的调试信息
- **INFO**：关键操作日志（推荐生产环境）
- **WARNING**：警告信息
- **ERROR**：错误信息

## 🔧 故障排除

### 问题1：pgvector 扩展未安装

**错误**：`extension "vector" does not exist`

**解决**：
```bash
# 在 PostgreSQL 服务器上
sudo apt-get install postgresql-14-pgvector  # 根据版本调整
```

### 问题2：向量生成失败

**错误**：`生成向量失败: ...`

**可能原因**：
1. Gemini API Key 未配置或无效
2. API调用方式不正确
3. 网络问题

**解决**：
1. 检查 `.env` 文件中的 `GEMINI_API_KEY`
2. 运行 `test_embedding_simple.py` 测试API调用
3. 查看日志了解详细错误信息

### 问题3：向量维度不匹配

**错误**：向量维度错误

**解决**：
- 检查 `embedding_service.py` 中的 `self.dimension`（应该是768）
- 确认数据库表定义中的向量维度

### 问题4：性能问题

**症状**：向量生成和存储很慢

**优化建议**：
1. 使用后台任务处理向量存储
2. 考虑实施Redis缓存
3. 批量处理时控制并发数量

### 问题5：相似度检查不准确

**解决**：
1. 调整相似度阈值
2. 检查向量是否正确生成和存储
3. 查看日志了解详细情况

## 📊 性能指标

### 预期性能

- **向量生成**：约1-3秒/章节
- **向量存储**：约0.5-1秒
- **相似度检索**：约0.1-0.5秒（使用索引）
- **智能上下文检索**：约1-2秒

### 优化建议

1. **使用后台任务**：向量存储不应阻塞主流程
2. **批量处理**：多个章节时可以批量生成向量
3. **缓存**：常用章节向量可以缓存
4. **索引优化**：确保HNSW索引已创建

## 🔗 相关文档

- **完整方案**：`PGVECTOR_INTEGRATION_PLAN.md`
- **任务清单**：`PGVECTOR_IMPLEMENTATION_CHECKLIST.md`
- **设置指南**：`PGVECTOR_SETUP_GUIDE.md`
- **测试指南**：`TEST_EMBEDDING.md`
- **最终总结**：`PGVECTOR_FINAL_SUMMARY.md`

## 💡 最佳实践

1. **错误处理**：所有向量操作都有错误处理，失败不应影响主流程
2. **日志记录**：启用日志以便排查问题
3. **阈值调优**：根据实际使用情况调整相似度阈值
4. **性能监控**：定期检查日志，识别慢操作
5. **测试验证**：在生产环境前充分测试

## 📞 支持

如有问题，请：
1. 查看日志了解详细错误信息
2. 运行测试脚本验证功能
3. 参考相关文档
4. 检查配置是否正确

