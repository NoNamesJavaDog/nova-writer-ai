"""
向量存储辅助函数
用于在章节、角色、世界观等创建/更新时自动存储向量
"""
import asyncio
import logging
import time
from typing import Optional
from sqlalchemy.orm import Session
from .embedding_service import EmbeddingService

# 配置日志
logger = logging.getLogger(__name__)


# 全局 embedding service 实例
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """获取 embedding service 实例（单例模式）"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def store_chapter_embedding_async(
    db: Session,
    chapter_id: str,
    novel_id: str,
    content: str
) -> None:
    """
    异步存储章节向量（在后台任务中执行）
    
    注意：这是同步函数，但向量生成和存储可能较慢，建议在后台任务中调用
    """
    start_time = time.time()
    try:
        logger.info(f"开始异步存储章节向量: chapter_id={chapter_id}")
        service = get_embedding_service()
        service.store_chapter_embedding(
            db=db,
            chapter_id=chapter_id,
            novel_id=novel_id,
            content=content
        )
        elapsed_time = time.time() - start_time
        logger.info(f"✅ 异步存储章节向量成功: chapter_id={chapter_id}, time={elapsed_time:.2f}s")
    except Exception as e:
        elapsed_time = time.time() - start_time
        # 向量存储失败不应影响主流程
        logger.error(f"⚠️  存储章节向量失败（章节ID: {chapter_id}）: {str(e)}, time={elapsed_time:.2f}s")
        # 不抛出异常，让主流程继续


def store_character_embedding(
    db: Session,
    character_id: str,
    novel_id: str,
    name: str,
    personality: str = "",
    background: str = "",
    goals: str = ""
) -> None:
    """
    存储角色向量
    
    Args:
        db: 数据库会话
        character_id: 角色ID
        novel_id: 小说ID
        name: 角色姓名
        personality: 性格特征
        background: 背景故事
        goals: 目标和动机
    """
    try:
        # 组合角色描述
        character_description = f"姓名：{name}"
        if personality:
            character_description += f"\n性格：{personality}"
        if background:
            character_description += f"\n背景：{background}"
        if goals:
            character_description += f"\n目标：{goals}"
        
        service = get_embedding_service()
        embedding = service.generate_embedding(character_description, task_type="RETRIEVAL_DOCUMENT")
        
        # 存储到数据库
        import uuid
        import time as time_module
        from sqlalchemy import text
        
        embedding_id = str(uuid.uuid4())
        current_time = int(time_module.time() * 1000)
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        
        # 检查是否已存在
        existing = db.execute(
            text("SELECT id FROM character_embeddings WHERE character_id = :character_id"),
            {"character_id": character_id}
        ).fetchone()
        
        if existing:
            embedding_id = existing[0]
        
        db.execute(
            text("""
                INSERT INTO character_embeddings 
                (id, character_id, novel_id, full_description_embedding, embedding_model, created_at, updated_at)
                VALUES (:id, :character_id, :novel_id, :embedding::vector, :model, :created_at, :updated_at)
                ON CONFLICT (character_id) DO UPDATE SET
                    full_description_embedding = EXCLUDED.full_description_embedding,
                    updated_at = EXCLUDED.updated_at,
                    embedding_model = EXCLUDED.embedding_model
            """),
            {
                "id": embedding_id,
                "character_id": character_id,
                "novel_id": novel_id,
                "embedding": embedding_str,
                "model": service.model,
                "created_at": current_time,
                "updated_at": current_time
            }
        )
        db.commit()
        
    except Exception as e:
        db.rollback()
        logger.error(f"⚠️  存储角色向量失败（角色ID: {character_id}）: {str(e)}")


def store_world_setting_embedding(
    db: Session,
    world_setting_id: str,
    novel_id: str,
    title: str,
    description: str
) -> None:
    """
    存储世界观设定向量
    """
    try:
        # 组合世界观描述
        world_description = f"{title}\n{description}"
        
        service = get_embedding_service()
        embedding = service.generate_embedding(world_description, task_type="RETRIEVAL_DOCUMENT")
        
        import uuid
        import time as time_module
        from sqlalchemy import text
        
        embedding_id = str(uuid.uuid4())
        current_time = int(time_module.time() * 1000)
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        
        existing = db.execute(
            text("SELECT id FROM world_setting_embeddings WHERE world_setting_id = :world_setting_id"),
            {"world_setting_id": world_setting_id}
        ).fetchone()
        
        if existing:
            embedding_id = existing[0]
        
        db.execute(
            text("""
                INSERT INTO world_setting_embeddings 
                (id, world_setting_id, novel_id, full_description_embedding, embedding_model, created_at, updated_at)
                VALUES (:id, :world_setting_id, :novel_id, :embedding::vector, :model, :created_at, :updated_at)
                ON CONFLICT (world_setting_id) DO UPDATE SET
                    full_description_embedding = EXCLUDED.full_description_embedding,
                    updated_at = EXCLUDED.updated_at,
                    embedding_model = EXCLUDED.embedding_model
            """),
            {
                "id": embedding_id,
                "world_setting_id": world_setting_id,
                "novel_id": novel_id,
                "embedding": embedding_str,
                "model": service.model,
                "created_at": current_time,
                "updated_at": current_time
            }
        )
        db.commit()
        
    except Exception as e:
        db.rollback()
        logger.error(f"⚠️  存储世界观向量失败（设定ID: {world_setting_id}）: {str(e)}")


def store_foreshadowing_embedding(
    db: Session,
    foreshadowing_id: str,
    novel_id: str,
    content: str
) -> None:
    """
    存储伏笔向量
    """
    try:
        service = get_embedding_service()
        embedding = service.generate_embedding(content, task_type="RETRIEVAL_DOCUMENT")
        
        import uuid
        import time as time_module
        from sqlalchemy import text
        
        embedding_id = str(uuid.uuid4())
        current_time = int(time_module.time() * 1000)
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        
        existing = db.execute(
            text("SELECT id FROM foreshadowing_embeddings WHERE foreshadowing_id = :foreshadowing_id"),
            {"foreshadowing_id": foreshadowing_id}
        ).fetchone()
        
        if existing:
            embedding_id = existing[0]
        
        db.execute(
            text("""
                INSERT INTO foreshadowing_embeddings 
                (id, foreshadowing_id, novel_id, content_embedding, embedding_model, created_at, updated_at)
                VALUES (:id, :foreshadowing_id, :novel_id, :embedding::vector, :model, :created_at, :updated_at)
                ON CONFLICT (foreshadowing_id) DO UPDATE SET
                    content_embedding = EXCLUDED.content_embedding,
                    updated_at = EXCLUDED.updated_at,
                    embedding_model = EXCLUDED.embedding_model
            """),
            {
                "id": embedding_id,
                "foreshadowing_id": foreshadowing_id,
                "novel_id": novel_id,
                "embedding": embedding_str,
                "model": service.model,
                "created_at": current_time,
                "updated_at": current_time
            }
        )
        db.commit()
        
    except Exception as e:
        db.rollback()
        logger.error(f"⚠️  存储伏笔向量失败（伏笔ID: {foreshadowing_id}）: {str(e)}")

