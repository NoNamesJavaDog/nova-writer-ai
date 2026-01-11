"""AI 提供商模块"""

from typing import Dict, Type, Optional
from .base import AIServiceProvider, StreamMode

# 导入具体实现
from .gemini import GeminiProvider
# from .claude import ClaudeProvider
# from .openai import OpenAIProvider

PROVIDERS: Dict[str, Type[AIServiceProvider]] = {
    "gemini": GeminiProvider,
    # "claude": ClaudeProvider,
    # "openai": OpenAIProvider,
}


def get_provider(
    provider_name: str,
    api_key: str,
    proxy: Optional[str] = None,
    **kwargs
) -> AIServiceProvider:
    """获取 AI 提供商实例

    Args:
        provider_name: 提供商名称 ("gemini", "claude", "openai")
        api_key: API 密钥
        proxy: 代理地址（可选）
        **kwargs: 其他提供商特定的参数

    Returns:
        AI 服务提供商实例

    Raises:
        ValueError: 如果提供商不支持
    """
    if provider_name not in PROVIDERS:
        raise ValueError(
            f"不支持的 AI 提供商: {provider_name}。"
            f"支持的提供商: {', '.join(PROVIDERS.keys())}"
        )

    provider_class = PROVIDERS[provider_name]
    return provider_class(api_key=api_key, proxy=proxy, **kwargs)


__all__ = [
    "AIServiceProvider",
    "StreamMode",
    "GeminiProvider",
    "get_provider",
    "PROVIDERS",
]
