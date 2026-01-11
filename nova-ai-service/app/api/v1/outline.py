"""大纲生成 API"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_ai_provider
from app.core.providers.base import AIServiceProvider
from app.schemas.requests import (
    GenerateFullOutlineRequest,
    GenerateVolumeOutlineRequest,
    GenerateVolumeOutlineStreamRequest,
    ModifyOutlineByDialogueRequest
)
from app.schemas.responses import (
    FullOutlineResponse,
    VolumeOutlineResponse,
    ModifyOutlineResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/outline", tags=["大纲生成"])


@router.post(
    "/generate-full",
    response_model=FullOutlineResponse,
    summary="生成完整大纲",
    description="生成小说的完整大纲和卷结构（非流式）",
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def generate_full_outline(
    request: GenerateFullOutlineRequest,
    provider: AIServiceProvider = Depends(get_ai_provider)
):
    """生成完整大纲

    Args:
        request: 包含小说标题、类型和简介的请求
        provider: AI 提供商实例（依赖注入）

    Returns:
        FullOutlineResponse: 包含完整大纲和卷结构的响应

    Raises:
        HTTPException: 当生成失败时抛出 500 错误
    """
    try:
        logger.info(f"开始生成完整大纲 - 标题: {request.title}, 类型: {request.genre}")

        result = await provider.generate_full_outline(
            title=request.title,
            genre=request.genre,
            synopsis=request.synopsis
        )

        logger.info(f"完整大纲生成成功 - 标题: {request.title}")

        return FullOutlineResponse(
            outline=result["outline"],
            volumes=result.get("volumes")
        )

    except Exception as e:
        logger.error(f"生成完整大纲失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"生成完整大纲失败: {str(e)}"
        )


@router.post(
    "/generate-volume",
    response_model=VolumeOutlineResponse,
    summary="生成卷大纲",
    description="生成卷的详细大纲（非流式）",
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def generate_volume_outline(
    request: GenerateVolumeOutlineRequest,
    provider: AIServiceProvider = Depends(get_ai_provider)
):
    """生成卷详细大纲（非流式）

    Args:
        request: 包含小说标题、完整大纲、卷信息等的请求
        provider: AI 提供商实例（依赖注入）

    Returns:
        VolumeOutlineResponse: 包含卷详细大纲的响应

    Raises:
        HTTPException: 当生成失败时抛出 500 错误
    """
    try:
        logger.info(f"开始生成卷大纲 - 小说: {request.novel_title}, 卷: {request.volume_title}")

        outline = await provider.generate_volume_outline(
            novel_title=request.novel_title,
            full_outline=request.full_outline,
            volume_title=request.volume_title,
            volume_summary=request.volume_summary,
            characters=request.characters,
            volume_index=request.volume_index
        )

        logger.info(f"卷大纲生成成功 - 卷: {request.volume_title}")

        return VolumeOutlineResponse(outline=outline)

    except Exception as e:
        logger.error(f"生成卷大纲失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"生成卷大纲失败: {str(e)}"
        )


@router.post(
    "/generate-volume-stream",
    summary="流式生成卷大纲",
    description="流式生成卷的详细大纲（返回 SSE 流）",
    responses={
        200: {
            "description": "成功返回流式响应",
            "content": {
                "text/event-stream": {
                    "example": 'data: {"chunk": "大纲内容..."}\n\ndata: {"done": true}\n\n'
                }
            }
        },
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def generate_volume_outline_stream(
    request: GenerateVolumeOutlineStreamRequest,
    provider: AIServiceProvider = Depends(get_ai_provider)
):
    """流式生成卷详细大纲

    Args:
        request: 包含小说标题、完整大纲、卷信息等的请求
        provider: AI 提供商实例（依赖注入）

    Returns:
        StreamingResponse: SSE 格式的流式响应

    Raises:
        HTTPException: 当生成失败时抛出 500 错误
    """
    try:
        logger.info(f"开始流式生成卷大纲 - 小说: {request.novel_title}, 卷: {request.volume_title}")

        async def stream_generator():
            """流式生成器"""
            try:
                async for chunk in provider.generate_volume_outline_stream(
                    novel_title=request.novel_title,
                    full_outline=request.full_outline,
                    volume_title=request.volume_title,
                    volume_summary=request.volume_summary,
                    characters=request.characters,
                    volume_index=request.volume_index
                ):
                    yield chunk

                logger.info(f"卷大纲流式生成完成 - 卷: {request.volume_title}")

            except Exception as e:
                logger.error(f"流式生成卷大纲失败: {str(e)}", exc_info=True)
                # 发送错误事件
                import json
                error_data = json.dumps({"error": str(e)})
                yield f"data: {error_data}\n\n"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
            }
        )

    except Exception as e:
        logger.error(f"启动流式生成失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"启动流式生成失败: {str(e)}"
        )


@router.post(
    "/modify-by-dialogue",
    response_model=ModifyOutlineResponse,
    summary="对话修改大纲",
    description="通过对话方式修改大纲，支持联动更新相关设定",
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def modify_outline_by_dialogue(
    request: ModifyOutlineByDialogueRequest,
    provider: AIServiceProvider = Depends(get_ai_provider)
):
    """通过对话修改大纲

    Args:
        request: 包含当前大纲和对话数据的请求
        provider: AI 提供商实例（依赖注入）

    Returns:
        ModifyOutlineResponse: 包含修改后的大纲、卷列表、角色列表等的响应

    Raises:
        HTTPException: 当修改失败时抛出 500 错误
    """
    try:
        logger.info("开始通过对话修改大纲")

        result = await provider.modify_outline_by_dialogue(
            outline=request.outline,
            dialogue_data=request.dialogue_data
        )

        logger.info("大纲修改成功")

        return ModifyOutlineResponse(
            outline=result["outline"],
            volumes=result.get("volumes"),
            characters=result.get("characters"),
            world_settings=result.get("world_settings"),
            timeline=result.get("timeline"),
            changes=result.get("changes", [])
        )

    except Exception as e:
        logger.error(f"修改大纲失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"修改大纲失败: {str(e)}"
        )
