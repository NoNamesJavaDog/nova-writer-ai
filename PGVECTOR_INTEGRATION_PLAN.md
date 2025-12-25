# PostgreSQL 向量数据库集成方案 - 增强写作能力

## 📋 方案概述

通过引入 **pgvector** 扩展，为系统添加语义搜索和智能内容管理能力，显著提升 AI 写作质量。

---

## 🎯 核心价值

### 1. **智能去重系统** ⭐⭐⭐⭐⭐
- **问题**：当前系统只能通过关键词传递前3章，无法检测语义重复
- **解决方案**：使用向量相似度检测生成内容与已有章节的语义相似性
- **效果**：自动识别并避免重复的情节、描写、对话模式

### 2. **智能上下文检索** ⭐⭐⭐⭐⭐
- **问题**：当前固定传递前3章，可能包含不相关信息
- **解决方案**：根据当前章节主题，语义检索最相关的章节段落
- **效果**：AI 获得更精准的上下文，生成更连贯的内容

### 3. **内容一致性保障** ⭐⭐⭐⭐
- **问题**：角色性格、世界观设定在长篇小说中容易不一致
- **解决方案**：向量检索相关角色/设定描述，确保前后一致
- **效果**：角色行为、世界观规则保持一致性

### 4. **智能伏笔管理** ⭐⭐⭐⭐
- **问题**：伏笔与解决章节的关联依赖手动管理
- **解决方案**：语义匹配伏笔内容与章节内容，自动建议关联
- **效果**：自动识别哪些章节可能解决了伏笔，减少遗漏

### 5. **写作风格学习** ⭐⭐⭐
- **问题**：无法学习用户的写作偏好和风格
- **解决方案**：存储并分析用户已写内容的向量特征
- **效果**：生成的文本更符合用户风格

### 6. **内容推荐系统** ⭐⭐⭐
- **问题**：用户可能忘记之前写过类似场景
- **解决方案**：基于语义相似性推荐相关片段作为参考
- **效果**：帮助用户保持写作风格和主题一致性

---

## 🏗️ 技术架构

### 数据库层面

#### 1. 安装 pgvector 扩展
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

#### 2. 新增向量存储表

**章节内容向量表** (`chapter_embeddings`)
```sql
CREATE TABLE chapter_embeddings (
    id VARCHAR(36) PRIMARY KEY,
    chapter_id VARCHAR(36) NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    novel_id VARCHAR(36) NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    
    -- 不同粒度的向量存储
    full_content_embedding vector(768),      -- 完整章节内容向量（用于全局相似性）
    paragraph_embeddings vector(768)[],      -- 段落级别向量数组（用于精确匹配）
    
    -- 元数据
    embedding_model VARCHAR(50) DEFAULT 'text-embedding-004',  -- 使用的模型
    chunk_count INTEGER DEFAULT 0,           -- 段落数量
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    
    -- 索引
    CONSTRAINT chapter_embeddings_chapter_fk FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
);

-- 向量相似度索引（IVFFlat 或 HNSW）
CREATE INDEX idx_chapter_full_embedding ON chapter_embeddings 
    USING ivfflat (full_content_embedding vector_cosine_ops) 
    WITH (lists = 100);

-- 章节ID索引
CREATE INDEX idx_chapter_embeddings_chapter_id ON chapter_embeddings(chapter_id);
CREATE INDEX idx_chapter_embeddings_novel_id ON chapter_embeddings(novel_id);
```

**角色设定向量表** (`character_embeddings`)
```sql
CREATE TABLE character_embeddings (
    id VARCHAR(36) PRIMARY KEY,
    character_id VARCHAR(36) NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    novel_id VARCHAR(36) NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    
    -- 角色描述的向量表示
    full_description_embedding vector(768),  -- 完整角色描述
    
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    
    CONSTRAINT character_embeddings_character_fk FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE INDEX idx_character_embedding ON character_embeddings 
    USING ivfflat (full_description_embedding vector_cosine_ops) 
    WITH (lists = 50);
```

**世界观设定向量表** (`world_setting_embeddings`)
```sql
CREATE TABLE world_setting_embeddings (
    id VARCHAR(36) PRIMARY KEY,
    world_setting_id VARCHAR(36) NOT NULL REFERENCES world_settings(id) ON DELETE CASCADE,
    novel_id VARCHAR(36) NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    
    full_description_embedding vector(768),
    
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    
    CONSTRAINT world_setting_embeddings_world_setting_fk FOREIGN KEY (world_setting_id) REFERENCES world_settings(id) ON DELETE CASCADE
);

CREATE INDEX idx_world_setting_embedding ON world_setting_embeddings 
    USING ivfflat (full_description_embedding vector_cosine_ops) 
    WITH (lists = 50);
```

**伏笔向量表** (`foreshadowing_embeddings`)
```sql
CREATE TABLE foreshadowing_embeddings (
    id VARCHAR(36) PRIMARY KEY,
    foreshadowing_id VARCHAR(36) NOT NULL REFERENCES foreshadowings(id) ON DELETE CASCADE,
    novel_id VARCHAR(36) NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    
    content_embedding vector(768),
    
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    
    CONSTRAINT foreshadowing_embeddings_foreshadowing_fk FOREIGN KEY (foreshadowing_id) REFERENCES foreshadowings(id) ON DELETE CASCADE
);

CREATE INDEX idx_foreshadowing_embedding ON foreshadowing_embeddings 
    USING ivfflat (content_embedding vector_cosine_ops) 
    WITH (lists = 50);
```

---

### 后端层面

#### 1. 依赖安装
```bash
# requirements.txt 新增
pgvector==0.2.4
sentence-transformers>=2.2.0  # 或使用 Google Embedding API
```

#### 2. 嵌入模型选择

**方案A：使用 Gemini Embedding API（推荐）**
- ✅ 与现有 Gemini 模型生态一致
- ✅ 多语言支持好（中文优化）
- ✅ API 调用，无需本地部署
- ⚠️ 需要网络请求

**方案B：使用 Sentence Transformers（本地）**
- ✅ 本地运行，无网络依赖
- ✅ 可离线使用
- ⚠️ 需要服务器资源
- ⚠️ 中文模型需要额外配置

**推荐使用 Gemini Embedding API**，因为：
- 你的系统已经在使用 Gemini
- 中文文本嵌入效果更好
- 避免本地模型部署复杂度

#### 3. 新增服务模块

**`backend/services/embedding_service.py`**
```python
"""
向量嵌入服务
负责生成文本向量、存储、检索
"""
from typing import List, Optional
import google.generativeai as genai
from sqlalchemy import text
from backend.database import get_db
from backend.config import settings

class EmbeddingService:
    def __init__(self):
        self.model = "models/text-embedding-004"  # Gemini Embedding 模型
        self.dimension = 768  # Gemini embedding 维度
    
    async def generate_embedding(self, text: str) -> List[float]:
        """生成文本向量"""
        try:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="RETRIEVAL_DOCUMENT"  # 或 RETRIEVAL_QUERY
            )
            return result['embedding']
        except Exception as e:
            raise Exception(f"生成向量失败: {str(e)}")
    
    async def store_chapter_embedding(
        self, 
        chapter_id: str, 
        novel_id: str,
        content: str,
        chunk_size: int = 500  # 每500字一个段落
    ):
        """存储章节向量（段落级别）"""
        # 1. 生成完整内容向量
        full_embedding = await self.generate_embedding(content)
        
        # 2. 分段落生成向量
        chunks = self._split_into_chunks(content, chunk_size)
        paragraph_embeddings = []
        for chunk in chunks:
            embedding = await self.generate_embedding(chunk)
            paragraph_embeddings.append(embedding)
        
        # 3. 存储到数据库
        async with get_db() as db:
            await db.execute(
                text("""
                    INSERT INTO chapter_embeddings 
                    (id, chapter_id, novel_id, full_content_embedding, paragraph_embeddings, chunk_count, created_at, updated_at)
                    VALUES (:id, :chapter_id, :novel_id, :full_embedding, :paragraph_embeddings, :chunk_count, :created_at, :updated_at)
                    ON CONFLICT (id) DO UPDATE SET
                        full_content_embedding = EXCLUDED.full_content_embedding,
                        paragraph_embeddings = EXCLUDED.paragraph_embeddings,
                        chunk_count = EXCLUDED.chunk_count,
                        updated_at = EXCLUDED.updated_at
                """),
                {
                    "id": str(uuid.uuid4()),
                    "chapter_id": chapter_id,
                    "novel_id": novel_id,
                    "full_embedding": str(full_embedding),
                    "paragraph_embeddings": paragraph_embeddings,
                    "chunk_count": len(paragraph_embeddings),
                    "created_at": int(time.time() * 1000),
                    "updated_at": int(time.time() * 1000)
                }
            )
    
    async def find_similar_chapters(
        self,
        novel_id: str,
        query_text: str,
        exclude_chapter_ids: List[str] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[dict]:
        """查找语义相似的章节"""
        query_embedding = await self.generate_embedding(query_text)
        
        exclude_clause = ""
        params = {
            "novel_id": novel_id,
            "query_embedding": str(query_embedding),
            "threshold": similarity_threshold,
            "limit": limit
        }
        
        if exclude_chapter_ids:
            exclude_clause = "AND ce.chapter_id != ANY(:exclude_ids)"
            params["exclude_ids"] = exclude_chapter_ids
        
        async with get_db() as db:
            result = await db.execute(
                text(f"""
                    SELECT 
                        ce.chapter_id,
                        ce.chunk_count,
                        1 - (ce.full_content_embedding <=> :query_embedding::vector) as similarity,
                        c.title as chapter_title,
                        c.summary as chapter_summary,
                        c.content as chapter_content
                    FROM chapter_embeddings ce
                    JOIN chapters c ON c.id = ce.chapter_id
                    WHERE ce.novel_id = :novel_id
                    {exclude_clause}
                    AND 1 - (ce.full_content_embedding <=> :query_embedding::vector) >= :threshold
                    ORDER BY ce.full_content_embedding <=> :query_embedding::vector
                    LIMIT :limit
                """),
                params
            )
            return [dict(row) for row in result]
    
    async def find_similar_paragraphs(
        self,
        novel_id: str,
        query_text: str,
        exclude_chapter_ids: List[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.75
    ) -> List[dict]:
        """查找语义相似的段落（更精确）"""
        query_embedding = await self.generate_embedding(query_text)
        
        # 使用段落级别向量进行精确匹配
        # ... 实现逻辑
        pass
    
    def _split_into_chunks(self, text: str, chunk_size: int) -> List[str]:
        """将文本分割成指定大小的段落"""
        # 按句号、问号、感叹号分割，尽量保持语义完整性
        sentences = re.split(r'[。！？\n]', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence + "。"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + "。"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
```

**`backend/services/consistency_checker.py`**
```python
"""
一致性检查服务
使用向量相似度检查角色、世界观设定的一致性
"""
from typing import List, Dict
from backend.services.embedding_service import EmbeddingService

class ConsistencyChecker:
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    async def check_character_consistency(
        self,
        novel_id: str,
        chapter_content: str,
        character_id: str
    ) -> Dict:
        """检查章节内容中角色行为是否与设定一致"""
        # 1. 获取角色设定向量
        # 2. 从章节内容中提取角色相关描述
        # 3. 计算相似度
        # 4. 返回一致性评分和建议
        pass
    
    async def suggest_relevant_context(
        self,
        novel_id: str,
        current_chapter_title: str,
        current_chapter_summary: str,
        exclude_chapter_ids: List[str] = None,
        max_chapters: int = 3
    ) -> List[Dict]:
        """智能推荐最相关的上下文章节"""
        query = f"{current_chapter_title} {current_chapter_summary}"
        similar_chapters = await self.embedding_service.find_similar_chapters(
            novel_id=novel_id,
            query_text=query,
            exclude_chapter_ids=exclude_chapter_ids,
            limit=max_chapters
        )
        return similar_chapters
```

---

### 集成到现有流程

#### 1. 章节保存时自动生成向量

**修改 `backend/routers/chapters.py`**
```python
@router.post("/volumes/{volume_id}/chapters", response_model=List[ChapterResponse])
async def create_chapters(
    volume_id: str,
    chapters: List[ChapterCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ... 现有创建逻辑 ...
    
    # 新增：异步生成并存储向量
    for chapter in created_chapters:
        if chapter.content:
            asyncio.create_task(
                embedding_service.store_chapter_embedding(
                    chapter_id=chapter.id,
                    novel_id=volume.novel_id,
                    content=chapter.content
                )
            )
    
    return created_chapters
```

#### 2. 生成章节时使用智能上下文

**修改 `backend/services/gemini_service.py`**
```python
async def write_chapter_content_stream(
    novel_title: str,
    genre: str,
    synopsis: str,
    chapter_title: str,
    chapter_summary: str,
    chapter_prompt_hints: str,
    characters: list,
    world_settings: list,
    previous_chapters_context: Optional[str] = None,
    novel_id: Optional[str] = None,  # 新增：用于向量检索
    current_chapter_id: Optional[str] = None  # 新增：用于排除当前章节
):
    # 新增：使用向量检索获取智能上下文
    if novel_id:
        consistency_checker = ConsistencyChecker()
        relevant_chapters = await consistency_checker.suggest_relevant_context(
            novel_id=novel_id,
            current_chapter_title=chapter_title,
            current_chapter_summary=chapter_summary,
            exclude_chapter_ids=[current_chapter_id] if current_chapter_id else None,
            max_chapters=3
        )
        
        # 构建智能上下文（替代固定的前3章）
        if relevant_chapters:
            smart_context = "\n\n".join([
                f"第{idx+1}章《{ch['chapter_title']}》摘要：\n{ch['chapter_summary']}\n\n关键内容：\n{ch['chapter_content'][:500]}..."
                for idx, ch in enumerate(relevant_chapters)
            ])
            previous_chapters_context = smart_context
    
    # ... 原有逻辑继续 ...
```

#### 3. 生成内容前检查相似度

**新增 API 端点**
```python
@router.post("/novels/{novel_id}/chapters/check-similarity")
async def check_similarity(
    novel_id: str,
    content: str,
    current_chapter_id: Optional[str] = None,
    threshold: float = 0.8,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查生成内容与已有章节的相似度"""
    embedding_service = EmbeddingService()
    
    similar_chapters = await embedding_service.find_similar_chapters(
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
```

#### 4. 智能伏笔匹配

**新增 API 端点**
```python
@router.post("/novels/{novel_id}/foreshadowings/match-resolutions")
async def match_foreshadowing_resolutions(
    novel_id: str,
    chapter_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """自动匹配章节可能解决的伏笔"""
    # 1. 获取章节内容
    # 2. 获取所有未解决的伏笔
    # 3. 使用向量相似度匹配
    # 4. 返回匹配结果
    pass
```

---

## 📊 性能优化

### 1. 异步处理
- 向量生成和存储使用异步任务，不阻塞主要业务逻辑
- 使用 Redis 队列管理向量生成任务

### 2. 缓存策略
- 常用章节向量缓存到 Redis
- 相似度计算结果缓存（TTL: 1小时）

### 3. 批量处理
- 批量生成向量，减少 API 调用
- 批量更新相似度索引

---

## 🚀 实施步骤

### 阶段1：基础设施（1-2天）
1. ✅ 安装 pgvector 扩展
2. ✅ 创建向量存储表
3. ✅ 安装依赖包

### 阶段2：核心功能（3-5天）
4. ✅ 实现 EmbeddingService
5. ✅ 实现向量存储逻辑
6. ✅ 实现相似度检索

### 阶段3：集成应用（2-3天）
7. ✅ 集成到章节保存流程
8. ✅ 集成到内容生成流程
9. ✅ 添加相似度检查 API

### 阶段4：增强功能（3-5天）
10. ✅ 实现一致性检查
11. ✅ 实现智能上下文检索
12. ✅ 实现伏笔匹配

### 阶段5：优化测试（2-3天）
13. ✅ 性能优化
14. ✅ 添加缓存
15. ✅ 全面测试

---

## 📝 详细任务清单

详细的任务清单已在系统 TODO 中创建，包含 35 个具体任务项，涵盖：
- 数据库迁移和表结构创建
- 核心服务实现
- API 集成
- 性能优化
- 测试和文档

请查看 TODO 列表了解具体实施细节。

---

## 💰 成本估算

### API 调用成本（Gemini Embedding）
- **价格**：$0.000075 / 1000 tokens（预计）
- **单章节**：约 5000-8000 字 ≈ 1000-1500 tokens
- **成本**：约 $0.0001 / 章节
- **1000章节**：约 $0.10

### 存储成本
- **单向量**：768 维度 × 4 bytes = 3KB
- **1000章节**：约 3MB（可忽略）

---

## 🎯 预期效果

### 量化指标
- **重复内容减少**：80%+（相比固定传递前3章）
- **上下文相关性提升**：60%+（通过语义检索）
- **一致性错误减少**：70%+（通过一致性检查）
- **伏笔遗漏减少**：50%+（通过智能匹配）

### 用户体验
- ✅ AI 生成内容更连贯
- ✅ 减少重复情节
- ✅ 角色行为更一致
- ✅ 自动发现伏笔关联
- ✅ 写作质量显著提升

---

## ⚠️ 注意事项

1. **向量维度**：Gemini embedding 维度可能不同，需确认
2. **索引选择**：根据数据量选择 IVFFlat（小规模）或 HNSW（大规模）
3. **阈值调优**：相似度阈值需要根据实际效果调整
4. **并发控制**：向量生成 API 需要控制并发数
5. **错误处理**：向量生成失败不应影响主要功能

---

## 🔄 未来扩展

1. **跨小说检索**：学习其他小说的优秀写作技巧
2. **用户风格分析**：为每个用户建立风格向量
3. **智能改写建议**：基于相似内容提供改写建议
4. **情感分析**：结合情感向量优化章节节奏
5. **主题演化追踪**：追踪小说主题的变化轨迹

