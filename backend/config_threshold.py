"""
相似度阈值配置
用于管理和调整各种场景下的相似度阈值
"""
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ThresholdConfig:
    """相似度阈值配置类"""
    
    def __init__(self):
        """初始化默认阈值配置"""
        # 默认阈值配置
        self.default_thresholds = {
            'chapter_similarity': 0.7,  # 章节相似度检索
            'paragraph_similarity': 0.75,  # 段落相似度匹配
            'foreshadowing_match': 0.8,  # 伏笔匹配
            'before_generation_check': 0.8,  # 生成前相似度检查（警告阈值）
            'after_generation_check': 0.85,  # 生成后相似度检查（严格阈值）
            'character_consistency': 0.65,  # 角色一致性检查
            'context_retrieval': 0.6,  # 上下文检索（较低，获取更多相关章节）
        }
        
        # 当前阈值（可以从配置文件或数据库加载）
        self.thresholds = self.default_thresholds.copy()
    
    def get(self, key: str) -> float:
        """
        获取阈值
        
        Args:
            key: 阈值键名
        
        Returns:
            阈值值
        """
        return self.thresholds.get(key, self.default_thresholds.get(key, 0.7))
    
    def set(self, key: str, value: float) -> bool:
        """
        设置阈值
        
        Args:
            key: 阈值键名
            value: 阈值值（0-1之间）
        
        Returns:
            是否成功
        """
        if not 0 <= value <= 1:
            logger.warning(f"阈值 {value} 不在有效范围内 [0, 1]")
            return False
        
        if key not in self.default_thresholds:
            logger.warning(f"未知的阈值键: {key}")
            return False
        
        old_value = self.thresholds.get(key)
        self.thresholds[key] = value
        logger.info(f"阈值更新: {key} = {old_value} -> {value}")
        return True
    
    def reset(self, key: Optional[str] = None):
        """
        重置阈值到默认值
        
        Args:
            key: 阈值键名（如果为None，重置所有）
        """
        if key:
            if key in self.default_thresholds:
                self.thresholds[key] = self.default_thresholds[key]
                logger.info(f"阈值重置: {key} = {self.default_thresholds[key]}")
        else:
            self.thresholds = self.default_thresholds.copy()
            logger.info("所有阈值已重置为默认值")
    
    def get_all(self) -> Dict[str, float]:
        """获取所有阈值"""
        return self.thresholds.copy()
    
    def load_from_dict(self, thresholds: Dict[str, float]) -> int:
        """
        从字典加载阈值
        
        Args:
            thresholds: 阈值字典
        
        Returns:
            成功加载的数量
        """
        count = 0
        for key, value in thresholds.items():
            if self.set(key, value):
                count += 1
        return count
    
    def export_to_dict(self) -> Dict[str, float]:
        """导出为字典"""
        return self.thresholds.copy()


# 全局配置实例（单例模式）
_threshold_config_instance: Optional[ThresholdConfig] = None


def get_threshold_config() -> ThresholdConfig:
    """获取阈值配置实例（单例模式）"""
    global _threshold_config_instance
    if _threshold_config_instance is None:
        _threshold_config_instance = ThresholdConfig()
    return _threshold_config_instance


# 便捷函数
def get_threshold(key: str) -> float:
    """获取阈值（便捷函数）"""
    return get_threshold_config().get(key)


def set_threshold(key: str, value: float) -> bool:
    """设置阈值（便捷函数）"""
    return get_threshold_config().set(key, value)


# 预定义的阈值键常量
class ThresholdKeys:
    """阈值键常量"""
    CHAPTER_SIMILARITY = 'chapter_similarity'
    PARAGRAPH_SIMILARITY = 'paragraph_similarity'
    FORESHADOWING_MATCH = 'foreshadowing_match'
    BEFORE_GENERATION_CHECK = 'before_generation_check'
    AFTER_GENERATION_CHECK = 'after_generation_check'
    CHARACTER_CONSISTENCY = 'character_consistency'
    CONTEXT_RETRIEVAL = 'context_retrieval'

