"""应用配置管理"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置类

    使用 Pydantic Settings 从环境变量中读取配置
    配置优先级：环境变量 > .env 文件 > 默认值
    """

    # ==================== 服务配置 ====================
    SERVICE_NAME: str = "nova-ai-service"
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = False

    # ==================== Gemini 配置 ====================
    GEMINI_API_KEY: Optional[str] = None  # 运行时必需，但允许为空以便测试
    GEMINI_PROXY: Optional[str] = "http://127.0.0.1:40000"
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    GEMINI_TIMEOUT_MS: int = 300000  # 5 分钟

    # ==================== Claude 配置（预留）====================
    CLAUDE_API_KEY: Optional[str] = None
    CLAUDE_MODEL: Optional[str] = "claude-3-5-sonnet-20241022"

    # ==================== OpenAI 配置（预留）====================
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: Optional[str] = "gpt-4"

    # ==================== 日志配置 ====================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # ==================== CORS 配置 ====================
    CORS_ORIGINS: list = ["*"]  # 生产环境应该设置具体的域名
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
