"""API 依赖注入"""

import logging
from fastapi import Header, HTTPException
from typing import Optional

from app.config import settings
from app.core.providers import get_provider, AIServiceProvider

logger = logging.getLogger(__name__)


async def get_ai_provider(
    x_provider: str = Header(default="gemini", description="AI 提供商名称（gemini, claude, openai）")
) -> AIServiceProvider:
    """依赖注入：获取 AI 提供商实例

    通过 HTTP Header X-Provider 选择提供商（gemini, claude, openai）

    Args:
        x_provider: AI 提供商名称，从 HTTP Header X-Provider 中获取

    Returns:
        AIServiceProvider: AI 服务提供商实例

    Raises:
        HTTPException: 当提供商不支持或配置缺失时抛出 400 错误
    """
    provider_name = x_provider.lower().strip()

    try:
        # 根据提供商类型获取相应的配置
        if provider_name == "gemini":
            if not settings.GEMINI_API_KEY:
                raise HTTPException(
                    status_code=500,
                    detail="Gemini API 密钥未配置，请在环境变量中设置 GEMINI_API_KEY"
                )

            logger.info(f"创建 Gemini 提供商实例，模型: {settings.GEMINI_MODEL}")
            return get_provider(
                provider_name="gemini",
                api_key=settings.GEMINI_API_KEY,
                proxy=settings.GEMINI_PROXY,
                model=settings.GEMINI_MODEL,
                timeout_ms=settings.GEMINI_TIMEOUT_MS
            )

        elif provider_name == "claude":
            if not settings.CLAUDE_API_KEY:
                raise HTTPException(
                    status_code=500,
                    detail="Claude API 密钥未配置，请在环境变量中设置 CLAUDE_API_KEY"
                )

            logger.info(f"创建 Claude 提供商实例，模型: {settings.CLAUDE_MODEL}")
            return get_provider(
                provider_name="claude",
                api_key=settings.CLAUDE_API_KEY,
                model=settings.CLAUDE_MODEL
            )

        elif provider_name == "openai":
            if not settings.OPENAI_API_KEY:
                raise HTTPException(
                    status_code=500,
                    detail="OpenAI API 密钥未配置，请在环境变量中设置 OPENAI_API_KEY"
                )

            logger.info(f"创建 OpenAI 提供商实例，模型: {settings.OPENAI_MODEL}")
            return get_provider(
                provider_name="openai",
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的 AI 提供商: {provider_name}。支持的提供商: gemini, claude, openai"
            )

    except HTTPException:
        # 直接抛出 HTTPException
        raise
    except ValueError as e:
        # 提供商不支持
        logger.error(f"获取 AI 提供商失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 其他错误
        logger.error(f"创建 AI 提供商实例时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"创建 AI 提供商实例失败: {str(e)}"
        )
