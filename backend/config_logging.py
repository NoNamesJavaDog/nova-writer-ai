"""
日志配置模块
用于统一配置所有服务的日志格式
"""
import logging
import sys

def setup_logging(level=logging.INFO):
    """
    配置日志系统
    
    Args:
        level: 日志级别，默认为 INFO
    """
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 移除已有的处理器
    root_logger.handlers.clear()
    
    # 添加新的处理器
    root_logger.addHandler(console_handler)
    
    # 为特定模块设置日志级别
    logging.getLogger('services').setLevel(level)
    logging.getLogger('services.embedding_service').setLevel(level)
    logging.getLogger('services.consistency_checker').setLevel(level)
    logging.getLogger('services.foreshadowing_matcher').setLevel(level)
    logging.getLogger('services.content_similarity_checker').setLevel(level)
    logging.getLogger('services.vector_helper').setLevel(level)


