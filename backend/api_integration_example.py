"""
API集成示例代码
展示如何在现有的API端点中集成向量存储功能

注意：这只是一个示例文件，实际的API路由可能在其他位置
需要根据实际的项目结构调整集成位置
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from auth import get_current_user
from models import Novel, Volume, Chapter, User
from schemas import ChapterCreate, ChapterUpdate, ChapterResponse
from services.vector_helper import store_chapter_embedding_async, store_character_embedding, store_world_setting_embedding
from services.embedding_service import EmbeddingService
from services.consistency_checker import ConsistencyChecker
from services.foreshadowing_matcher import ForeshadowingMatcher
from services.content_similarity_checker import ContentSimilarityChecker

router = APIRouter(prefix="/api", tags=["chapters"])


# ==================== 章节相关API ====================

@router.post("/volumes/{volume_id}/chapters", response_model=List[ChapterResponse])
async def create_chapters(
    volume_id: str,
    chapters: List[ChapterCreate],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量创建章节（已集成向量存储）
    """
    # 1. 验证权限和获取卷信息
    volume = db.query(Volume).join(Novel).filter(
        Volume.id == volume_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not volume:
        raise HTTPException(status_code=404, detail="卷不存在")
    
    # 2. 创建章节（原有逻辑）
    created_chapters = []
    for chapter_data in chapters:
        chapter = Chapter(
            id=str(uuid.uuid4()),
            volume_id=volume_id,
            title=chapter_data.title,
            summary=chapter_data.summary,
            content=chapter_data.content or "",
            ai_prompt_hints=chapter_data.ai_prompt_hints or "",
            chapter_order=chapter_data.chapter_order or 0,
            created_at=int(time.time() * 1000),
            updated_at=int(time.time() * 1000)
        )
        db.add(chapter)
        created_chapters.append(chapter)
    
    db.commit()
    
    # 3. 新增：异步存储章节向量（使用后台任务）
    for chapter in created_chapters:
        if chapter.content and chapter.content.strip():
            background_tasks.add_task(
                store_chapter_embedding_async,
                db=db,
                chapter_id=chapter.id,
                novel_id=volume.novel_id,
                content=chapter.content
            )
    
    return created_chapters


@router.put("/volumes/{volume_id}/chapters/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(
    volume_id: str,
    chapter_id: str,
    chapter_update: ChapterUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新章节（已集成向量更新）
    """
    # 1. 验证权限
    chapter = db.query(Chapter).join(Volume).join(Novel).filter(
        Chapter.id == chapter_id,
        Chapter.volume_id == volume_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    # 2. 检查内容是否变更
    content_changed = chapter_update.content and chapter_update.content != chapter.content
    
    # 3. 更新章节（原有逻辑）
    if chapter_update.title is not None:
        chapter.title = chapter_update.title
    if chapter_update.summary is not None:
        chapter.summary = chapter_update.summary
    if chapter_update.content is not None:
        chapter.content = chapter_update.content
    if chapter_update.ai_prompt_hints is not None:
        chapter.ai_prompt_hints = chapter_update.ai_prompt_hints
    
    chapter.updated_at = int(time.time() * 1000)
    db.commit()
    
    # 4. 新增：如果内容变更，更新向量
    if content_changed and chapter.content and chapter.content.strip():
        volume = db.query(Volume).filter(Volume.id == volume_id).first()
        if volume:
            background_tasks.add_task(
                store_chapter_embedding_async,
                db=db,
                chapter_id=chapter_id,
                novel_id=volume.novel_id,
                content=chapter.content
            )
    
    return chapter


# ==================== 新增API端点：相似度检查 ====================

@router.post("/novels/{novel_id}/chapters/check-similarity")
async def check_similarity(
    novel_id: str,
    content: str,
    current_chapter_id: Optional[str] = None,
    threshold: float = 0.8,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    检查生成内容与已有章节的相似度
    """
    # 1. 验证权限
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 2. 查找相似章节
    try:
        service = EmbeddingService()
        similar_chapters = service.find_similar_chapters(
            db=db,
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
                "warning": f"发现 {len(similar_chapters)} 个相似章节，建议检查是否重复",
                "threshold": threshold
            }
        
        return {
            "has_similar_content": False,
            "similar_chapters": [],
            "threshold": threshold
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查相似度失败: {str(e)}")


# ==================== 角色相关API集成示例 ====================

@router.post("/novels/{novel_id}/characters")
async def create_characters(
    novel_id: str,
    characters: List[CharacterCreate],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量创建角色（已集成向量存储）
    """
    # 验证权限...
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 创建角色（原有逻辑）...
    created_characters = []
    for char_data in characters:
        character = Character(
            id=str(uuid.uuid4()),
            novel_id=novel_id,
            name=char_data.name,
            age=char_data.age or "",
            role=char_data.role or "",
            personality=char_data.personality or "",
            background=char_data.background or "",
            goals=char_data.goals or "",
            character_order=char_data.character_order or 0,
            created_at=int(time.time() * 1000),
            updated_at=int(time.time() * 1000)
        )
        db.add(character)
        created_characters.append(character)
    
    db.commit()
    
    # 新增：存储角色向量
    for character in created_characters:
        background_tasks.add_task(
            store_character_embedding,
            db=db,
            character_id=character.id,
            novel_id=novel_id,
            name=character.name,
            personality=character.personality or "",
            background=character.background or "",
            goals=character.goals or ""
        )
    
    return created_characters


# ==================== 世界观相关API集成示例 ====================

@router.post("/novels/{novel_id}/world-settings")
async def create_world_settings(
    novel_id: str,
    world_settings: List[WorldSettingCreate],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量创建世界观设定（已集成向量存储）
    """
    # 验证权限...
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 创建世界观设定（原有逻辑）...
    created_settings = []
    for setting_data in world_settings:
        setting = WorldSetting(
            id=str(uuid.uuid4()),
            novel_id=novel_id,
            title=setting_data.title,
            description=setting_data.description,
            category=setting_data.category,
            setting_order=setting_data.setting_order or 0,
            created_at=int(time.time() * 1000),
            updated_at=int(time.time() * 1000)
        )
        db.add(setting)
        created_settings.append(setting)
    
    db.commit()
    
    # 新增：存储世界观向量
    for setting in created_settings:
        background_tasks.add_task(
            store_world_setting_embedding,
            db=db,
            world_setting_id=setting.id,
            novel_id=novel_id,
            title=setting.title,
            description=setting.description
        )
    
    return created_settings


# ==================== 新增API端点：伏笔匹配 ====================

@router.post("/novels/{novel_id}/foreshadowings/match-resolutions")
async def match_foreshadowing_resolutions(
    novel_id: str,
    chapter_id: str,
    auto_update: bool = False,
    similarity_threshold: float = 0.8,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    自动匹配章节内容可能解决的伏笔
    """
    # 1. 验证权限
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 2. 获取章节内容
    chapter = db.query(Chapter).join(Volume).filter(
        Chapter.id == chapter_id,
        Volume.novel_id == novel_id
    ).first()
    
    if not chapter or not chapter.content:
        raise HTTPException(status_code=404, detail="章节不存在或内容为空")
    
    # 3. 匹配伏笔
    try:
        matcher = ForeshadowingMatcher()
        result = matcher.auto_update_foreshadowing_resolution(
            db=db,
            novel_id=novel_id,
            chapter_id=chapter_id,
            chapter_content=chapter.content,
            similarity_threshold=similarity_threshold,
            auto_update=auto_update
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"伏笔匹配失败: {str(e)}")


# ==================== 新增API端点：内容相似度预检查 ====================

@router.post("/novels/{novel_id}/chapters/check-before-generation")
async def check_before_generation(
    novel_id: str,
    chapter_title: str,
    chapter_summary: str,
    current_chapter_id: Optional[str] = None,
    similarity_threshold: float = 0.8,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    在生成章节内容前检查相似度（可选）
    """
    # 1. 验证权限
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 2. 检查相似度
    try:
        checker = ContentSimilarityChecker()
        result = checker.check_before_generation(
            db=db,
            novel_id=novel_id,
            chapter_title=chapter_title,
            chapter_summary=chapter_summary,
            exclude_chapter_ids=[current_chapter_id] if current_chapter_id else None,
            similarity_threshold=similarity_threshold
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"相似度检查失败: {str(e)}")


# ==================== 使用智能上下文的AI生成示例 ====================

@router.post("/ai/write-chapter")
async def write_chapter_with_smart_context(
    request: WriteChapterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    使用智能上下文的章节生成（示例）
    注意：实际实现可能需要根据项目结构调整
    """
    from gemini_service import write_chapter_content_stream
    
    # 验证权限...
    novel = db.query(Novel).filter(
        Novel.title == request.novel_title,  # 或使用 novel_id
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 使用智能上下文生成内容
    stream = write_chapter_content_stream(
        novel_title=request.novel_title,
        genre=request.genre,
        synopsis=request.synopsis,
        chapter_title=request.chapter_title,
        chapter_summary=request.chapter_summary,
        chapter_prompt_hints=request.chapter_prompt_hints,
        characters=request.characters or [],
        world_settings=request.world_settings or [],
        previous_chapters_context=request.previous_chapters_context,  # 可选，会被智能上下文覆盖
        novel_id=novel.id,  # 新增：传递 novel_id
        current_chapter_id=None,  # 如果是更新现有章节，传递 chapter_id
        db_session=db  # 新增：传递数据库会话
    )
    
    # 返回流式响应...
    return stream

