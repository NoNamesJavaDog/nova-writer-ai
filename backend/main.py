"""
NovaWrite AI 后端主应用
包含所有 API 路由
"""
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload, selectinload
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
    generate_full_outline, generate_volume_outline_stream, generate_volume_outline as generate_volume_outline_impl,
    generate_chapter_outline as generate_chapter_outline_impl, write_chapter_content_stream,
    write_chapter_content as write_chapter_content_impl,
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

@app.get("/api/novels")  # 移除response_model验证
async def get_novels(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有小说 - 优化版：不加载章节内容"""
    try:
        # 优化：使用selectinload代替joinedload，避免笛卡尔积
        # 加载chapters但不包含content字段，减少内存占用
        novels = db.query(Novel).options(
            selectinload(Novel.volumes).selectinload(Volume.chapters),  # 加载chapters
            selectinload(Novel.characters),
            selectinload(Novel.world_settings),
            selectinload(Novel.timeline_events),
            selectinload(Novel.foreshadowings)
        ).filter(Novel.user_id == current_user.id).order_by(Novel.updated_at.desc()).all()
        result = []
        for novel in novels:
            # 直接手动转换为camelCase，避免schema验证问题
            novel_dict = {
                "id": novel.id,
                "userId": novel.user_id,
                "title": novel.title,
                "genre": novel.genre,
                "synopsis": novel.synopsis or "",
                "fullOutline": novel.full_outline or "",
                "createdAt": novel.created_at,
                "updatedAt": novel.updated_at,
                "volumes": sorted([{
                    "id": v.id,
                    "novelId": v.novel_id,
                    "title": v.title,
                    "summary": v.summary or "",
                    "outline": v.outline or "",
                    "volumeOrder": v.volume_order,
                    "createdAt": v.created_at,
                    "updatedAt": v.updated_at,
                    "chapters": [{
                        "id": ch.id,
                        "title": ch.title,
                        "summary": ch.summary or "",
                        "content": "",  # 不返回章节内容，减少数据量
                        "aiPromptHints": ch.ai_prompt_hints or "",
                    } for ch in sorted(v.chapters, key=lambda c: c.chapter_order)]
                } for v in novel.volumes], key=lambda x: x["volumeOrder"]),
                "characters": [{
                    "id": c.id,
                    "novelId": c.novel_id,
                    "name": c.name,
                    "age": c.age or "",
                    "role": c.role or "",
                    "personality": c.personality or "",
                    "background": c.background or "",
                    "goals": c.goals or "",
                    "characterOrder": c.character_order,
                    "createdAt": c.created_at,
                    "updatedAt": c.updated_at
                } for c in novel.characters],
                "worldSettings": [{
                    "id": w.id,
                    "novelId": w.novel_id,
                    "title": w.title,
                    "description": w.description,
                    "category": w.category,
                    "settingOrder": w.setting_order,
                    "createdAt": w.created_at,
                    "updatedAt": w.updated_at
                } for w in novel.world_settings],
                "timeline": [{  # 改为timeline而不是timeline_events
                    "id": t.id,
                    "novelId": t.novel_id,  # 前端期待camelCase
                    "time": t.time,
                    "event": t.event,
                    "impact": t.impact or "",
                    "eventOrder": t.event_order,
                    "createdAt": t.created_at,
                    "updatedAt": t.updated_at
                } for t in novel.timeline_events],
                "foreshadowings": [{
                    "id": f.id,
                    "novelId": f.novel_id,
                    "content": f.content,
                    "chapterId": f.chapter_id,
                    "resolvedChapterId": f.resolved_chapter_id,
                    "isResolved": f.is_resolved,
                    "foreshadowingOrder": f.foreshadowing_order,
                    "createdAt": f.created_at,
                    "updatedAt": f.updated_at
                } for f in novel.foreshadowings]
            }
            result.append(novel_dict)  # 不使用convert_to_camel_case，已经手动转换
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
        "volumes": sorted([{
            "id": v.id,
            "novel_id": v.novel_id,
            "title": v.title,
            "summary": v.summary or "",
            "outline": v.outline or "",
            "volume_order": v.volume_order,
            "created_at": v.created_at,
            "updated_at": v.updated_at,
            "chapters": sorted([{
                "id": c.id,
                "volume_id": c.volume_id,
                "title": c.title,
                "summary": c.summary or "",
                "content": c.content or "",
                "ai_prompt_hints": c.ai_prompt_hints or "",
                "chapter_order": c.chapter_order,
                "created_at": c.created_at,
                "updated_at": c.updated_at
            } for c in v.chapters], key=lambda x: x["chapter_order"])
        } for v in novel.volumes], key=lambda x: x["volume_order"]),
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
    return novel_dict

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
        
        for volume_index, volume_data in enumerate(volumes_data):
            if not volume_data or not volume_data.get("id"):
                continue
            volume_id = volume_data["id"]
            
            if volume_id in existing_volumes:
                # 更新现有卷
                volume = existing_volumes[volume_id]
                volume.title = volume_data.get("title", "")
                volume.summary = volume_data.get("summary", "")
                volume.outline = volume_data.get("outline", "")
                volume.volume_order = volume_index
                volume.updated_at = current_time
                
                # 同步章节
                chapters_data = volume_data.get("chapters", []) or []
                existing_chapters = {c.id: c for c in volume.chapters}
                chapter_ids = {c.get("id") for c in chapters_data if c and c.get("id")}
                
                for chapter_index, chapter_data in enumerate(chapters_data):
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
                        chapter.chapter_order = chapter_index
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
                            chapter_order=chapter_index,
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
                    volume_order=volume_index,
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
    
    # 按 volume_order 排序
    volumes = sorted(novel.volumes, key=lambda v: v.volume_order)
    
    result = []
    for volume in volumes:
        # 按 chapter_order 排序章节
        chapters = sorted(volume.chapters, key=lambda c: c.chapter_order)
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
            } for c in chapters]
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

@app.post("/api/chapters/{chapter_id}/store-embedding-sync")
async def store_chapter_embedding_sync(
    chapter_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    同步存储章节向量（阻塞直到完成）
    用于批量生成时确保向量及时存储，避免后续章节缺少上下文
    """
    try:
        # 验证章节权限
        chapter = db.query(Chapter).join(Volume).join(Novel).filter(
            Chapter.id == chapter_id,
            Novel.user_id == current_user.id
        ).first()
        
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        if not chapter.content or not chapter.content.strip():
            return {
                "success": True,
                "message": "章节内容为空，跳过向量存储",
                "stored": False
            }
        
        # 同步存储向量（直接调用，不使用后台任务）
        from services.embedding_service import EmbeddingService
        service = EmbeddingService()
        
        service.store_chapter_embedding(
            db=db,
            chapter_id=chapter.id,
            novel_id=chapter.volume.novel_id,
            content=chapter.content
        )
        
        return {
            "success": True,
            "message": "章节向量存储成功",
            "stored": True,
            "chapter_id": chapter_id,
            "content_length": len(chapter.content)
        }
        
    except Exception as e:
        logger.error(f"同步存储章节向量失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"向量存储失败: {str(e)}"
        )

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
    chapters = generate_chapter_outline_impl(
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

@app.post("/api/novels/{novel_id}/generate-complete-outline")
async def generate_complete_outline(
    novel_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成完整大纲（包括卷、角色、世界观、时间线、伏笔）并直接保存到数据库
    前端只需要调用这一个接口，所有业务逻辑都在后端完成
    """
    # 验证小说存在
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 创建任务
    task = create_task(
        db=db,
        novel_id=novel_id,
        user_id=current_user.id,
        task_type="generate_complete_outline",
        task_data={
            "title": novel.title,
            "genre": novel.genre,
            "synopsis": novel.synopsis
        }
    )
    
    # 在后台执行完整的大纲生成流程
    def execute_complete_outline_generation():
        task_db = SessionLocal()
        try:
            logger.info(f"开始生成完整大纲，任务ID: {task.id}，小说ID: {novel_id}")
            
            # 获取小说信息
            novel_obj = task_db.query(Novel).filter(Novel.id == novel_id).first()
            if not novel_obj:
                raise Exception("小说不存在")
            
            current_time = int(time.time() * 1000)
            
            # 清理旧数据，避免重复生成时数据累积
            logger.info("清理旧的大纲数据...")
            task_db.query(Volume).filter(Volume.novel_id == novel_id).delete()
            task_db.query(Character).filter(Character.novel_id == novel_id).delete()
            task_db.query(WorldSetting).filter(WorldSetting.novel_id == novel_id).delete()
            task_db.query(TimelineEvent).filter(TimelineEvent.novel_id == novel_id).delete()
            task_db.query(Foreshadowing).filter(Foreshadowing.novel_id == novel_id).delete()
            task_db.commit()
            logger.info("旧数据清理完成")
            
            # 1. 生成完整大纲和卷结构（20%）
            logger.info("步骤 1/6: 生成完整大纲和卷结构")
            update_task_progress(task_db, task.id, 5, "正在生成完整大纲...")
            outline_result = generate_full_outline(
                title=novel_obj.title,
                genre=novel_obj.genre,
                synopsis=novel_obj.synopsis
            )
            
            # 保存大纲
            novel_obj.full_outline = outline_result.get("outline", "")
            task_db.commit()
            update_task_progress(task_db, task.id, 20, "大纲生成完成")
            
            # 保存卷结构
            volumes_data = outline_result.get("volumes", [])
            for idx, volume_data in enumerate(volumes_data):
                volume = Volume(
                    id=generate_uuid(),
                    novel_id=novel_id,
                    title=volume_data.get("title", f"第{idx+1}卷"),
                    summary=volume_data.get("summary", ""),
                    outline="",
                    volume_order=idx,
                    created_at=current_time,
                    updated_at=current_time
                )
                task_db.add(volume)
            task_db.commit()
            
            # 2. 生成角色（40%）
            logger.info("步骤 2/6: 生成角色")
            update_task_progress(task_db, task.id, 25, "正在生成角色...")
            characters_result = generate_characters(
                title=novel_obj.title,
                genre=novel_obj.genre,
                synopsis=novel_obj.synopsis,
                outline=novel_obj.full_outline
            )
            
            # characters_result 直接是列表，不是字典
            for idx, char_data in enumerate(characters_result):
                character = Character(
                    id=generate_uuid(),
                    novel_id=novel_id,
                    name=char_data.get("name", ""),
                    age=char_data.get("age", ""),
                    role=char_data.get("role", ""),
                    personality=char_data.get("personality", ""),
                    background=char_data.get("background", ""),
                    goals=char_data.get("goals", ""),
                    character_order=idx,
                    created_at=current_time,
                    updated_at=current_time
                )
                task_db.add(character)
            task_db.commit()
            update_task_progress(task_db, task.id, 40, "角色生成完成")
            
            # 3. 生成世界观（60%）
            logger.info("步骤 3/6: 生成世界观")
            update_task_progress(task_db, task.id, 45, "正在生成世界观...")
            world_settings_result = generate_world_settings(
                title=novel_obj.title,
                genre=novel_obj.genre,
                synopsis=novel_obj.synopsis,
                outline=novel_obj.full_outline
            )
            
            # world_settings_result 直接是列表，不是字典
            for idx, ws_data in enumerate(world_settings_result):
                world_setting = WorldSetting(
                    id=generate_uuid(),
                    novel_id=novel_id,
                    title=ws_data.get("title", ""),
                    description=ws_data.get("description", ""),
                    category=ws_data.get("category", "其他"),
                    setting_order=idx,
                    created_at=current_time,
                    updated_at=current_time
                )
                task_db.add(world_setting)
            task_db.commit()
            update_task_progress(task_db, task.id, 60, "世界观生成完成")
            
            # 4. 生成时间线（75%）
            logger.info("步骤 4/6: 生成时间线")
            update_task_progress(task_db, task.id, 65, "正在生成时间线...")
            timeline_result = generate_timeline_events(
                title=novel_obj.title,
                genre=novel_obj.genre,
                synopsis=novel_obj.synopsis,
                outline=novel_obj.full_outline
            )
            
            # timeline_result 直接是列表，不是字典
            for idx, event_data in enumerate(timeline_result):
                timeline_event = TimelineEvent(
                    id=generate_uuid(),
                    novel_id=novel_id,
                    time=event_data.get("time", ""),
                    event=event_data.get("event", ""),
                    impact=event_data.get("impact", ""),
                    event_order=idx,
                    created_at=current_time,
                    updated_at=current_time
                )
                task_db.add(timeline_event)
            task_db.commit()
            update_task_progress(task_db, task.id, 75, "时间线生成完成")
            
            # 5. 生成伏笔（90%）
            logger.info("步骤 5/6: 生成伏笔")
            update_task_progress(task_db, task.id, 80, "正在生成伏笔...")
            foreshadowings_result = generate_foreshadowings_from_outline(
                title=novel_obj.title,
                genre=novel_obj.genre,
                synopsis=novel_obj.synopsis,
                outline=novel_obj.full_outline
            )
            
            # foreshadowings_result 直接是列表，不是字典
            for idx, foreshadowing_data in enumerate(foreshadowings_result):
                foreshadowing = Foreshadowing(
                    id=generate_uuid(),
                    novel_id=novel_id,
                    content=foreshadowing_data.get("content", ""),
                    chapter_id=None,
                    resolved_chapter_id=None,
                    is_resolved="false",
                    foreshadowing_order=idx,
                    created_at=current_time,
                    updated_at=current_time
                )
                task_db.add(foreshadowing)
            task_db.commit()
            update_task_progress(task_db, task.id, 90, "伏笔生成完成")
            
            # 6. 完成任务（100%）
            logger.info("步骤 6/6: 完成")
            task_obj = task_db.query(Task).filter(Task.id == task.id).first()
            if task_obj:
                task_obj.status = "completed"
                task_obj.progress = 100
                task_obj.result = json.dumps({
                    "message": "完整大纲生成成功",
                    "novel_id": novel_id
                })
                task_obj.completed_at = current_time
                task_db.commit()
            
            logger.info(f"完整大纲生成完成，任务ID: {task.id}")
            
        except Exception as e:
            logger.error(f"生成完整大纲失败: {str(e)}", exc_info=True)
            task_obj = task_db.query(Task).filter(Task.id == task.id).first()
            if task_obj:
                task_obj.status = "failed"
                task_obj.error_message = str(e)
                task_obj.completed_at = int(time.time() * 1000)
                task_db.commit()
        finally:
            task_db.close()
    
    # 提交后台任务
    executor = get_task_executor()
    executor.submit(execute_complete_outline_generation)
    
    return {
        "task_id": task.id,
        "status": "pending",
        "message": "完整大纲生成任务已创建，正在后台执行"
    }

@app.post("/api/novels/{novel_id}/volumes/{volume_index}/generate-outline")
async def generate_volume_outline_task(
    novel_id: str,
    volume_index: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成卷详细大纲并直接保存到数据库
    前端只需要调用这一个接口，所有业务逻辑都在后端完成
    """
    # 验证小说存在
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 验证卷存在
    volumes = db.query(Volume).filter(
        Volume.novel_id == novel_id
    ).order_by(Volume.volume_order).all()
    
    if volume_index < 0 or volume_index >= len(volumes):
        raise HTTPException(status_code=404, detail="卷索引无效")
    
    volume = volumes[volume_index]
    
    # 创建任务
    task = create_task(
        db=db,
        novel_id=novel_id,
        user_id=current_user.id,
        task_type="generate_volume_outline",
        task_data={
            "volume_index": volume_index,
            "volume_id": volume.id,
            "volume_title": volume.title
        }
    )
    
    # 在后台执行卷大纲生成
    def execute_volume_outline_generation():
        task_db = SessionLocal()
        try:
            logger.info(f"开始生成卷大纲，任务ID: {task.id}，小说ID: {novel_id}，卷索引: {volume_index}")
            
            # 获取小说和卷信息
            novel_obj = task_db.query(Novel).filter(Novel.id == novel_id).first()
            if not novel_obj:
                raise Exception("小说不存在")
            
            volume_obj = task_db.query(Volume).filter(Volume.id == volume.id).first()
            if not volume_obj:
                raise Exception("卷不存在")
            
            # 获取角色信息
            characters = task_db.query(Character).filter(
                Character.novel_id == novel_id
            ).all()
            characters_data = [{
                "name": c.name,
                "role": c.role
            } for c in characters]
            
            # 创建进度回调
            progress = ProgressCallback(task.id)
            progress.update(10, f"开始生成第 {volume_index + 1} 卷《{volume_obj.title}》的详细大纲...")
            
            # 生成卷大纲
            volume_outline = generate_volume_outline_impl(
                novel_title=novel_obj.title,
                full_outline=novel_obj.full_outline or "",
                volume_title=volume_obj.title,
                volume_summary=volume_obj.summary or "",
                characters=characters_data,
                volume_index=volume_index,
                progress_callback=progress
            )
            
            progress.update(90, "正在保存卷大纲到数据库...")
            
            # 保存卷大纲到数据库
            volume_obj.outline = volume_outline
            volume_obj.updated_at = int(time.time() * 1000)
            task_db.commit()
            
            progress.update(100, "卷大纲生成完成")
            
            # 更新任务状态
            task_obj = task_db.query(Task).filter(Task.id == task.id).first()
            if task_obj:
                task_obj.status = "completed"
                task_obj.progress = 100
                task_obj.progress_message = "卷大纲生成完成"
                task_obj.result = json.dumps({
                    "success": True,
                    "message": "卷大纲已生成并保存",
                    "volume_index": volume_index,
                    "volume_title": volume_obj.title
                })
                task_obj.completed_at = int(time.time() * 1000)
                task_db.commit()
                logger.info(f"卷大纲生成任务完成，任务ID: {task.id}")
        except Exception as e:
            logger.error(f"生成卷大纲失败: {str(e)}", exc_info=True)
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
            raise
    
    executor = get_task_executor()
    executor.submit(execute_volume_outline_generation)
    
    return {
        "task_id": task.id,
        "status": "pending",
        "message": f"卷大纲生成任务已创建，正在后台执行（第 {volume_index + 1} 卷：{volume.title}）"
    }

@app.post("/api/novels/{novel_id}/generate-all-volume-outlines")
async def generate_all_volume_outlines_task(
    novel_id: str,
    force: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    一键生成所有卷的详细大纲并保存到数据库
    - 默认只生成缺失卷大纲的卷；force=true 时会覆盖已存在的卷大纲
    """
    # 验证小说存在
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    volumes = db.query(Volume).filter(
        Volume.novel_id == novel_id
    ).order_by(Volume.volume_order).all()
    if not volumes:
        raise HTTPException(status_code=400, detail="该小说还没有卷结构，请先生成或创建卷")

    task = create_task(
        db=db,
        novel_id=novel_id,
        user_id=current_user.id,
        task_type="generate_all_volume_outlines",
        task_data={
            "force": force,
            "volume_count": len(volumes)
        }
    )

    def execute_all_volume_outlines_generation():
        task_db = SessionLocal()
        try:
            novel_obj = task_db.query(Novel).filter(Novel.id == novel_id).first()
            if not novel_obj:
                raise Exception("小说不存在")
            if not (novel_obj.full_outline or "").strip():
                raise Exception("完整大纲为空，请先生成完整大纲后再生成卷大纲")

            volumes_obj = task_db.query(Volume).filter(
                Volume.novel_id == novel_id
            ).order_by(Volume.volume_order).all()
            if not volumes_obj:
                raise Exception("卷不存在")

            characters = task_db.query(Character).filter(Character.novel_id == novel_id).all()
            characters_data = [{"name": c.name, "role": c.role} for c in characters]

            progress = ProgressCallback(task.id)
            total = len(volumes_obj)
            generated_count = 0
            skipped_count = 0
            progress.update(5, f"准备生成全部卷大纲（共 {total} 卷）...")

            for idx, volume_obj in enumerate(volumes_obj):
                current_progress = 5 + int(((idx) / max(total, 1)) * 90)
                vol_title = volume_obj.title or f"第{volume_obj.volume_order + 1}卷"

                if not force and (volume_obj.outline or "").strip():
                    skipped_count += 1
                    progress.update(current_progress, f"跳过第 {volume_obj.volume_order + 1} 卷《{vol_title}》（已存在卷大纲）")
                    continue

                progress.update(current_progress, f"生成第 {volume_obj.volume_order + 1} 卷《{vol_title}》卷大纲... ({idx + 1}/{total})")
                volume_outline = generate_volume_outline_impl(
                    novel_title=novel_obj.title,
                    full_outline=novel_obj.full_outline or "",
                    volume_title=vol_title,
                    volume_summary=volume_obj.summary or "",
                    characters=characters_data,
                    volume_index=volume_obj.volume_order,
                    progress_callback=None
                )

                volume_obj.outline = volume_outline
                volume_obj.updated_at = int(time.time() * 1000)
                task_db.commit()
                generated_count += 1

            progress.update(95, f"卷大纲生成完成，正在更新任务状态...（生成 {generated_count}，跳过 {skipped_count}）")

            task_obj = task_db.query(Task).filter(Task.id == task.id).first()
            if task_obj:
                task_obj.status = "completed"
                task_obj.progress = 100
                task_obj.progress_message = f"全部卷大纲生成完成（生成 {generated_count}，跳过 {skipped_count}）"
                task_obj.result = json.dumps({
                    "success": True,
                    "message": "全部卷大纲已生成并保存",
                    "generated_count": generated_count,
                    "skipped_count": skipped_count,
                    "volume_count": total,
                    "force": force
                })
                task_obj.completed_at = int(time.time() * 1000)
                task_db.commit()
        except Exception as e:
            logger.error(f"一键生成全部卷大纲失败: {str(e)}", exc_info=True)
            try:
                task_obj = task_db.query(Task).filter(Task.id == task.id).first()
                if task_obj:
                    task_obj.status = "failed"
                    task_obj.error_message = str(e)
                    task_obj.completed_at = int(time.time() * 1000)
                    task_db.commit()
            finally:
                pass
        finally:
            task_db.close()

    executor = get_task_executor()
    executor.submit(execute_all_volume_outlines_generation)

    return {
        "task_id": task.id,
        "status": "pending",
        "message": f"全部卷大纲生成任务已创建，正在后台执行（共 {len(volumes)} 卷）"
    }

@app.post("/api/novels/{novel_id}/generate-all-chapters")
async def generate_all_chapters_task(
    novel_id: str,
    force: bool = Query(False),
    chapter_count: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    一键生成所有卷的章节列表并保存到数据库
    - 默认只生成没有章节的卷；force=true 时会覆盖已存在章节列表
    - chapter_count: 可选，指定“每卷”生成的章节数量（1-50）
    """
    # 验证小说存在
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    volumes = db.query(Volume).filter(
        Volume.novel_id == novel_id
    ).order_by(Volume.volume_order).all()
    if not volumes:
        raise HTTPException(status_code=400, detail="该小说还没有卷结构，请先生成或创建卷")

    if chapter_count is not None and (chapter_count < 1 or chapter_count > 50):
        raise HTTPException(status_code=400, detail="chapter_count 必须在 1-50 之间")

    task = create_task(
        db=db,
        novel_id=novel_id,
        user_id=current_user.id,
        task_type="generate_all_chapters",
        task_data={
            "force": force,
            "chapter_count": chapter_count,
            "volume_count": len(volumes)
        }
    )

    def execute_all_chapters_generation():
        task_db = SessionLocal()
        try:
            novel_obj = task_db.query(Novel).filter(Novel.id == novel_id).first()
            if not novel_obj:
                raise Exception("小说不存在")
            if not (novel_obj.full_outline or "").strip():
                raise Exception("完整大纲为空，请先生成完整大纲后再生成章节列表")

            volumes_obj = task_db.query(Volume).filter(
                Volume.novel_id == novel_id
            ).order_by(Volume.volume_order).all()
            if not volumes_obj:
                raise Exception("卷不存在")

            characters = task_db.query(Character).filter(Character.novel_id == novel_id).all()
            characters_data = [{"name": c.name, "role": c.role} for c in characters]

            progress = ProgressCallback(task.id)
            total = len(volumes_obj)
            generated_volume_count = 0
            skipped_volume_count = 0
            generated_chapter_count = 0
            skipped_chapter_count = 0

            progress.update(5, f"准备生成全部章节列表（共 {total} 卷）...")

            for idx, volume_obj in enumerate(volumes_obj):
                base_progress = 5 + int(((idx) / max(total, 1)) * 90)
                vol_index = volume_obj.volume_order
                vol_title = volume_obj.title or f"第{vol_index + 1}卷"

                existing_chapter_count = task_db.query(Chapter).filter(Chapter.volume_id == volume_obj.id).count()
                if not force and existing_chapter_count > 0:
                    skipped_volume_count += 1
                    skipped_chapter_count += existing_chapter_count
                    progress.update(base_progress, f"跳过第 {vol_index + 1} 卷《{vol_title}》（已存在 {existing_chapter_count} 章）")
                    continue

                # 强制确保存在“卷详细大纲”，否则章节容易不连贯/串卷
                if not (volume_obj.outline or "").strip():
                    progress.update(base_progress, f"本卷缺少卷大纲，正在生成第 {vol_index + 1} 卷《{vol_title}》卷详细大纲...")
                    volume_outline = generate_volume_outline_impl(
                        novel_title=novel_obj.title,
                        full_outline=novel_obj.full_outline or "",
                        volume_title=vol_title,
                        volume_summary=volume_obj.summary or "",
                        characters=characters_data,
                        volume_index=vol_index,
                        progress_callback=None
                    )
                    volume_obj.outline = volume_outline
                    volume_obj.updated_at = int(time.time() * 1000)
                    task_db.commit()

                # 构建“前面卷参考信息”：使用已经落库的章节标题+摘要，确保连贯且不重复
                previous_volumes_info = []
                if vol_index > 0:
                    prev_vols = task_db.query(Volume).filter(
                        Volume.novel_id == novel_id,
                        Volume.volume_order < vol_index
                    ).order_by(Volume.volume_order).all()
                    for prev_vol in prev_vols:
                        prev_chapters = task_db.query(Chapter).filter(
                            Chapter.volume_id == prev_vol.id
                        ).order_by(Chapter.chapter_order).all()
                        previous_volumes_info.append({
                            "title": prev_vol.title,
                            "summary": prev_vol.summary or "",
                            "chapters": [{
                                "title": ch.title,
                                "summary": ch.summary or ""
                            } for ch in prev_chapters]
                        })

                # 构建“后续卷规划（避雷）”：避免把后续卷大事件提前写到本卷
                future_volumes_info = []
                next_vols = task_db.query(Volume).filter(
                    Volume.novel_id == novel_id,
                    Volume.volume_order > vol_index
                ).order_by(Volume.volume_order).limit(3).all()
                for next_vol in next_vols:
                    future_volumes_info.append({
                        "title": next_vol.title,
                        "summary": next_vol.summary or "",
                        "outline": (next_vol.outline or "")[:1200]
                    })

                progress.update(base_progress, f"生成第 {vol_index + 1} 卷《{vol_title}》章节列表... ({idx + 1}/{total})")
                chapters_data = generate_chapter_outline_impl(
                    novel_title=novel_obj.title,
                    genre=novel_obj.genre,
                    full_outline=novel_obj.full_outline or "",
                    volume_title=vol_title,
                    volume_summary=volume_obj.summary or "",
                    volume_outline=volume_obj.outline or "",
                    characters=characters_data,
                    volume_index=vol_index,
                    chapter_count=chapter_count,
                    previous_volumes_info=previous_volumes_info if previous_volumes_info else None,
                    future_volumes_info=future_volumes_info if future_volumes_info else None
                )

                progress.update(base_progress + 5, f"已生成 {len(chapters_data)} 章，正在保存到数据库...")

                # 删除旧章节并写入新章节
                if existing_chapter_count > 0:
                    task_db.query(Chapter).filter(Chapter.volume_id == volume_obj.id).delete()
                    task_db.commit()

                current_time = int(time.time() * 1000)
                for ch_idx, chapter_data in enumerate(chapters_data):
                    chapter = Chapter(
                        id=generate_uuid(),
                        volume_id=volume_obj.id,
                        title=chapter_data.get("title", f"第{ch_idx+1}章"),
                        summary=chapter_data.get("summary", ""),
                        content="",
                        ai_prompt_hints=chapter_data.get("aiPromptHints", ""),
                        chapter_order=ch_idx,
                        created_at=current_time,
                        updated_at=current_time
                    )
                    task_db.add(chapter)
                task_db.commit()

                generated_volume_count += 1
                generated_chapter_count += len(chapters_data)

            progress.update(
                95,
                f"章节列表生成完成，正在更新任务状态...（生成卷 {generated_volume_count}，跳过卷 {skipped_volume_count}）"
            )

            task_obj = task_db.query(Task).filter(Task.id == task.id).first()
            if task_obj:
                task_obj.status = "completed"
                task_obj.progress = 100
                task_obj.progress_message = (
                    f"全部章节列表生成完成（生成卷 {generated_volume_count}，跳过卷 {skipped_volume_count}）"
                )
                task_obj.result = json.dumps({
                    "success": True,
                    "message": "全部章节列表已生成并保存",
                    "generated_volume_count": generated_volume_count,
                    "skipped_volume_count": skipped_volume_count,
                    "generated_chapter_count": generated_chapter_count,
                    "skipped_chapter_count": skipped_chapter_count,
                    "volume_count": total,
                    "force": force,
                    "chapter_count": chapter_count
                })
                task_obj.completed_at = int(time.time() * 1000)
                task_db.commit()
        except Exception as e:
            logger.error(f"一键生成全部章节列表失败: {str(e)}", exc_info=True)
            try:
                task_obj = task_db.query(Task).filter(Task.id == task.id).first()
                if task_obj:
                    task_obj.status = "failed"
                    task_obj.error_message = str(e)
                    task_obj.completed_at = int(time.time() * 1000)
                    task_db.commit()
            finally:
                pass
        finally:
            task_db.close()

    executor = get_task_executor()
    executor.submit(execute_all_chapters_generation)

    return {
        "task_id": task.id,
        "status": "pending",
        "message": f"全部章节列表生成任务已创建，正在后台执行（共 {len(volumes)} 卷）"
    }

@app.post("/api/novels/{novel_id}/volumes/{volume_index}/generate-chapters")
async def generate_chapters_task(
    novel_id: str,
    volume_index: int,
    chapter_count: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成章节列表并直接保存到数据库
    前端只需要调用这一个接口，所有业务逻辑都在后端完成
    """
    # 验证小说存在
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 验证卷存在
    volumes = db.query(Volume).filter(
        Volume.novel_id == novel_id
    ).order_by(Volume.volume_order).all()
    
    if volume_index < 0 or volume_index >= len(volumes):
        raise HTTPException(status_code=404, detail="卷索引无效")
    
    volume = volumes[volume_index]
    
    # 创建任务
    task = create_task(
        db=db,
        novel_id=novel_id,
        user_id=current_user.id,
        task_type="generate_chapters",
        task_data={
            "volume_index": volume_index,
            "volume_id": volume.id,
            "volume_title": volume.title,
            "chapter_count": chapter_count
        }
    )
    
    # 在后台执行章节列表生成
    def execute_chapters_generation():
        task_db = SessionLocal()
        try:
            logger.info(f"开始生成章节列表，任务ID: {task.id}，小说ID: {novel_id}，卷索引: {volume_index}")
            
            # 获取小说和卷信息
            novel_obj = task_db.query(Novel).filter(Novel.id == novel_id).first()
            if not novel_obj:
                raise Exception("小说不存在")
            
            volume_obj = task_db.query(Volume).filter(Volume.id == volume.id).first()
            if not volume_obj:
                raise Exception("卷不存在")

            # 创建进度回调
            progress = ProgressCallback(task.id)
            progress.update(5, f"准备生成第 {volume_index + 1} 卷《{volume_obj.title}》的章节列表...")

            # 强制确保存在“卷详细大纲”：没有卷大纲时，章节列表容易串卷/重复
            if not (volume_obj.outline or "").strip():
                progress.update(8, "检测到本卷尚未生成卷大纲，正在自动生成卷详细大纲以约束章节范围...")
                volume_outline = generate_volume_outline_impl(
                    novel_title=novel_obj.title,
                    full_outline=novel_obj.full_outline or "",
                    volume_title=volume_obj.title,
                    volume_summary=volume_obj.summary or "",
                    characters=[{"name": c.name, "role": c.role} for c in task_db.query(Character).filter(Character.novel_id == novel_id).all()],
                    volume_index=volume_index,
                    progress_callback=progress
                )
                volume_obj.outline = volume_outline
                volume_obj.updated_at = int(time.time() * 1000)
                task_db.commit()
                progress.update(12, "卷详细大纲已自动生成并保存")
            
            # 获取角色信息
            characters = task_db.query(Character).filter(
                Character.novel_id == novel_id
            ).all()
            characters_data = [{
                "name": c.name,
                "role": c.role
            } for c in characters]
            
            # 获取前面卷的信息（用于确保连贯性）
            # 使用向量数据库查找最相关的章节，确保语义连贯
            previous_volumes_info = []
            if volume_index > 0:
                previous_volumes = task_db.query(Volume).filter(
                    Volume.novel_id == novel_id,
                    Volume.volume_order < volume_index
                ).order_by(Volume.volume_order).all()
                
                # 使用向量数据库查找与当前卷大纲最相关的章节
                try:
                    from services.consistency_checker import ConsistencyChecker
                    checker = ConsistencyChecker()
                    
                    # 构建当前卷的查询文本
                    current_volume_query = f"{volume_obj.title} {volume_obj.summary or ''} {volume_obj.outline[:500] if volume_obj.outline else ''}"
                    
                    # 查找语义相关的章节（从所有前面卷中）
                    similar_chapters = checker.embedding_service.find_similar_chapters(
                        db=task_db,
                        novel_id=novel_id,
                        query_text=current_volume_query,
                        exclude_chapter_ids=[],
                        limit=20,  # 获取前20个最相关的章节
                        similarity_threshold=0.5  # 降低阈值，获取更多相关章节
                    )
                    
                    # 按卷分组相关章节
                    volume_chapters_map = {}
                    for sim_ch in similar_chapters:
                        # 获取章节所属的卷
                        chapter_obj = task_db.query(Chapter).filter(Chapter.id == sim_ch["chapter_id"]).first()
                        if chapter_obj:
                            prev_vol_obj = task_db.query(Volume).filter(Volume.id == chapter_obj.volume_id).first()
                            if prev_vol_obj and prev_vol_obj.volume_order < volume_index:
                                vol_key = prev_vol_obj.id
                                if vol_key not in volume_chapters_map:
                                    volume_chapters_map[vol_key] = {
                                        "title": prev_vol_obj.title,
                                        "summary": prev_vol_obj.summary or "",
                                        "chapters": []
                                    }
                                volume_chapters_map[vol_key]["chapters"].append({
                                    "title": sim_ch.get("chapter_title", ""),
                                    "summary": sim_ch.get("chapter_summary", ""),
                                    "similarity": sim_ch.get("similarity", 0)
                                })
                    
                    # 如果向量检索找到了相关章节，使用它们
                    if volume_chapters_map:
                        previous_volumes_info = list(volume_chapters_map.values())
                        logger.info(f"使用向量数据库找到 {len(previous_volumes_info)} 个相关卷的章节")
                    else:
                        # 如果向量检索没找到，回退到获取所有前面卷的章节
                        for prev_vol in previous_volumes:
                            prev_chapters = task_db.query(Chapter).filter(
                                Chapter.volume_id == prev_vol.id
                            ).order_by(Chapter.chapter_order).all()
                            
                            previous_volumes_info.append({
                                "title": prev_vol.title,
                                "summary": prev_vol.summary or "",
                                "chapters": [{
                                    "title": ch.title,
                                    "summary": ch.summary or ""
                                } for ch in prev_chapters]
                            })
                except Exception as e:
                    # 如果向量检索失败，回退到简单方法
                    logger.warning(f"向量检索失败，使用简单方法: {str(e)}")
                    for prev_vol in previous_volumes:
                        prev_chapters = task_db.query(Chapter).filter(
                            Chapter.volume_id == prev_vol.id
                        ).order_by(Chapter.chapter_order).all()
                        
                        previous_volumes_info.append({
                            "title": prev_vol.title,
                            "summary": prev_vol.summary or "",
                            "chapters": [{
                                "title": ch.title,
                                "summary": ch.summary or ""
                            } for ch in prev_chapters]
                        })
            
            # 获取后续卷信息（用于避免把后续卷情节提前写进本卷）
            future_volumes_info = []
            try:
                next_volumes = task_db.query(Volume).filter(
                    Volume.novel_id == novel_id,
                    Volume.volume_order > volume_index
                ).order_by(Volume.volume_order).limit(3).all()
                for next_vol in next_volumes:
                    future_volumes_info.append({
                        "title": next_vol.title,
                        "summary": next_vol.summary or "",
                        "outline": (next_vol.outline or "")[:1200]
                    })
            except Exception as e:
                logger.warning(f"获取后续卷信息失败（继续生成章节）：{str(e)}")

            progress.update(15, f"开始生成第 {volume_index + 1} 卷《{volume_obj.title}》的章节列表...")
            
            # 生成章节列表
            chapters_data = generate_chapter_outline_impl(
                novel_title=novel_obj.title,
                genre=novel_obj.genre,
                full_outline=novel_obj.full_outline or "",
                volume_title=volume_obj.title,
                volume_summary=volume_obj.summary or "",
                volume_outline=volume_obj.outline or "",
                characters=characters_data,
                volume_index=volume_index,
                chapter_count=chapter_count,
                previous_volumes_info=previous_volumes_info if previous_volumes_info else None,
                future_volumes_info=future_volumes_info if future_volumes_info else None
            )
            
            progress.update(80, f"已生成 {len(chapters_data)} 个章节，正在保存到数据库...")
            
            # 删除该卷的旧章节
            task_db.query(Chapter).filter(Chapter.volume_id == volume_obj.id).delete()
            task_db.commit()
            
            # 保存新章节到数据库
            current_time = int(time.time() * 1000)
            for idx, chapter_data in enumerate(chapters_data):
                chapter = Chapter(
                    id=generate_uuid(),
                    volume_id=volume_obj.id,
                    title=chapter_data.get("title", f"第{idx+1}章"),
                    summary=chapter_data.get("summary", ""),
                    content="",
                    ai_prompt_hints=chapter_data.get("aiPromptHints", ""),
                    chapter_order=idx,
                    created_at=current_time,
                    updated_at=current_time
                )
                task_db.add(chapter)
            task_db.commit()
            
            progress.update(100, f"章节列表生成完成，共 {len(chapters_data)} 个章节")
            
            # 更新任务状态
            task_obj = task_db.query(Task).filter(Task.id == task.id).first()
            if task_obj:
                task_obj.status = "completed"
                task_obj.progress = 100
                task_obj.progress_message = f"章节列表生成完成，共 {len(chapters_data)} 个章节"
                task_obj.result = json.dumps({
                    "success": True,
                    "message": "章节列表已生成并保存",
                    "volume_index": volume_index,
                    "volume_title": volume_obj.title,
                    "chapter_count": len(chapters_data)
                })
                task_obj.completed_at = int(time.time() * 1000)
                task_db.commit()
                logger.info(f"章节列表生成任务完成，任务ID: {task.id}")
        except Exception as e:
            logger.error(f"生成章节列表失败: {str(e)}", exc_info=True)
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
            raise
    
    executor = get_task_executor()
    executor.submit(execute_chapters_generation)
    
    return {
        "task_id": task.id,
        "status": "pending",
        "message": f"章节列表生成任务已创建，正在后台执行（第 {volume_index + 1} 卷：{volume.title}）"
    }

def update_task_progress(db: Session, task_id: str, progress: int, message: str):
    """更新任务进度"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.progress = progress
        task.status = "processing" if progress < 100 else "completed"
        db.commit()
        logger.info(f"任务 {task_id} 进度更新: {progress}% - {message}")

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
            progress.update(10, "正在分析修改请求...")
            
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
            
            progress.update(80, "正在保存修改后的数据...")
            
            # 保存修改后的数据到数据库
            task_db = SessionLocal()
            try:
                novel_obj = task_db.query(Novel).filter(Novel.id == request.novel_id).first()
                if novel_obj:
                    current_time = int(time.time() * 1000)
                    update_count = 0
                    
                    # 更新大纲
                    if result.get("outline"):
                        novel_obj.full_outline = result["outline"]
                        novel_obj.updated_at = current_time
                        update_count += 1
                        progress.update(82, "✓ 大纲已更新")
                    
                    # 更新卷结构（如果有修改）
                    if result.get("volumes"):
                        # 不删除旧卷，而是更新已有的卷或添加新卷
                        existing_volumes = task_db.query(Volume).filter(
                            Volume.novel_id == request.novel_id
                        ).order_by(Volume.volume_order).all()
                        
                        # 处理返回的卷数据
                        for idx, vol_data in enumerate(result["volumes"]):
                            if idx < len(existing_volumes):
                                # 更新现有卷
                                vol = existing_volumes[idx]
                                if vol_data.get("title"):
                                    vol.title = vol_data["title"]
                                if vol_data.get("summary"):
                                    vol.summary = vol_data["summary"]
                                if vol_data.get("outline"):
                                    vol.outline = vol_data["outline"]
                                vol.volume_order = idx
                                vol.updated_at = current_time
                            else:
                                # 添加新卷
                                new_volume = Volume(
                                    id=generate_uuid(),
                                    novel_id=request.novel_id,
                                    title=vol_data.get("title", f"第{idx+1}卷"),
                                    summary=vol_data.get("summary", ""),
                                    outline=vol_data.get("outline", ""),
                                    volume_order=idx,
                                    created_at=current_time,
                                    updated_at=current_time
                                )
                                task_db.add(new_volume)
                        
                        # 如果返回的卷数少于现有卷数，删除多余的卷
                        if len(result["volumes"]) < len(existing_volumes):
                            for vol in existing_volumes[len(result["volumes"]):]:
                                task_db.delete(vol)
                        
                        update_count += 1
                        progress.update(84, f"✓ 已更新 {len(result['volumes'])} 个卷")
                    
                    # 更新角色（如果有修改）
                    if result.get("characters"):
                        # 删除旧角色
                        task_db.query(Character).filter(Character.novel_id == request.novel_id).delete()
                        # 添加新角色
                        for idx, char_data in enumerate(result["characters"]):
                            character = Character(
                                id=generate_uuid(),
                                novel_id=request.novel_id,
                                name=char_data.get("name", ""),
                                age=char_data.get("age", ""),
                                role=char_data.get("role", ""),
                                personality=char_data.get("personality", ""),
                                background=char_data.get("background", ""),
                                goals=char_data.get("goals", ""),
                                character_order=idx,
                                created_at=current_time,
                                updated_at=current_time
                            )
                            task_db.add(character)
                        update_count += 1
                        progress.update(87, f"✓ 已更新 {len(result['characters'])} 个角色")
                    
                    # 更新世界观（如果有修改）
                    if result.get("world_settings"):
                        task_db.query(WorldSetting).filter(WorldSetting.novel_id == request.novel_id).delete()
                        for idx, ws_data in enumerate(result["world_settings"]):
                            world_setting = WorldSetting(
                                id=generate_uuid(),
                                novel_id=request.novel_id,
                                title=ws_data.get("title", ""),
                                description=ws_data.get("description", ""),
                                category=ws_data.get("category", "其他"),
                                setting_order=idx,
                                created_at=current_time,
                                updated_at=current_time
                            )
                            task_db.add(world_setting)
                        update_count += 1
                        progress.update(90, f"✓ 已更新 {len(result['world_settings'])} 个世界观设定")
                    
                    # 更新时间线（如果有修改）
                    if result.get("timeline"):
                        task_db.query(TimelineEvent).filter(TimelineEvent.novel_id == request.novel_id).delete()
                        for idx, t_data in enumerate(result["timeline"]):
                            timeline_event = TimelineEvent(
                                id=generate_uuid(),
                                novel_id=request.novel_id,
                                time=t_data.get("time", ""),
                                event=t_data.get("event", ""),
                                impact=t_data.get("impact", ""),
                                event_order=idx,
                                created_at=current_time,
                                updated_at=current_time
                            )
                            task_db.add(timeline_event)
                        update_count += 1
                        progress.update(93, f"✓ 已更新 {len(result['timeline'])} 个时间线事件")
                    
                    task_db.commit()
                    progress.update(95, f"✅ 数据保存成功，共更新了 {update_count} 项内容")
                
                task_obj = task_db.query(Task).filter(Task.id == task.id).first()
                if task_obj:
                    task_obj.status = "completed"
                    task_obj.progress = 100
                    task_obj.progress_message = "大纲修改完成"
                    
                    # 构建返回结果，包含更改说明
                    result_data = {
                        "success": True,
                        "message": "大纲已更新",
                        "changes": result.get("changes", []),  # 包含AI返回的更改说明
                        "updated_items": {
                            "outline": bool(result.get("outline")),
                            "volumes": len(result.get("volumes", [])),
                            "characters": len(result.get("characters", [])),
                            "world_settings": len(result.get("world_settings", [])),
                            "timeline": len(result.get("timeline", []))
                        }
                    }
                    task_obj.result = json.dumps(result_data)
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
        result.append(task_dict)
    return result

@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task_by_id(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个任务详情"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
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
    return task_dict

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
        result.append(task_dict)
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
