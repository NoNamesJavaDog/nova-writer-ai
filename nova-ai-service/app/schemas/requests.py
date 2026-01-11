"""API 请求模型"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ==================== 大纲生成 ====================

class GenerateFullOutlineRequest(BaseModel):
    """生成完整大纲请求"""
    title: str = Field(..., description="小说标题")
    genre: str = Field(..., description="小说类型/体裁")
    synopsis: str = Field(..., description="简介/创意")


class GenerateVolumeOutlineRequest(BaseModel):
    """生成卷详细大纲请求（非流式）"""
    novel_title: str = Field(..., description="小说标题")
    full_outline: str = Field(..., description="完整大纲")
    volume_title: str = Field(..., description="卷标题")
    volume_summary: str = Field("", description="卷简介")
    characters: List[Dict] = Field(default_factory=list, description="角色列表")
    volume_index: int = Field(..., ge=0, description="卷索引（从0开始）")


class GenerateVolumeOutlineStreamRequest(BaseModel):
    """生成卷详细大纲请求（流式）"""
    novel_title: str = Field(..., description="小说标题")
    full_outline: str = Field(..., description="完整大纲")
    volume_title: str = Field(..., description="卷标题")
    volume_summary: str = Field("", description="卷简介")
    characters: List[Dict] = Field(default_factory=list, description="角色列表")
    volume_index: int = Field(..., ge=0, description="卷索引（从0开始）")


class ModifyOutlineByDialogueRequest(BaseModel):
    """通过对话修改大纲请求"""
    outline: str = Field(..., description="当前大纲")
    dialogue_data: Dict[str, Any] = Field(..., description="对话数据（包含 title, genre, synopsis, characters, world_settings, timeline, user_message）")


# ==================== 章节生成 ====================

class GenerateChapterOutlineRequest(BaseModel):
    """生成章节列表请求"""
    novel_title: str = Field(..., description="小说标题")
    genre: str = Field(..., description="小说类型")
    full_outline: str = Field(..., description="完整大纲")
    volume_title: str = Field(..., description="卷标题")
    volume_summary: str = Field("", description="卷简介")
    volume_outline: str = Field(..., description="卷详细大纲")
    characters: List[Dict] = Field(default_factory=list, description="角色列表")
    volume_index: int = Field(..., ge=0, description="卷索引")
    chapter_count: Optional[int] = Field(None, ge=1, description="期望的章节数（可选）")
    previous_volumes_info: Optional[List[Dict]] = Field(None, description="之前卷的信息（可选）")
    future_volumes_info: Optional[List[Dict]] = Field(None, description="未来卷的信息（可选）")


class WriteChapterContentRequest(BaseModel):
    """生成章节内容请求（非流式）"""
    novel_title: str = Field(..., description="小说标题")
    genre: str = Field(..., description="小说类型")
    synopsis: str = Field(..., description="简介")
    chapter_title: str = Field(..., description="章节标题")
    chapter_summary: str = Field(..., description="章节简介")
    chapter_prompt_hints: str = Field("", description="章节提示（额外指导）")
    characters: List[Dict] = Field(default_factory=list, description="角色列表")
    world_settings: List[Dict] = Field(default_factory=list, description="世界观设定列表")
    previous_chapters_context: Optional[str] = Field(None, description="前面章节的上下文（可选）")


class WriteChapterContentStreamRequest(BaseModel):
    """生成章节内容请求（流式）"""
    novel_title: str = Field(..., description="小说标题")
    genre: str = Field(..., description="小说类型")
    synopsis: str = Field(..., description="简介")
    chapter_title: str = Field(..., description="章节标题")
    chapter_summary: str = Field(..., description="章节简介")
    chapter_prompt_hints: str = Field("", description="章节提示（额外指导）")
    characters: List[Dict] = Field(default_factory=list, description="角色列表")
    world_settings: List[Dict] = Field(default_factory=list, description="世界观设定列表")
    previous_chapters_context: Optional[str] = Field(None, description="前面章节的上下文（可选）")


class SummarizeChapterRequest(BaseModel):
    """总结章节内容请求"""
    chapter_title: str = Field(..., description="章节标题")
    chapter_content: str = Field(..., description="章节内容")
    max_len: int = Field(400, ge=100, le=1000, description="最大总结长度")


# ==================== 元数据生成 ====================

class GenerateCharactersRequest(BaseModel):
    """生成角色列表请求"""
    title: str = Field(..., description="小说标题")
    genre: str = Field(..., description="小说类型")
    synopsis: str = Field(..., description="简介")
    outline: str = Field(..., description="大纲")


class GenerateWorldSettingsRequest(BaseModel):
    """生成世界观设定请求"""
    title: str = Field(..., description="小说标题")
    genre: str = Field(..., description="小说类型")
    synopsis: str = Field(..., description="简介")
    outline: str = Field(..., description="大纲")


class GenerateTimelineEventsRequest(BaseModel):
    """生成时间线事件请求"""
    title: str = Field(..., description="小说标题")
    genre: str = Field(..., description="小说类型")
    synopsis: str = Field(..., description="简介")
    outline: str = Field(..., description="大纲")


class GenerateForeshadowingsRequest(BaseModel):
    """从大纲生成伏笔请求"""
    full_outline: str = Field(..., description="完整大纲")


# ==================== 内容提取 ====================

class ExtractForeshadowingsRequest(BaseModel):
    """从章节提取伏笔请求"""
    chapter_content: str = Field(..., description="章节内容")


class ExtractChapterHookRequest(BaseModel):
    """提取章节钩子请求"""
    chapter_content: str = Field(..., description="章节内容")
