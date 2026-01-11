"""FastAPI 主应用入口"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.v1 import api_router


# ==================== 配置日志 ====================

def setup_logging():
    """配置日志系统"""
    # 配置日志格式
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # 设置第三方库的日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"日志系统已配置 - 日志级别: {settings.LOG_LEVEL}")


# ==================== 生命周期管理 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理

    Args:
        app: FastAPI 应用实例

    Yields:
        None
    """
    # 启动时执行
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info(f"启动服务: {settings.SERVICE_NAME}")
    logger.info(f"服务地址: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"API 文档: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f"调试模式: {settings.DEBUG}")
    logger.info("=" * 60)

    yield

    # 关闭时执行
    logger.info(f"关闭服务: {settings.SERVICE_NAME}")


# ==================== 创建应用 ====================

# 配置日志
setup_logging()

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.SERVICE_NAME,
    description="Nova AI 小说创作助手 - AI 服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# ==================== 配置 CORS ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

logger = logging.getLogger(__name__)
logger.info(f"CORS 已配置 - 允许的源: {settings.CORS_ORIGINS}")


# ==================== 全局异常处理 ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        JSONResponse: 包含错误信息的 JSON 响应
    """
    logger = logging.getLogger(__name__)
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "服务器内部错误",
            "detail": str(exc) if settings.DEBUG else "请联系管理员"
        }
    )


# ==================== 注册路由 ====================

# 注册 API v1 路由
app.include_router(api_router)

# 根路径
@app.get("/", tags=["根路径"])
async def root():
    """根路径端点

    Returns:
        dict: 包含服务信息的字典
    """
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


# ==================== 主函数 ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
