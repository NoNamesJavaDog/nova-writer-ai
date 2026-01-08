"""
内容相似度检查服务
在生成章节内容前检查是否与已有内容重复
"""
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from services.embedding.embedding_service import EmbeddingService

# 配置日志
logger = logging.getLogger(__name__)


class ContentSimilarityChecker:
    """内容相似度检查器"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    def check_before_generation(
        self,
        db: Session,
        novel_id: str,
        chapter_title: str,
        chapter_summary: str,
        existing_content: Optional[str] = None,
        exclude_chapter_ids: Optional[List[str]] = None,
        similarity_threshold: float = 0.7  # 降低阈值到0.7，更早发现潜在重复
    ) -> Dict:
        """
        在生成章节内容前检查相似度
        
        Args:
            db: 数据库会话
            novel_id: 小说ID
            chapter_title: 章节标题
            chapter_summary: 章节摘要
            existing_content: 现有内容（如果更新现有章节）
            exclude_chapter_ids: 要排除的章节ID列表
            similarity_threshold: 相似度阈值
        
        Returns:
            检查结果，包含警告和建议
        """
        try:
            # 构建查询文本
            query_text = f"{chapter_title} {chapter_summary}"
            
            # 查找相似章节（降低阈值以获取更多候选，更全面检测重复风险）
            similar_chapters = self.embedding_service.find_similar_chapters(
                db=db,
                novel_id=novel_id,
                query_text=query_text,
                exclude_chapter_ids=exclude_chapter_ids,
                limit=8,  # 增加检查数量
                similarity_threshold=similarity_threshold - 0.15  # 更低的阈值以获取更多结果
            )
            
            # 分析结果（更细粒度的分类）
            high_similarity = [ch for ch in similar_chapters if ch["similarity"] >= similarity_threshold]
            medium_similarity = [
                ch for ch in similar_chapters 
                if similarity_threshold - 0.15 <= ch["similarity"] < similarity_threshold
            ]
            low_similarity = [
                ch for ch in similar_chapters
                if similarity_threshold - 0.25 <= ch["similarity"] < similarity_threshold - 0.15
            ]
            
            warnings = []
            suggestions = []
            
            if high_similarity:
                warnings.append(
                    f"⚠️ 发现 {len(high_similarity)} 个高度相似的章节（相似度 >= {similarity_threshold:.1f}）"
                )
                for ch in high_similarity[:3]:  # 列出前3个最相似的
                    warnings.append(
                        f"   - 《{ch.get('chapter_title', '未知')}》相似度: {ch['similarity']:.2f}"
                    )
                suggestions.append("🔍 强烈建议：查看上述相似章节，确保本章情节完全不同")
                suggestions.append("💡 调整建议：修改章节主题、场景设置或角色互动方式")
            
            if medium_similarity:
                warnings.append(
                    f"ℹ️ 发现 {len(medium_similarity)} 个中等相似的章节（相似度 {similarity_threshold - 0.15:.1f}-{similarity_threshold:.1f}）"
                )
                suggestions.append("💡 建议在生成时明确区分与前文的差异，采用不同叙事手法")
            
            if low_similarity:
                suggestions.append(
                    f"📊 参考信息：还有 {len(low_similarity)} 个略微相似的章节可作为背景参考"
                )
            
            return {
                "has_similar_content": len(high_similarity) > 0,
                "high_similarity_chapters": high_similarity,
                "medium_similarity_chapters": medium_similarity,
                "low_similarity_chapters": low_similarity,
                "all_similar_chapters": similar_chapters,
                "warnings": warnings,
                "suggestions": suggestions,
                "similarity_summary": {
                    "high": len(high_similarity),
                    "medium": len(medium_similarity),
                    "low": len(low_similarity)
                },
                "recommendation": "继续生成（注意差异化）" if not high_similarity else "⚠️ 建议仔细审查后生成"
            }
            
        except Exception as e:
            # 检查失败不应阻止生成
            return {
                "has_similar_content": False,
                "error": str(e),
                "recommendation": "继续生成（检查失败）"
            }
    
    def check_after_generation(
        self,
        db: Session,
        novel_id: str,
        generated_content: str,
        current_chapter_id: Optional[str] = None,
        similarity_threshold: float = 0.85
    ) -> Dict:
        """
        在生成章节内容后检查相似度（更严格）
        
        Args:
            db: 数据库会话
            novel_id: 小说ID
            generated_content: 生成的章节内容
            current_chapter_id: 当前章节ID（用于排除）
            similarity_threshold: 相似度阈值（更严格，默认0.85）
        
        Returns:
            检查结果
        """
        try:
            similar_chapters = self.embedding_service.find_similar_chapters(
                db=db,
                novel_id=novel_id,
                query_text=generated_content[:1000],  # 使用前1000字作为查询
                exclude_chapter_ids=[current_chapter_id] if current_chapter_id else None,
                limit=5,
                similarity_threshold=similarity_threshold
            )
            
            if similar_chapters:
                return {
                    "has_duplicate_content": True,
                    "similar_chapters": similar_chapters,
                    "warning": f"生成的内容与 {len(similar_chapters)} 个章节高度相似，可能存在重复",
                    "recommendation": "建议重新生成或手动修改内容"
                }
            
            return {
                "has_duplicate_content": False,
                "similar_chapters": [],
                "recommendation": "内容独特，可以使用"
            }
            
        except Exception as e:
            return {
                "has_duplicate_content": False,
                "error": str(e),
                "recommendation": "检查失败，建议人工审查"
            }

