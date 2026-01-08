"""配置管理模块"""
import os
from dotenv import load_dotenv
from typing import List

# 加载环境变量
load_dotenv()

# ==================== 数据库配置 ====================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:novawrite_db_2024@localhost:5432/novawrite_ai"
)

# ==================== JWT 认证配置 ====================
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))  # 访问令牌1小时
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))  # 刷新令牌7天

# ==================== 服务器配置 ====================
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# ==================== CORS 配置 ====================
# 允许的前端地址
CORS_ORIGINS_STR = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,https://66.154.108.62,http://66.154.108.62"
)
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(",") if origin.strip()]

# ==================== Gemini API 配置 ====================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ==================== 环境检测 ====================
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# 生产环境检查
if ENVIRONMENT == "production":
    if SECRET_KEY == "your-secret-key-change-this-in-production":
        raise ValueError(
            "⚠️  警告：生产环境必须设置 SECRET_KEY！"
            "\n请在 .env 文件中设置一个强随机密钥。"
            "\n可以使用以下命令生成: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )

