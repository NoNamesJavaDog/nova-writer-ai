"""
NovaWrite AI 后端主应用
包含所有 API 路由
"""
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
import time
import json
import uuid
import logging

from config import CORS_ORIGINS, DEBUG
from database import get_db, SessionLocal
from auth import (
    get_current_user, create_access_token, create_refresh_token,
    verify_refresh_token, get_password_hash, verify_password,
    get_user_by_username_or_email, generate_uuid
)
from models import (
    User, Novel, Volume, Chapter, Character, WorldSetting,
    TimelineEvent, Foreshadowing, UserCurrentNovel, Task
)
from schemas import (
    # 用户相关
    UserCreate, UserLogin, UserResponse, Token, RefreshTokenRequest,
    # 小说相关
    NovelCreate, NovelUpdate, NovelResponse,
    # 卷相关
    VolumeCreate, VolumeUpdate, VolumeResponse,
    # 章节相关
    ChapterCreate, ChapterUpdate, ChapterResponse,
    # 角色相关
    CharacterCreate, CharacterUpdate, CharacterResponse,
    # 世界观相关
    WorldSettingCreate, WorldSettingUpdate, WorldSettingResponse,
    # 时间线相关
    TimelineEventCreate, TimelineEventUpdate, TimelineEventResponse,
    # 伏笔相关
    ForeshadowingCreate, ForeshadowingUpdate, ForeshadowingResponse,
    # 当前小说
    CurrentNovelResponse, CurrentNovelUpdate,
    # AI 相关
    GenerateOutlineRequest, GenerateVolumeOutlineRequest,
    GenerateChapterOutlineRequest, WriteChapterRequest,
    GenerateCharactersRequest, GenerateWorldSettingsRequest,
    GenerateTimelineEventsRequest, ModifyOutlineByDialogueRequest,
    ModifyOutlineByDialogueResponse,
    # 任务相关
    TaskResponse
)
from pydantic import BaseModel
from captcha import generate_captcha, verify_captcha, check_login_status
from gemini_service import (
    generate_full_outline, generate_volume_outline_stream,
    generate_chapter_outline, write_chapter_content_stream,
    generate_characters, generate_world_settings, generate_timeline_events,
    generate_foreshadowings_from_outline, modify_outline_by_dialogue,
    extract_foreshadowings_from_chapter
)
from task_service import create_task, get_task_executor, ProgressCallback
from services.vector_helper import (
    store_chapter_embedding_async, store_character_embedding,
    store_world_setting_embedding
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="NovaWrite AI API",
    description="专业小说创作助手后端 API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 辅助函数 ====================

def to_camel_case(snake_str: str) -> str:
    """将 snake_case 转换为 camelCase"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.capitalize() for x in components[1:])

def convert_to_camel_case(data: Any) -> Any:
    """递归转换字典键为 camelCase"""
    if isinstance(data, dict):
        return {to_camel_case(k): convert_to_camel_case(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_to_camel_case(item) for item in data]
    else:
        return data

# ==================== 认证路由 ====================

@app.post("/api/auth/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user_data.email.lower()).first():
        raise HTTPException(status_code=400, detail="邮箱已存在")
    
    # 创建新用户
    user = User(
        id=generate_uuid(),
        username=user_data.username,
        email=user_data.email.lower(),
        password_hash=get_password_hash(user_data.password),
        created_at=int(time.time() * 1000),
        password_fail_count=0,
        captcha_fail_count=0
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 生成令牌
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            last_login_at=None
        )
    }

@app.get("/api/auth/captcha")
async def get_captcha():
    """获取验证码"""
    captcha = generate_captcha()
    return {
        "captcha_id": captcha["captcha_id"],
        "image": captcha["image"]
    }

@app.get("/api/auth/login-status")
async def check_login_status_endpoint(
    username_or_email: str,
    db: Session = Depends(get_db)
):
    """检查登录状态（是否需要验证码等）"""
    status_info = check_login_status(db, username_or_email)
    return status_info

@app.post("/api/auth/login", response_model=Token)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = get_user_by_username_or_email(db, login_data.username_or_email)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 检查账户是否被锁定
    if user.locked_until and user.locked_until > int(time.time() * 1000):
        lock_seconds = (user.locked_until - int(time.time() * 1000)) // 1000
        raise HTTPException(
            status_code=403,
            detail=f"账户已被锁定，请在 {lock_seconds} 秒后重试"
        )
    
    # 检查是否需要验证码
    requires_captcha = check_login_status(db, login_data.username_or_email).get("requires_captcha", False)
    if requires_captcha:
        if not login_data.captcha_id or not login_data.captcha_code:
            raise HTTPException(status_code=400, detail="需要验证码")
        if not verify_captcha(login_data.captcha_id, login_data.captcha_code):
            raise HTTPException(status_code=400, detail="验证码错误")
    
    # 验证密码
    if not verify_password(login_data.password, user.password_hash):
        # 更新失败计数
        from auth_helper import handle_login_failure
        handle_login_failure(db, user, login_data.captcha_id, login_data.captcha_code)
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 登录成功，重置失败计数
    user.password_fail_count = 0
    user.captcha_fail_count = 0
    user.locked_until = None
    user.last_login_at = int(time.time() * 1000)
    db.commit()
    
    # 生成令牌
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )
    }

@app.post("/api/auth/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """刷新访问令牌"""
    user_id = verify_refresh_token(refresh_data.refresh_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的刷新令牌")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    # 生成新令牌
    access_token = create_access_token(data={"sub": user.id})
    new_refresh_token = create_refresh_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )
    }

@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at
    )

# ==================== 小说路由 ====================

@app.get("/api/novels", response_model=List[NovelResponse])
async def get_novels(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有小说"""
    try:
        novels = db.query(Novel).options(
            joinedload(Novel.volumes).joinedload(Volume.chapters),
            joinedload(Novel.characters),
            joinedload(Novel.world_settings),
            joinedload(Novel.timeline_events),
            joinedload(Novel.foreshadowings)
        ).filter(Novel.user_id == current_user.id).order_by(Novel.updated_at.desc()).all()
        result = []
        for novel in novels:
            novel_dict = {
                "id": novel.id,
                "user_id": novel.user_id,
                "title": novel.title,
                "genre": novel.genre,
                "synopsis": novel.synopsis or "",
                "full_outline": novel.full_outline or "",
                "created_at": novel.created_at,
                "updated_at": novel.updated_at,
                "volumes": [{
                    "id": v.id,
                    "novel_id": v.novel_id,
                    "title": v.title,
                    "summary": v.summary or "",
                    "outline": v.outline or "",
                    "volume_order": v.volume_order,
                    "created_at": v.created_at,
                    "updated_at": v.updated_at,
                    "chapters": [{
                        "id": c.id,
                        "volume_id": c.volume_id,
                        "title": c.title,
                        "summary": c.summary or "",
                        "content": c.content or "",
                        "ai_prompt_hints": c.ai_prompt_hints or "",
                        "chapter_order": c.chapter_order,
                        "created_at": c.created_at,
                        "updated_at": c.updated_at
                    } for c in v.chapters]
                } for v in novel.volumes],
                "characters": [{
                    "id": c.id,
                    "novel_id": c.novel_id,
                    "name": c.name,
                    "age": c.age or "",
                    "role": c.role or "",
                    "personality": c.personality or "",
                    "background": c.background or "",
                    "goals": c.goals or "",
                    "character_order": c.character_order,
                    "created_at": c.created_at,
                    "updated_at": c.updated_at
                } for c in novel.characters],
                "world_settings": [{
                    "id": w.id,
                    "novel_id": w.novel_id,
                    "title": w.title,
                    "description": w.description,
                    "category": w.category,
                    "setting_order": w.setting_order,
                    "created_at": w.created_at,
                    "updated_at": w.updated_at
                } for w in novel.world_settings],
                "timeline_events": [{
                    "id": t.id,
                    "novel_id": t.novel_id,
                    "time": t.time,
                    "event": t.event,
                    "impact": t.impact or "",
                    "event_order": t.event_order,
                    "created_at": t.created_at,
                    "updated_at": t.updated_at
                } for t in novel.timeline_events],
                "foreshadowings": [{
                    "id": f.id,
                    "novel_id": f.novel_id,
                    "content": f.content,
                    "chapter_id": f.chapter_id,
                    "resolved_chapter_id": f.resolved_chapter_id,
                    "is_resolved": f.is_resolved,
                    "foreshadowing_order": f.foreshadowing_order,
                    "created_at": f.created_at,
                    "updated_at": f.updated_at
                } for f in novel.foreshadowings]
            }
            result.append(convert_to_camel_case(novel_dict))
        return result
    except Exception as e:
        logger.error(f"获取小说列表失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"获取小说列表失败: {str(e)}")

@app.get("/api/novels/{novel_id}", response_model=NovelResponse)
async def get_novel(
    novel_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个小说详情"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    novel_dict = {
        "id": novel.id,
        "user_id": novel.user_id,
        "title": novel.title,
        "genre": novel.genre,
        "synopsis": novel.synopsis or "",
        "full_outline": novel.full_outline or "",
        "created_at": novel.created_at,
        "updated_at": novel.updated_at,
        "volumes": [{
            "id": v.id,
            "novel_id": v.novel_id,
            "title": v.title,
            "summary": v.summary or "",
            "outline": v.outline or "",
            "volume_order": v.volume_order,
            "created_at": v.created_at,
            "updated_at": v.updated_at,
            "chapters": [{
                "id": c.id,
                "volume_id": c.volume_id,
                "title": c.title,
                "summary": c.summary or "",
                "content": c.content or "",
                "ai_prompt_hints": c.ai_prompt_hints or "",
                "chapter_order": c.chapter_order,
                "created_at": c.created_at,
                "updated_at": c.updated_at
            } for c in v.chapters]
        } for v in novel.volumes],
        "characters": [{
            "id": c.id,
            "novel_id": c.novel_id,
            "name": c.name,
            "age": c.age or "",
            "role": c.role or "",
            "personality": c.personality or "",
            "background": c.background or "",
            "goals": c.goals or "",
            "character_order": c.character_order,
            "created_at": c.created_at,
            "updated_at": c.updated_at
        } for c in novel.characters],
        "world_settings": [{
            "id": w.id,
            "novel_id": w.novel_id,
            "title": w.title,
            "description": w.description,
            "category": w.category,
            "setting_order": w.setting_order,
            "created_at": w.created_at,
            "updated_at": w.updated_at
        } for w in novel.world_settings],
        "timeline_events": [{
            "id": t.id,
            "novel_id": t.novel_id,
            "time": t.time,
            "event": t.event,
            "impact": t.impact or "",
            "event_order": t.event_order,
            "created_at": t.created_at,
            "updated_at": t.updated_at
        } for t in novel.timeline_events],
        "foreshadowings": [{
            "id": f.id,
            "novel_id": f.novel_id,
            "content": f.content,
            "chapter_id": f.chapter_id,
            "resolved_chapter_id": f.resolved_chapter_id,
            "is_resolved": f.is_resolved,
            "foreshadowing_order": f.foreshadowing_order,
            "created_at": f.created_at,
            "updated_at": f.updated_at
        } for f in novel.foreshadowings]
    }
    return convert_to_camel_case(novel_dict)

@app.post("/api/novels", response_model=NovelResponse)
async def create_novel(
    novel_data: NovelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新小说"""
    try:
        novel = Novel(
            id=generate_uuid(),
            user_id=current_user.id,
            title=novel_data.title,
            genre=novel_data.genre,
            synopsis=novel_data.synopsis or "",
            full_outline=novel_data.full_outline or "",
            created_at=int(time.time() * 1000),
            updated_at=int(time.time() * 1000)
        )
        db.add(novel)
        db.commit()
        db.refresh(novel)
        
        novel_dict = {
            "id": novel.id,
            "user_id": novel.user_id,
            "title": novel.title,
            "genre": novel.genre,
            "synopsis": novel.synopsis or "",
            "full_outline": novel.full_outline or "",
            "created_at": novel.created_at,
            "updated_at": novel.updated_at,
            "volumes": [],
            "characters": [],
            "world_settings": [],
            "timeline_events": [],
            "foreshadowings": []
        }
        try:
            result = convert_to_camel_case(novel_dict)
            return result
        except Exception as convert_error:
            logger.error(f"转换数据格式失败: {str(convert_error)}", exc_info=True)
            # 如果转换失败，直接返回原始数据
            return novel_dict
    except Exception as e:
        logger.error(f"创建小说失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建小说失败: {str(e)}")

@app.put("/api/novels/{novel_id}", response_model=NovelResponse)
async def update_novel(
    novel_id: str,
    novel_data: NovelUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新小说信息"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    if novel_data.title is not None:
        novel.title = novel_data.title
    if novel_data.genre is not None:
        novel.genre = novel_data.genre
    if novel_data.synopsis is not None:
        novel.synopsis = novel_data.synopsis
    if novel_data.full_outline is not None:
        novel.full_outline = novel_data.full_outline
    novel.updated_at = int(time.time() * 1000)
    
    db.commit()
    db.refresh(novel)
    
    return await get_novel(novel_id, current_user, db)

@app.delete("/api/novels/{novel_id}")
async def delete_novel(
    novel_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除小说"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    db.delete(novel)
    db.commit()
    return {"message": "小说已删除"}

# ==================== 同步路由 ====================

@app.post("/api/novels/{novel_id}/sync", response_model=NovelResponse)
async def sync_novel(
    novel_id: str,
    novel_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """完整同步小说（包括所有子项）"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    current_time = int(time.time() * 1000)
    
    # 1. 更新基本信息
    if "title" in novel_data:
        novel.title = novel_data["title"]
    if "genre" in novel_data:
        novel.genre = novel_data["genre"]
    if "synopsis" in novel_data:
        novel.synopsis = novel_data.get("synopsis", "")
    if "fullOutline" in novel_data:
        novel.full_outline = novel_data.get("fullOutline", "")
    novel.updated_at = current_time
    
    # 2. 同步卷和章节
    if "volumes" in novel_data:
        volumes_data = novel_data["volumes"] or []
        existing_volumes = {v.id: v for v in novel.volumes}
        volume_ids = {v.get("id") for v in volumes_data if v and v.get("id")}
        
        for volume_data in volumes_data:
            if not volume_data or not volume_data.get("id"):
                continue
            volume_id = volume_data["id"]
            
            if volume_id in existing_volumes:
                # 更新现有卷
                volume = existing_volumes[volume_id]
                volume.title = volume_data.get("title", "")
                volume.summary = volume_data.get("summary", "")
                volume.outline = volume_data.get("outline", "")
                volume.updated_at = current_time
                
                # 同步章节
                chapters_data = volume_data.get("chapters", []) or []
                existing_chapters = {c.id: c for c in volume.chapters}
                chapter_ids = {c.get("id") for c in chapters_data if c and c.get("id")}
                
                for chapter_data in chapters_data:
                    if not chapter_data or not chapter_data.get("id"):
                        continue
                    chapter_id = chapter_data["id"]
                    
                    if chapter_id in existing_chapters:
                        # 更新现有章节
                        chapter = existing_chapters[chapter_id]
                        chapter.title = chapter_data.get("title", "")
                        chapter.summary = chapter_data.get("summary", "")
                        chapter.content = chapter_data.get("content", "")
                        chapter.ai_prompt_hints = chapter_data.get("aiPromptHints", "")
                        chapter.updated_at = current_time
                        
                        # 异步存储向量
                        if chapter.content and chapter.content.strip():
                            background_tasks.add_task(
                                store_chapter_embedding_async,
                                db=db,
                                chapter_id=chapter.id,
                                novel_id=novel_id,
                                content=chapter.content
                            )
                    else:
                        # 创建新章节
                        chapter = Chapter(
                            id=chapter_id,
                            volume_id=volume_id,
                            title=chapter_data.get("title", ""),
                            summary=chapter_data.get("summary", ""),
                            content=chapter_data.get("content", ""),
                            ai_prompt_hints=chapter_data.get("aiPromptHints", ""),
                            chapter_order=len(volume.chapters),
                            created_at=current_time,
                            updated_at=current_time
                        )
                        db.add(chapter)
                        if chapter.content and chapter.content.strip():
                            background_tasks.add_task(
                                store_chapter_embedding_async,
                                db=db,
                                chapter_id=chapter.id,
                                novel_id=novel_id,
                                content=chapter.content
                            )
                
                # 删除不在列表中的章节
                for chapter_id, chapter in existing_chapters.items():
                    if chapter_id not in chapter_ids:
                        db.delete(chapter)
            else:
                # 创建新卷
                volume = Volume(
                    id=volume_id,
                    novel_id=novel_id,
                    title=volume_data.get("title", ""),
                    summary=volume_data.get("summary", ""),
                    outline=volume_data.get("outline", ""),
                    volume_order=len(novel.volumes),
                    created_at=current_time,
                    updated_at=current_time
                )
                db.add(volume)
                
                # 创建章节
                chapters_data = volume_data.get("chapters", []) or []
                for idx, chapter_data in enumerate(chapters_data):
                    if not chapter_data:
                        continue
                    chapter = Chapter(
                        id=chapter_data.get("id") or generate_uuid(),
                        volume_id=volume_id,
                        title=chapter_data.get("title", ""),
                        summary=chapter_data.get("summary", ""),
                        content=chapter_data.get("content", ""),
                        ai_prompt_hints=chapter_data.get("aiPromptHints", ""),
                        chapter_order=idx,
                        created_at=current_time,
                        updated_at=current_time
                    )
                    db.add(chapter)
                    if chapter.content and chapter.content.strip():
                        background_tasks.add_task(
                            store_chapter_embedding_async,
                            db=db,
                            chapter_id=chapter.id,
                            novel_id=novel_id,
                            content=chapter.content
                        )
        
        # 删除不在列表中的卷
        for volume_id, volume in existing_volumes.items():
            if volume_id not in volume_ids:
                db.delete(volume)
    
    # 3. 同步角色
    if "characters" in novel_data:
        characters_data = novel_data["characters"] or []
        existing_characters = {c.id: c for c in novel.characters}
        character_ids = {c.get("id") for c in characters_data if c and c.get("id")}
        
        for character_data in characters_data:
            if not character_data or not character_data.get("id"):
                continue
            character_id = character_data["id"]
            
            if character_id in existing_characters:
                character = existing_characters[character_id]
                character.name = character_data.get("name", "")
                character.age = character_data.get("age", "")
                character.role = character_data.get("role", "")
                character.personality = character_data.get("personality", "")
                character.background = character_data.get("background", "")
                character.goals = character_data.get("goals", "")
                character.updated_at = current_time
            else:
                character = Character(
                    id=character_id,
                    novel_id=novel_id,
                    name=character_data.get("name", ""),
                    age=character_data.get("age", ""),
                    role=character_data.get("role", ""),
                    personality=character_data.get("personality", ""),
                    background=character_data.get("background", ""),
                    goals=character_data.get("goals", ""),
                    character_order=len(novel.characters),
                    created_at=current_time,
                    updated_at=current_time
                )
                db.add(character)
        
        # 删除不在列表中的角色
        for character_id, character in existing_characters.items():
            if character_id not in character_ids:
                db.delete(character)
    
    # 4. 同步世界观设定
    if "worldSettings" in novel_data:
        world_settings_data = novel_data["worldSettings"] or []
        existing_world_settings = {w.id: w for w in novel.world_settings}
        world_setting_ids = {w.get("id") for w in world_settings_data if w and w.get("id")}
        
        for world_setting_data in world_settings_data:
            if not world_setting_data or not world_setting_data.get("id"):
                continue
            world_setting_id = world_setting_data["id"]
            
            if world_setting_id in existing_world_settings:
                world_setting = existing_world_settings[world_setting_id]
                world_setting.title = world_setting_data.get("title", "")
                world_setting.description = world_setting_data.get("description", "")
                world_setting.category = world_setting_data.get("category", "其他")
                world_setting.updated_at = current_time
            else:
                world_setting = WorldSetting(
                    id=world_setting_id,
                    novel_id=novel_id,
                    title=world_setting_data.get("title", ""),
                    description=world_setting_data.get("description", ""),
                    category=world_setting_data.get("category", "其他"),
                    setting_order=len(novel.world_settings),
                    created_at=current_time,
                    updated_at=current_time
                )
                db.add(world_setting)
        
        # 删除不在列表中的世界观设定
        for world_setting_id, world_setting in existing_world_settings.items():
            if world_setting_id not in world_setting_ids:
                db.delete(world_setting)
    
    # 5. 同步时间线
    if "timeline" in novel_data:
        timeline_data = novel_data["timeline"] or []
        existing_timeline = {t.id: t for t in novel.timeline_events}
        timeline_ids = {t.get("id") for t in timeline_data if t and t.get("id")}
        
        for timeline_event_data in timeline_data:
            if not timeline_event_data or not timeline_event_data.get("id"):
                continue
            timeline_event_id = timeline_event_data["id"]
            
            if timeline_event_id in existing_timeline:
                timeline_event = existing_timeline[timeline_event_id]
                timeline_event.time = timeline_event_data.get("time", "")
                timeline_event.event = timeline_event_data.get("event", "")
                timeline_event.impact = timeline_event_data.get("impact", "")
                timeline_event.updated_at = current_time
            else:
                timeline_event = TimelineEvent(
                    id=timeline_event_id,
                    novel_id=novel_id,
                    time=timeline_event_data.get("time", ""),
                    event=timeline_event_data.get("event", ""),
                    impact=timeline_event_data.get("impact", ""),
                    event_order=len(novel.timeline_events),
                    created_at=current_time,
                    updated_at=current_time
                )
                db.add(timeline_event)
        
        # 删除不在列表中的时间线事件
        for timeline_event_id, timeline_event in existing_timeline.items():
            if timeline_event_id not in timeline_ids:
                db.delete(timeline_event)
    
    # 6. 同步伏笔
    if "foreshadowings" in novel_data:
        foreshadowings_data = novel_data["foreshadowings"] or []
        existing_foreshadowings = {f.id: f for f in novel.foreshadowings}
        foreshadowing_ids = {f.get("id") for f in foreshadowings_data if f and f.get("id")}
        
        for foreshadowing_data in foreshadowings_data:
            if not foreshadowing_data or not foreshadowing_data.get("id"):
                continue
            foreshadowing_id = foreshadowing_data["id"]
            
            if foreshadowing_id in existing_foreshadowings:
                foreshadowing = existing_foreshadowings[foreshadowing_id]
                foreshadowing.content = foreshadowing_data.get("content", "")
                foreshadowing.chapter_id = foreshadowing_data.get("chapterId")
                foreshadowing.resolved_chapter_id = foreshadowing_data.get("resolvedChapterId")
                foreshadowing.is_resolved = foreshadowing_data.get("isResolved", "false")
                foreshadowing.updated_at = current_time
            else:
                foreshadowing = Foreshadowing(
                    id=foreshadowing_id,
                    novel_id=novel_id,
                    content=foreshadowing_data.get("content", ""),
                    chapter_id=foreshadowing_data.get("chapterId"),
                    resolved_chapter_id=foreshadowing_data.get("resolvedChapterId"),
                    is_resolved=foreshadowing_data.get("isResolved", "false"),
                    foreshadowing_order=len(novel.foreshadowings),
                    created_at=current_time,
                    updated_at=current_time
                )
                db.add(foreshadowing)
        
        # 删除不在列表中的伏笔
        for foreshadowing_id, foreshadowing in existing_foreshadowings.items():
            if foreshadowing_id not in foreshadowing_ids:
                db.delete(foreshadowing)
    
    db.commit()
    return await get_novel(novel_id, current_user, db)

# ==================== 卷路由 ====================

@app.get("/api/novels/{novel_id}/volumes", response_model=List[VolumeResponse])
async def get_volumes(
    novel_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取小说的所有卷"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    result = []
    for volume in novel.volumes:
        volume_dict = {
            "id": volume.id,
            "novel_id": volume.novel_id,
            "title": volume.title,
            "summary": volume.summary or "",
            "outline": volume.outline or "",
            "volume_order": volume.volume_order,
            "created_at": volume.created_at,
            "updated_at": volume.updated_at,
            "chapters": [{
                "id": c.id,
                "volume_id": c.volume_id,
                "title": c.title,
                "summary": c.summary or "",
                "content": c.content or "",
                "ai_prompt_hints": c.ai_prompt_hints or "",
                "chapter_order": c.chapter_order,
                "created_at": c.created_at,
                "updated_at": c.updated_at
            } for c in volume.chapters]
        }
        result.append(convert_to_camel_case(volume_dict))
    return result

@app.post("/api/novels/{novel_id}/volumes", response_model=VolumeResponse)
async def create_volume(
    novel_id: str,
    volume_data: VolumeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新卷"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    volume = Volume(
        id=generate_uuid(),
        novel_id=novel_id,
        title=volume_data.title,
        summary=volume_data.summary or "",
        outline=volume_data.outline or "",
        volume_order=len(novel.volumes),
        created_at=int(time.time() * 1000),
        updated_at=int(time.time() * 1000)
    )
    db.add(volume)
    db.commit()
    db.refresh(volume)
    
    volume_dict = {
        "id": volume.id,
        "novel_id": volume.novel_id,
        "title": volume.title,
        "summary": volume.summary or "",
        "outline": volume.outline or "",
        "volume_order": volume.volume_order,
        "created_at": volume.created_at,
        "updated_at": volume.updated_at,
        "chapters": []
    }
    return convert_to_camel_case(volume_dict)

@app.put("/api/novels/{novel_id}/volumes/{volume_id}", response_model=VolumeResponse)
async def update_volume(
    novel_id: str,
    volume_id: str,
    volume_data: VolumeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新卷信息"""
    volume = db.query(Volume).join(Novel).filter(
        Volume.id == volume_id,
        Volume.novel_id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not volume:
        raise HTTPException(status_code=404, detail="卷不存在")
    
    if volume_data.title is not None:
        volume.title = volume_data.title
    if volume_data.summary is not None:
        volume.summary = volume_data.summary
    if volume_data.outline is not None:
        volume.outline = volume_data.outline
    volume.updated_at = int(time.time() * 1000)
    
    db.commit()
    db.refresh(volume)
    
    volume_dict = {
        "id": volume.id,
        "novel_id": volume.novel_id,
        "title": volume.title,
        "summary": volume.summary or "",
        "outline": volume.outline or "",
        "volume_order": volume.volume_order,
        "created_at": volume.created_at,
        "updated_at": volume.updated_at,
        "chapters": [{
            "id": c.id,
            "volume_id": c.volume_id,
            "title": c.title,
            "summary": c.summary or "",
            "content": c.content or "",
            "ai_prompt_hints": c.ai_prompt_hints or "",
            "chapter_order": c.chapter_order,
            "created_at": c.created_at,
            "updated_at": c.updated_at
        } for c in volume.chapters]
    }
    return convert_to_camel_case(volume_dict)

@app.delete("/api/novels/{novel_id}/volumes/{volume_id}")
async def delete_volume(
    novel_id: str,
    volume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除卷"""
    volume = db.query(Volume).join(Novel).filter(
        Volume.id == volume_id,
        Volume.novel_id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not volume:
        raise HTTPException(status_code=404, detail="卷不存在")
    
    db.delete(volume)
    db.commit()
    return {"message": "卷已删除"}

# ==================== 章节路由 ====================

@app.get("/api/volumes/{volume_id}/chapters", response_model=List[ChapterResponse])
async def get_chapters(
    volume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取卷的所有章节"""
    volume = db.query(Volume).join(Novel).filter(
        Volume.id == volume_id,
        Novel.user_id == current_user.id
    ).first()
    if not volume:
        raise HTTPException(status_code=404, detail="卷不存在")
    
    result = []
    for chapter in volume.chapters:
        chapter_dict = {
            "id": chapter.id,
            "volume_id": chapter.volume_id,
            "title": chapter.title,
            "summary": chapter.summary or "",
            "content": chapter.content or "",
            "ai_prompt_hints": chapter.ai_prompt_hints or "",
            "chapter_order": chapter.chapter_order,
            "created_at": chapter.created_at,
            "updated_at": chapter.updated_at
        }
        result.append(convert_to_camel_case(chapter_dict))
    return result

@app.post("/api/volumes/{volume_id}/chapters", response_model=List[ChapterResponse])
async def create_chapters(
    volume_id: str,
    chapters_data: List[ChapterCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """批量创建章节"""
    volume = db.query(Volume).join(Novel).filter(
        Volume.id == volume_id,
        Novel.user_id == current_user.id
    ).first()
    if not volume:
        raise HTTPException(status_code=404, detail="卷不存在")
    
    current_time = int(time.time() * 1000)
    created_chapters = []
    
    for idx, chapter_data in enumerate(chapters_data):
        chapter = Chapter(
            id=generate_uuid(),
            volume_id=volume_id,
            title=chapter_data.title,
            summary=chapter_data.summary or "",
            content=chapter_data.content or "",
            ai_prompt_hints=chapter_data.ai_prompt_hints or "",
            chapter_order=len(volume.chapters) + idx,
            created_at=current_time,
            updated_at=current_time
        )
        db.add(chapter)
        created_chapters.append(chapter)
        
        # 异步存储向量
        if chapter.content and chapter.content.strip():
            background_tasks.add_task(
                store_chapter_embedding_async,
                db=db,
                chapter_id=chapter.id,
                novel_id=volume.novel_id,
                content=chapter.content
            )
    
    db.commit()
    
    result = []
    for chapter in created_chapters:
        chapter_dict = {
            "id": chapter.id,
            "volume_id": chapter.volume_id,
            "title": chapter.title,
            "summary": chapter.summary or "",
            "content": chapter.content or "",
            "ai_prompt_hints": chapter.ai_prompt_hints or "",
            "chapter_order": chapter.chapter_order,
            "created_at": chapter.created_at,
            "updated_at": chapter.updated_at
        }
        result.append(convert_to_camel_case(chapter_dict))
    return result

@app.put("/api/volumes/{volume_id}/chapters/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(
    volume_id: str,
    chapter_id: str,
    chapter_data: ChapterUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """更新章节信息"""
    chapter = db.query(Chapter).join(Volume).join(Novel).filter(
        Chapter.id == chapter_id,
        Chapter.volume_id == volume_id,
        Novel.user_id == current_user.id
    ).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    old_content = chapter.content
    if chapter_data.title is not None:
        chapter.title = chapter_data.title
    if chapter_data.summary is not None:
        chapter.summary = chapter_data.summary
    if chapter_data.content is not None:
        chapter.content = chapter_data.content
    if chapter_data.ai_prompt_hints is not None:
        chapter.ai_prompt_hints = chapter_data.ai_prompt_hints
    chapter.updated_at = int(time.time() * 1000)
    
    # 如果内容发生变化，更新向量
    if chapter_data.content is not None and chapter.content != old_content:
        if chapter.content and chapter.content.strip():
            background_tasks.add_task(
                store_chapter_embedding_async,
                db=db,
                chapter_id=chapter.id,
                novel_id=chapter.volume.novel_id,
                content=chapter.content
            )
    
    db.commit()
    db.refresh(chapter)
    
    chapter_dict = {
        "id": chapter.id,
        "volume_id": chapter.volume_id,
        "title": chapter.title,
        "summary": chapter.summary or "",
        "content": chapter.content or "",
        "ai_prompt_hints": chapter.ai_prompt_hints or "",
        "chapter_order": chapter.chapter_order,
        "created_at": chapter.created_at,
        "updated_at": chapter.updated_at
    }
    return convert_to_camel_case(chapter_dict)

@app.delete("/api/volumes/{volume_id}/chapters/{chapter_id}")
async def delete_chapter(
    volume_id: str,
    chapter_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除章节"""
    chapter = db.query(Chapter).join(Volume).join(Novel).filter(
        Chapter.id == chapter_id,
        Chapter.volume_id == volume_id,
        Novel.user_id == current_user.id
    ).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    db.delete(chapter)
    db.commit()
    return {"message": "章节已删除"}

# ==================== 角色路由 ====================

@app.get("/api/novels/{novel_id}/characters", response_model=List[CharacterResponse])
async def get_characters(
    novel_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取小说的所有角色"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    result = []
    for character in novel.characters:
        character_dict = {
            "id": character.id,
            "novel_id": character.novel_id,
            "name": character.name,
            "age": character.age or "",
            "role": character.role or "",
            "personality": character.personality or "",
            "background": character.background or "",
            "goals": character.goals or "",
            "character_order": character.character_order,
            "created_at": character.created_at,
            "updated_at": character.updated_at
        }
        result.append(convert_to_camel_case(character_dict))
    return result

@app.post("/api/novels/{novel_id}/characters", response_model=List[CharacterResponse])
async def create_characters(
    novel_id: str,
    characters_data: List[CharacterCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """批量创建角色"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    current_time = int(time.time() * 1000)
    created_characters = []
    
    for idx, character_data in enumerate(characters_data):
        character = Character(
            id=generate_uuid(),
            novel_id=novel_id,
            name=character_data.name,
            age=character_data.age or "",
            role=character_data.role or "",
            personality=character_data.personality or "",
            background=character_data.background or "",
            goals=character_data.goals or "",
            character_order=len(novel.characters) + idx,
            created_at=current_time,
            updated_at=current_time
        )
        db.add(character)
        created_characters.append(character)
        
        # 异步存储向量
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
    
    db.commit()
    
    result = []
    for character in created_characters:
        character_dict = {
            "id": character.id,
            "novel_id": character.novel_id,
            "name": character.name,
            "age": character.age or "",
            "role": character.role or "",
            "personality": character.personality or "",
            "background": character.background or "",
            "goals": character.goals or "",
            "character_order": character.character_order,
            "created_at": character.created_at,
            "updated_at": character.updated_at
        }
        result.append(convert_to_camel_case(character_dict))
    return result

@app.put("/api/novels/{novel_id}/characters/{character_id}", response_model=CharacterResponse)
async def update_character(
    novel_id: str,
    character_id: str,
    character_data: CharacterUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """更新角色信息"""
    character = db.query(Character).join(Novel).filter(
        Character.id == character_id,
        Character.novel_id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    if character_data.name is not None:
        character.name = character_data.name
    if character_data.age is not None:
        character.age = character_data.age
    if character_data.role is not None:
        character.role = character_data.role
    if character_data.personality is not None:
        character.personality = character_data.personality
    if character_data.background is not None:
        character.background = character_data.background
    if character_data.goals is not None:
        character.goals = character_data.goals
    character.updated_at = int(time.time() * 1000)
    
    # 更新向量
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
    
    db.commit()
    db.refresh(character)
    
    character_dict = {
        "id": character.id,
        "novel_id": character.novel_id,
        "name": character.name,
        "age": character.age or "",
        "role": character.role or "",
        "personality": character.personality or "",
        "background": character.background or "",
        "goals": character.goals or "",
        "character_order": character.character_order,
        "created_at": character.created_at,
        "updated_at": character.updated_at
    }
    return convert_to_camel_case(character_dict)

@app.delete("/api/novels/{novel_id}/characters/{character_id}")
async def delete_character(
    novel_id: str,
    character_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除角色"""
    character = db.query(Character).join(Novel).filter(
        Character.id == character_id,
        Character.novel_id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    db.delete(character)
    db.commit()
    return {"message": "角色已删除"}

# ==================== 世界观路由 ====================

@app.get("/api/novels/{novel_id}/world-settings", response_model=List[WorldSettingResponse])
async def get_world_settings(
    novel_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取小说的所有世界观设定"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    result = []
    for world_setting in novel.world_settings:
        world_setting_dict = {
            "id": world_setting.id,
            "novel_id": world_setting.novel_id,
            "title": world_setting.title,
            "description": world_setting.description,
            "category": world_setting.category,
            "setting_order": world_setting.setting_order,
            "created_at": world_setting.created_at,
            "updated_at": world_setting.updated_at
        }
        result.append(convert_to_camel_case(world_setting_dict))
    return result

@app.post("/api/novels/{novel_id}/world-settings", response_model=List[WorldSettingResponse])
async def create_world_settings(
    novel_id: str,
    world_settings_data: List[WorldSettingCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """批量创建世界观设定"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    current_time = int(time.time() * 1000)
    created_world_settings = []
    
    for idx, world_setting_data in enumerate(world_settings_data):
        world_setting = WorldSetting(
            id=generate_uuid(),
            novel_id=novel_id,
            title=world_setting_data.title,
            description=world_setting_data.description,
            category=world_setting_data.category,
            setting_order=len(novel.world_settings) + idx,
            created_at=current_time,
            updated_at=current_time
        )
        db.add(world_setting)
        created_world_settings.append(world_setting)
        
        # 异步存储向量
        background_tasks.add_task(
            store_world_setting_embedding,
            db=db,
            world_setting_id=world_setting.id,
            novel_id=novel_id,
            title=world_setting.title,
            description=world_setting.description,
            category=world_setting.category
        )
    
    db.commit()
    
    result = []
    for world_setting in created_world_settings:
        world_setting_dict = {
            "id": world_setting.id,
            "novel_id": world_setting.novel_id,
            "title": world_setting.title,
            "description": world_setting.description,
            "category": world_setting.category,
            "setting_order": world_setting.setting_order,
            "created_at": world_setting.created_at,
            "updated_at": world_setting.updated_at
        }
        result.append(convert_to_camel_case(world_setting_dict))
    return result

@app.put("/api/novels/{novel_id}/world-settings/{world_setting_id}", response_model=WorldSettingResponse)
async def update_world_setting(
    novel_id: str,
    world_setting_id: str,
    world_setting_data: WorldSettingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """更新世界观设定"""
    world_setting = db.query(WorldSetting).join(Novel).filter(
        WorldSetting.id == world_setting_id,
        WorldSetting.novel_id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not world_setting:
        raise HTTPException(status_code=404, detail="世界观设定不存在")
    
    if world_setting_data.title is not None:
        world_setting.title = world_setting_data.title
    if world_setting_data.description is not None:
        world_setting.description = world_setting_data.description
    if world_setting_data.category is not None:
        world_setting.category = world_setting_data.category
    world_setting.updated_at = int(time.time() * 1000)
    
    # 更新向量
    background_tasks.add_task(
        store_world_setting_embedding,
        db=db,
        world_setting_id=world_setting.id,
        novel_id=novel_id,
        title=world_setting.title,
        description=world_setting.description,
        category=world_setting.category
    )
    
    db.commit()
    db.refresh(world_setting)
    
    world_setting_dict = {
        "id": world_setting.id,
        "novel_id": world_setting.novel_id,
        "title": world_setting.title,
        "description": world_setting.description,
        "category": world_setting.category,
        "setting_order": world_setting.setting_order,
        "created_at": world_setting.created_at,
        "updated_at": world_setting.updated_at
    }
    return convert_to_camel_case(world_setting_dict)

@app.delete("/api/novels/{novel_id}/world-settings/{world_setting_id}")
async def delete_world_setting(
    novel_id: str,
    world_setting_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除世界观设定"""
    world_setting = db.query(WorldSetting).join(Novel).filter(
        WorldSetting.id == world_setting_id,
        WorldSetting.novel_id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not world_setting:
        raise HTTPException(status_code=404, detail="世界观设定不存在")
    
    db.delete(world_setting)
    db.commit()
    return {"message": "世界观设定已删除"}

# ==================== 时间线路由 ====================

@app.get("/api/novels/{novel_id}/timeline", response_model=List[TimelineEventResponse])
async def get_timeline(
    novel_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取小说的所有时间线事件"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    result = []
    for timeline_event in novel.timeline_events:
        timeline_event_dict = {
            "id": timeline_event.id,
            "novel_id": timeline_event.novel_id,
            "time": timeline_event.time,
            "event": timeline_event.event,
            "impact": timeline_event.impact or "",
            "event_order": timeline_event.event_order,
            "created_at": timeline_event.created_at,
            "updated_at": timeline_event.updated_at
        }
        result.append(convert_to_camel_case(timeline_event_dict))
    return result

@app.post("/api/novels/{novel_id}/timeline", response_model=List[TimelineEventResponse])
async def create_timeline_events(
    novel_id: str,
    timeline_events_data: List[TimelineEventCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量创建时间线事件"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    current_time = int(time.time() * 1000)
    created_timeline_events = []
    
    for idx, timeline_event_data in enumerate(timeline_events_data):
        timeline_event = TimelineEvent(
            id=generate_uuid(),
            novel_id=novel_id,
            time=timeline_event_data.time,
            event=timeline_event_data.event,
            impact=timeline_event_data.impact or "",
            event_order=len(novel.timeline_events) + idx,
            created_at=current_time,
            updated_at=current_time
        )
        db.add(timeline_event)
        created_timeline_events.append(timeline_event)
    
    db.commit()
    
    result = []
    for timeline_event in created_timeline_events:
        timeline_event_dict = {
            "id": timeline_event.id,
            "novel_id": timeline_event.novel_id,
            "time": timeline_event.time,
            "event": timeline_event.event,
            "impact": timeline_event.impact or "",
            "event_order": timeline_event.event_order,
            "created_at": timeline_event.created_at,
            "updated_at": timeline_event.updated_at
        }
        result.append(convert_to_camel_case(timeline_event_dict))
    return result

@app.put("/api/novels/{novel_id}/timeline/{timeline_event_id}", response_model=TimelineEventResponse)
async def update_timeline_event(
    novel_id: str,
    timeline_event_id: str,
    timeline_event_data: TimelineEventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新时间线事件"""
    timeline_event = db.query(TimelineEvent).join(Novel).filter(
        TimelineEvent.id == timeline_event_id,
        TimelineEvent.novel_id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not timeline_event:
        raise HTTPException(status_code=404, detail="时间线事件不存在")
    
    if timeline_event_data.time is not None:
        timeline_event.time = timeline_event_data.time
    if timeline_event_data.event is not None:
        timeline_event.event = timeline_event_data.event
    if timeline_event_data.impact is not None:
        timeline_event.impact = timeline_event_data.impact
    timeline_event.updated_at = int(time.time() * 1000)
    
    db.commit()
    db.refresh(timeline_event)
    
    timeline_event_dict = {
        "id": timeline_event.id,
        "novel_id": timeline_event.novel_id,
        "time": timeline_event.time,
        "event": timeline_event.event,
        "impact": timeline_event.impact or "",
        "event_order": timeline_event.event_order,
        "created_at": timeline_event.created_at,
        "updated_at": timeline_event.updated_at
    }
    return convert_to_camel_case(timeline_event_dict)

@app.delete("/api/novels/{novel_id}/timeline/{timeline_event_id}")
async def delete_timeline_event(
    novel_id: str,
    timeline_event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除时间线事件"""
    timeline_event = db.query(TimelineEvent).join(Novel).filter(
        TimelineEvent.id == timeline_event_id,
        TimelineEvent.novel_id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not timeline_event:
        raise HTTPException(status_code=404, detail="时间线事件不存在")
    
    db.delete(timeline_event)
    db.commit()
    return {"message": "时间线事件已删除"}

# ==================== 伏笔路由 ====================

@app.get("/api/novels/{novel_id}/foreshadowings", response_model=List[ForeshadowingResponse])
async def get_foreshadowings(
    novel_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取小说的所有伏笔"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    result = []
    for foreshadowing in novel.foreshadowings:
        foreshadowing_dict = {
            "id": foreshadowing.id,
            "novel_id": foreshadowing.novel_id,
            "content": foreshadowing.content,
            "chapter_id": foreshadowing.chapter_id,
            "resolved_chapter_id": foreshadowing.resolved_chapter_id,
            "is_resolved": foreshadowing.is_resolved,
            "foreshadowing_order": foreshadowing.foreshadowing_order,
            "created_at": foreshadowing.created_at,
            "updated_at": foreshadowing.updated_at
        }
        result.append(convert_to_camel_case(foreshadowing_dict))
    return result

@app.post("/api/novels/{novel_id}/foreshadowings", response_model=List[ForeshadowingResponse])
async def create_foreshadowings(
    novel_id: str,
    foreshadowings_data: List[ForeshadowingCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量创建伏笔"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    current_time = int(time.time() * 1000)
    created_foreshadowings = []
    
    for idx, foreshadowing_data in enumerate(foreshadowings_data):
        foreshadowing = Foreshadowing(
            id=generate_uuid(),
            novel_id=novel_id,
            content=foreshadowing_data.content,
            chapter_id=foreshadowing_data.chapter_id,
            resolved_chapter_id=foreshadowing_data.resolved_chapter_id,
            is_resolved=foreshadowing_data.is_resolved or "false",
            foreshadowing_order=len(novel.foreshadowings) + idx,
            created_at=current_time,
            updated_at=current_time
        )
        db.add(foreshadowing)
        created_foreshadowings.append(foreshadowing)
    
    db.commit()
    
    result = []
    for foreshadowing in created_foreshadowings:
        foreshadowing_dict = {
            "id": foreshadowing.id,
            "novel_id": foreshadowing.novel_id,
            "content": foreshadowing.content,
            "chapter_id": foreshadowing.chapter_id,
            "resolved_chapter_id": foreshadowing.resolved_chapter_id,
            "is_resolved": foreshadowing.is_resolved,
            "foreshadowing_order": foreshadowing.foreshadowing_order,
            "created_at": foreshadowing.created_at,
            "updated_at": foreshadowing.updated_at
        }
        result.append(convert_to_camel_case(foreshadowing_dict))
    return result

@app.put("/api/novels/{novel_id}/foreshadowings/{foreshadowing_id}", response_model=ForeshadowingResponse)
async def update_foreshadowing(
    novel_id: str,
    foreshadowing_id: str,
    foreshadowing_data: ForeshadowingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新伏笔"""
    foreshadowing = db.query(Foreshadowing).join(Novel).filter(
        Foreshadowing.id == foreshadowing_id,
        Foreshadowing.novel_id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not foreshadowing:
        raise HTTPException(status_code=404, detail="伏笔不存在")
    
    if foreshadowing_data.content is not None:
        foreshadowing.content = foreshadowing_data.content
    if foreshadowing_data.chapter_id is not None:
        foreshadowing.chapter_id = foreshadowing_data.chapter_id
    if foreshadowing_data.resolved_chapter_id is not None:
        foreshadowing.resolved_chapter_id = foreshadowing_data.resolved_chapter_id
    if foreshadowing_data.is_resolved is not None:
        foreshadowing.is_resolved = foreshadowing_data.is_resolved
    foreshadowing.updated_at = int(time.time() * 1000)
    
    db.commit()
    db.refresh(foreshadowing)
    
    foreshadowing_dict = {
        "id": foreshadowing.id,
        "novel_id": foreshadowing.novel_id,
        "content": foreshadowing.content,
        "chapter_id": foreshadowing.chapter_id,
        "resolved_chapter_id": foreshadowing.resolved_chapter_id,
        "is_resolved": foreshadowing.is_resolved,
        "foreshadowing_order": foreshadowing.foreshadowing_order,
        "created_at": foreshadowing.created_at,
        "updated_at": foreshadowing.updated_at
    }
    return convert_to_camel_case(foreshadowing_dict)

@app.delete("/api/novels/{novel_id}/foreshadowings/{foreshadowing_id}")
async def delete_foreshadowing(
    novel_id: str,
    foreshadowing_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除伏笔"""
    foreshadowing = db.query(Foreshadowing).join(Novel).filter(
        Foreshadowing.id == foreshadowing_id,
        Foreshadowing.novel_id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not foreshadowing:
        raise HTTPException(status_code=404, detail="伏笔不存在")
    
    db.delete(foreshadowing)
    db.commit()
    return {"message": "伏笔已删除"}

# ==================== 当前小说路由 ====================

@app.get("/api/current-novel", response_model=CurrentNovelResponse)
async def get_current_novel(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户当前选择的小说ID"""
    current_novel = db.query(UserCurrentNovel).filter(
        UserCurrentNovel.user_id == current_user.id
    ).first()
    
    if not current_novel:
        return {"novel_id": None}
    
    return {"novel_id": current_novel.novel_id}

@app.put("/api/current-novel", response_model=CurrentNovelResponse)
async def set_current_novel(
    current_novel_data: CurrentNovelUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """设置用户当前选择的小说ID"""
    # 验证小说是否存在且属于当前用户
    novel = db.query(Novel).filter(
        Novel.id == current_novel_data.novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    current_novel = db.query(UserCurrentNovel).filter(
        UserCurrentNovel.user_id == current_user.id
    ).first()
    
    if current_novel:
        current_novel.novel_id = current_novel_data.novel_id
        current_novel.updated_at = int(time.time() * 1000)
    else:
        current_novel = UserCurrentNovel(
            user_id=current_user.id,
            novel_id=current_novel_data.novel_id,
            updated_at=int(time.time() * 1000)
        )
        db.add(current_novel)
    
    db.commit()
    return {"novel_id": current_novel.novel_id}

# ==================== AI 生成路由 ====================

@app.post("/api/ai/generate-outline")
async def generate_outline(
    request: GenerateOutlineRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成完整大纲和卷结构（任务模式）"""
    # 如果提供了 novel_id，创建任务
    if request.novel_id:
        task = create_task(
            db=db,
            novel_id=request.novel_id,
            user_id=current_user.id,
            task_type="generate_outline",
            task_data={
                "title": request.title,
                "genre": request.genre,
                "synopsis": request.synopsis
            }
        )
        
        # 在后台执行任务
        def execute_task():
            try:
                progress = ProgressCallback(task.id)
                result = generate_full_outline(
                    title=request.title,
                    genre=request.genre,
                    synopsis=request.synopsis,
                    progress_callback=progress
                )
                
                # 更新任务状态
                task_db = SessionLocal()
                try:
                    task_obj = task_db.query(Task).filter(Task.id == task.id).first()
                    if task_obj:
                        task_obj.status = "completed"
                        task_obj.progress = 100
                        task_obj.result = json.dumps(result)
                        task_obj.completed_at = int(time.time() * 1000)
                        task_db.commit()
                finally:
                    task_db.close()
            except Exception as e:
                task_db = SessionLocal()
                try:
                    task_obj = task_db.query(Task).filter(Task.id == task.id).first()
                    if task_obj:
                        task_obj.status = "failed"
                        task_obj.error_message = str(e)
                        task_obj.completed_at = int(time.time() * 1000)
                        task_db.commit()
                finally:
                    task_db.close()
        
        executor = get_task_executor()
        executor.submit(execute_task)
        
        return {
            "task_id": task.id,
            "status": "pending",
            "message": "任务已创建，正在后台执行"
        }
    else:
        # 同步模式（不推荐，但保留兼容性）
        result = generate_full_outline(
            title=request.title,
            genre=request.genre,
            synopsis=request.synopsis
        )
        return result

@app.post("/api/ai/generate-volume-outline")
async def generate_volume_outline(
    request: GenerateVolumeOutlineRequest,
    current_user: User = Depends(get_current_user)
):
    """生成卷详细大纲（流式）"""
    stream = generate_volume_outline_stream(
        novel_title=request.novel_title,
        full_outline=request.full_outline,
        volume_title=request.volume_title,
        volume_summary=request.volume_summary or "",
        characters=request.characters or [],
        volume_index=request.volume_index
    )
    
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/api/ai/generate-chapter-outline", response_model=List[Dict[str, Any]])
async def generate_chapter_outline(
    request: GenerateChapterOutlineRequest,
    current_user: User = Depends(get_current_user)
):
    """生成章节列表"""
    chapters = generate_chapter_outline(
        novel_title=request.novel_title,
        genre=request.genre,
        full_outline=request.full_outline,
        volume_title=request.volume_title,
        volume_summary=request.volume_summary or "",
        volume_outline=request.volume_outline or "",
        characters=request.characters or [],
        volume_index=request.volume_index,
        chapter_count=request.chapter_count
    )
    return convert_to_camel_case(chapters)

class WriteChapterRequestWithNovelId(WriteChapterRequest):
    novel_id: Optional[str] = None  # 可选的小说ID，如果提供则优先使用

@app.post("/api/ai/write-chapter")
async def write_chapter(
    request: WriteChapterRequestWithNovelId,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成章节内容（流式，带智能上下文）"""
    # 查找小说（优先使用 novel_id，否则通过标题查找）
    novel = None
    if request.novel_id:
        novel = db.query(Novel).filter(
            Novel.id == request.novel_id,
            Novel.user_id == current_user.id
        ).first()
    else:
        novel = db.query(Novel).filter(
            Novel.title == request.novel_title,
            Novel.user_id == current_user.id
        ).first()
    
    novel_id = novel.id if novel else None
    
    stream = write_chapter_content_stream(
        novel_title=request.novel_title,
        genre=request.genre,
        synopsis=request.synopsis,
        chapter_title=request.chapter_title,
        chapter_summary=request.chapter_summary,
        chapter_prompt_hints=request.chapter_prompt_hints,
        characters=request.characters or [],
        world_settings=request.world_settings or [],
        previous_chapters_context=request.previous_chapters_context,
        novel_id=novel_id,
        current_chapter_id=None,
        db_session=db
    )
    
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/api/ai/generate-characters")
async def generate_characters_endpoint(
    request: GenerateCharactersRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成角色列表（任务模式）"""
    if request.novel_id:
        task = create_task(
            db=db,
            novel_id=request.novel_id,
            user_id=current_user.id,
            task_type="generate_characters",
            task_data={
                "title": request.title,
                "genre": request.genre,
                "synopsis": request.synopsis,
                "outline": request.outline
            }
        )
        
        def execute_task():
            try:
                progress = ProgressCallback(task.id)
                result = generate_characters(
                    title=request.title,
                    genre=request.genre,
                    synopsis=request.synopsis,
                    outline=request.outline,
                    progress_callback=progress
                )
                
                task_db = SessionLocal()
                try:
                    task_obj = task_db.query(Task).filter(Task.id == task.id).first()
                    if task_obj:
                        task_obj.status = "completed"
                        task_obj.progress = 100
                        task_obj.result = json.dumps(result)
                        task_obj.completed_at = int(time.time() * 1000)
                        task_db.commit()
                finally:
                    task_db.close()
            except Exception as e:
                task_db = SessionLocal()
                try:
                    task_obj = task_db.query(Task).filter(Task.id == task.id).first()
                    if task_obj:
                        task_obj.status = "failed"
                        task_obj.error_message = str(e)
                        task_obj.completed_at = int(time.time() * 1000)
                        task_db.commit()
                finally:
                    task_db.close()
        
        executor = get_task_executor()
        executor.submit(execute_task)
        
        return {
            "task_id": task.id,
            "status": "pending",
            "message": "任务已创建，正在后台执行"
        }
    else:
        result = generate_characters(
            title=request.title,
            genre=request.genre,
            synopsis=request.synopsis,
            outline=request.outline
        )
        return convert_to_camel_case(result)

@app.post("/api/ai/generate-world-settings")
async def generate_world_settings_endpoint(
    request: GenerateWorldSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成世界观设定（任务模式）"""
    if request.novel_id:
        task = create_task(
            db=db,
            novel_id=request.novel_id,
            user_id=current_user.id,
            task_type="generate_world_settings",
            task_data={
                "title": request.title,
                "genre": request.genre,
                "synopsis": request.synopsis,
                "outline": request.outline
            }
        )
        
        def execute_task():
            try:
                progress = ProgressCallback(task.id)
                result = generate_world_settings(
                    title=request.title,
                    genre=request.genre,
                    synopsis=request.synopsis,
                    outline=request.outline,
                    progress_callback=progress
                )
                
                task_db = SessionLocal()
                try:
                    task_obj = task_db.query(Task).filter(Task.id == task.id).first()
                    if task_obj:
                        task_obj.status = "completed"
                        task_obj.progress = 100
                        task_obj.result = json.dumps(result)
                        task_obj.completed_at = int(time.time() * 1000)
                        task_db.commit()
                finally:
                    task_db.close()
            except Exception as e:
                task_db = SessionLocal()
                try:
                    task_obj = task_db.query(Task).filter(Task.id == task.id).first()
                    if task_obj:
                        task_obj.status = "failed"
                        task_obj.error_message = str(e)
                        task_obj.completed_at = int(time.time() * 1000)
                        task_db.commit()
                finally:
                    task_db.close()
        
        executor = get_task_executor()
        executor.submit(execute_task)
        
        return {
            "task_id": task.id,
            "status": "pending",
            "message": "任务已创建，正在后台执行"
        }
    else:
        result = generate_world_settings(
            title=request.title,
            genre=request.genre,
            synopsis=request.synopsis,
            outline=request.outline
        )
        return convert_to_camel_case(result)

@app.post("/api/ai/generate-timeline-events")
async def generate_timeline_events_endpoint(
    request: GenerateTimelineEventsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成时间线事件（任务模式）"""
    if request.novel_id:
        task = create_task(
            db=db,
            novel_id=request.novel_id,
            user_id=current_user.id,
            task_type="generate_timeline_events",
            task_data={
                "title": request.title,
                "genre": request.genre,
                "synopsis": request.synopsis,
                "outline": request.outline
            }
        )
        
        def execute_task():
            try:
                progress = ProgressCallback(task.id)
                result = generate_timeline_events(
                    title=request.title,
                    genre=request.genre,
                    synopsis=request.synopsis,
                    outline=request.outline,
                    progress_callback=progress
                )
                
                task_db = SessionLocal()
                try:
                    task_obj = task_db.query(Task).filter(Task.id == task.id).first()
                    if task_obj:
                        task_obj.status = "completed"
                        task_obj.progress = 100
                        task_obj.result = json.dumps(result)
                        task_obj.completed_at = int(time.time() * 1000)
                        task_db.commit()
                finally:
                    task_db.close()
            except Exception as e:
                task_db = SessionLocal()
                try:
                    task_obj = task_db.query(Task).filter(Task.id == task.id).first()
                    if task_obj:
                        task_obj.status = "failed"
                        task_obj.error_message = str(e)
                        task_obj.completed_at = int(time.time() * 1000)
                        task_db.commit()
                finally:
                    task_db.close()
        
        executor = get_task_executor()
        executor.submit(execute_task)
        
        return {
            "task_id": task.id,
            "status": "pending",
            "message": "任务已创建，正在后台执行"
        }
    else:
        result = generate_timeline_events(
            title=request.title,
            genre=request.genre,
            synopsis=request.synopsis,
            outline=request.outline
        )
        return convert_to_camel_case(result)

@app.post("/api/ai/generate-foreshadowings")
async def generate_foreshadowings_endpoint(
    request: GenerateCharactersRequest,  # 复用相同的请求结构
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成伏笔（任务模式）"""
    if request.novel_id:
        task = create_task(
            db=db,
            novel_id=request.novel_id,
            user_id=current_user.id,
            task_type="generate_foreshadowings",
            task_data={
                "title": request.title,
                "genre": request.genre,
                "synopsis": request.synopsis,
                "outline": request.outline
            }
        )
        
        def execute_task():
            try:
                progress = ProgressCallback(task.id)
                result = generate_foreshadowings_from_outline(
                    title=request.title,
                    genre=request.genre,
                    synopsis=request.synopsis,
                    outline=request.outline,
                    progress_callback=progress
                )
                
                task_db = SessionLocal()
                try:
                    task_obj = task_db.query(Task).filter(Task.id == task.id).first()
                    if task_obj:
                        task_obj.status = "completed"
                        task_obj.progress = 100
                        task_obj.result = json.dumps(result)
                        task_obj.completed_at = int(time.time() * 1000)
                        task_db.commit()
                finally:
                    task_db.close()
            except Exception as e:
                task_db = SessionLocal()
                try:
                    task_obj = task_db.query(Task).filter(Task.id == task.id).first()
                    if task_obj:
                        task_obj.status = "failed"
                        task_obj.error_message = str(e)
                        task_obj.completed_at = int(time.time() * 1000)
                        task_db.commit()
                finally:
                    task_db.close()
        
        executor = get_task_executor()
        executor.submit(execute_task)
        
        return {
            "task_id": task.id,
            "status": "pending",
            "message": "任务已创建，正在后台执行"
        }
    else:
        result = generate_foreshadowings_from_outline(
            title=request.title,
            genre=request.genre,
            synopsis=request.synopsis,
            outline=request.outline
        )
        return convert_to_camel_case(result)

class ExtractForeshadowingsRequest(BaseModel):
    title: str
    genre: str
    chapter_title: str
    chapter_content: str
    existing_foreshadowings: Optional[List[Dict[str, Any]]] = None

@app.post("/api/ai/extract-foreshadowings-from-chapter", response_model=List[Dict[str, Any]])
async def extract_foreshadowings_from_chapter_endpoint(
    request: ExtractForeshadowingsRequest,
    current_user: User = Depends(get_current_user)
):
    """从章节内容提取伏笔"""
    result = extract_foreshadowings_from_chapter(
        title=request.title,
        genre=request.genre,
        chapter_title=request.chapter_title,
        chapter_content=request.chapter_content,
        existing_foreshadowings=request.existing_foreshadowings
    )
    return convert_to_camel_case(result)

@app.post("/api/ai/modify-outline-by-dialogue", response_model=ModifyOutlineByDialogueResponse)
async def modify_outline_by_dialogue_endpoint(
    request: ModifyOutlineByDialogueRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """通过对话修改大纲（任务模式）"""
    novel = db.query(Novel).filter(
        Novel.id == request.novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    task = create_task(
        db=db,
        novel_id=request.novel_id,
        user_id=current_user.id,
        task_type="modify_outline_by_dialogue",
        task_data={
            "user_message": request.user_message
        }
    )
    
    def execute_task():
        try:
            # 获取小说信息
            task_db = SessionLocal()
            try:
                novel_obj = task_db.query(Novel).filter(Novel.id == request.novel_id).first()
                if not novel_obj:
                    raise Exception("小说不存在")
                
                novel_title = novel_obj.title
                novel_genre = novel_obj.genre
                novel_synopsis = novel_obj.synopsis or ""
                novel_outline = novel_obj.full_outline or ""
                
                # 获取角色、世界观、时间线
                characters = [{
                    "name": c.name,
                    "role": c.role,
                    "personality": c.personality
                } for c in novel_obj.characters]
                
                world_settings = [{
                    "title": w.title,
                    "category": w.category,
                    "description": w.description
                } for w in novel_obj.world_settings]
                
                timeline = [{
                    "time": t.time,
                    "event": t.event,
                    "impact": t.impact
                } for t in novel_obj.timeline_events]
            finally:
                task_db.close()
            
            progress = ProgressCallback(task.id)
            result = modify_outline_by_dialogue(
                title=novel_title,
                genre=novel_genre,
                synopsis=novel_synopsis,
                current_outline=novel_outline,
                characters=characters,
                world_settings=world_settings,
                timeline=timeline,
                user_message=request.user_message,
                progress_callback=progress
            )
            
            task_db = SessionLocal()
            try:
                task_obj = task_db.query(Task).filter(Task.id == task.id).first()
                if task_obj:
                    task_obj.status = "completed"
                    task_obj.progress = 100
                    task_obj.result = json.dumps(result)
                    task_obj.completed_at = int(time.time() * 1000)
                    task_db.commit()
            finally:
                task_db.close()
        except Exception as e:
            task_db = SessionLocal()
            try:
                task_obj = task_db.query(Task).filter(Task.id == task.id).first()
                if task_obj:
                    task_obj.status = "failed"
                    task_obj.error_message = str(e)
                    task_obj.completed_at = int(time.time() * 1000)
                    task_db.commit()
            finally:
                task_db.close()
    
    executor = get_task_executor()
    executor.submit(execute_task)
    
    return {
        "task_id": task.id,
        "status": "pending",
        "message": "任务已创建，正在后台执行"
    }

@app.post("/api/ai/expand-text")
async def expand_text(
    text: str,
    context: str,
    current_user: User = Depends(get_current_user)
):
    """扩展文本"""
    from google import genai
    from config import GEMINI_API_KEY
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""请扩展以下文本，使其更加详细和丰富。保持原有的风格和主题。

上下文：{context}

原始文本：{text}

请提供扩展后的文本："""
    
    response = client.models.generate_content(
        model="gemini-3-pro-preview",
        contents=prompt,
        config={
            "temperature": 0.7,
            "max_output_tokens": 4096
        }
    )
    
    expanded_text = response.text if response.text else text
    return {"expanded_text": expanded_text}

@app.post("/api/ai/polish-text")
async def polish_text(
    text: str,
    current_user: User = Depends(get_current_user)
):
    """润色文本"""
    from google import genai
    from config import GEMINI_API_KEY
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""请润色以下文本，使其更加流畅、优美，但保持原意不变。

原始文本：{text}

请提供润色后的文本："""
    
    response = client.models.generate_content(
        model="gemini-3-pro-preview",
        contents=prompt,
        config={
            "temperature": 0.6,
            "max_output_tokens": 4096
        }
    )
    
    polished_text = response.text if response.text else text
    return {"polished_text": polished_text}

# ==================== 任务路由 ====================

# 注意：必须将具体路径放在参数路径之前，否则会被参数路径匹配
@app.get("/api/tasks/active", response_model=List[TaskResponse])
async def get_active_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的活跃任务（pending 或 running）"""
    tasks = db.query(Task).filter(
        Task.user_id == current_user.id,
        Task.status.in_(["pending", "running"])
    ).order_by(Task.created_at.desc()).all()
    
    result = []
    for task in tasks:
        result_data = None
        if task.result:
            try:
                result_data = json.loads(task.result)
            except:
                result_data = task.result
        
        task_dict = {
            "id": task.id,
            "novel_id": task.novel_id,
            "task_type": task.task_type,
            "status": task.status,
            "progress": task.progress,
            "progress_message": task.progress_message,
            "result": result_data,
            "error_message": task.error_message,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at
        }
        result.append(convert_to_camel_case(task_dict))
    return result

@app.get("/api/tasks/novel/{novel_id}", response_model=List[TaskResponse])
async def get_novel_tasks(
    novel_id: str,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取小说的所有任务"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    query = db.query(Task).filter(Task.novel_id == novel_id)
    if status_filter:
        query = query.filter(Task.status == status_filter)
    
    tasks = query.order_by(Task.created_at.desc()).all()
    
    result = []
    for task in tasks:
        result_data = None
        if task.result:
            try:
                result_data = json.loads(task.result)
            except:
                result_data = task.result
        
        task_dict = {
            "id": task.id,
            "novel_id": task.novel_id,
            "task_type": task.task_type,
            "status": task.status,
            "progress": task.progress,
            "progress_message": task.progress_message,
            "result": result_data,
            "error_message": task.error_message,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at
        }
        result.append(convert_to_camel_case(task_dict))
    return result

# ==================== 健康检查 ====================

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "API is running"}

@app.get("/")
async def root():
    """根路径"""
    return {"message": "NovaWrite AI API", "version": "1.0.0", "docs": "/api/docs"}
