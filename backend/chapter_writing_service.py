"""
章节写作服务 - 抽象和复用章节生成、保存、向量存储、伏笔提取等逻辑
"""
import time
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from models import Novel, Volume, Chapter, Character, WorldSetting, Foreshadowing
from gemini_service import (
    write_chapter_content as write_chapter_content_impl,
    extract_foreshadowings_from_chapter,
    extract_next_chapter_hook
)
from services.embedding_service import EmbeddingService
from auth import generate_uuid

logger = logging.getLogger(__name__)


class ChapterWritingContext:
    """章节写作上下文，包含所有必要的数据"""
    def __init__(
        self,
        task_db: Session,
        novel: Novel,
        volume: Volume,
        chapter: Chapter,
        characters: List[Character],
        world_settings: List[WorldSetting],
        previous_chapter_hook: str = "",
        forced_previous_chapter_context: str = ""
    ):
        self.task_db = task_db
        self.novel = novel
        self.volume = volume
        self.chapter = chapter
        self.characters = characters
        self.world_settings = world_settings
        self.previous_chapter_hook = previous_chapter_hook
        self.forced_previous_chapter_context = forced_previous_chapter_context


def write_and_save_chapter(
    context: ChapterWritingContext,
    progress_callback: Optional[callable] = None,
    next_chapter: Optional[Chapter] = None
) -> Dict[str, Any]:
    """
    通用的章节生成、保存、向量存储、伏笔提取函数
    
    Args:
        context: 章节写作上下文
        progress_callback: 进度回调函数，接受 (progress: int, message: str)
        next_chapter: 下一章节对象（用于提取钩子）
    
    Returns:
        {
            "success": bool,
            "content": str,
            "foreshadowings": List[str],
            "next_chapter_hook": str,
            "error": str (如果失败)
        }
    """
    result = {
        "success": False,
        "content": "",
        "foreshadowings": [],
        "next_chapter_hook": "",
        "error": None
    }
    
    try:
        # 1. 准备章节提示词（包含上一章的钩子）
        current_prompt_hints = context.chapter.ai_prompt_hints or ""
        if context.previous_chapter_hook:
            if "【上一章钩子】" not in current_prompt_hints:
                if current_prompt_hints:
                    current_prompt_hints = f"【上一章钩子】{context.previous_chapter_hook}\n\n{current_prompt_hints}".strip()
                else:
                    current_prompt_hints = f"【上一章钩子】{context.previous_chapter_hook}"
        
        if progress_callback:
            progress_callback(10, f"正在生成章节：{context.chapter.title}")
        
        # 2. 生成章节内容
        content = write_chapter_content_impl(
            novel_title=context.novel.title,
            genre=context.novel.genre,
            synopsis=context.novel.synopsis or "",
            chapter_title=context.chapter.title,
            chapter_summary=context.chapter.summary or "",
            chapter_prompt_hints=current_prompt_hints,
            characters=[{"name": c.name, "personality": c.personality} for c in context.characters],
            world_settings=[{"title": w.title, "description": w.description} for w in context.world_settings],
            previous_chapters_context=None,  # 使用向量数据库智能检索
            novel_id=context.novel.id,
            current_chapter_id=context.chapter.id,
            db_session=context.task_db,
            forced_previous_chapter_context=context.forced_previous_chapter_context
        )
        
        # 3. 保存内容到数据库
        context.chapter.content = content
        context.chapter.updated_at = int(time.time() * 1000)
        context.task_db.commit()
        
        if progress_callback:
            progress_callback(50, "章节内容生成完成，正在存储向量...")
        
        # 4. 存储向量
        embedding_service = EmbeddingService()
        try:
            embedding_service.store_chapter_embedding(
                db=context.task_db,
                chapter_id=context.chapter.id,
                novel_id=context.novel.id,
                content=content
            )
            logger.info(f"✅ 章节 {context.chapter.title} 向量存储成功")
        except Exception as e:
            logger.warning(f"⚠️ 章节向量存储失败（继续）: {str(e)}")
        
        # 短暂延迟，确保向量索引建立完成
        time.sleep(0.5)
        
        if progress_callback:
            progress_callback(70, "正在提取伏笔和钩子...")
        
        # 5. 提取并保存伏笔
        extracted_foreshadowings = []
        try:
            existing_foreshadowings = context.task_db.query(Foreshadowing).filter(
                Foreshadowing.novel_id == context.novel.id
            ).all()
            existing_foreshadowings_list = [{"content": f.content} for f in existing_foreshadowings]
            
            foreshadowings_data = extract_foreshadowings_from_chapter(
                title=context.novel.title,
                genre=context.novel.genre,
                chapter_title=context.chapter.title,
                chapter_content=content,
                existing_foreshadowings=existing_foreshadowings_list
            )
            
            if foreshadowings_data:
                for foreshadowing_data in foreshadowings_data:
                    if foreshadowing_data.get("content"):
                        foreshadowing = Foreshadowing(
                            id=generate_uuid(),
                            novel_id=context.novel.id,
                            chapter_id=context.chapter.id,
                            content=foreshadowing_data["content"],
                            is_resolved="false",
                            foreshadowing_order=len(existing_foreshadowings) + len(extracted_foreshadowings),
                            created_at=int(time.time() * 1000),
                            updated_at=int(time.time() * 1000)
                        )
                        context.task_db.add(foreshadowing)
                        extracted_foreshadowings.append(foreshadowing_data["content"])
                context.task_db.commit()
                logger.info(f"✅ 章节 {context.chapter.title} 提取到 {len(extracted_foreshadowings)} 个伏笔")
        except Exception as e:
            logger.warning(f"⚠️ 提取伏笔失败（继续）: {str(e)}")
        
        # 6. 提取并保存下一章钩子
        next_chapter_hook = ""
        try:
            next_chapter_title = next_chapter.title if next_chapter else None
            next_chapter_summary = next_chapter.summary if next_chapter else None
            
            next_chapter_hook = extract_next_chapter_hook(
                title=context.novel.title,
                genre=context.novel.genre,
                chapter_title=context.chapter.title,
                chapter_content=content,
                next_chapter_title=next_chapter_title,
                next_chapter_summary=next_chapter_summary
            )
            
            if next_chapter_hook:
                # 将钩子保存到章节的ai_prompt_hints字段
                original_hints = context.chapter.ai_prompt_hints or ""
                if original_hints:
                    # 移除旧的钩子（如果有）
                    original_hints = original_hints.replace("【下一章钩子】", "").strip()
                    context.chapter.ai_prompt_hints = f"【下一章钩子】{next_chapter_hook}\n\n{original_hints}".strip()
                else:
                    context.chapter.ai_prompt_hints = f"【下一章钩子】{next_chapter_hook}"
                context.task_db.add(context.chapter)
                context.task_db.commit()
                logger.info(f"✅ 章节 {context.chapter.title} 提取到下一章钩子：{next_chapter_hook[:50]}...")
        except Exception as e:
            logger.warning(f"⚠️ 提取下一章钩子失败（继续）: {str(e)}")
        
        result.update({
            "success": True,
            "content": content,
            "foreshadowings": extracted_foreshadowings,
            "next_chapter_hook": next_chapter_hook
        })
        
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"生成章节失败: chapter_id={context.chapter.id}, error={str(e)}", exc_info=True)
        context.task_db.rollback()
    
    return result


def get_previous_chapter_hook(
    task_db: Session,
    volume_id: str,
    chapter_order: int
) -> str:
    """获取上一章的钩子"""
    if chapter_order <= 0:
        return ""
    
    prev_chapter = task_db.query(Chapter).filter(
        Chapter.volume_id == volume_id,
        Chapter.chapter_order == chapter_order - 1
    ).first()
    
    if prev_chapter and prev_chapter.ai_prompt_hints and "【下一章钩子】" in prev_chapter.ai_prompt_hints:
        hook_part = prev_chapter.ai_prompt_hints.split("【下一章钩子】")
        if len(hook_part) > 1:
            hook = hook_part[-1].strip()
            logger.info(f"💡 获取到上一章钩子：{hook[:50]}...")
            return hook
    
    return ""


def get_forced_previous_chapter_context(
    task_db: Session,
    volume_id: str,
    chapter_order: int
) -> str:
    """获取上一章的完整内容作为强制上下文（用于生成下一章时保证连贯性）"""
    if chapter_order <= 0:
        return ""
    
    prev_chapter = task_db.query(Chapter).filter(
        Chapter.volume_id == volume_id,
        Chapter.chapter_order == chapter_order - 1
    ).first()
    
    if prev_chapter and prev_chapter.content and prev_chapter.content.strip():
        context = f"""【上一章完整内容】（必须承接）：
章节标题：{prev_chapter.title}
章节摘要：{prev_chapter.summary or ""}
完整章节内容：
{prev_chapter.content}"""
        logger.info(f"✅ 强制包含上一章完整内容作为上下文（{len(prev_chapter.content)}字）")
        return context
    
    return ""


def prepare_chapter_writing_context(
    task_db: Session,
    novel_id: str,
    volume_id: str,
    chapter_id: str,
    include_previous_context: bool = False
) -> Optional[ChapterWritingContext]:
    """
    准备章节写作上下文
    
    Args:
        task_db: 数据库会话
        novel_id: 小说ID
        volume_id: 卷ID
        chapter_id: 章节ID
        include_previous_context: 是否包含上一章的完整内容作为强制上下文
    
    Returns:
        ChapterWritingContext 对象，如果相关对象不存在则返回 None
    """
    novel = task_db.query(Novel).filter(Novel.id == novel_id).first()
    volume = task_db.query(Volume).filter(Volume.id == volume_id).first()
    chapter = task_db.query(Chapter).filter(Chapter.id == chapter_id).first()
    
    if not novel or not volume or not chapter:
        return None
    
    characters = task_db.query(Character).filter(Character.novel_id == novel_id).all()
    world_settings = task_db.query(WorldSetting).filter(WorldSetting.novel_id == novel_id).all()
    
    # 获取上一章的钩子
    previous_chapter_hook = get_previous_chapter_hook(
        task_db, volume_id, chapter.chapter_order
    )
    
    # 获取上一章的完整内容（如果需要）
    forced_previous_chapter_context = ""
    if include_previous_context:
        forced_previous_chapter_context = get_forced_previous_chapter_context(
            task_db, volume_id, chapter.chapter_order
        )
    
    return ChapterWritingContext(
        task_db=task_db,
        novel=novel,
        volume=volume,
        chapter=chapter,
        characters=characters,
        world_settings=world_settings,
        previous_chapter_hook=previous_chapter_hook,
        forced_previous_chapter_context=forced_previous_chapter_context
    )

