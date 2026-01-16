"""Dependency injection helpers for API routers."""

import logging
from fastapi import Header, HTTPException
from typing import Optional

from app.config import settings
from app.core.providers import get_provider, AIServiceProvider

logger = logging.getLogger(__name__)


async def get_ai_provider(
    x_provider: Optional[str] = Header(
        default=None,
        description="AI provider name (gemini, deepseek, claude, openai). If omitted, the backend DEFAULT_AI_PROVIDER is used."
    )
) -> AIServiceProvider:
    """Resolve an AI service provider instance using the X-Provider header or the configured default."""
    provider_name = (x_provider or settings.DEFAULT_AI_PROVIDER).lower().strip()

    try:
        if provider_name == "gemini":
            if not settings.GEMINI_API_KEY:
                raise HTTPException(
                    status_code=500,
                    detail="Gemini API key is not configured; set GEMINI_API_KEY"
                )
            logger.info(f"Creating Gemini provider (model={settings.GEMINI_MODEL})")
            return get_provider(
                provider_name="gemini",
                api_key=settings.GEMINI_API_KEY,
                proxy=settings.GEMINI_PROXY,
                model=settings.GEMINI_MODEL,
                timeout_ms=settings.GEMINI_TIMEOUT_MS
            )

        if provider_name == "deepseek":
            if not settings.DEEPSEEK_API_KEY:
                raise HTTPException(
                    status_code=500,
                    detail="DeepSeek API key is not configured; set DEEPSEEK_API_KEY"
                )
            logger.info(f"Creating DeepSeek provider (model={settings.DEEPSEEK_MODEL})")
            return get_provider(
                provider_name="deepseek",
                api_key=settings.DEEPSEEK_API_KEY,
                proxy=settings.DEEPSEEK_PROXY,
                base_url=settings.DEEPSEEK_BASE_URL,
                model=settings.DEEPSEEK_MODEL,
                timeout_ms=settings.DEEPSEEK_TIMEOUT_MS
            )

        if provider_name == "claude":
            if not settings.CLAUDE_API_KEY:
                raise HTTPException(
                    status_code=500,
                    detail="Claude API key is not configured; set CLAUDE_API_KEY"
                )
            logger.info(f"Creating Claude provider (model={settings.CLAUDE_MODEL})")
            return get_provider(
                provider_name="claude",
                api_key=settings.CLAUDE_API_KEY,
                model=settings.CLAUDE_MODEL
            )

        if provider_name == "openai":
            if not settings.OPENAI_API_KEY:
                raise HTTPException(
                    status_code=500,
                    detail="OpenAI API key is not configured; set OPENAI_API_KEY"
                )
            logger.info(f"Creating OpenAI provider (model={settings.OPENAI_MODEL})")
            return get_provider(
                provider_name="openai",
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL
            )

        raise HTTPException(
            status_code=400,
            detail=f"Unsupported AI provider {provider_name}. Available providers: gemini, deepseek, claude, openai"
        )

    except HTTPException:
        raise
    except ValueError as exc:
        logger.error(f"AI provider lookup failed: {str(exc)}")
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to instantiate AI provider", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create AI provider: {str(exc)}")
