"""Application configuration manager."""

from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Settings stored in environment variables and .env file."""

    SERVICE_NAME: str = "nova-ai-service"
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = False
    DEFAULT_AI_PROVIDER: str = "gemini"

    # Gemini configuration
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_PROXY: Optional[str] = "http://127.0.0.1:40000"
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    GEMINI_TIMEOUT_MS: int = 300000

    # DeepSeek configuration
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_PROXY: Optional[str] = None
    DEEPSEEK_MODEL: str = "deepseek-reasoner"
    DEEPSEEK_TIMEOUT_MS: int = 300000

    # Claude configuration (placeholders)
    CLAUDE_API_KEY: Optional[str] = None
    CLAUDE_MODEL: Optional[str] = "claude-3-5-sonnet-20241022"

    # OpenAI configuration (placeholders)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: Optional[str] = "gpt-4"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
