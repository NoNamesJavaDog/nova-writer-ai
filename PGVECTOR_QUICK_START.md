# pgvector 向量数据库集成 - 快速开始指南

## 🚀 5分钟快速部署

### 步骤1：安装依赖（1分钟）

```bash
cd backend
pip install -r requirements.txt
```

### 步骤2：运行数据库迁移（1分钟）

```bash
python migrate_add_pgvector.py
```

**注意**：如果提示 pgvector 扩展未安装，需要在 PostgreSQL 服务器上执行：
```bash
sudo apt-get install postgresql-14-pgvector  # 根据你的 PostgreSQL 版本调整
```

### 步骤3：配置环境变量（30秒）

确保 `.env` 文件中有：
```env
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:password@host:port/database
```

### 步骤4：测试（1分钟）

```bash
# 测试API调用方式
python test_embedding_simple.py

# 完整测试
python test_embedding.py
```

### 步骤5：配置日志（可选，30秒）

在 `main.py` 或 `run.py` 中添加：
```python
from config_logging import setup_logging
import logging

setup_logging(level=logging.INFO)
```

## ✅ 验证安装

如果所有步骤都成功，你应该看到：

1. ✅ 数据库迁移成功，4个表已创建
2. ✅ 向量生成测试通过（维度768）
3. ✅ 文本分块测试通过
4. ✅ 数据库连接测试通过

## 🔧 快速集成

### 在章节API中添加向量存储

```python
from services.vector_helper import store_chapter_embedding_async
from fastapi import BackgroundTasks

@router.post("/volumes/{volume_id}/chapters")
async def create_chapters(
    volume_id: str,
    chapters: List[ChapterCreate],
    background_tasks: BackgroundTasks,  # 新增
    db: Session = Depends(get_db),
    ...
):
    # ... 创建章节 ...
    
    # 存储向量
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

### 在AI生成中使用智能上下文

```python
from gemini_service import write_chapter_content_stream

stream = write_chapter_content_stream(
    # ... 原有参数 ...
    novel_id=novel.id,  # 新增
    db_session=db  # 新增
)
```

## 📚 下一步

- **完整文档**：查看 `PGVECTOR_README.md`
- **集成示例**：查看 `api_integration_example.py`
- **详细方案**：查看 `PGVECTOR_INTEGRATION_PLAN.md`

## ⚠️ 常见问题

**Q: 迁移脚本失败？**
A: 检查 PostgreSQL 版本，确保 pgvector 扩展已安装

**Q: 向量生成失败？**
A: 运行 `test_embedding_simple.py` 检查 API 调用方式

**Q: 性能慢？**
A: 确保使用后台任务，不要阻塞主流程


