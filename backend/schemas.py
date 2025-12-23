"""Pydantic 数据模型"""
from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

# 用户相关
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式：只能包含字母、数字和下划线"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """验证密码强度：至少8位，包含字母和数字"""
        if len(v) < 8:
            raise ValueError('密码长度至少为8位')
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('密码必须包含至少一个字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含至少一个数字')
        return v

class UserLogin(BaseModel):
    username_or_email: str
    password: str
    captcha_id: Optional[str] = None  # 验证码ID
    captcha_code: Optional[str] = None  # 验证码内容

class UserResponse(UserBase):
    id: str
    created_at: int
    last_login_at: Optional[int] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# 角色相关
class CharacterBase(BaseModel):
    name: str
    age: Optional[str] = None
    role: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    goals: Optional[str] = None

class CharacterCreate(CharacterBase):
    pass

class CharacterResponse(CharacterBase):
    id: str
    novel_id: str
    character_order: int
    created_at: int
    updated_at: int
    
    class Config:
        from_attributes = True

# 世界观相关
class WorldSettingBase(BaseModel):
    title: str
    description: str
    category: str
    
    @validator('category')
    def validate_category(cls, v):
        valid_categories = ['地理', '社会', '魔法/科技', '历史', '其他']
        if v not in valid_categories:
            raise ValueError(f'分类必须是以下值之一: {", ".join(valid_categories)}')
        return v

class WorldSettingCreate(WorldSettingBase):
    pass

class WorldSettingResponse(WorldSettingBase):
    id: str
    novel_id: str
    setting_order: int
    created_at: int
    updated_at: int
    
    class Config:
        from_attributes = True

# 时间线相关
class TimelineEventBase(BaseModel):
    time: str
    event: str
    impact: Optional[str] = None

class TimelineEventCreate(TimelineEventBase):
    pass

class TimelineEventResponse(TimelineEventBase):
    id: str
    novel_id: str
    event_order: int
    created_at: int
    updated_at: int
    
    class Config:
        from_attributes = True

# 伏笔相关
class ForeshadowingBase(BaseModel):
    content: str
    chapter_id: Optional[str] = None  # 伏笔产生的章节ID，可为空（大纲阶段生成）
    resolved_chapter_id: Optional[str] = None  # 闭环章节ID
    is_resolved: str = "false"  # "true" 或 "false"

class ForeshadowingCreate(ForeshadowingBase):
    pass

class ForeshadowingResponse(ForeshadowingBase):
    id: str
    novel_id: str
    foreshadowing_order: int
    created_at: int
    updated_at: int
    
    class Config:
        from_attributes = True

# 章节相关
class ChapterBase(BaseModel):
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    ai_prompt_hints: Optional[str] = None

class ChapterCreate(ChapterBase):
    pass

class ChapterResponse(ChapterBase):
    id: str
    volume_id: str
    chapter_order: int
    created_at: int
    updated_at: int
    
    class Config:
        from_attributes = True

# 卷相关
class VolumeBase(BaseModel):
    title: str
    summary: Optional[str] = None
    outline: Optional[str] = None

class VolumeCreate(VolumeBase):
    pass

class VolumeResponse(VolumeBase):
    id: str
    novel_id: str
    volume_order: int
    created_at: int
    updated_at: int
    chapters: List[ChapterResponse] = []
    
    class Config:
        from_attributes = True

# 小说相关
class NovelBase(BaseModel):
    title: str
    genre: str
    synopsis: Optional[str] = None
    full_outline: Optional[str] = None

class NovelCreate(NovelBase):
    pass

class NovelUpdate(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    synopsis: Optional[str] = None
    full_outline: Optional[str] = None

class NovelResponse(NovelBase):
    id: str
    user_id: str
    created_at: int
    updated_at: int
    volumes: List[VolumeResponse] = []
    characters: List[CharacterResponse] = []
    world_settings: List[WorldSettingResponse] = []
    timeline: List[TimelineEventResponse] = []
    
    class Config:
        from_attributes = True

# 当前小说ID
class CurrentNovelResponse(BaseModel):
    novel_id: Optional[str] = None

class CurrentNovelUpdate(BaseModel):
    novel_id: str

# 批量更新相关
class NovelFullUpdate(BaseModel):
    """完整的小说更新（包括所有子项）"""
    title: Optional[str] = None
    genre: Optional[str] = None
    synopsis: Optional[str] = None
    full_outline: Optional[str] = None
    volumes: Optional[List[VolumeCreate]] = None
    characters: Optional[List[CharacterCreate]] = None
    world_settings: Optional[List[WorldSettingCreate]] = None
    timeline: Optional[List[TimelineEventCreate]] = None

# AI 相关
class GenerateOutlineRequest(BaseModel):
    title: str
    genre: str
    synopsis: str
    novel_id: Optional[str] = None  # 小说ID，用于关联任务

class GenerateOutlineResponse(BaseModel):
    outline: str
    volumes: Optional[List[dict]] = None

class GenerateVolumeOutlineRequest(BaseModel):
    novel_title: str
    full_outline: str
    volume_title: str
    volume_summary: Optional[str] = None
    characters: Optional[List[dict]] = None
    volume_index: int

class GenerateChapterOutlineRequest(BaseModel):
    novel_title: str
    genre: str
    full_outline: str
    volume_title: str
    volume_summary: Optional[str] = None
    volume_outline: Optional[str] = None
    characters: Optional[List[dict]] = None
    volume_index: int
    chapter_count: Optional[int] = None

class WriteChapterRequest(BaseModel):
    novel_title: str
    genre: str
    synopsis: str
    chapter_title: str
    chapter_summary: str
    chapter_prompt_hints: str
    characters: Optional[List[dict]] = None
    world_settings: Optional[List[dict]] = None

class GenerateCharactersRequest(BaseModel):
    title: str
    genre: str
    synopsis: str
    outline: str
    novel_id: Optional[str] = None  # 小说ID，用于关联任务

class GenerateWorldSettingsRequest(BaseModel):
    title: str
    genre: str
    synopsis: str
    outline: str
    novel_id: Optional[str] = None  # 小说ID，用于关联任务

class GenerateTimelineEventsRequest(BaseModel):
    title: str
    genre: str
    synopsis: str
    outline: str
    novel_id: Optional[str] = None  # 小说ID，用于关联任务

class ModifyOutlineByDialogueRequest(BaseModel):
    novel_id: str
    user_message: str

class ModifyOutlineByDialogueResponse(BaseModel):
    task_id: str
    status: str
    message: str

# ==================== 任务相关 ====================

class TaskResponse(BaseModel):
    id: str
    novel_id: str
    task_type: str
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    progress_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: int
    updated_at: int
    started_at: Optional[int] = None
    completed_at: Optional[int] = None
    
    class Config:
        from_attributes = True

