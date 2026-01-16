"""DeepSeek AI service provider that reuses Gemini prompts via an OpenAI-compatible client."""

import json
import logging
from typing import Optional, AsyncGenerator

import httpx

from app.core.providers.gemini import GeminiProvider

logger = logging.getLogger(__name__)


class DeepSeekStreamChunk:
    """Minimal chunk shaped like Gemini streaming result."""

    def __init__(self, text: str):
        self.text = text


class DeepSeekResponse:
    """Wraps a synchronous completion so `.text` is available like Gemini."""

    def __init__(self, text: str, raw: dict):
        self.text = text
        self.raw = raw


class DeepSeekClient:
    """Simple OpenAI-compatible wrapper for DeepSeek HTTP endpoints."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        proxy: Optional[str] = None,
        timeout: float = 300.0
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = max(1.0, timeout)
        self.proxies = self._normalize_proxy(proxy)
        self.models = self

    def _normalize_proxy(self, proxy: Optional[str]) -> Optional[dict]:
        if not proxy:
            return None
        proxy_url = proxy.strip()
        if not proxy_url.startswith(("http://", "https://", "socks5://", "socks5h://")):
            proxy_url = f"http://{proxy_url}"
        return {"http://": proxy_url, "https://": proxy_url}

    def _build_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _build_endpoint(self, path: str) -> str:
        """Ensure the endpoint includes /v1 exactly once."""
        base = self.base_url
        if base.endswith("/v1"):
            return f"{base}{path}"
        return f"{base}/v1{path}"

    async def generate_content(self, model: str, contents: str, config: dict) -> DeepSeekResponse:
        """Mirror the Gemini client API by returning an object with `.text`."""
        config = config or {}
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": contents}],
            "temperature": config.get("temperature", 0.7),
        }
        max_tokens = config.get("max_output_tokens")
        if max_tokens:
            payload["max_tokens"] = max_tokens

        # carry through any extra tolerable params
        extra = {
            key: value
            for key, value in config.items()
            if key not in {"temperature", "max_output_tokens", "response_mime_type"}
        }
        payload.update(extra)

        endpoint = self._build_endpoint("/chat/completions")
        async with httpx.AsyncClient(timeout=self.timeout, proxies=self.proxies, trust_env=False) as client:
            response = await client.post(endpoint, json=payload, headers=self._build_headers())
            response.raise_for_status()
            data = response.json()

        text = self._extract_text(data)
        return DeepSeekResponse(text=text, raw=data)

    async def generate_content_stream(
        self,
        model: str,
        contents: str,
        config: dict
    ) -> AsyncGenerator[DeepSeekStreamChunk, None]:
        config = config or {}
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": contents}],
            "temperature": config.get("temperature", 0.7),
            "stream": True
        }
        max_tokens = config.get("max_output_tokens")
        if max_tokens:
            payload["max_tokens"] = max_tokens

        endpoint = self._build_endpoint("/chat/completions")
        async with httpx.AsyncClient(timeout=self.timeout, proxies=self.proxies, trust_env=False) as client:
            async with client.stream("POST", endpoint, json=payload, headers=self._build_headers()) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    line = line.strip()
                    if not line.startswith("data:"):
                        continue
                    content = line[len("data:"):].strip()
                    if content == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(content)
                    except json.JSONDecodeError:
                        continue
                    chunk_text = self._extract_delta_text(chunk_data)
                    if chunk_text:
                        yield DeepSeekStreamChunk(chunk_text)

    @staticmethod
    def _extract_text(data: dict) -> str:
        choices = data.get("choices") or []
        text = []
        for choice in choices:
            message = choice.get("message", {})
            content = message.get("content") or choice.get("text") or ""
            text.append(content)
        return "".join(text)

    @staticmethod
    def _extract_delta_text(data: dict) -> str:
        choices = data.get("choices") or []
        text = []
        for choice in choices:
            delta = choice.get("delta", {})
            content = delta.get("content")
            if content:
                text.append(content)
        return "".join(text)


class DeepSeekProvider(GeminiProvider):
    """Provider that reuses the Gemini plan but routes requests to DeepSeek."""

    def __init__(
        self,
        api_key: str,
        proxy: Optional[str] = None,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-reasoner",
        timeout_ms: int = 300000,
        **kwargs
    ):
        self.base_url = base_url
        self.timeout_ms = timeout_ms
        super().__init__(api_key=api_key, proxy=proxy, model=model, timeout_ms=timeout_ms, **kwargs)

    def _configure_client(self):
        self.client = DeepSeekClient(
            api_key=self.api_key,
            base_url=self.base_url,
            proxy=self.proxy,
            timeout=self.timeout_ms / 1000
        )
        logger.info(f"DeepSeek client initialized (model={self.model}, base_url={self.base_url})")
