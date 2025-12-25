# 段落级精确匹配功能

## 📋 功能说明

`find_similar_paragraphs()` 提供了段落级别的精确匹配功能，可以找到与查询文本语义相似的特定段落，而不仅仅是整个章节。

## 🎯 使用场景

1. **精确查找重复段落**：找到与某段文本高度相似的段落
2. **细节对比**：比较不同章节中的相似描写或对话
3. **内容审核**：检查是否有重复的描写模式

## 🔧 API 使用

```python
from services.embedding_service import EmbeddingService

service = EmbeddingService()
similar_paragraphs = service.find_similar_paragraphs(
    db=db,
    novel_id=novel_id,
    query_text="一段要查询的文本",
    exclude_chapter_ids=["chapter_id_1", "chapter_id_2"],  # 可选
    limit=10,  # 返回最多10个结果
    similarity_threshold=0.75  # 相似度阈值（默认0.75，比章节级更严格）
)

for para in similar_paragraphs:
    print(f"章节: {para['chapter_title']}")
    print(f"段落索引: {para['paragraph_index']}")
    print(f"相似度: {para['similarity']:.2f}")
    print(f"段落内容: {para['paragraph_text']}")
    print("---")
```

## 📊 返回值

每个结果包含：
- `chapter_id`: 章节ID
- `chapter_title`: 章节标题
- `paragraph_index`: 段落索引（从0开始）
- `similarity`: 相似度分数（0-1之间）
- `paragraph_text`: 段落文本内容

## ⚙️ 技术实现

### 工作原理

1. **向量存储**：每个章节的内容被分割成多个段落，每个段落都有独立的向量
2. **段落向量数组**：所有段落的向量存储在 `paragraph_embeddings` 字段中（vector数组）
3. **相似度计算**：使用 `unnest` 展开段落向量数组，逐个计算与查询向量的相似度
4. **文本提取**：根据段落索引从章节内容中提取对应的段落文本

### 性能考虑

- 使用 PostgreSQL 的数组操作和 `unnest` 函数
- 使用向量索引（HNSW）加速相似度计算
- 限制返回结果数量（默认10个）

### 阈值建议

- **0.85+**：几乎完全相同的段落
- **0.75-0.85**：高度相似的段落（默认阈值）
- **0.65-0.75**：中等相似，可能需要人工判断
- **< 0.65**：较低相似度，可能只是主题相关

## 💡 示例用法

### 示例1：检查重复描写

```python
# 检查是否有重复的环境描写
query = "月光洒在古老的石阶上，斑驳的光影随着夜风摇曳"
similar = service.find_similar_paragraphs(
    db=db,
    novel_id=novel_id,
    query_text=query,
    similarity_threshold=0.8  # 较高的阈值，找几乎相同的段落
)

if similar:
    print(f"发现 {len(similar)} 个高度相似的段落")
    for para in similar:
        print(f"章节 {para['chapter_title']}: {para['paragraph_text'][:100]}...")
```

### 示例2：查找相关对话模式

```python
# 查找相似的对话模式
query = "你确定要这样做吗？"
similar = service.find_similar_paragraphs(
    db=db,
    novel_id=novel_id,
    query_text=query,
    limit=20  # 返回更多结果
)

# 分析对话模式
dialogue_patterns = [para['paragraph_text'] for para in similar]
```

## 🔍 与章节级匹配的区别

| 特性 | 章节级匹配 | 段落级匹配 |
|------|-----------|-----------|
| 粒度 | 整个章节 | 单个段落 |
| 精度 | 较粗 | 较细 |
| 用途 | 整体相似性 | 精确重复检测 |
| 阈值 | 0.7（默认） | 0.75（默认，更严格） |
| 性能 | 较快 | 稍慢（需要展开数组） |

## ⚠️ 注意事项

1. **段落索引**：段落索引从0开始，对应章节内容分割后的段落顺序
2. **内容分割**：段落分割基于标点符号，可能与实际段落不完全一致
3. **性能**：对于有很多段落的长章节，查询可能稍慢
4. **阈值选择**：建议使用较高的阈值（0.75+）以获得有意义的结果

## 🚀 集成建议

### 在API中使用

```python
@router.post("/novels/{novel_id}/chapters/find-similar-paragraphs")
async def find_similar_paragraphs(
    novel_id: str,
    query_text: str,
    similarity_threshold: float = 0.75,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查找相似段落"""
    service = EmbeddingService()
    results = service.find_similar_paragraphs(
        db=db,
        novel_id=novel_id,
        query_text=query_text,
        similarity_threshold=similarity_threshold,
        limit=limit
    )
    return {"results": results, "count": len(results)}
```

### 在内容审核中使用

```python
# 生成章节后，检查是否有重复段落
def check_duplicate_paragraphs(chapter_content: str, novel_id: str, db: Session):
    service = EmbeddingService()
    
    # 将新章节内容分割成段落
    chunks = service._split_into_chunks(chapter_content, chunk_size=500)
    
    duplicates = []
    for chunk in chunks[:10]:  # 只检查前10个段落
        similar = service.find_similar_paragraphs(
            db=db,
            novel_id=novel_id,
            query_text=chunk,
            similarity_threshold=0.8  # 高阈值
        )
        if similar:
            duplicates.extend(similar)
    
    return duplicates
```

