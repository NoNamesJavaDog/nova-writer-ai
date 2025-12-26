# pgvector 向量数据库集成 - 快速参考

## 🚀 快速命令

### 数据库迁移
```bash
cd backend
python migrate_add_pgvector.py
```

### 运行测试
```bash
# 功能完整性测试
python test_vector_features.py

# API调用测试
python test_embedding_simple.py

# 完整测试
python test_embedding.py
```

### 配置日志
```python
from config_logging import setup_logging
import logging
setup_logging(level=logging.INFO)
```

## 📡 API使用示例

### 1. 存储章节向量

```python
from services.vector_helper import store_chapter_embedding_async
from fastapi import BackgroundTasks

@router.post("/volumes/{volume_id}/chapters")
async def create_chapters(
    volume_id: str,
    chapters: List[ChapterCreate],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
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

### 2. 智能上下文检索

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

### 3. 查找相似章节

```python
from services.embedding_service import EmbeddingService

service = EmbeddingService()
similar = service.find_similar_chapters(
    db=db,
    novel_id=novel_id,
    query_text="查询文本",
    similarity_threshold=0.7,
    limit=5
)
```

### 4. 查找相似段落

```python
from services.embedding_service import EmbeddingService

service = EmbeddingService()
similar_paragraphs = service.find_similar_paragraphs(
    db=db,
    novel_id=novel_id,
    query_text="查询文本",
    similarity_threshold=0.75,
    limit=10
)
```

### 5. 伏笔匹配

```python
from services.foreshadowing_matcher import ForeshadowingMatcher

matcher = ForeshadowingMatcher()
result = matcher.match_foreshadowing_resolutions(
    db=db,
    novel_id=novel_id,
    chapter_id=chapter_id,
    chapter_content=chapter.content,
    similarity_threshold=0.8
)
```

### 6. 相似度检查

```python
from services.content_similarity_checker import ContentSimilarityChecker

checker = ContentSimilarityChecker()
result = checker.check_before_generation(
    db=db,
    novel_id=novel_id,
    chapter_title="章节标题",
    chapter_summary="章节摘要",
    similarity_threshold=0.8
)
```

### 7. 在AI生成中使用智能上下文

```python
from gemini_service import write_chapter_content_stream

stream = write_chapter_content_stream(
    # ... 原有参数 ...
    novel_id=novel.id,  # 新增
    current_chapter_id=chapter_id,  # 新增（可选）
    db_session=db  # 新增
)
```

## ⚙️ 配置参数

### 相似度阈值建议

| 用途 | 推荐值 | 说明 |
|------|--------|------|
| 章节级检索 | 0.7 | 整体相似性 |
| 段落级匹配 | 0.75 | 精确匹配 |
| 伏笔匹配 | 0.8 | 高精度 |
| 生成前检查 | 0.8 | 警告阈值 |
| 生成后检查 | 0.85 | 严格阈值 |
| 一致性检查 | 0.65 | 较宽松 |

### 重试配置

```python
# 在 embedding_service.py 中
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 1  # 重试延迟（秒）
```

## 📊 性能指标

### 预期性能

- 向量生成：1-3秒/章节
- 向量存储：0.5-1秒
- 章节级检索：0.1-0.5秒
- 段落级检索：0.2-0.8秒
- 智能上下文检索：1-2秒

## 🔧 常用操作

### 存储向量

```python
# 章节
store_chapter_embedding_async(db, chapter_id, novel_id, content)

# 角色
store_character_embedding(db, character_id, novel_id, name, personality, background, goals)

# 世界观
store_world_setting_embedding(db, world_setting_id, novel_id, title, description)

# 伏笔
store_foreshadowing_embedding(db, foreshadowing_id, novel_id, content)
```

### 检索操作

```python
# 章节级
service.find_similar_chapters(db, novel_id, query_text, threshold=0.7, limit=5)

# 段落级
service.find_similar_paragraphs(db, novel_id, query_text, threshold=0.75, limit=10)

# 智能上下文
checker.get_relevant_context_text(db, novel_id, title, summary, max_chapters=3)
```

### 检查操作

```python
# 一致性检查
checker.check_character_consistency(db, novel_id, chapter_content, character_id)

# 相似度检查
similarity_checker.check_before_generation(db, novel_id, title, summary)

# 伏笔匹配
matcher.match_foreshadowing_resolutions(db, novel_id, chapter_id, content)
```

## 📁 文件结构

```
backend/
├── services/
│   ├── embedding_service.py          # 向量嵌入服务
│   ├── consistency_checker.py        # 一致性检查服务
│   ├── foreshadowing_matcher.py      # 伏笔匹配服务
│   ├── content_similarity_checker.py # 相似度检查服务
│   └── vector_helper.py              # 向量存储辅助
├── migrate_add_pgvector.py           # 数据库迁移脚本
├── config_logging.py                 # 日志配置
├── test_vector_features.py           # 功能测试
├── test_embedding.py                 # 完整测试
└── api_integration_example.py        # API集成示例
```

## 🔗 相关文档

- **快速开始**：`PGVECTOR_QUICK_START.md`
- **使用指南**：`PGVECTOR_README.md`
- **部署清单**：`PGVECTOR_DEPLOYMENT_CHECKLIST.md`
- **功能清单**：`PGVECTOR_ALL_FEATURES.md`
- **完整方案**：`PGVECTOR_INTEGRATION_PLAN.md`

## ⚠️ 注意事项

1. **后台任务**：向量存储应使用后台任务，避免阻塞主流程
2. **错误处理**：所有向量操作都有错误处理，失败不应影响主流程
3. **性能**：向量生成可能需要时间，注意API调用频率限制
4. **阈值**：根据实际使用情况调整相似度阈值
5. **日志**：启用日志以便排查问题和监控性能

## 🎯 故障排除

### API调用失败
- 检查 API Key
- 运行 `test_embedding_simple.py` 验证

### 数据库错误
- 检查连接配置
- 验证表和扩展是否存在

### 性能问题
- 使用后台任务
- 检查网络延迟
- 监控日志


