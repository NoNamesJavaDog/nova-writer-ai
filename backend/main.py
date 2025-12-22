"""FastAPI 主应用"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional
import time
import json
import traceback

from database import get_db, engine, Base
from models import User, Novel, Volume, Chapter, Character, WorldSetting, TimelineEvent, Foreshadowing, UserCurrentNovel
from schemas import (
    UserCreate, UserLogin, UserResponse, Token, RefreshTokenRequest,
    NovelCreate, NovelUpdate, NovelResponse,
    VolumeCreate, VolumeResponse,
    ChapterCreate, ChapterResponse,
    CharacterCreate, CharacterResponse,
    WorldSettingCreate, WorldSettingResponse,
    TimelineEventCreate, TimelineEventResponse,
    ForeshadowingCreate, ForeshadowingResponse,
    CurrentNovelResponse, CurrentNovelUpdate,
    GenerateOutlineRequest, GenerateOutlineResponse,
    GenerateVolumeOutlineRequest, GenerateChapterOutlineRequest,
    WriteChapterRequest, GenerateCharactersRequest,
    GenerateWorldSettingsRequest, GenerateTimelineEventsRequest
)
from auth import (
    verify_password, get_password_hash, create_access_token, create_refresh_token,
    verify_refresh_token, get_user_by_username_or_email, get_current_user, generate_uuid
)

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="NovaWrite AI API", version="1.0.0")

# CORS配置
from config import CORS_ORIGINS, ENVIRONMENT, DEBUG

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # 从配置文件读取允许的前端地址
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 明确指定允许的 HTTP 方法
    allow_headers=["Content-Type", "Authorization", "Accept"],  # 明确指定允许的请求头
)

# 速率限制
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 安全响应头中间件
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Content-Security-Policy (CSP) - 根据实际需求调整
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    return response

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理，避免泄露敏感信息"""
    # 记录详细错误日志（仅开发环境）
    if DEBUG:
        error_detail = str(exc)
        error_traceback = traceback.format_exc()
        print(f"❌ 错误详情: {error_detail}")
        print(f"❌ 错误堆栈:\n{error_traceback}")
    else:
        error_detail = "内部服务器错误"
    
    # 根据异常类型返回不同的状态码
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    # 生产环境不返回详细错误信息
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": error_detail if DEBUG else "内部服务器错误，请稍后重试"}
    )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


# ==================== 认证相关 ====================

@app.post("/api/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")  # 注册限制：5次/分钟
async def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # Pydantic 会自动验证 username、email 格式和 password 强度
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email.lower())
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已被使用"
        )
    
    # 创建新用户
    user_id = generate_uuid()
    now = int(time.time() * 1000)
    
    user = User(
        id=user_id,
        username=user_data.username,
        email=user_data.email.lower(),
        password_hash=get_password_hash(user_data.password),
        created_at=now,
        last_login_at=None
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 生成访问令牌和刷新令牌
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


@app.post("/api/auth/login", response_model=Token)
@limiter.limit("10/minute")  # 登录限制：10次/分钟，防止暴力破解
async def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = get_user_by_username_or_email(db, credentials.username_or_email)
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名/邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 更新最后登录时间
    user.last_login_at = int(time.time() * 1000)
    db.commit()
    
    # 生成访问令牌和刷新令牌
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


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at
    )


# ==================== 小说相关 ====================

@app.get("/api/novels", response_model=List[NovelResponse])
async def get_novels(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有小说"""
    novels = db.query(Novel).filter(Novel.user_id == current_user.id).order_by(Novel.created_at.desc()).all()
    return novels


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    return novel


@app.post("/api/novels", response_model=NovelResponse, status_code=status.HTTP_201_CREATED)
async def create_novel(
    novel_data: NovelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新小说"""
    novel_id = generate_uuid()
    now = int(time.time() * 1000)
    
    novel = Novel(
        id=novel_id,
        user_id=current_user.id,
        title=novel_data.title or "未命名小说",
        genre=novel_data.genre or "奇幻",
        synopsis=novel_data.synopsis,
        full_outline=novel_data.full_outline,
        created_at=now,
        updated_at=now
    )
    
    db.add(novel)
    db.commit()
    db.refresh(novel)
    
    return novel


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    # 更新字段
    update_data = novel_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(novel, field, value)
    
    novel.updated_at = int(time.time() * 1000)
    db.commit()
    db.refresh(novel)
    
    return novel


@app.delete("/api/novels/{novel_id}", status_code=status.HTTP_204_NO_CONTENT)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    db.delete(novel)
    db.commit()
    return None


# ==================== 卷相关 ====================

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    return novel.volumes


@app.post("/api/novels/{novel_id}/volumes", response_model=VolumeResponse, status_code=status.HTTP_201_CREATED)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    # 获取当前最大order
    max_order = db.query(Volume.volume_order).filter(Volume.novel_id == novel_id).order_by(Volume.volume_order.desc()).first()
    next_order = (max_order[0] + 1) if max_order else 0
    
    volume_id = generate_uuid()
    now = int(time.time() * 1000)
    
    volume = Volume(
        id=volume_id,
        novel_id=novel_id,
        title=volume_data.title,
        summary=volume_data.summary,
        outline=volume_data.outline,
        volume_order=next_order,
        created_at=now,
        updated_at=now
    )
    
    db.add(volume)
    db.commit()
    db.refresh(volume)
    
    return volume


@app.put("/api/novels/{novel_id}/volumes/{volume_id}", response_model=VolumeResponse)
async def update_volume(
    novel_id: str,
    volume_id: str,
    volume_data: VolumeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新卷信息"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    volume = db.query(Volume).filter(
        Volume.id == volume_id,
        Volume.novel_id == novel_id
    ).first()
    
    if not volume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="卷不存在")
    
    volume.title = volume_data.title
    volume.summary = volume_data.summary
    volume.outline = volume_data.outline
    volume.updated_at = int(time.time() * 1000)
    
    db.commit()
    db.refresh(volume)
    
    return volume


@app.delete("/api/novels/{novel_id}/volumes/{volume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_volume(
    novel_id: str,
    volume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除卷"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    volume = db.query(Volume).filter(
        Volume.id == volume_id,
        Volume.novel_id == novel_id
    ).first()
    
    if not volume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="卷不存在")
    
    db.delete(volume)
    db.commit()
    return None


# ==================== 章节相关 ====================

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="卷不存在")
    
    return volume.chapters


@app.post("/api/volumes/{volume_id}/chapters", response_model=List[ChapterResponse], status_code=status.HTTP_201_CREATED)
async def create_chapters(
    volume_id: str,
    chapters_data: List[ChapterCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量创建章节"""
    volume = db.query(Volume).join(Novel).filter(
        Volume.id == volume_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not volume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="卷不存在")
    
    # 获取当前最大order
    max_order = db.query(Chapter.chapter_order).filter(Chapter.volume_id == volume_id).order_by(Chapter.chapter_order.desc()).first()
    next_order = (max_order[0] + 1) if max_order else 0
    
    now = int(time.time() * 1000)
    chapters = []
    
    for idx, chapter_data in enumerate(chapters_data):
        chapter_id = generate_uuid()
        chapter = Chapter(
            id=chapter_id,
            volume_id=volume_id,
            title=chapter_data.title,
            summary=chapter_data.summary,
            content=chapter_data.content,
            ai_prompt_hints=chapter_data.ai_prompt_hints,
            chapter_order=next_order + idx,
            created_at=now,
            updated_at=now
        )
        chapters.append(chapter)
        db.add(chapter)
    
    db.commit()
    
    for chapter in chapters:
        db.refresh(chapter)
    
    return chapters


@app.put("/api/volumes/{volume_id}/chapters/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(
    volume_id: str,
    chapter_id: str,
    chapter_data: ChapterCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新章节信息"""
    volume = db.query(Volume).join(Novel).filter(
        Volume.id == volume_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not volume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="卷不存在")
    
    chapter = db.query(Chapter).filter(
        Chapter.id == chapter_id,
        Chapter.volume_id == volume_id
    ).first()
    
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="章节不存在")
    
    chapter.title = chapter_data.title
    chapter.summary = chapter_data.summary
    chapter.content = chapter_data.content
    chapter.ai_prompt_hints = chapter_data.ai_prompt_hints
    chapter.updated_at = int(time.time() * 1000)
    
    db.commit()
    db.refresh(chapter)
    
    return chapter


@app.delete("/api/volumes/{volume_id}/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chapter(
    volume_id: str,
    chapter_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除章节"""
    volume = db.query(Volume).join(Novel).filter(
        Volume.id == volume_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not volume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="卷不存在")
    
    chapter = db.query(Chapter).filter(
        Chapter.id == chapter_id,
        Chapter.volume_id == volume_id
    ).first()
    
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="章节不存在")
    
    db.delete(chapter)
    db.commit()
    return None


# ==================== 角色相关 ====================

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    return novel.characters


@app.post("/api/novels/{novel_id}/characters", response_model=List[CharacterResponse], status_code=status.HTTP_201_CREATED)
async def create_characters(
    novel_id: str,
    characters_data: List[CharacterCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量创建角色"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    # 获取当前最大order
    max_order = db.query(Character.character_order).filter(Character.novel_id == novel_id).order_by(Character.character_order.desc()).first()
    next_order = (max_order[0] + 1) if max_order else 0
    
    now = int(time.time() * 1000)
    characters = []
    
    for idx, character_data in enumerate(characters_data):
        character_id = generate_uuid()
        character = Character(
            id=character_id,
            novel_id=novel_id,
            name=character_data.name,
            age=character_data.age,
            role=character_data.role,
            personality=character_data.personality,
            background=character_data.background,
            goals=character_data.goals,
            character_order=next_order + idx,
            created_at=now,
            updated_at=now
        )
        characters.append(character)
        db.add(character)
    
    db.commit()
    
    for character in characters:
        db.refresh(character)
    
    return characters


@app.put("/api/novels/{novel_id}/characters/{character_id}", response_model=CharacterResponse)
async def update_character(
    novel_id: str,
    character_id: str,
    character_data: CharacterCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新角色信息"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    character = db.query(Character).filter(
        Character.id == character_id,
        Character.novel_id == novel_id
    ).first()
    
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    
    character.name = character_data.name
    character.age = character_data.age
    character.role = character_data.role
    character.personality = character_data.personality
    character.background = character_data.background
    character.goals = character_data.goals
    character.updated_at = int(time.time() * 1000)
    
    db.commit()
    db.refresh(character)
    
    return character


@app.delete("/api/novels/{novel_id}/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    novel_id: str,
    character_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除角色"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    character = db.query(Character).filter(
        Character.id == character_id,
        Character.novel_id == novel_id
    ).first()
    
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    
    db.delete(character)
    db.commit()
    return None


# ==================== 世界观相关 ====================

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    return novel.world_settings


@app.post("/api/novels/{novel_id}/world-settings", response_model=List[WorldSettingResponse], status_code=status.HTTP_201_CREATED)
async def create_world_settings(
    novel_id: str,
    world_settings_data: List[WorldSettingCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量创建世界观设定"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    # 获取当前最大order
    max_order_result = db.query(WorldSetting.setting_order).filter(WorldSetting.novel_id == novel_id).order_by(WorldSetting.setting_order.desc()).first()
    if max_order_result is not None:
        max_order_value = max_order_result[0] if isinstance(max_order_result, tuple) else max_order_result
        next_order = max_order_value + 1
    else:
        next_order = 0
    
    now = int(time.time() * 1000)
    world_settings = []
    
    for idx, world_setting_data in enumerate(world_settings_data):
        world_setting_id = generate_uuid()
        world_setting = WorldSetting(
            id=world_setting_id,
            novel_id=novel_id,
            title=world_setting_data.title,
            description=world_setting_data.description,
            category=world_setting_data.category,
            setting_order=next_order + idx,
            created_at=now,
            updated_at=now
        )
        world_settings.append(world_setting)
        db.add(world_setting)
    
    db.commit()
    
    for world_setting in world_settings:
        db.refresh(world_setting)
    
    return world_settings


@app.put("/api/novels/{novel_id}/world-settings/{world_setting_id}", response_model=WorldSettingResponse)
async def update_world_setting(
    novel_id: str,
    world_setting_id: str,
    world_setting_data: WorldSettingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新世界观设定"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    world_setting = db.query(WorldSetting).filter(
        WorldSetting.id == world_setting_id,
        WorldSetting.novel_id == novel_id
    ).first()
    
    if not world_setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="世界观设定不存在")
    
    world_setting.title = world_setting_data.title
    world_setting.description = world_setting_data.description
    world_setting.category = world_setting_data.category
    world_setting.updated_at = int(time.time() * 1000)
    
    db.commit()
    db.refresh(world_setting)
    
    return world_setting


@app.delete("/api/novels/{novel_id}/world-settings/{world_setting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_world_setting(
    novel_id: str,
    world_setting_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除世界观设定"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    world_setting = db.query(WorldSetting).filter(
        WorldSetting.id == world_setting_id,
        WorldSetting.novel_id == novel_id
    ).first()
    
    if not world_setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="世界观设定不存在")
    
    db.delete(world_setting)
    db.commit()
    return None


# ==================== 时间线相关 ====================

@app.get("/api/novels/{novel_id}/timeline", response_model=List[TimelineEventResponse])
async def get_timeline_events(
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    return novel.timeline_events


@app.post("/api/novels/{novel_id}/timeline", response_model=List[TimelineEventResponse], status_code=status.HTTP_201_CREATED)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    # 获取当前最大order
    max_order = db.query(TimelineEvent.event_order).filter(TimelineEvent.novel_id == novel_id).order_by(TimelineEvent.event_order.desc()).first()
    next_order = (max_order[0] + 1) if max_order else 0
    
    now = int(time.time() * 1000)
    timeline_events = []
    
    for idx, timeline_event_data in enumerate(timeline_events_data):
        timeline_event_id = generate_uuid()
        timeline_event = TimelineEvent(
            id=timeline_event_id,
            novel_id=novel_id,
            time=timeline_event_data.time,
            event=timeline_event_data.event,
            impact=timeline_event_data.impact,
            event_order=next_order + idx,
            created_at=now,
            updated_at=now
        )
        timeline_events.append(timeline_event)
        db.add(timeline_event)
    
    db.commit()
    
    for timeline_event in timeline_events:
        db.refresh(timeline_event)
    
    return timeline_events


@app.put("/api/novels/{novel_id}/timeline/{timeline_event_id}", response_model=TimelineEventResponse)
async def update_timeline_event(
    novel_id: str,
    timeline_event_id: str,
    timeline_event_data: TimelineEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新时间线事件"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    timeline_event = db.query(TimelineEvent).filter(
        TimelineEvent.id == timeline_event_id,
        TimelineEvent.novel_id == novel_id
    ).first()
    
    if not timeline_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="时间线事件不存在")
    
    timeline_event.time = timeline_event_data.time
    timeline_event.event = timeline_event_data.event
    timeline_event.impact = timeline_event_data.impact
    timeline_event.updated_at = int(time.time() * 1000)
    
    db.commit()
    db.refresh(timeline_event)
    
    return timeline_event


@app.delete("/api/novels/{novel_id}/timeline/{timeline_event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timeline_event(
    novel_id: str,
    timeline_event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除时间线事件"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    timeline_event = db.query(TimelineEvent).filter(
        TimelineEvent.id == timeline_event_id,
        TimelineEvent.novel_id == novel_id
    ).first()
    
    if not timeline_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="时间线事件不存在")
    
    db.delete(timeline_event)
    db.commit()
    return None


# ==================== 伏笔相关 ====================

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    return novel.foreshadowings


@app.post("/api/novels/{novel_id}/foreshadowings", response_model=List[ForeshadowingResponse], status_code=status.HTTP_201_CREATED)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    # 验证章节ID是否属于该小说（如果提供了chapter_id）
    if any(f.chapter_id for f in foreshadowings_data):
        chapter_ids = [f.chapter_id for f in foreshadowings_data if f.chapter_id]
        if chapter_ids:
            chapters = db.query(Chapter).join(Volume).filter(
                Chapter.id.in_(chapter_ids),
                Volume.novel_id == novel_id
            ).all()
            valid_chapter_ids = {c.id for c in chapters}
            for f in foreshadowings_data:
                if f.chapter_id and f.chapter_id not in valid_chapter_ids:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"章节ID {f.chapter_id} 不属于该小说")
    
    # 验证闭环章节ID（如果提供了resolved_chapter_id）
    if any(f.resolved_chapter_id for f in foreshadowings_data):
        resolved_chapter_ids = [f.resolved_chapter_id for f in foreshadowings_data if f.resolved_chapter_id]
        if resolved_chapter_ids:
            chapters = db.query(Chapter).join(Volume).filter(
                Chapter.id.in_(resolved_chapter_ids),
                Volume.novel_id == novel_id
            ).all()
            valid_chapter_ids = {c.id for c in chapters}
            for f in foreshadowings_data:
                if f.resolved_chapter_id and f.resolved_chapter_id not in valid_chapter_ids:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"闭环章节ID {f.resolved_chapter_id} 不属于该小说")
    
    # 获取当前最大order
    max_order_result = db.query(Foreshadowing.foreshadowing_order).filter(Foreshadowing.novel_id == novel_id).order_by(Foreshadowing.foreshadowing_order.desc()).first()
    if max_order_result is not None:
        max_order_value = max_order_result[0] if isinstance(max_order_result, tuple) else max_order_result
        next_order = max_order_value + 1
    else:
        next_order = 0
    
    now = int(time.time() * 1000)
    foreshadowings = []
    
    for idx, foreshadowing_data in enumerate(foreshadowings_data):
        foreshadowing_id = generate_uuid()
        foreshadowing = Foreshadowing(
            id=foreshadowing_id,
            novel_id=novel_id,
            chapter_id=foreshadowing_data.chapter_id,
            resolved_chapter_id=foreshadowing_data.resolved_chapter_id,
            content=foreshadowing_data.content,
            is_resolved=foreshadowing_data.is_resolved or "false",
            foreshadowing_order=next_order + idx,
            created_at=now,
            updated_at=now
        )
        foreshadowings.append(foreshadowing)
        db.add(foreshadowing)
    
    db.commit()
    
    for foreshadowing in foreshadowings:
        db.refresh(foreshadowing)
    
    return foreshadowings


@app.put("/api/novels/{novel_id}/foreshadowings/{foreshadowing_id}", response_model=ForeshadowingResponse)
async def update_foreshadowing(
    novel_id: str,
    foreshadowing_id: str,
    foreshadowing_data: ForeshadowingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新伏笔（包括标记闭环）"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    foreshadowing = db.query(Foreshadowing).filter(
        Foreshadowing.id == foreshadowing_id,
        Foreshadowing.novel_id == novel_id
    ).first()
    
    if not foreshadowing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="伏笔不存在")
    
    # 验证章节ID
    if foreshadowing_data.chapter_id:
        chapter = db.query(Chapter).join(Volume).filter(
            Chapter.id == foreshadowing_data.chapter_id,
            Volume.novel_id == novel_id
        ).first()
        if not chapter:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="章节ID不属于该小说")
    
    # 验证闭环章节ID
    if foreshadowing_data.resolved_chapter_id:
        chapter = db.query(Chapter).join(Volume).filter(
            Chapter.id == foreshadowing_data.resolved_chapter_id,
            Volume.novel_id == novel_id
        ).first()
        if not chapter:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="闭环章节ID不属于该小说")
    
    foreshadowing.content = foreshadowing_data.content
    foreshadowing.chapter_id = foreshadowing_data.chapter_id
    foreshadowing.resolved_chapter_id = foreshadowing_data.resolved_chapter_id
    foreshadowing.is_resolved = foreshadowing_data.is_resolved or "false"
    foreshadowing.updated_at = int(time.time() * 1000)
    
    db.commit()
    db.refresh(foreshadowing)
    
    return foreshadowing


@app.delete("/api/novels/{novel_id}/foreshadowings/{foreshadowing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_foreshadowing(
    novel_id: str,
    foreshadowing_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除伏笔"""
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    foreshadowing = db.query(Foreshadowing).filter(
        Foreshadowing.id == foreshadowing_id,
        Foreshadowing.novel_id == novel_id
    ).first()
    
    if not foreshadowing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="伏笔不存在")
    
    db.delete(foreshadowing)
    db.commit()
    return None


# ==================== 当前小说ID ====================

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
        return CurrentNovelResponse(novel_id=None)
    
    return CurrentNovelResponse(novel_id=current_novel.novel_id)


@app.put("/api/current-novel", response_model=CurrentNovelResponse)
async def set_current_novel(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """设置用户当前选择的小说ID"""
    novel_id = data.get("novel_id")
    if not novel_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少 novel_id 参数")
    
    # 验证小说是否存在且属于当前用户
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    
    current_novel = db.query(UserCurrentNovel).filter(
        UserCurrentNovel.user_id == current_user.id
    ).first()
    
    now = int(time.time() * 1000)
    
    if current_novel:
        current_novel.novel_id = novel_id
        current_novel.updated_at = now
    else:
        current_novel = UserCurrentNovel(
            user_id=current_user.id,
            novel_id=novel_id,
            updated_at=now
        )
        db.add(current_novel)
    
    db.commit()
    db.refresh(current_novel)
    
    return CurrentNovelResponse(novel_id=current_novel.novel_id)


# ==================== AI 相关 ====================

from gemini_service import (
    generate_full_outline,
    generate_volume_outline_stream,
    generate_chapter_outline,
    write_chapter_content_stream,
    generate_characters,
    generate_world_settings,
    generate_timeline_events,
    generate_foreshadowings_from_outline,
    extract_foreshadowings_from_chapter
)

@app.post("/api/ai/generate-outline", response_model=GenerateOutlineResponse)
async def api_generate_outline(
    request: GenerateOutlineRequest,
    current_user: User = Depends(get_current_user)
):
    """生成完整大纲和卷结构"""
    try:
        # 在后台任务中执行，避免阻塞
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = await loop.run_in_executor(
            None,
            generate_full_outline,
            request.title,
            request.genre,
            request.synopsis
        )
        return GenerateOutlineResponse(
            outline=result["outline"],
            volumes=result.get("volumes")
        )
    except Exception as e:
        # 不泄露详细错误信息（全局异常处理器会处理）
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成大纲失败，请稍后重试" if not DEBUG else str(e)
        )

@app.post("/api/ai/generate-volume-outline")
@limiter.limit("20/hour")  # AI 接口限制：20次/小时
async def api_generate_volume_outline(
    request: Request,
    volume_request: GenerateVolumeOutlineRequest,
    current_user: User = Depends(get_current_user)
):
    """生成卷详细大纲（流式）"""
    try:
        async def generate():
            stream = generate_volume_outline_stream(
                novel_title=volume_request.novel_title,
                full_outline=volume_request.full_outline,
                volume_title=volume_request.volume_title,
                volume_summary=volume_request.volume_summary or "",
                characters=volume_request.characters or [],
                volume_index=volume_request.volume_index
            )
            for chunk in stream:
                yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"
            yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    except Exception as e:
        # 不泄露详细错误信息（全局异常处理器会处理）
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成大纲失败，请稍后重试" if not DEBUG else str(e)
        )

@app.post("/api/ai/generate-chapter-outline")
@limiter.limit("20/hour")  # AI 接口限制：20次/小时
async def api_generate_chapter_outline(
    request: Request,
    chapter_request: GenerateChapterOutlineRequest,
    current_user: User = Depends(get_current_user)
):
    """生成章节列表"""
    try:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        chapters = await loop.run_in_executor(
            None,
            generate_chapter_outline,
            chapter_request.novel_title,
            chapter_request.genre,
            chapter_request.full_outline,
            chapter_request.volume_title,
            chapter_request.volume_summary or "",
            chapter_request.volume_outline or "",
            chapter_request.characters or [],
            chapter_request.volume_index,
            chapter_request.chapter_count
        )
        return chapters
    except Exception as e:
        # 不泄露详细错误信息（全局异常处理器会处理）
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成大纲失败，请稍后重试" if not DEBUG else str(e)
        )

@app.post("/api/ai/write-chapter")
@limiter.limit("30/hour")  # AI 接口限制：30次/小时
async def api_write_chapter(
    request: Request,
    write_request: WriteChapterRequest,
    current_user: User = Depends(get_current_user)
):
    """生成章节内容（流式）"""
    try:
        async def generate():
            stream = write_chapter_content_stream(
                novel_title=write_request.novel_title,
                genre=write_request.genre,
                synopsis=write_request.synopsis,
                chapter_title=write_request.chapter_title,
                chapter_summary=write_request.chapter_summary,
                chapter_prompt_hints=write_request.chapter_prompt_hints,
                characters=write_request.characters or [],
                world_settings=write_request.world_settings or []
            )
            for chunk in stream:
                yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"
            yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    except Exception as e:
        # 不泄露详细错误信息（全局异常处理器会处理）
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成大纲失败，请稍后重试" if not DEBUG else str(e)
        )

@app.post("/api/ai/generate-characters")
@limiter.limit("20/hour")  # AI 接口限制：20次/小时
async def api_generate_characters(
    request: Request,
    characters_request: GenerateCharactersRequest,
    current_user: User = Depends(get_current_user)
):
    """生成角色列表"""
    try:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        characters = await loop.run_in_executor(
            None,
            generate_characters,
            characters_request.title,
            characters_request.genre,
            characters_request.synopsis,
            characters_request.outline
        )
        return characters
    except Exception as e:
        # 不泄露详细错误信息（全局异常处理器会处理）
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成大纲失败，请稍后重试" if not DEBUG else str(e)
        )

@app.post("/api/ai/generate-world-settings")
@limiter.limit("20/hour")  # AI 接口限制：20次/小时
async def api_generate_world_settings(
    request: Request,
    world_request: GenerateWorldSettingsRequest,
    current_user: User = Depends(get_current_user)
):
    """生成世界观设定"""
    try:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        settings = await loop.run_in_executor(
            None,
            generate_world_settings,
            world_request.title,
            world_request.genre,
            world_request.synopsis,
            world_request.outline
        )
        return settings
    except Exception as e:
        # 不泄露详细错误信息（全局异常处理器会处理）
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成大纲失败，请稍后重试" if not DEBUG else str(e)
        )

@app.post("/api/ai/generate-timeline-events")
@limiter.limit("20/hour")  # AI 接口限制：20次/小时
async def api_generate_timeline_events(
    request: Request,
    timeline_request: GenerateTimelineEventsRequest,
    current_user: User = Depends(get_current_user)
):
    """生成时间线事件"""
    try:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        events = await loop.run_in_executor(
            None,
            generate_timeline_events,
            timeline_request.title,
            timeline_request.genre,
            timeline_request.synopsis,
            timeline_request.outline
        )
        return events
    except Exception as e:
        # 不泄露详细错误信息（全局异常处理器会处理）
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成大纲失败，请稍后重试" if not DEBUG else str(e)
        )

@app.post("/api/ai/generate-foreshadowings")
@limiter.limit("20/hour")  # AI 接口限制：20次/小时
async def api_generate_foreshadowings(
    request: Request,
    foreshadowings_request: GenerateWorldSettingsRequest,  # 复用相同的请求结构
    current_user: User = Depends(get_current_user)
):
    """从大纲生成伏笔"""
    try:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        foreshadowings = await loop.run_in_executor(
            None,
            generate_foreshadowings_from_outline,
            foreshadowings_request.title,
            foreshadowings_request.genre,
            foreshadowings_request.synopsis,
            foreshadowings_request.outline
        )
        return foreshadowings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成伏笔失败，请稍后重试" if not DEBUG else str(e)
        )

@app.post("/api/ai/extract-foreshadowings-from-chapter")
@limiter.limit("30/hour")  # AI 接口限制：30次/小时
async def api_extract_foreshadowings_from_chapter(
    request: Request,
    extract_request: dict,  # {"title": str, "genre": str, "chapter_title": str, "chapter_content": str, "existing_foreshadowings": list}
    current_user: User = Depends(get_current_user)
):
    """从章节内容提取伏笔"""
    try:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        foreshadowings = await loop.run_in_executor(
            None,
            extract_foreshadowings_from_chapter,
            extract_request.get("title", ""),
            extract_request.get("genre", ""),
            extract_request.get("chapter_title", ""),
            extract_request.get("chapter_content", ""),
            extract_request.get("existing_foreshadowings", [])
        )
        return foreshadowings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="提取伏笔失败，请稍后重试" if not DEBUG else str(e)
        )


@app.get("/")
async def root():
    """根路径"""
    return {"message": "NovaWrite AI API", "version": "1.0.0"}

