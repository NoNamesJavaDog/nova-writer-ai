"""Pydantic 数据模型"""
from .schemas import (
    # 用户相关
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    RefreshTokenRequest,
    # 小说相关
    NovelCreate,
    NovelUpdate,
    NovelResponse,
    # 卷相关
    VolumeCreate,
    VolumeUpdate,
    VolumeResponse,
    # 章节相关
    ChapterCreate,
    ChapterUpdate,
    ChapterResponse,
    # 角色相关
    CharacterCreate,
    CharacterUpdate,
    CharacterResponse,
    # 世界观相关
    WorldSettingCreate,
    WorldSettingUpdate,
    WorldSettingResponse,
    # 时间线相关
    TimelineEventCreate,
    TimelineEventUpdate,
    TimelineEventResponse,
    # 伏笔相关
    ForeshadowingCreate,
    ForeshadowingUpdate,
    ForeshadowingResponse,
    # 当前小说
    CurrentNovelResponse,
    CurrentNovelUpdate,
    # AI 相关
    GenerateOutlineRequest,
    GenerateVolumeOutlineRequest,
    GenerateChapterOutlineRequest,
    WriteChapterRequest,
    GenerateCharactersRequest,
    GenerateWorldSettingsRequest,
    GenerateTimelineEventsRequest,
    ModifyOutlineByDialogueRequest,
    ModifyOutlineByDialogueResponse,
    # 任务相关
    TaskResponse
)

__all__ = [
    'UserCreate',
    'UserLogin',
    'UserResponse',
    'Token',
    'RefreshTokenRequest',
    'NovelCreate',
    'NovelUpdate',
    'NovelResponse',
    'VolumeCreate',
    'VolumeUpdate',
    'VolumeResponse',
    'ChapterCreate',
    'ChapterUpdate',
    'ChapterResponse',
    'CharacterCreate',
    'CharacterUpdate',
    'CharacterResponse',
    'WorldSettingCreate',
    'WorldSettingUpdate',
    'WorldSettingResponse',
    'TimelineEventCreate',
    'TimelineEventUpdate',
    'TimelineEventResponse',
    'ForeshadowingCreate',
    'ForeshadowingUpdate',
    'ForeshadowingResponse',
    'CurrentNovelResponse',
    'CurrentNovelUpdate',
    'GenerateOutlineRequest',
    'GenerateVolumeOutlineRequest',
    'GenerateChapterOutlineRequest',
    'WriteChapterRequest',
    'GenerateCharactersRequest',
    'GenerateWorldSettingsRequest',
    'GenerateTimelineEventsRequest',
    'ModifyOutlineByDialogueRequest',
    'ModifyOutlineByDialogueResponse',
    'TaskResponse',
]

