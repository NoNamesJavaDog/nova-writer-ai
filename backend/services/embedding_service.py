"""
向量嵌入服务
负责生成文本向量、存储、检索
"""
import uuid
import time
import re
import logging
from typing import List, Optional, Dict
from sqlalchemy import text
from sqlalchemy.orm import Session
from google import genai
from config import GEMINI_API_KEY

# 配置日志
logger = logging.getLogger(__name__)

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 1  # 秒

# 初始化 Gemini 客户端
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY 未配置，请在 .env 文件中设置")

client = genai.Client(api_key=GEMINI_API_KEY)

class EmbeddingService:
    """向量嵌入服务类"""
    
    def __init__(self):
        # 注意：根据实际情况，gemini-embedding-001 可能需要调整
        # 如果该模型不存在，可以尝试使用 text-embedding-004 或其他可用模型
        self.model = "models/text-embedding-004"  # 使用 text-embedding-004（Gemini Embedding 模型）
        self.dimension = 768  # text-embedding-004 的维度是 768
    
    def generate_embedding(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """
        生成文本向量（带重试机制）
        
        Args:
            text: 要生成向量的文本
            task_type: 任务类型，可选值：
                - "RETRIEVAL_DOCUMENT": 用于文档嵌入（存储）
                - "RETRIEVAL_QUERY": 用于查询嵌入（检索）
        
        Returns:
            向量数组（List[float]）
        """
        if not text or not text.strip():
            raise ValueError("文本不能为空")
        
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                logger.debug(f"生成向量（尝试 {attempt + 1}/{MAX_RETRIES}）: {text[:50]}...")
                
                # 使用 Google Gemini Embedding API
                # 注意：API 使用 contents 参数（复数），接受列表
                from google.genai import types
                result = client.models.embed_content(
                    model=self.model,
                    contents=[text],
                    config=types.EmbedContentConfig(task_type=task_type)
                )
                
                # 提取向量
                # EmbedContentResponse 包含 embeddings 属性（列表）
                # 每个元素是 ContentEmbedding 对象，有 values 属性（向量列表）
                embedding = None
                if hasattr(result, 'embeddings') and isinstance(result.embeddings, list) and len(result.embeddings) > 0:
                    # 获取第一个 ContentEmbedding 对象的 values 属性
                    content_embedding = result.embeddings[0]
                    if hasattr(content_embedding, 'values'):
                        embedding = content_embedding.values
                    elif hasattr(content_embedding, 'embedding'):
                        embedding = content_embedding.embedding
                elif hasattr(result, 'embedding'):
                    embedding = result.embedding
                elif isinstance(result, dict) and 'embeddings' in result:
                    embeddings_list = result['embeddings']
                    if isinstance(embeddings_list, list) and len(embeddings_list) > 0:
                        emb_obj = embeddings_list[0]
                        if isinstance(emb_obj, dict) and 'values' in emb_obj:
                            embedding = emb_obj['values']
                        elif isinstance(emb_obj, dict) and 'embedding' in emb_obj:
                            embedding = emb_obj['embedding']
                        else:
                            embedding = emb_obj
                elif isinstance(result, dict) and 'embedding' in result:
                    embedding = result['embedding']
                elif isinstance(result, list):
                    embedding = result[0] if len(result) > 0 else None
                
                if embedding:
                    # 确保是列表格式
                    if not isinstance(embedding, list):
                        embedding = list(embedding) if hasattr(embedding, '__iter__') else [embedding]
                    logger.debug(f"✅ 向量生成成功，维度: {len(embedding)}")
                    return embedding
                else:
                    raise ValueError(f"无法从API响应中提取向量: {result}")
                    
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️  向量生成失败（尝试 {attempt + 1}/{MAX_RETRIES}）: {str(e)}")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))  # 指数退避
                else:
                    logger.error(f"❌ 向量生成失败，已重试 {MAX_RETRIES} 次: {str(e)}")
                    raise Exception(f"生成向量失败（已重试 {MAX_RETRIES} 次）: {str(e)}")
        
        # 不应该到达这里，但为了类型检查
        raise Exception(f"生成向量失败: {str(last_error) if last_error else '未知错误'}")
    
    def _split_into_chunks(self, text: str, chunk_size: int = 500) -> List[str]:
        """
        将文本分割成指定大小的段落
        
        Args:
            text: 要分割的文本
            chunk_size: 每个段落的目标大小（字符数）
        
        Returns:
            段落列表
        """
        if not text:
            return []
        
        # 按句号、问号、感叹号分割
        sentences = re.split(r'[。！？.!?]\s*', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 如果当前段落加上新句子不超过限制，就添加
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence + "。"
            else:
                # 保存当前段落，开始新段落
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + "。"
        
        # 添加最后一个段落
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def store_chapter_embedding(
        self,
        db: Session,
        chapter_id: str,
        novel_id: str,
        content: str,
        chunk_size: int = 500
    ) -> None:
        """
        存储章节向量（段落级别）
        
        Args:
            db: 数据库会话
            chapter_id: 章节ID
            novel_id: 小说ID
            content: 章节内容
            chunk_size: 段落大小（默认500字）
        """
        start_time = time.time()
        try:
            if not content or not content.strip():
                logger.debug(f"章节 {chapter_id} 内容为空，跳过向量存储")
                return  # 如果内容为空，不存储向量
            
            logger.info(f"开始存储章节向量: chapter_id={chapter_id}, content_length={len(content)}")
            
            # 1. 生成完整内容向量
            logger.debug(f"生成完整内容向量...")
            full_embedding = self.generate_embedding(content, task_type="RETRIEVAL_DOCUMENT")
            
            # 2. 分段落生成向量
            chunks = self._split_into_chunks(content, chunk_size)
            logger.debug(f"文本分割为 {len(chunks)} 个段落")
            paragraph_embeddings = []
            
            for idx, chunk in enumerate(chunks):
                if chunk.strip():
                    logger.debug(f"生成段落 {idx + 1}/{len(chunks)} 向量...")
                    embedding = self.generate_embedding(chunk.strip(), task_type="RETRIEVAL_DOCUMENT")
                    paragraph_embeddings.append(embedding)
            
            # 3. 准备向量数据（转换为字符串格式）
            def _vector_literal(vec: List[float]) -> str:
                return "[" + ",".join(map(str, vec)) + "]"

            full_embedding_str = _vector_literal(full_embedding)

            # pgvector 的 vector[] 需要使用 PostgreSQL 数组字面量格式；元素内含逗号必须加引号
            # 例：{"[1,2,3]","[4,5,6]"}::vector[]
            if paragraph_embeddings:
                paragraph_embeddings_str = "{" + ",".join([f"\"{_vector_literal(emb)}\"" for emb in paragraph_embeddings]) + "}"
            else:
                paragraph_embeddings_str = "{}"
            
            # 4. 存储到数据库（使用 ON CONFLICT 处理更新）
            import time as time_module
            embedding_id = str(uuid.uuid4())
            current_time = int(time_module.time() * 1000)
            
            # 检查是否已存在（有些环境的 chapter_embeddings.chapter_id 没有唯一约束，不能用 ON CONFLICT）
            existing = db.execute(
                text("SELECT id FROM chapter_embeddings WHERE chapter_id = :chapter_id"),
                {"chapter_id": chapter_id},
            ).fetchone()

            params = {
                "id": embedding_id,
                "chapter_id": chapter_id,
                "novel_id": novel_id,
                "full_embedding": full_embedding_str,
                "paragraph_embeddings": paragraph_embeddings_str,
                "chunk_count": len(paragraph_embeddings),
                "model": self.model,
                "created_at": current_time,
                "updated_at": current_time,
            }

            if existing:
                embedding_id = existing[0]
                params["id"] = embedding_id
                db.execute(
                    text("""
                        UPDATE chapter_embeddings SET
                            novel_id = :novel_id,
                            full_content_embedding = CAST(:full_embedding AS vector),
                            paragraph_embeddings = CAST(:paragraph_embeddings AS vector[]),
                            chunk_count = :chunk_count,
                            embedding_model = :model,
                            updated_at = :updated_at
                        WHERE id = :id
                    """),
                    params,
                )
            else:
                db.execute(
                    text("""
                        INSERT INTO chapter_embeddings
                        (id, chapter_id, novel_id, full_content_embedding, paragraph_embeddings, chunk_count, embedding_model, created_at, updated_at)
                        VALUES (:id, :chapter_id, :novel_id, CAST(:full_embedding AS vector), CAST(:paragraph_embeddings AS vector[]), :chunk_count, :model, :created_at, :updated_at)
                    """),
                    params,
                )
            db.commit()
            
            elapsed_time = time.time() - start_time
            logger.info(f"✅ 章节向量存储成功: chapter_id={chapter_id}, chunks={len(paragraph_embeddings)}, time={elapsed_time:.2f}s")
            
        except Exception as e:
            db.rollback()
            elapsed_time = time.time() - start_time
            logger.error(f"❌ 存储章节向量失败: chapter_id={chapter_id}, error={str(e)}, time={elapsed_time:.2f}s")
            raise Exception(f"存储章节向量失败: {str(e)}")
    
    def find_similar_chapters(
        self,
        db: Session,
        novel_id: str,
        query_text: str,
        exclude_chapter_ids: Optional[List[str]] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """
        查找语义相似的章节
        
        Args:
            db: 数据库会话
            novel_id: 小说ID
            query_text: 查询文本
            exclude_chapter_ids: 要排除的章节ID列表
            limit: 返回结果数量
            similarity_threshold: 相似度阈值（0-1之间）
        
        Returns:
            相似章节列表，每个元素包含：chapter_id, similarity, chapter_title, chapter_summary, chapter_content
        """
        try:
            # 生成查询向量
            query_embedding = self.generate_embedding(query_text, task_type="RETRIEVAL_QUERY")
            query_embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # 构建SQL查询
            exclude_clause = ""
            params = {
                "novel_id": novel_id,
                "query_embedding": query_embedding_str,
                "threshold": similarity_threshold,
                "limit": limit
            }
            
            if exclude_chapter_ids:
                exclude_clause = "AND ce.chapter_id != ALL(:exclude_ids)"
                params["exclude_ids"] = exclude_chapter_ids
            
            # 使用 cosine 相似度（<=> 操作符返回距离，1 - 距离 = 相似度）
            sql = f"""
                SELECT 
                    ce.chapter_id,
                    ce.chunk_count,
                    1 - (ce.full_content_embedding <=> CAST(:query_embedding AS vector)) as similarity,
                    c.title as chapter_title,
                    c.summary as chapter_summary,
                    LEFT(c.content, 500) as chapter_content_preview
                FROM chapter_embeddings ce
                JOIN chapters c ON c.id = ce.chapter_id
                JOIN volumes v ON v.id = c.volume_id
                WHERE v.novel_id = :novel_id
                AND ce.full_content_embedding IS NOT NULL
                AND 1 - (ce.full_content_embedding <=> CAST(:query_embedding AS vector)) >= :threshold
                {exclude_clause}
                ORDER BY ce.full_content_embedding <=> CAST(:query_embedding AS vector)
                LIMIT :limit
            """
            
            result = db.execute(text(sql), params)
            rows = result.fetchall()
            
            return [
                {
                    "chapter_id": row[0],
                    "chunk_count": row[1],
                    "similarity": float(row[2]),
                    "chapter_title": row[3],
                    "chapter_summary": row[4],
                    "chapter_content_preview": row[5]
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"查找相似章节失败: {str(e)}")
            return []
    
    def find_similar_paragraphs(
        self,
        db: Session,
        novel_id: str,
        query_text: str,
        exclude_chapter_ids: Optional[List[str]] = None,
        limit: int = 10,
        similarity_threshold: float = 0.75
    ) -> List[Dict]:
        """
        查找语义相似的段落（段落级别精确匹配）
        
        Args:
            db: 数据库会话
            novel_id: 小说ID
            query_text: 查询文本
            exclude_chapter_ids: 要排除的章节ID列表
            limit: 返回结果数量
            similarity_threshold: 相似度阈值（0-1之间，默认0.75，比章节级更严格）
        
        Returns:
            相似段落列表，每个元素包含：chapter_id, paragraph_index, similarity, paragraph_text, chapter_title
        """
        try:
            logger.debug(f"查找相似段落: novel_id={novel_id}, query_text={query_text[:50]}...")
            
            # 生成查询向量
            query_embedding = self.generate_embedding(query_text, task_type="RETRIEVAL_QUERY")
            query_embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # 构建SQL查询
            exclude_clause = ""
            params = {
                "novel_id": novel_id,
                "query_embedding": query_embedding_str,
                "threshold": similarity_threshold,
                "limit": limit
            }
            
            if exclude_chapter_ids:
                exclude_clause = "AND ce.chapter_id != ALL(:exclude_ids)"
                params["exclude_ids"] = exclude_chapter_ids
            
            # 使用 unnest 展开段落向量数组，然后计算相似度
            # 注意：PostgreSQL 的数组索引从1开始
            sql = f"""
                SELECT 
                    ce.chapter_id,
                    c.title as chapter_title,
                    (paragraph_idx - 1) as paragraph_index,
                    paragraph_emb,
                    1 - (paragraph_emb <=> CAST(:query_embedding AS vector)) as similarity
                FROM chapter_embeddings ce
                JOIN chapters c ON c.id = ce.chapter_id
                JOIN volumes v ON v.id = c.volume_id
                CROSS JOIN LATERAL unnest(ce.paragraph_embeddings) WITH ORDINALITY AS t(paragraph_emb, paragraph_idx)
                WHERE v.novel_id = :novel_id
                AND ce.paragraph_embeddings IS NOT NULL
                AND array_length(ce.paragraph_embeddings, 1) > 0
                AND 1 - (paragraph_emb <=> CAST(:query_embedding AS vector)) >= :threshold
                {exclude_clause}
                ORDER BY paragraph_emb <=> CAST(:query_embedding AS vector)
                LIMIT :limit
            """
            
            result = db.execute(text(sql), params)
            rows = result.fetchall()
            
            # 获取段落文本（需要从章节内容中提取）
            results = []
            for row in rows:
                chapter_id = row[0]
                chapter_title = row[1]
                paragraph_index = row[2]
                similarity = float(row[4])
                
                # 获取章节内容并提取对应段落
                chapter_result = db.execute(
                    text("SELECT content FROM chapters WHERE id = :chapter_id"),
                    {"chapter_id": chapter_id}
                ).fetchone()
                
                paragraph_text = ""
                if chapter_result and chapter_result[0]:
                    chunks = self._split_into_chunks(chapter_result[0], chunk_size=500)
                    if paragraph_index < len(chunks):
                        paragraph_text = chunks[paragraph_index]
                
                results.append({
                    "chapter_id": chapter_id,
                    "chapter_title": chapter_title,
                    "paragraph_index": paragraph_index,
                    "similarity": similarity,
                    "paragraph_text": paragraph_text
                })
            
            logger.debug(f"找到 {len(results)} 个相似段落")
            return results
            
        except Exception as e:
            logger.error(f"查找相似段落失败: {str(e)}")
            return []
