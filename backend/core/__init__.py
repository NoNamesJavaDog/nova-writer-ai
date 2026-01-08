"""
核心模块 - 配置、数据库、安全等基础设施
"""
from .config import (
    DATABASE_URL,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    HOST,
    PORT,
    CORS_ORIGINS,
    GEMINI_API_KEY,
    ENVIRONMENT,
    DEBUG
)
from .database import get_db, SessionLocal, Base
from .security import (
    get_current_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_password_hash,
    verify_password,
    get_user_by_username_or_email,
    generate_uuid,
    handle_login_failure,
    generate_captcha,
    verify_captcha,
    check_login_status
)

__all__ = [
    # 配置
    'DATABASE_URL',
    'SECRET_KEY',
    'ALGORITHM',
    'ACCESS_TOKEN_EXPIRE_MINUTES',
    'REFRESH_TOKEN_EXPIRE_DAYS',
    'HOST',
    'PORT',
    'CORS_ORIGINS',
    'GEMINI_API_KEY',
    'ENVIRONMENT',
    'DEBUG',
    # 数据库
    'get_db',
    'SessionLocal',
    'Base',
    # 安全
    'get_current_user',
    'create_access_token',
    'create_refresh_token',
    'verify_refresh_token',
    'get_password_hash',
    'verify_password',
    'get_user_by_username_or_email',
    'generate_uuid',
    'handle_login_failure',
    'generate_captcha',
    'verify_captcha',
    'check_login_status',
]

