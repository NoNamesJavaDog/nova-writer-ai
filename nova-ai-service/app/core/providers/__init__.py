"""AI service provider registry."""

from typing import Dict, Type, Optional
from .base import AIServiceProvider, StreamMode

from .gemini import GeminiProvider
from .deepseek import DeepSeekProvider
# from .claude import ClaudeProvider
# from .openai import OpenAIProvider

PROVIDERS: Dict[str, Type[AIServiceProvider]] = {
    "gemini": GeminiProvider,
    "deepseek": DeepSeekProvider,
    # "claude": ClaudeProvider,
    # "openai": OpenAIProvider,
}


def get_provider(
    provider_name: str,
    api_key: str,
    proxy: Optional[str] = None,
    **kwargs
) -> AIServiceProvider:
    """Retrieve a registered AI service provider."""
    provider_name = provider_name.lower()
    if provider_name not in PROVIDERS:
        raise ValueError(
            f"Unsupported AI provider {provider_name}. "
            f"Available providers: {', '.join(PROVIDERS.keys())}"
        )

    provider_class = PROVIDERS[provider_name]
    return provider_class(api_key=api_key, proxy=proxy, **kwargs)


__all__ = [
    "AIServiceProvider",
    "StreamMode",
    "GeminiProvider",
    "DeepSeekProvider",
    "get_provider",
    "PROVIDERS",
]
