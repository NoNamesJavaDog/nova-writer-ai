"""
向量缓存服务
使用Redis缓存常用章节向量，减少数据库查询
"""
import json
import logging
from typing import Optional, List, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Redis客户端（可选，如果未安装则禁用缓存）
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis未安装，缓存功能将被禁用。安装: pip install redis")


class EmbeddingCache:
    """向量缓存管理器"""
    
    def __init__(self, redis_client=None, enabled: bool = True):
        """
        初始化缓存管理器
        
        Args:
            redis_client: Redis客户端实例（可选）
            enabled: 是否启用缓存（默认True）
        """
        self.enabled = enabled and REDIS_AVAILABLE
        self.redis_client = redis_client
        
        # 缓存TTL配置（秒）
        self.CHAPTER_EMBEDDING_TTL = 3600  # 1小时
        self.QUERY_RESULT_TTL = 300  # 5分钟
        self.CHARACTER_EMBEDDING_TTL = 7200  # 2小时
        self.WORLD_SETTING_TTL = 7200  # 2小时
        self.FORESHADOWING_TTL = 7200  # 2小时
    
    def _get_client(self):
        """获取Redis客户端"""
        if not self.enabled:
            return None
        
        if self.redis_client is None:
            # 尝试从环境变量或配置获取Redis连接
            try:
                import os
                redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # 测试连接
                self.redis_client.ping()
                logger.info("✅ Redis缓存已连接")
            except Exception as e:
                logger.warning(f"⚠️  Redis连接失败，禁用缓存: {str(e)}")
                self.enabled = False
                return None
        
        return self.redis_client
    
    def get_chapter_embedding(self, chapter_id: str) -> Optional[List[float]]:
        """
        从缓存获取章节向量
        
        Args:
            chapter_id: 章节ID
        
        Returns:
            向量列表，如果未命中返回None
        """
        if not self.enabled:
            return None
        
        try:
            client = self._get_client()
            if not client:
                return None
            
            cache_key = f"chapter_embedding:{chapter_id}"
            cached = client.get(cache_key)
            
            if cached:
                embedding = json.loads(cached)
                logger.debug(f"✅ 缓存命中: {cache_key}")
                return embedding
            
            return None
        except Exception as e:
            logger.warning(f"⚠️  缓存读取失败: {str(e)}")
            return None
    
    def set_chapter_embedding(self, chapter_id: str, embedding: List[float]) -> bool:
        """
        缓存章节向量
        
        Args:
            chapter_id: 章节ID
            embedding: 向量列表
        
        Returns:
            是否成功
        """
        if not self.enabled:
            return False
        
        try:
            client = self._get_client()
            if not client:
                return False
            
            cache_key = f"chapter_embedding:{chapter_id}"
            client.setex(
                cache_key,
                self.CHAPTER_EMBEDDING_TTL,
                json.dumps(embedding)
            )
            logger.debug(f"✅ 缓存写入: {cache_key}")
            return True
        except Exception as e:
            logger.warning(f"⚠️  缓存写入失败: {str(e)}")
            return False
    
    def invalidate_chapter_cache(self, chapter_id: str) -> bool:
        """
        使章节缓存失效
        
        Args:
            chapter_id: 章节ID
        
        Returns:
            是否成功
        """
        if not self.enabled:
            return False
        
        try:
            client = self._get_client()
            if not client:
                return False
            
            # 清除章节向量缓存
            cache_key = f"chapter_embedding:{chapter_id}"
            client.delete(cache_key)
            
            # 清除相关的查询结果缓存
            pattern = f"chapter_similar:*:{chapter_id}"
            for key in client.scan_iter(match=pattern):
                client.delete(key)
            
            logger.debug(f"✅ 缓存失效: {cache_key}")
            return True
        except Exception as e:
            logger.warning(f"⚠️  缓存失效失败: {str(e)}")
            return False
    
    def get_query_result(self, novel_id: str, query_hash: str) -> Optional[List[Dict]]:
        """
        从缓存获取查询结果
        
        Args:
            novel_id: 小说ID
            query_hash: 查询哈希值
        
        Returns:
            查询结果列表，如果未命中返回None
        """
        if not self.enabled:
            return None
        
        try:
            client = self._get_client()
            if not client:
                return None
            
            cache_key = f"chapter_similar:{novel_id}:{query_hash}"
            cached = client.get(cache_key)
            
            if cached:
                result = json.loads(cached)
                logger.debug(f"✅ 查询缓存命中: {cache_key}")
                return result
            
            return None
        except Exception as e:
            logger.warning(f"⚠️  查询缓存读取失败: {str(e)}")
            return None
    
    def set_query_result(self, novel_id: str, query_hash: str, result: List[Dict]) -> bool:
        """
        缓存查询结果
        
        Args:
            novel_id: 小说ID
            query_hash: 查询哈希值
            result: 查询结果列表
        
        Returns:
            是否成功
        """
        if not self.enabled:
            return False
        
        try:
            client = self._get_client()
            if not client:
                return False
            
            cache_key = f"chapter_similar:{novel_id}:{query_hash}"
            client.setex(
                cache_key,
                self.QUERY_RESULT_TTL,
                json.dumps(result)
            )
            logger.debug(f"✅ 查询缓存写入: {cache_key}")
            return True
        except Exception as e:
            logger.warning(f"⚠️  查询缓存写入失败: {str(e)}")
            return False
    
    def clear_all_cache(self, pattern: str = "*") -> int:
        """
        清除所有匹配模式的缓存
        
        Args:
            pattern: 匹配模式（默认"*"清除所有）
        
        Returns:
            清除的键数量
        """
        if not self.enabled:
            return 0
        
        try:
            client = self._get_client()
            if not client:
                return 0
            
            count = 0
            for key in client.scan_iter(match=pattern):
                client.delete(key)
                count += 1
            
            logger.info(f"✅ 清除缓存: {count} 个键 (pattern: {pattern})")
            return count
        except Exception as e:
            logger.warning(f"⚠️  清除缓存失败: {str(e)}")
            return 0


# 全局缓存实例（单例模式）
_cache_instance: Optional[EmbeddingCache] = None


def get_embedding_cache(redis_client=None, enabled: bool = True) -> EmbeddingCache:
    """
    获取缓存实例（单例模式）
    
    Args:
        redis_client: Redis客户端（可选）
        enabled: 是否启用缓存
    
    Returns:
        EmbeddingCache实例
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = EmbeddingCache(redis_client=redis_client, enabled=enabled)
    return _cache_instance


def cache_embedding_result(cache_key_func):
    """
    装饰器：缓存函数结果
    
    Args:
        cache_key_func: 生成缓存键的函数
    
    Usage:
        @cache_embedding_result(lambda chapter_id: f"embedding:{chapter_id}")
        def get_embedding(chapter_id):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_embedding_cache()
            
            # 生成缓存键
            cache_key = cache_key_func(*args, **kwargs)
            
            # 尝试从缓存获取
            cached = cache.get_chapter_embedding(cache_key) if 'chapter' in cache_key else None
            if cached is not None:
                return cached
            
            # 缓存未命中，执行函数
            result = func(*args, **kwargs)
            
            # 写入缓存
            if result is not None:
                cache.set_chapter_embedding(cache_key, result)
            
            return result
        return wrapper
    return decorator


