# 向量数据库使用说明

## ✅ `write_and_save_chapter` 确实使用了向量数据库

### 工作原理

`write_and_save_chapter` 函数在生成章节内容时**确实使用了向量数据库**，但使用方式是通过内部自动检索，而不是显式传入上下文。

### 使用流程

1. **传入参数**
   ```python
   previous_chapters_context=None,  # 传入 None，让函数内部自动检索
   novel_id=context.novel.id,       # 提供小说ID
   current_chapter_id=context.chapter.id,  # 提供当前章节ID
   db_session=context.task_db       # 提供数据库会话
   ```

2. **内部自动检索**（在 `write_chapter_content_impl` 中）
   ```python
   # 第742-784行：如果提供了 novel_id 和 db_session
   if novel_id and db_session:
       # 使用 ConsistencyChecker 从向量数据库检索相关章节
       checker = ConsistencyChecker()
       smart_context = checker.get_relevant_context_text(
           db=db_session,
           novel_id=novel_id,
           current_chapter_title=chapter_title,
           current_chapter_summary=chapter_summary,
           exclude_chapter_ids=[current_chapter_id] if current_chapter_id else None,
           max_chapters=5
       )
       
       if smart_context and smart_context.strip():
           previous_chapters_context = smart_context  # 使用检索到的上下文
   ```

3. **向量检索过程**
   - `ConsistencyChecker.get_relevant_context_text()` 调用
   - `EmbeddingService.find_similar_chapters()` 进行向量相似度搜索
   - 返回最相关的 5 个章节作为上下文

### 向量数据库的作用

1. **智能上下文检索**
   - 基于章节标题和摘要的语义相似度
   - 自动找到最相关的前文章节
   - 避免手动传递上下文

2. **相似度检查**
   - 在生成前检查是否与已有内容重复
   - 使用 `ContentSimilarityChecker` 进行相似度检查
   - 如果相似度超过阈值（0.8），会发出警告

3. **上下文格式**
   - 检索到的章节会格式化为文本
   - 包含章节标题、摘要和关键内容预览
   - 作为 AI 提示的一部分传入

### 代码位置

- **调用位置**: `backend/services/ai/chapter_writing_service.py` 第88-102行
- **检索逻辑**: `backend/services/ai/gemini_service.py` 第742-784行
- **检索服务**: `backend/services/analysis/consistency_checker.py`
- **向量服务**: `backend/services/embedding/embedding_service.py`

### 验证方法

可以通过日志确认向量数据库是否被使用：

```python
# 成功使用向量检索时，会输出：
logger.info("✅ 使用智能上下文检索，找到 X 个相关章节")

# 如果检索失败，会输出警告：
logger.warning("⚠️  智能上下文检索失败，使用原始上下文: {error}")
```

### 注意事项

1. **条件要求**
   - 必须提供 `novel_id` 和 `db_session`
   - 如果缺少这些参数，不会进行向量检索

2. **失败处理**
   - 如果向量检索失败，不会影响章节生成
   - 会继续使用其他上下文（如 `forced_previous_chapter_context`）

3. **性能考虑**
   - 向量检索需要时间，但通常很快（< 1秒）
   - 检索结果会被缓存以提高性能

## 总结

✅ **`write_and_save_chapter` 确实使用了向量数据库**

- 通过 `ConsistencyChecker` 自动检索相关章节
- 基于语义相似度找到最相关的前文
- 检索到的上下文会自动添加到 AI 提示中
- 如果检索失败，不会影响章节生成流程

这种设计让向量数据库的使用对调用者透明，只需要提供 `novel_id` 和 `db_session`，函数会自动进行智能上下文检索。

