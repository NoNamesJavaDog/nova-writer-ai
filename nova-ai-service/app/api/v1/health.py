"""健康检查 API"""

import logging
from fastapi import APIRouter

from app.schemas.responses import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="检查服务是否正常运行"
)
async def health_check():
    """健康检查端点

    Returns:
        HealthResponse: 包含服务状态、名称和版本信息
    """
    logger.debug("执行健康检查")

    return HealthResponse(
        status="ok",
        service="nova-ai-service",
        version="1.0.0"
    )
