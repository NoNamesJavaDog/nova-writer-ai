"""
一致性检查服务
使用向量相似度检查角色、世界观设定的一致性，并提供智能上下文推荐
"""
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from .embedding_service import EmbeddingService

# 配置日志
logger = logging.getLogger(__name__)


class ConsistencyChecker:
    """一致性检查器"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    def suggest_relevant_context(
        self,
        db: Session,
        novel_id: str,
        current_chapter_title: str,
        current_chapter_summary: str,
        exclude_chapter_ids: Optional[List[str]] = None,
        max_chapters: int = 3
    ) -> List[Dict]:
        """
        智能推荐最相关的上下文章节
        
        Args:
            db: 数据库会话
            novel_id: 小说ID
            current_chapter_title: 当前章节标题
            current_chapter_summary: 当前章节摘要
            exclude_chapter_ids: 要排除的章节ID列表
            max_chapters: 最大返回章节数
        
        Returns:
            相似章节列表，包含章节信息
        """
        try:
            # 构建查询文本（使用标题和摘要）
            query_text = f"{current_chapter_title} {current_chapter_summary}"
            
            # 使用 embedding service 查找相似章节
            similar_chapters = self.embedding_service.find_similar_chapters(
                db=db,
                novel_id=novel_id,
                query_text=query_text,
                exclude_chapter_ids=exclude_chapter_ids,
                limit=max_chapters,
                similarity_threshold=0.6  # 较低阈值，以获取更多相关章节
            )
            
            return similar_chapters
            
        except Exception as e:
            # 如果向量检索失败，返回空列表（不影响主流程）
            logger.error(f"⚠️  智能上下文推荐失败: {str(e)}")
            return []
    
    def get_relevant_context_text(
        self,
        db: Session,
        novel_id: str,
        current_chapter_title: str,
        current_chapter_summary: str,
        exclude_chapter_ids: Optional[List[str]] = None,
        max_chapters: int = 3
    ) -> str:
        """
        获取相关上下文的文本格式（用于AI提示）
        
        Returns:
            格式化的上下文文本
        """
        similar_chapters = self.suggest_relevant_context(
            db=db,
            novel_id=novel_id,
            current_chapter_title=current_chapter_title,
            current_chapter_summary=current_chapter_summary,
            exclude_chapter_ids=exclude_chapter_ids,
            max_chapters=max_chapters
        )
        
        if not similar_chapters:
            return ""
        
        # 格式化上下文文本
        context_parts = []
        for idx, ch in enumerate(similar_chapters, 1):
            context_part = f"第{idx}章《{ch['chapter_title']}》"
            if ch.get('chapter_summary'):
                context_part += f"\n摘要：{ch['chapter_summary']}"
            if ch.get('chapter_content_preview'):
                context_part += f"\n关键内容：{ch['chapter_content_preview']}"
            context_parts.append(context_part)
        
        return "\n\n---\n\n".join(context_parts)
    
    def check_character_consistency(
        self,
        db: Session,
        novel_id: str,
        chapter_content: str,
        character_id: str
    ) -> Dict:
        """
        检查章节内容中角色行为是否与设定一致
        
        Args:
            db: 数据库会话
            novel_id: 小说ID
            chapter_content: 章节内容
            character_id: 角色ID
        
        Returns:
            一致性检查结果，包含相似度分数和建议
        """
        try:
            # 1. 获取角色设定向量
            result = db.execute(
                text("""
                    SELECT ce.full_description_embedding, c.name, c.personality, c.background
                    FROM character_embeddings ce
                    JOIN characters c ON c.id = ce.character_id
                    WHERE ce.character_id = :character_id AND ce.novel_id = :novel_id
                """),
                {"character_id": character_id, "novel_id": novel_id}
            ).fetchone()
            
            if not result:
                return {
                    "consistent": True,  # 如果没有向量，默认一致
                    "score": 1.0,
                    "message": "角色向量未找到，跳过一致性检查"
                }
            
            character_embedding_str = result[0]
            character_name = result[1]
            
            # 2. 从章节内容中提取角色相关描述（简化：使用整个内容）
            # 注意：实际应用中可以提取更精确的角色相关段落
            chapter_embedding = self.embedding_service.generate_embedding(
                chapter_content,
                task_type="RETRIEVAL_DOCUMENT"
            )
            chapter_embedding_str = "[" + ",".join(map(str, chapter_embedding)) + "]"
            
            # 3. 计算相似度
            similarity_result = db.execute(
                text("""
                    SELECT 1 - (CAST(:chapter_embedding AS vector) <=> CAST(:character_embedding AS vector)) as similarity
                """),
                {
                    "chapter_embedding": chapter_embedding_str,
                    "character_embedding": character_embedding_str
                }
            ).fetchone()
            
            similarity = float(similarity_result[0]) if similarity_result else 0.5
            
            # 4. 判断一致性（相似度阈值可调整）
            threshold = 0.7
            is_consistent = similarity >= threshold
            
            return {
                "consistent": is_consistent,
                "score": similarity,
                "threshold": threshold,
                "character_name": character_name,
                "message": f"角色 {character_name} 的一致性评分: {similarity:.2f} ({'一致' if is_consistent else '可能存在不一致'})"
            }
            
        except Exception as e:
            # 出错时返回默认值，不影响主流程
            logger.error(f"⚠️  角色一致性检查失败: {str(e)}")
            return {
                "consistent": True,
                "score": 1.0,
                "message": f"一致性检查失败: {str(e)}"
            }
