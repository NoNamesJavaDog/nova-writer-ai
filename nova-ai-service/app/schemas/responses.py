"""API 响应模型"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ==================== 通用响应 ====================

class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细错误信息")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field("ok", description="服务状态")
    service: str = Field("nova-ai-service", description="服务名称")
    version: str = Field("1.0.0", description="版本号")


# ==================== 大纲生成响应 ====================

class VolumeInfo(BaseModel):
    """卷信息"""
    title: str = Field(..., description="卷标题")
    summary: str = Field(..., description="卷简介")


class FullOutlineResponse(BaseModel):
    """完整大纲响应"""
    outline: str = Field(..., description="完整大纲文本")
    volumes: Optional[List[VolumeInfo]] = Field(None, description="卷结构列表")


class VolumeOutlineResponse(BaseModel):
    """卷详细大纲响应"""
    outline: str = Field(..., description="卷详细大纲文本")


class ModifyOutlineResponse(BaseModel):
    """修改大纲响应"""
    outline: str = Field(..., description="修改后的大纲")
    volumes: Optional[List[Dict]] = Field(None, description="修改后的卷列表")
    characters: Optional[List[Dict]] = Field(None, description="修改后的角色列表")
    world_settings: Optional[List[Dict]] = Field(None, description="修改后的世界观列表")
    timeline: Optional[List[Dict]] = Field(None, description="修改后的时间线列表")
    changes: List[str] = Field(default_factory=list, description="变更说明列表")


# ==================== 章节生成响应 ====================

class ChapterInfo(BaseModel):
    """章节信息"""
    title: str = Field(..., description="章节标题")
    summary: str = Field(..., description="章节摘要")
    aiPromptHints: Optional[str] = Field(None, description="AI 提示")


class ChapterOutlineResponse(BaseModel):
    """章节列表响应"""
    chapters: List[ChapterInfo] = Field(..., description="章节列表")


class ChapterContentResponse(BaseModel):
    """章节内容响应"""
    content: str = Field(..., description="章节内容")


class ChapterSummaryResponse(BaseModel):
    """章节摘要响应"""
    summary: str = Field(..., description="章节摘要")


# ==================== 元数据生成响应 ====================

class CharacterInfo(BaseModel):
    """角色信息"""
    name: str = Field(..., description="角色姓名")
    age: Optional[str] = Field(None, description="年龄")
    role: str = Field(..., description="角色定位")
    personality: str = Field(..., description="性格特征")
    background: Optional[str] = Field(None, description="背景故事")
    goals: Optional[str] = Field(None, description="目标和动机")


class CharactersResponse(BaseModel):
    """角色列表响应"""
    characters: List[CharacterInfo] = Field(..., description="角色列表")


class WorldSettingInfo(BaseModel):
    """世界观设定信息"""
    title: str = Field(..., description="设定标题")
    category: str = Field(..., description="分类")
    description: str = Field(..., description="详细描述")


class WorldSettingsResponse(BaseModel):
    """世界观设定响应"""
    settings: List[WorldSettingInfo] = Field(..., description="世界观设定列表")


class TimelineEventInfo(BaseModel):
    """时间线事件信息"""
    time: str = Field(..., description="时间/年代")
    event: str = Field(..., description="事件标题")
    impact: str = Field(..., description="事件影响")


class TimelineEventsResponse(BaseModel):
    """时间线事件响应"""
    events: List[TimelineEventInfo] = Field(..., description="时间线事件列表")


class ForeshadowingInfo(BaseModel):
    """伏笔信息"""
    content: str = Field(..., description="伏笔内容")


class ForeshadowingsResponse(BaseModel):
    """伏笔列表响应"""
    foreshadowings: List[ForeshadowingInfo] = Field(..., description="伏笔列表")


# ==================== 内容提取响应 ====================

class ChapterHookResponse(BaseModel):
    """章节钩子响应"""
    hook: str = Field(..., description="章节钩子文本")
