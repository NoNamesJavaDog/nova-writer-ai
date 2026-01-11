"""API v1 路由器"""

from fastapi import APIRouter

from app.api.v1 import health, outline, chapter, analysis

# 创建 v1 API 路由器
api_router = APIRouter(prefix="/api/v1")

# 注册所有子路由
api_router.include_router(health.router)  # 健康检查
api_router.include_router(outline.router)  # 大纲生成
api_router.include_router(chapter.router)  # 章节生成
api_router.include_router(analysis.router)  # 元数据分析

__all__ = ["api_router"]
