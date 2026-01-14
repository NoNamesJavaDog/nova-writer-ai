"""元数据分析 API"""

import logging
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_ai_provider
from app.core.providers.base import AIServiceProvider
from app.schemas.requests import (
    GenerateCharactersRequest,
    GenerateWorldSettingsRequest,
    GenerateTimelineEventsRequest,
    GenerateCharacterRelationsRequest,
    GenerateForeshadowingsRequest,
    ExtractForeshadowingsRequest,
    ExtractChapterHookRequest,
)
from app.schemas.responses import (
    CharactersResponse,
    WorldSettingsResponse,
    TimelineEventsResponse,
    CharacterRelationsResponse,
    ForeshadowingsResponse,
    ChapterHookResponse,
    CharacterInfo,
    WorldSettingInfo,
    TimelineEventInfo,
    ForeshadowingInfo,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["元数据分析"])


@router.post(
    "/generate-characters",
    response_model=CharactersResponse,
    summary="生成角色列表",
    description="基于小说信息生成主要角色列表",
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"},
    },
)
async def generate_characters(
    request: GenerateCharactersRequest,
    provider: AIServiceProvider = Depends(get_ai_provider),
):
    """生成角色列表"""
    try:
        logger.info(f"开始生成角色列表 - 标题: {request.title}")

        characters = await provider.generate_characters(
            title=request.title,
            genre=request.genre,
            synopsis=request.synopsis,
            outline=request.outline,
        )

        logger.info(f"角色列表生成成功 - 标题: {request.title}, 角色数: {len(characters)}")

        character_list = [
            CharacterInfo(
                name=ch.get("name", ""),
                age=ch.get("age"),
                role=ch.get("role", ""),
                personality=ch.get("personality", ""),
                background=ch.get("background"),
                goals=ch.get("goals"),
            )
            for ch in characters
        ]

        return CharactersResponse(characters=character_list)

    except Exception as e:
        logger.error(f"生成角色列表失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"生成角色列表失败: {str(e)}",
        )


@router.post(
    "/generate-world-settings",
    response_model=WorldSettingsResponse,
    summary="生成世界观设定",
    description="基于小说信息生成世界观设定列表",
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"},
    },
)
async def generate_world_settings(
    request: GenerateWorldSettingsRequest,
    provider: AIServiceProvider = Depends(get_ai_provider),
):
    """生成世界观设定"""
    try:
        logger.info(f"开始生成世界观设定 - 标题: {request.title}")

        settings = await provider.generate_world_settings(
            title=request.title,
            genre=request.genre,
            synopsis=request.synopsis,
            outline=request.outline,
        )

        logger.info(f"世界观设定生成成功 - 标题: {request.title}, 设定数: {len(settings)}")

        setting_list = [
            WorldSettingInfo(
                title=s.get("title", ""),
                category=s.get("category", ""),
                description=s.get("description", ""),
            )
            for s in settings
        ]

        return WorldSettingsResponse(settings=setting_list)

    except Exception as e:
        logger.error(f"生成世界观设定失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"生成世界观设定失败: {str(e)}",
        )


@router.post(
    "/generate-character-relations",
    response_model=CharacterRelationsResponse,
    summary="生成角色关系",
    description="基于小说信息与角色列表生成角色关系",
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"},
    },
)
async def generate_character_relations(
    request: GenerateCharacterRelationsRequest,
    provider: AIServiceProvider = Depends(get_ai_provider),
):
    """生成角色关系"""
    try:
        logger.info(f"开始生成角色关系 - 标题: {request.title}")

        relations = await provider.generate_character_relations(
            title=request.title,
            genre=request.genre,
            synopsis=request.synopsis,
            outline=request.outline,
            characters=request.characters,
        )

        logger.info(f"角色关系生成成功 - 标题: {request.title}, 关系数: {len(relations)}")

        return CharacterRelationsResponse(relations=relations)
    except Exception as e:
        logger.error(f"生成角色关系失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"生成角色关系失败: {str(e)}",
        )


@router.post(
    "/generate-timeline",
    response_model=TimelineEventsResponse,
    summary="生成时间线事件",
    description="基于小说信息生成重要时间线事件列表",
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"},
    },
)
async def generate_timeline_events(
    request: GenerateTimelineEventsRequest,
    provider: AIServiceProvider = Depends(get_ai_provider),
):
    """生成时间线事件"""
    try:
        logger.info(f"开始生成时间线事件 - 标题: {request.title}")

        events = await provider.generate_timeline_events(
            title=request.title,
            genre=request.genre,
            synopsis=request.synopsis,
            outline=request.outline,
        )

        logger.info(f"时间线事件生成成功 - 标题: {request.title}, 事件数: {len(events)}")

        event_list = [
            TimelineEventInfo(
                time=e.get("time", ""),
                event=e.get("event", ""),
                impact=e.get("impact", ""),
            )
            for e in events
        ]

        return TimelineEventsResponse(events=event_list)

    except Exception as e:
        logger.error(f"生成时间线事件失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"生成时间线事件失败: {str(e)}",
        )


@router.post(
    "/generate-foreshadowings",
    response_model=ForeshadowingsResponse,
    summary="生成伏笔列表",
    description="从大纲中生成伏笔列表",
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"},
    },
)
async def generate_foreshadowings(
    request: GenerateForeshadowingsRequest,
    provider: AIServiceProvider = Depends(get_ai_provider),
):
    """从大纲生成伏笔"""
    try:
        logger.info("开始从大纲生成伏笔")

        foreshadowings = await provider.generate_foreshadowings_from_outline(
            full_outline=request.full_outline,
        )

        logger.info(f"伏笔列表生成成功 - 伏笔数: {len(foreshadowings)}")

        foreshadowing_list = [
            ForeshadowingInfo(content=f.get("content", ""))
            for f in foreshadowings
        ]

        return ForeshadowingsResponse(foreshadowings=foreshadowing_list)

    except Exception as e:
        logger.error(f"生成伏笔列表失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"生成伏笔列表失败: {str(e)}",
        )


@router.post(
    "/extract-foreshadowings",
    response_model=ForeshadowingsResponse,
    summary="提取章节伏笔",
    description="从章节内容中提取新出现的伏笔线索",
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"},
    },
)
async def extract_foreshadowings(
    request: ExtractForeshadowingsRequest,
    provider: AIServiceProvider = Depends(get_ai_provider),
):
    """从章节提取伏笔"""
    try:
        logger.info("开始从章节提取伏笔")

        foreshadowings = await provider.extract_foreshadowings_from_chapter(
            chapter_content=request.chapter_content,
        )

        logger.info(f"章节伏笔提取成功 - 伏笔数: {len(foreshadowings)}")

        foreshadowing_list = [
            ForeshadowingInfo(content=f.get("content", ""))
            for f in foreshadowings
        ]

        return ForeshadowingsResponse(foreshadowings=foreshadowing_list)

    except Exception as e:
        logger.error(f"提取章节伏笔失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"提取章节伏笔失败: {str(e)}",
        )


@router.post(
    "/extract-chapter-hook",
    response_model=ChapterHookResponse,
    summary="提取章节钩子",
    description="从章节内容中提取下一章钩子（悬念、转折点等）",
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"},
    },
)
async def extract_chapter_hook(
    request: ExtractChapterHookRequest,
    provider: AIServiceProvider = Depends(get_ai_provider),
):
    """提取章节钩子"""
    try:
        logger.info("开始提取章节钩子")

        hook = await provider.extract_next_chapter_hook(
            chapter_content=request.chapter_content,
        )

        logger.info(f"章节钩子提取成功 - 钩子长度: {len(hook)}")

        return ChapterHookResponse(hook=hook)

    except Exception as e:
        logger.error(f"提取章节钩子失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"提取章节钩子失败: {str(e)}",
        )
