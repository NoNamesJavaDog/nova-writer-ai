# 向量数据库在提示词生成中的作用

## ✅ 确认：向量数据库确实用于生成提示词，确保上下文连贯

### 工作原理

在生成章节内容时，系统会：
1. **从向量数据库检索相关章节** - 基于语义相似度
2. **将检索结果添加到提示词** - 作为上下文参考
3. **确保内容连贯** - 提供前文参考，避免重复

### 详细流程

#### 第一步：向量检索（第742-784行）

```python
# 在 write_chapter_content 函数中
if novel_id and db_session:
    # 1. 使用 ConsistencyChecker 从向量数据库检索
    checker = ConsistencyChecker()
    smart_context = checker.get_relevant_context_text(
        db=db_session,
        novel_id=novel_id,
        current_chapter_title=chapter_title,
        current_chapter_summary=chapter_summary,
        exclude_chapter_ids=[current_chapter_id] if current_chapter_id else None,
        max_chapters=5  # 检索最多5个相关章节
    )
    
    if smart_context and smart_context.strip():
        previous_chapters_context = smart_context  # 保存检索结果
```

#### 第二步：构建提示词上下文部分（第617-658行）

```python
# 构建前文上下文部分
previous_context_section = ""

# 1. 优先使用强制上下文（上一章完整内容，用于"生成下一章"）
if forced_previous_chapter_context:
    previous_context_section = f"""
{forced_previous_chapter_context}
⚠️ 重要：这是上一章的结尾内容，下一章必须自然承接这个结尾。
"""

# 2. 添加向量检索的相关章节（作为参考）
if previous_chapters_context and previous_chapters_context.strip():
    previous_context_section += f"""

【相关前文参考】（基于向量相似度智能推荐的其他相关章节）：
{previous_chapters_context}
"""

# 3. 添加重复内容检查要求
if previous_context_section:
    previous_context_section += """
🚨 【重复内容检查要求】- 必须严格遵守：
1. ❌ 绝对禁止：重复前文中已经完整描述过的场景、事件、对话
2. ✅ 正确做法：本章必须推进全新情节，展现新的冲突和发展
...
"""
```

#### 第三步：将上下文插入最终提示词（第660-691行）

```python
prompt = f"""请为小说《{novel_title}》创作一个完整的章节。

【章节基本信息】
- 标题：{chapter_title}
- 情节摘要：{chapter_summary}

【小说背景信息】
- 完整简介：{synopsis}
- 涉及角色：{characters_text}
- 世界观规则：{world_text}

{previous_context_section}  # ← 向量检索的上下文在这里！

【创作要求】
...
⚠️ 最重要：认真阅读【前文内容参考】，确保本章内容完全原创，不与前文重复！
"""
```

### 向量检索的上下文格式

检索到的章节会被格式化为：

```
第1章《章节标题》
摘要：章节摘要
关键内容：章节内容预览（前500字）

---

第2章《章节标题》
摘要：章节摘要
关键内容：章节内容预览（前500字）

...
```

### 连贯性保证机制

#### 1. **强制上下文**（上一章完整内容）
- 用于"生成下一章"场景
- 确保直接承接上一章的结尾
- 优先级最高

#### 2. **向量检索上下文**（相关章节）
- 基于语义相似度自动推荐
- 提供角色、情节、世界观的相关参考
- 帮助保持整体连贯性

#### 3. **重复内容检查**
- 在提示词中明确要求避免重复
- 强调推进新情节
- 要求不同的叙述风格

### 使用场景

#### ✅ 场景1：生成下一章
```python
# 包含：
# 1. 上一章完整内容（forced_previous_chapter_context）
# 2. 向量检索的相关章节（previous_chapters_context）
# → 确保直接连贯 + 整体连贯
```

#### ✅ 场景2：AI生成草稿
```python
# 包含：
# 1. 向量检索的相关章节（previous_chapters_context）
# → 确保整体连贯
```

#### ✅ 场景3：一键写作本卷
```python
# 包含：
# 1. 向量检索的相关章节（previous_chapters_context）
# → 每章都能参考相关前文，保持连贯
```

### 向量检索的智能性

1. **语义相似度** - 基于章节标题和摘要的语义，不是简单的关键词匹配
2. **自动排除** - 自动排除当前章节，避免自引用
3. **动态检索** - 每次生成时实时检索，总是获取最新的相关章节
4. **数量控制** - 最多5个相关章节，避免提示词过长

### 总结

✅ **向量数据库确实用于生成提示词，确保上下文连贯**

- **检索机制**：基于语义相似度自动检索最相关的前文章节
- **提示词集成**：检索结果被格式化为文本，插入到AI提示词中
- **连贯性保证**：
  - 直接连贯：通过强制上下文（上一章完整内容）
  - 整体连贯：通过向量检索（相关章节参考）
  - 避免重复：通过明确的检查要求

这种设计确保了生成的章节既能自然承接上一章，又能与整体故事保持连贯，同时避免内容重复。

