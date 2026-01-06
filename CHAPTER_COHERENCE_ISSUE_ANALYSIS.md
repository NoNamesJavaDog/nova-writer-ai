# 生成下一章不连贯问题排查报告

## 问题描述
用户反馈：生成下一章时，小说内容不连贯。

## 问题分析

### 🔴 关键问题1：当前章节内容可能未被包含在上下文中

**位置**：`backend/main.py` 第2576-2590行

**问题**：
1. 在生成下一章时，`write_chapter_content_impl` 使用向量数据库检索上下文
2. `exclude_chapter_ids` 参数排除了 `next_chapter_obj.id`（下一章ID），这是正确的
3. **但是**，当前章节（`current_chapter_obj`）的内容可能没有被包含在上下文中，因为：
   - 向量检索可能没有找到当前章节（如果当前章节刚生成，向量可能还没存储或索引未更新）
   - 向量检索是基于语义相似度的，可能检索到其他章节，但遗漏了当前章节
   - 当前章节是下一章最直接的上下文，应该被**强制包含**

**代码位置**：
```python
# backend/main.py:2577-2590
content = write_chapter_content_impl(
    ...
    current_chapter_id=next_chapter_obj.id,  # 这里传递的是下一章的ID
    ...
)
```

**在 gemini_service.py 中**：
```python
# backend/gemini_service.py:748
exclude_chapter_ids=[current_chapter_id] if current_chapter_id else None,
# 这里排除的是 next_chapter_obj.id，所以下一章被排除了（正确）
# 但是当前章节（current_chapter_obj）没有被强制包含
```

### 🔴 关键问题2：当前章节内容可能未存储向量

**问题**：
- 如果当前章节刚刚生成，向量可能还没有存储
- 即使存储了，向量索引可能还没有更新
- 导致向量检索无法找到当前章节

### 🔴 关键问题3：向量检索可能遗漏当前章节

**问题**：
- 向量检索是基于语义相似度的，可能检索到其他相关章节
- 但当前章节可能因为相似度不够高而被遗漏
- 当前章节是下一章最直接的上下文，应该被**优先包含**

### ⚠️ 次要问题4：上下文格式可能不够清晰

**问题**：
- 向量检索返回的上下文格式可能不够清晰
- 当前章节的内容应该被明确标记为"上一章内容"

## 解决方案

### 方案1：强制包含当前章节内容（推荐）

在生成下一章时，**强制将当前章节的内容添加到上下文中**，无论向量检索是否找到它。

**实现步骤**：
1. 在 `write_next_chapter` 任务中，获取当前章节的完整内容
2. 将当前章节内容格式化后，**优先添加到上下文的最前面**
3. 然后再添加向量检索找到的其他相关章节

**优点**：
- 确保当前章节内容被包含
- 不依赖向量检索的准确性
- 保证章节之间的连贯性

### 方案2：确保当前章节向量已存储

在生成下一章之前，确保当前章节的向量已经存储并索引更新。

**实现步骤**：
1. 检查当前章节是否有向量
2. 如果没有，先存储向量
3. 等待索引更新（或使用同步存储）

**缺点**：
- 可能增加延迟
- 仍然依赖向量检索的准确性

### 方案3：增强上下文格式

改进上下文格式，明确标记当前章节和其他章节。

**实现步骤**：
1. 将当前章节标记为"【上一章内容】"
2. 将其他章节标记为"【相关前文参考】"
3. 在提示词中强调必须承接上一章内容

## 推荐方案

**采用方案1 + 方案3的组合**：
1. 强制包含当前章节内容（方案1）
2. 改进上下文格式，明确标记（方案3）

这样可以：
- 确保当前章节内容被包含
- 明确告诉AI这是上一章内容，必须承接
- 不依赖向量检索的准确性

## 具体实现建议

### 修改点1：在 `write_next_chapter` 任务中

```python
# 在生成下一章之前，获取当前章节内容
current_chapter_content = current_chapter_obj.content or ""

# 构建强制上下文（当前章节）
forced_context = ""
if current_chapter_content and current_chapter_content.strip():
    # 取当前章节的最后1000字（结尾部分，最重要）
    content_preview = current_chapter_content[-1000:] if len(current_chapter_content) > 1000 else current_chapter_content
    forced_context = f"""
【上一章内容】（必须承接）：
章节标题：{current_chapter_obj.title}
章节结尾内容：
{content_preview}

⚠️ 重要：这是上一章的结尾内容，下一章必须自然承接这个结尾，不能出现情节跳跃或逻辑断裂。
"""

# 将强制上下文传递给 write_chapter_content_impl
# 或者修改 write_chapter_content_impl 支持强制上下文参数
```

### 修改点2：修改 `write_chapter_content_impl` 函数

添加 `forced_previous_chapter_context` 参数，用于传递当前章节内容。

### 修改点3：修改 `ConsistencyChecker.get_relevant_context_text`

在返回上下文时，如果提供了强制上下文，将其放在最前面。

## 验证方法

修复后，验证以下场景：
1. 连续生成多章，检查章节之间的连贯性
2. 检查当前章节内容是否被包含在下一章的上下文中
3. 检查AI是否能够正确承接上一章的结尾

## 预期效果

修复后，生成下一章时：
1. ✅ 当前章节内容被强制包含在上下文中
2. ✅ 上下文格式清晰，明确标记"上一章内容"
3. ✅ AI能够正确承接上一章的结尾
4. ✅ 章节之间连贯性显著提升

