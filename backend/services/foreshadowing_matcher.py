"""
伏笔匹配服务
使用向量相似度自动匹配章节内容与伏笔，识别哪些章节可能解决了伏笔
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from .embedding_service import EmbeddingService


class ForeshadowingMatcher:
    """伏笔匹配器"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    def match_foreshadowing_resolutions(
        self,
        db: Session,
        novel_id: str,
        chapter_id: str,
        chapter_content: str,
        similarity_threshold: float = 0.75
    ) -> List[Dict]:
        """
        匹配章节内容可能解决的伏笔
        
        Args:
            db: 数据库会话
            novel_id: 小说ID
            chapter_id: 章节ID
            chapter_content: 章节内容
            similarity_threshold: 相似度阈值（0-1之间）
        
        Returns:
            匹配的伏笔列表，每个元素包含：foreshadowing_id, similarity, content, is_resolved
        """
        try:
            # 1. 获取所有未解决的伏笔
            unresolved_foreshadowings = db.execute(
                text("""
                    SELECT f.id, f.content, f.is_resolved, fe.content_embedding
                    FROM foreshadowings f
                    LEFT JOIN foreshadowing_embeddings fe ON fe.foreshadowing_id = f.id
                    WHERE f.novel_id = :novel_id
                    AND (f.is_resolved IS NULL OR f.is_resolved = 'false')
                    AND fe.content_embedding IS NOT NULL
                """),
                {"novel_id": novel_id}
            ).fetchall()
            
            if not unresolved_foreshadowings:
                return []
            
            # 2. 生成章节内容的向量
            chapter_embedding = self.embedding_service.generate_embedding(
                chapter_content,
                task_type="RETRIEVAL_DOCUMENT"
            )
            chapter_embedding_str = "[" + ",".join(map(str, chapter_embedding)) + "]"
            
            # 3. 计算每个伏笔与章节内容的相似度
            matches = []
            for foreshadowing in unresolved_foreshadowings:
                foreshadowing_id = foreshadowing[0]
                foreshadowing_content = foreshadowing[1]
                foreshadowing_embedding_str = str(foreshadowing[3]) if foreshadowing[3] else None
                
                if not foreshadowing_embedding_str:
                    continue
                
                # 计算相似度
                similarity_result = db.execute(
                    text("""
                        SELECT 1 - (CAST(:chapter_embedding AS vector) <=> CAST(:foreshadowing_embedding AS vector)) as similarity
                    """),
                    {
                        "chapter_embedding": chapter_embedding_str,
                        "foreshadowing_embedding": foreshadowing_embedding_str
                    }
                ).fetchone()
                
                similarity = float(similarity_result[0]) if similarity_result else 0.0
                
                # 如果相似度超过阈值，认为是匹配的
                if similarity >= similarity_threshold:
                    matches.append({
                        "foreshadowing_id": foreshadowing_id,
                        "foreshadowing_content": foreshadowing_content,
                        "similarity": similarity,
                        "chapter_id": chapter_id,
                        "is_match": True
                    })
            
            # 按相似度排序
            matches.sort(key=lambda x: x["similarity"], reverse=True)
            
            return matches
            
        except Exception as e:
            logger.error(f"⚠️  伏笔匹配失败: {str(e)}")
            return []
    
    def auto_update_foreshadowing_resolution(
        self,
        db: Session,
        novel_id: str,
        chapter_id: str,
        chapter_content: str,
        similarity_threshold: float = 0.8,
        auto_update: bool = False
    ) -> Dict:
        """
        自动匹配并可选地更新伏笔的解决状态
        
        Args:
            db: 数据库会话
            novel_id: 小说ID
            chapter_id: 章节ID
            chapter_content: 章节内容
            similarity_threshold: 相似度阈值（更高的阈值，默认0.8）
            auto_update: 是否自动更新伏笔状态
        
        Returns:
            匹配结果和更新状态
        """
        try:
            matches = self.match_foreshadowing_resolutions(
                db=db,
                novel_id=novel_id,
                chapter_id=chapter_id,
                chapter_content=chapter_content,
                similarity_threshold=similarity_threshold
            )
            
            updated_count = 0
            if auto_update and matches:
                # 只更新相似度最高的伏笔（避免误匹配）
                best_match = matches[0]
                if best_match["similarity"] >= similarity_threshold:
                    db.execute(
                        text("""
                            UPDATE foreshadowings
                            SET is_resolved = 'true',
                                resolved_chapter_id = :chapter_id,
                                updated_at = :updated_at
                            WHERE id = :foreshadowing_id
                        """),
                        {
                            "foreshadowing_id": best_match["foreshadowing_id"],
                            "chapter_id": chapter_id,
                            "updated_at": int(time_module.time() * 1000)
                        }
                    )
                    db.commit()
                    updated_count = 1
            
            return {
                "matches_found": len(matches),
                "matches": matches,
                "updated_count": updated_count,
                "auto_update_enabled": auto_update
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"⚠️  自动更新伏笔解决状态失败: {str(e)}")
            return {
                "matches_found": 0,
                "matches": [],
                "updated_count": 0,
                "error": str(e)
            }
    
    def find_related_foreshadowings(
        self,
        db: Session,
        novel_id: str,
        query_text: str,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """
        查找与查询文本相关的伏笔（用于章节生成前的提示）
        
        Args:
            db: 数据库会话
            novel_id: 小说ID
            query_text: 查询文本（如章节标题和摘要）
            limit: 返回结果数量
            similarity_threshold: 相似度阈值
        
        Returns:
            相关伏笔列表
        """
        try:
            # 生成查询向量
            query_embedding = self.embedding_service.generate_embedding(
                query_text,
                task_type="RETRIEVAL_QUERY"
            )
            query_embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # 查找相关伏笔
            result = db.execute(
                text("""
                    SELECT 
                        f.id,
                        f.content,
                        f.is_resolved,
                        f.chapter_id,
                        f.resolved_chapter_id,
                        1 - (fe.content_embedding <=> CAST(:query_embedding AS vector)) as similarity
                    FROM foreshadowings f
                    JOIN foreshadowing_embeddings fe ON fe.foreshadowing_id = f.id
                    WHERE f.novel_id = :novel_id
                    AND fe.content_embedding IS NOT NULL
                    AND 1 - (fe.content_embedding <=> CAST(:query_embedding AS vector)) >= :threshold
                    ORDER BY fe.content_embedding <=> CAST(:query_embedding AS vector)
                    LIMIT :limit
                """),
                {
                    "novel_id": novel_id,
                    "query_embedding": query_embedding_str,
                    "threshold": similarity_threshold,
                    "limit": limit
                }
            )
            rows = result.fetchall()
            
            return [
                {
                    "foreshadowing_id": row[0],
                    "content": row[1],
                    "is_resolved": row[2],
                    "chapter_id": row[3],
                    "resolved_chapter_id": row[4],
                    "similarity": float(row[5])
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"⚠️  查找相关伏笔失败: {str(e)}")
            return []
