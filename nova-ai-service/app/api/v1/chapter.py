"""章节生成 API"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_ai_provider
from app.core.providers.base import AIServiceProvider
from app.schemas.requests import (
    GenerateChapterOutlineRequest,
    WriteChapterContentRequest,
    WriteChapterContentStreamRequest,
    SummarizeChapterRequest
)
from app.schemas.responses import (
    ChapterOutlineResponse,
    ChapterContentResponse,
    ChapterSummaryResponse,
    ChapterInfo,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chapter", tags=["章节生成"])


@router.post(
    "/generate-outline",
    response_model=ChapterOutlineResponse,
    summary="生成章节列表",
    description="根据卷大纲生成章节列表",
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def generate_chapter_outline(
    request: GenerateChapterOutlineRequest,
    provider: AIServiceProvider = Depends(get_ai_provider)
):
    """生成章节列表

    Args:
        request: 包含小说标题、完整大纲、卷信息等的请求
        provider: AI 提供商实例（依赖注入）

    Returns:
        ChapterOutlineResponse: 包含章节列表的响应

    Raises:
        HTTPException: 当生成失败时抛出 500 错误
    """
    try:
        logger.info(f"开始生成章节列表 - 小说: {request.novel_title}, 卷: {request.volume_title}")

        chapters = await provider.generate_chapter_outline(
            novel_title=request.novel_title,
            genre=request.genre,
            full_outline=request.full_outline,
            volume_title=request.volume_title,
            volume_summary=request.volume_summary,
            volume_outline=request.volume_outline,
            characters=request.characters,
            volume_index=request.volume_index,
            chapter_count=request.chapter_count,
            previous_volumes_info=request.previous_volumes_info,
            future_volumes_info=request.future_volumes_info
        )

        logger.info(f"章节列表生成成功 - 卷: {request.volume_title}, 章节数: {len(chapters)}")

        # 转换为响应模型
        chapter_list = [
            ChapterInfo(
                title=ch.get("title", ""),
                summary=ch.get("summary", ""),
                aiPromptHints=ch.get("aiPromptHints")
            )
            for ch in chapters
        ]

        return ChapterOutlineResponse(chapters=chapter_list)

    except Exception as e:
        logger.error(f"生成章节列表失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"生成章节列表失败: {str(e)}"
        )


@router.post(
    "/write-content",
    response_model=ChapterContentResponse,
    summary="生成章节内容",
    description="生成章节的完整内容（非流式）",
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def write_chapter_content(
    request: WriteChapterContentRequest,
    provider: AIServiceProvider = Depends(get_ai_provider)
):
    """生成章节内容（非流式）

    Args:
        request: 包含小说信息、章节信息、角色和世界观等的请求
        provider: AI 提供商实例（依赖注入）

    Returns:
        ChapterContentResponse: 包含章节内容的响应

    Raises:
        HTTPException: 当生成失败时抛出 500 错误
    """
    try:
        logger.info(f"开始生成章节内容 - 小说: {request.novel_title}, 章节: {request.chapter_title}")

        content = await provider.write_chapter_content(
            novel_title=request.novel_title,
            genre=request.genre,
            synopsis=request.synopsis,
            chapter_title=request.chapter_title,
            chapter_summary=request.chapter_summary,
            chapter_prompt_hints=request.chapter_prompt_hints,
            characters=request.characters,
            world_settings=request.world_settings,
            previous_chapters_context=request.previous_chapters_context
        )

        logger.info(f"章节内容生成成功 - 章节: {request.chapter_title}, 字数: {len(content)}")

        return ChapterContentResponse(content=content)

    except Exception as e:
        logger.error(f"生成章节内容失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"生成章节内容失败: {str(e)}"
        )


@router.post(
    "/write-content-stream",
    summary="流式生成章节内容",
    description="流式生成章节的完整内容（返回 SSE 流）",
    responses={
        200: {
            "description": "成功返回流式响应",
            "content": {
                "text/event-stream": {
                    "example": 'data: {"chunk": "章节内容..."}\n\ndata: {"done": true}\n\n'
                }
            }
        },
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def write_chapter_content_stream(
    request: WriteChapterContentStreamRequest,
    provider: AIServiceProvider = Depends(get_ai_provider)
):
    """流式生成章节内容

    Args:
        request: 包含小说信息、章节信息、角色和世界观等的请求
        provider: AI 提供商实例（依赖注入）

    Returns:
        StreamingResponse: SSE 格式的流式响应

    Raises:
        HTTPException: 当生成失败时抛出 500 错误
    """
    try:
        logger.info(f"开始流式生成章节内容 - 小说: {request.novel_title}, 章节: {request.chapter_title}")

        async def stream_generator():
            """流式生成器"""
            try:
                async for chunk in provider.write_chapter_content_stream(
                    novel_title=request.novel_title,
                    genre=request.genre,
                    synopsis=request.synopsis,
                    chapter_title=request.chapter_title,
                    chapter_summary=request.chapter_summary,
                    chapter_prompt_hints=request.chapter_prompt_hints,
                    characters=request.characters,
                    world_settings=request.world_settings,
                    previous_chapters_context=request.previous_chapters_context
                ):
                    yield chunk

                logger.info(f"章节内容流式生成完成 - 章节: {request.chapter_title}")

            except Exception as e:
                logger.error(f"流式生成章节内容失败: {str(e)}", exc_info=True)
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
    "/summarize",
    response_model=ChapterSummaryResponse,
    summary="总结章节内容",
    description="生成章节内容的简要总结",
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def summarize_chapter_content(
    request: SummarizeChapterRequest,
    provider: AIServiceProvider = Depends(get_ai_provider)
):
    """总结章节内容

    Args:
        request: 包含章节标题和内容的请求
        provider: AI 提供商实例（依赖注入）

    Returns:
        ChapterSummaryResponse: 包含章节总结的响应

    Raises:
        HTTPException: 当生成失败时抛出 500 错误
    """
    try:
        logger.info(f"开始总结章节内容 - 章节: {request.chapter_title}")

        summary = await provider.summarize_chapter_content(
            chapter_title=request.chapter_title,
            chapter_content=request.chapter_content,
            max_len=request.max_len
        )

        logger.info(f"章节总结生成成功 - 章节: {request.chapter_title}, 字数: {len(summary)}")

        return ChapterSummaryResponse(summary=summary)

    except Exception as e:
        logger.error(f"总结章节内容失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"总结章节内容失败: {str(e)}"
        )
