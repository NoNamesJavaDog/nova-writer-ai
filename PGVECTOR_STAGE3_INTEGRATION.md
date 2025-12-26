# 阶段3：集成应用 - 实施指南

## 📋 已完成的工作

### 1. ConsistencyChecker 服务 ✅
- 创建 `backend/services/consistency_checker.py`
- 实现 `suggest_relevant_context()` - 智能上下文推荐
- 实现 `get_relevant_context_text()` - 获取格式化上下文文本
- 实现 `check_character_consistency()` - 角色一致性检查

### 2. Vector Helper 函数 ✅
- 创建 `backend/services/vector_helper.py`
- 实现 `store_chapter_embedding_async()` - 章节向量存储
- 实现 `store_character_embedding()` - 角色向量存储
- 实现 `store_world_setting_embedding()` - 世界观向量存储
- 实现 `store_foreshadowing_embedding()` - 伏笔向量存储

### 3. 数据库迁移脚本更新 ✅
- 为所有向量表的 ID 字段添加 UNIQUE 约束
- 确保 ON CONFLICT 能正确工作

## 🔧 下一步：集成到现有 API

由于无法直接访问 `main.py` 的完整内容，这里提供集成指南：

### 集成点1：章节创建/更新 API

在章节创建和更新的 API 端点中添加向量存储：

```python
from services.vector_helper import store_chapter_embedding_async

# 在章节创建后
@router.post("/volumes/{volume_id}/chapters")
async def create_chapters(...):
    # ... 现有创建逻辑 ...
    
    # 新增：异步存储向量
    for chapter in created_chapters:
        if chapter.content:
            # 使用后台任务存储向量
            store_chapter_embedding_async(
                db=db,
                chapter_id=chapter.id,
                novel_id=volume.novel_id,
                content=chapter.content
            )
    
    return created_chapters

# 在章节更新时
@router.put("/volumes/{volume_id}/chapters/{chapter_id}")
async def update_chapter(...):
    # ... 现有更新逻辑 ...
    
    # 新增：如果内容变更，更新向量
    if updates.content:
        store_chapter_embedding_async(
            db=db,
            chapter_id=chapter_id,
            novel_id=volume.novel_id,
            content=updates.content
        )
    
    return updated_chapter
```

### 集成点2：修改 gemini_service.py

修改 `write_chapter_content_stream()` 函数，使用智能上下文：

```python
from services.consistency_checker import ConsistencyChecker

def write_chapter_content_stream(
    novel_title: str,
    genre: str,
    synopsis: str,
    chapter_title: str,
    chapter_summary: str,
    chapter_prompt_hints: str,
    characters: list,
    world_settings: list,
    previous_chapters_context: Optional[str] = None,
    novel_id: Optional[str] = None,  # 新增
    current_chapter_id: Optional[str] = None,  # 新增
    db: Optional[Session] = None  # 新增
):
    """生成章节内容（流式）"""
    try:
        # ... 现有代码 ...
        
        # 新增：使用向量检索获取智能上下文
        if novel_id and db:
            try:
                checker = ConsistencyChecker()
                smart_context = checker.get_relevant_context_text(
                    db=db,
                    novel_id=novel_id,
                    current_chapter_title=chapter_title,
                    current_chapter_summary=chapter_summary,
                    exclude_chapter_ids=[current_chapter_id] if current_chapter_id else None,
                    max_chapters=3
                )
                
                if smart_context:
                    previous_chapters_context = smart_context
            except Exception as e:
                # 如果向量检索失败，使用原始上下文
                print(f"⚠️  智能上下文检索失败，使用原始上下文: {str(e)}")
        
        # ... 后续使用 previous_chapters_context ...
```

### 集成点3：创建新的 API 端点

在 `main.py` 或相应的路由文件中添加：

```python
from services.embedding_service import EmbeddingService
from services.consistency_checker import ConsistencyChecker

@router.post("/api/novels/{novel_id}/chapters/check-similarity")
async def check_similarity(
    novel_id: str,
    content: str,
    current_chapter_id: Optional[str] = None,
    threshold: float = 0.8,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查生成内容与已有章节的相似度"""
    try:
        # 验证权限
        novel = db.query(Novel).filter(Novel.id == novel_id, Novel.user_id == current_user.id).first()
        if not novel:
            raise HTTPException(status_code=404, detail="小说不存在")
        
        service = EmbeddingService()
        similar_chapters = service.find_similar_chapters(
            db=db,
            novel_id=novel_id,
            query_text=content,
            exclude_chapter_ids=[current_chapter_id] if current_chapter_id else None,
            limit=5,
            similarity_threshold=threshold
        )
        
        if similar_chapters:
            return {
                "has_similar_content": True,
                "similar_chapters": similar_chapters,
                "warning": f"发现 {len(similar_chapters)} 个相似章节，建议检查是否重复"
            }
        
        return {
            "has_similar_content": False,
            "similar_chapters": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查相似度失败: {str(e)}")
```

## ⚠️ 注意事项

1. **异步处理**：向量生成和存储可能较慢，建议：
   - 使用后台任务（如 Celery）
   - 或使用 `asyncio.create_task()`（FastAPI 支持）
   - 确保不阻塞主请求流程

2. **错误处理**：向量存储失败不应影响主要业务逻辑

3. **性能优化**：
   - 仅在内容变更时更新向量
   - 批量处理多个章节的向量生成
   - 使用缓存减少 API 调用

4. **向后兼容**：
   - 如果向量检索失败，应回退到原始逻辑
   - 确保没有向量时系统仍能正常工作

## 📝 测试建议

1. **单元测试**：
   - 测试 ConsistencyChecker 的方法
   - 测试 vector_helper 的函数

2. **集成测试**：
   - 测试章节创建后向量是否正确存储
   - 测试智能上下文检索是否正常工作
   - 测试相似度检查 API

3. **性能测试**：
   - 测试向量生成时间
   - 测试相似度检索响应时间


