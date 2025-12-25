# Services package

# 配置日志
import logging

# 为 services 包配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

__all__ = [
    'EmbeddingService',
    'ConsistencyChecker',
    'ForeshadowingMatcher',
    'ContentSimilarityChecker',
]
