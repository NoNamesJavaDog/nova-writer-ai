"""向量嵌入服务模块"""
from .embedding_service import EmbeddingService
from .vector_helper import (
    store_chapter_embedding_async,
    store_character_embedding,
    store_world_setting_embedding,
    get_embedding_service
)

__all__ = [
    'EmbeddingService',
    'store_chapter_embedding_async',
    'store_character_embedding',
    'store_world_setting_embedding',
    'get_embedding_service',
]

