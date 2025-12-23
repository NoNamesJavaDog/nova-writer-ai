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
from models import User, Novel, Volume, Chapter, Character, WorldSetting, TimelineEvent, Foreshadowing, UserCurrentNovel, Task
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
    GenerateWorldSettingsRequest, GenerateTimelineEventsRequest,
    ModifyOutlineByDialogueRequest, ModifyOutlineByDialogueResponse,
    TaskResponse
)
from auth import (
    verify_password, get_password_hash, create_access_token, create_refresh_token,
    verify_refresh_token, get_user_by_username_or_email, get_current_user, generate_uuid
)
from captcha import create_captcha, verify_captcha
from auth_helper import (
    reset_fail_counters, increment_password_fail, increment_captcha_fail,
    is_account_locked, requires_captcha, LOCK_DURATION
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
    
    # 检查账户是否存在
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名/邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查账户是否被锁定
    if is_account_locked(user):
        lock_time_left = (user.locked_until - int(time.time() * 1000)) // 1000
        minutes_left = lock_time_left // 60
        seconds_left = lock_time_left % 60
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"账户已被锁定，请在 {minutes_left} 分 {seconds_left} 秒后重试",
        )
    
    # 检查是否需要验证码
    need_captcha = requires_captcha(user)
    if need_captcha:
        if not credentials.captcha_id or not credentials.captcha_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="需要输入验证码",
            )
        
        # 验证验证码
        if not verify_captcha(credentials.captcha_id, credentials.captcha_code):
            increment_captcha_fail(user)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误",
            )
    
    # 验证密码
    if not verify_password(credentials.password, user.password_hash):
        increment_password_fail(user)
        db.commit()
        
        # 如果现在需要验证码，提示用户
        if requires_captcha(user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码错误，需要输入验证码",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名/邮箱或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # 登录成功，重置失败计数器
    reset_fail_counters(user)
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


@app.get("/api/auth/captcha")
async def get_captcha():
    """获取验证码"""
    captcha_id, image_data_url = create_captcha()
    return {
        "captcha_id": captcha_id,
        "image": image_data_url
    }

@app.get("/api/auth/login-status")
async def get_login_status(username_or_email: str, db: Session = Depends(get_db)):
    """检查登录状态（是否需要验证码等）"""
    user = get_user_by_username_or_email(db, username_or_email)
    
    if not user:
        return {
            "requires_captcha": False,
            "locked": False
        }
    
    locked = is_account_locked(user)
    need_captcha = requires_captcha(user)
    
    result = {
        "requires_captcha": need_captcha,
        "locked": locked
    }
    
    if locked:
        lock_time_left = (user.locked_until - int(time.time() * 1000)) // 1000
        minutes_left = lock_time_left // 60
        seconds_left = lock_time_left % 60
        result["lock_message"] = f"账户已被锁定，请在 {minutes_left} 分 {seconds_left} 秒后重试"
    
    return result

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
    
    # 追加模式：从现有最大order+1开始
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


@app.post("/api/volumes/{volume_id}/chapters/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_chapters(
    volume_id: str,
    chapter_ids: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重新排序章节（按照传入的chapter_ids顺序）"""
    volume = db.query(Volume).join(Novel).filter(
        Volume.id == volume_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not volume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="卷不存在")
    
    # 获取所有章节
    chapters = db.query(Chapter).filter(Chapter.volume_id == volume_id).all()
    chapter_dict = {ch.id: ch for ch in chapters}
    
    # 按照传入的顺序更新order
    for idx, chapter_id in enumerate(chapter_ids):
        if chapter_id in chapter_dict:
            chapter_dict[chapter_id].chapter_order = idx
            chapter_dict[chapter_id].updated_at = int(time.time() * 1000)
    
    db.commit()


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
    
    # 允许的分类值（与数据库约束保持一致）
    valid_categories = ['地理', '社会', '魔法/科技', '历史', '其他']
    
    for idx, world_setting_data in enumerate(world_settings_data):
        # 验证并规范化分类值
        category = world_setting_data.category
        if category not in valid_categories:
            # 如果分类不在有效列表中，默认使用"其他"
            category = '其他'
        
        world_setting_id = generate_uuid()
        world_setting = WorldSetting(
            id=world_setting_id,
            novel_id=novel_id,
            title=world_setting_data.title,
            description=world_setting_data.description,
            category=category,
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
    
    # 允许的分类值（与数据库约束保持一致）
    valid_categories = ['地理', '社会', '魔法/科技', '历史', '其他']
    category = world_setting_data.category
    if category not in valid_categories:
        # 如果分类不在有效列表中，默认使用"其他"
        category = '其他'
    
    world_setting.title = world_setting_data.title
    world_setting.description = world_setting_data.description
    world_setting.category = category
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


# ==================== 任务管理 ====================

from task_service import create_task, get_task, get_novel_tasks, get_user_active_tasks, get_task_executor, update_task_progress

# 注意：必须先定义 /api/tasks/active，再定义 /api/tasks/{task_id}，避免路由冲突
@app.get("/api/tasks/active", response_model=List[TaskResponse])
async def get_active_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的活跃任务"""
    tasks = get_user_active_tasks(db, current_user.id)
    
    result_list = []
    import json as json_lib
    for task in tasks:
        result = None
        if task.result:
            try:
                result = json_lib.loads(task.result)
            except:
                pass
        
        result_list.append(TaskResponse(
            id=task.id,
            novel_id=task.novel_id,
            task_type=task.task_type,
            status=task.status,
            progress=task.progress,
            progress_message=task.progress_message,
            result=result,
            error_message=task.error_message,
            created_at=task.created_at,
            updated_at=task.updated_at,
            started_at=task.started_at,
            completed_at=task.completed_at
        ))
    
    return result_list

@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务状态"""
    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此任务")
    
    result = None
    if task.result:
        import json as json_lib
        try:
            result = json_lib.loads(task.result)
        except:
            pass
    
    return TaskResponse(
        id=task.id,
        novel_id=task.novel_id,
        task_type=task.task_type,
        status=task.status,
        progress=task.progress,
        progress_message=task.progress_message,
        result=result,
        error_message=task.error_message,
        created_at=task.created_at,
        updated_at=task.updated_at,
        started_at=task.started_at,
        completed_at=task.completed_at
    )

@app.get("/api/novels/{novel_id}/tasks", response_model=List[TaskResponse])
async def get_novel_task_list(
    novel_id: str,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取小说的任务列表"""
    # 验证小说所有权
    novel = db.query(Novel).filter(
        Novel.id == novel_id,
        Novel.user_id == current_user.id
    ).first()
    
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    tasks = get_novel_tasks(db, novel_id, status)
    
    result_list = []
    import json as json_lib
    for task in tasks:
        result = None
        if task.result:
            try:
                result = json_lib.loads(task.result)
            except:
                pass
        
        result_list.append(TaskResponse(
            id=task.id,
            novel_id=task.novel_id,
            task_type=task.task_type,
            status=task.status,
            progress=task.progress,
            progress_message=task.progress_message,
            result=result,
            error_message=task.error_message,
            created_at=task.created_at,
            updated_at=task.updated_at,
            started_at=task.started_at,
            completed_at=task.completed_at
        ))
    
    return result_list


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
    extract_foreshadowings_from_chapter,
    modify_outline_by_dialogue
)

@app.post("/api/ai/generate-outline")
async def api_generate_outline(
    request: GenerateOutlineRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成完整大纲和卷结构（异步任务模式）"""
    try:
        # 如果没有 novel_id，返回错误（要求前端必须传递）
        if not request.novel_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请求中缺少 novel_id"
            )
        
        # 验证小说所有权
        novel = db.query(Novel).filter(
            Novel.id == request.novel_id,
            Novel.user_id == current_user.id
        ).first()
        
        if not novel:
            raise HTTPException(status_code=404, detail="小说不存在")
        
        # 创建任务
        task_data = {
            "title": request.title,
            "genre": request.genre,
            "synopsis": request.synopsis
        }
        
        task = create_task(
            db=db,
            novel_id=request.novel_id,
            user_id=current_user.id,
            task_type="generate_outline",
            task_data=task_data
        )
        
        # 定义任务执行函数
        def task_function():
            from task_service import ProgressCallback
            progress_callback = ProgressCallback(task.id)
            return generate_full_outline(
                request.title,
                request.genre,
                request.synopsis,
                progress_callback=progress_callback
            )
        
        # 提交任务到后台执行
        executor = get_task_executor()
        executor.submit_task(task.id, task_function)
        
        # 返回任务ID，前端可以通过任务ID查询进度
        return {
            "task_id": task.id,
            "status": task.status,
            "message": "任务已创建，正在后台执行"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建任务失败，请稍后重试" if not DEBUG else str(e)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成角色列表（异步任务模式）"""
    try:
        if not characters_request.novel_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请求中缺少 novel_id"
            )
        
        # 验证小说所有权
        novel = db.query(Novel).filter(
            Novel.id == characters_request.novel_id,
            Novel.user_id == current_user.id
        ).first()
        
        if not novel:
            raise HTTPException(status_code=404, detail="小说不存在")
        
        # 创建任务
        task_data = {
            "title": characters_request.title,
            "genre": characters_request.genre,
            "synopsis": characters_request.synopsis,
            "outline": characters_request.outline
        }
        
        task = create_task(
            db=db,
            novel_id=characters_request.novel_id,
            user_id=current_user.id,
            task_type="generate_characters",
            task_data=task_data
        )
        
        # 定义任务执行函数
        def task_function():
            from task_service import ProgressCallback
            progress_callback = ProgressCallback(task.id)
            return generate_characters(
                characters_request.title,
                characters_request.genre,
                characters_request.synopsis,
                characters_request.outline,
                progress_callback=progress_callback
            )
        
        # 提交任务到后台执行
        executor = get_task_executor()
        executor.submit_task(task.id, task_function)
        
        # 返回任务ID
        return {
            "task_id": task.id,
            "status": task.status,
            "message": "任务已创建，正在后台执行"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建任务失败，请稍后重试" if not DEBUG else str(e)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成时间线事件（异步任务模式）"""
    try:
        if not timeline_request.novel_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请求中缺少 novel_id"
            )
        
        # 验证小说所有权
        novel = db.query(Novel).filter(
            Novel.id == timeline_request.novel_id,
            Novel.user_id == current_user.id
        ).first()
        
        if not novel:
            raise HTTPException(status_code=404, detail="小说不存在")
        
        # 创建任务
        task_data = {
            "title": timeline_request.title,
            "genre": timeline_request.genre,
            "synopsis": timeline_request.synopsis,
            "outline": timeline_request.outline
        }
        
        task = create_task(
            db=db,
            novel_id=timeline_request.novel_id,
            user_id=current_user.id,
            task_type="generate_timeline_events",
            task_data=task_data
        )
        
        # 定义任务执行函数
        def task_function():
            from task_service import ProgressCallback
            progress_callback = ProgressCallback(task.id)
            return generate_timeline_events(
                timeline_request.title,
                timeline_request.genre,
                timeline_request.synopsis,
                timeline_request.outline,
                progress_callback=progress_callback
            )
        
        # 提交任务到后台执行
        executor = get_task_executor()
        executor.submit_task(task.id, task_function)
        
        # 返回任务ID
        return {
            "task_id": task.id,
            "status": task.status,
            "message": "任务已创建，正在后台执行"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建任务失败，请稍后重试" if not DEBUG else str(e)
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

@app.post("/api/ai/modify-outline-by-dialogue", response_model=ModifyOutlineByDialogueResponse)
async def api_modify_outline_by_dialogue(
    request: ModifyOutlineByDialogueRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """通过对话修改大纲（异步任务模式）"""
    try:
        # 验证小说所有权
        novel = db.query(Novel).filter(
            Novel.id == request.novel_id,
            Novel.user_id == current_user.id
        ).first()
        
        if not novel:
            raise HTTPException(status_code=404, detail="小说不存在")
        
        # 准备数据（在会话内显式加载relationship和所有属性，避免延迟加载问题）
        # 使用eager loading或者在会话关闭前访问所有需要的属性
        characters_list = list(novel.characters) if novel.characters else []
        world_settings_list = list(novel.world_settings) if novel.world_settings else []
        timeline_events_list = list(novel.timeline_events) if novel.timeline_events else []
        
        # 在session关闭前提取所有需要的数据到普通变量，避免在后台线程中访问novel对象
        novel_title = novel.title
        novel_genre = novel.genre
        novel_synopsis = novel.synopsis or ""
        novel_full_outline = novel.full_outline or ""
        
        characters_data = [{
            "name": c.name,
            "age": c.age or "",
            "role": c.role or "",
            "personality": c.personality or "",
            "background": c.background or "",
            "goals": c.goals or ""
        } for c in characters_list]
        
        world_settings_data = [{
            "title": w.title,
            "category": w.category,
            "description": w.description
        } for w in world_settings_list]
        
        timeline_data = [{
            "time": t.time,
            "event": t.event,
            "impact": t.impact or ""
        } for t in timeline_events_list]
        
        # 创建任务
        task_data = {
            "user_message": request.user_message,
            "title": novel_title,
            "genre": novel_genre,
            "synopsis": novel_synopsis,
            "current_outline": novel_full_outline
        }
        
        task = create_task(
            db=db,
            novel_id=request.novel_id,
            user_id=current_user.id,
            task_type="modify_outline_by_dialogue",
            task_data=task_data
        )
        
        # 定义任务执行函数（使用提取的值而不是novel对象）
        def task_function():
            from task_service import ProgressCallback
            progress_callback = ProgressCallback(task.id)
            return modify_outline_by_dialogue(
                title=novel_title,
                genre=novel_genre,
                synopsis=novel_synopsis,
                current_outline=novel_full_outline,
                characters=characters_data,
                world_settings=world_settings_data,
                timeline=timeline_data,
                user_message=request.user_message,
                progress_callback=progress_callback
            )
        
        # 提交任务到后台执行
        executor = get_task_executor()
        executor.submit_task(task.id, task_function)
        
        # 返回任务ID
        return {
            "task_id": task.id,
            "status": task.status,
            "message": "任务已创建，正在后台执行"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建任务失败，请稍后重试" if not DEBUG else str(e)
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

