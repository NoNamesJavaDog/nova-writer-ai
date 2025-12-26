"""
批量向量生成处理器
优化批量处理场景，减少API调用，提高处理效率
"""
import time
import logging
from typing import List, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import threading

logger = logging.getLogger(__name__)


class BatchEmbeddingProcessor:
    """批量向量生成处理器"""
    
    def __init__(
        self,
        max_workers: int = 3,
        delay_between_calls: float = 0.5,
        batch_size: int = 10,
        max_retries: int = 3
    ):
        """
        初始化批量处理器
        
        Args:
            max_workers: 最大并发工作线程数
            delay_between_calls: API调用间隔（秒）
            batch_size: 每批处理的任务数量
            max_retries: 最大重试次数
        """
        self.max_workers = max_workers
        self.delay_between_calls = delay_between_calls
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.last_call_time = {}  # 跟踪每个线程的最后调用时间
    
    def process_batch(
        self,
        tasks: List[Dict],
        embedding_function: Callable,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        批量处理任务
        
        Args:
            tasks: 任务列表，每个任务包含：
                - id: 任务ID
                - text: 要生成向量的文本
                - metadata: 可选的元数据
            embedding_function: 向量生成函数（接受text参数，返回向量）
            progress_callback: 进度回调函数（可选）
                - 参数: (completed, total, current_task)
        
        Returns:
            结果列表，每个结果包含：
                - id: 任务ID
                - status: 'success' 或 'failed'
                - embedding: 向量（成功时）
                - error: 错误信息（失败时）
                - metadata: 原始元数据
        """
        total = len(tasks)
        results = []
        
        logger.info(f"开始批量处理 {total} 个任务")
        
        # 使用线程池处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_task = {}
            for task in tasks:
                future = executor.submit(
                    self._process_single_task,
                    task,
                    embedding_function
                )
                future_to_task[future] = task
            
            # 收集结果
            completed = 0
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    
                    if progress_callback:
                        progress_callback(completed, total, task)
                    
                    logger.debug(f"任务 {task.get('id', 'unknown')} 完成 ({completed}/{total})")
                except Exception as e:
                    logger.error(f"任务 {task.get('id', 'unknown')} 失败: {str(e)}")
                    results.append({
                        'id': task.get('id'),
                        'status': 'failed',
                        'error': str(e),
                        'metadata': task.get('metadata')
                    })
                    completed += 1
        
        success_count = sum(1 for r in results if r.get('status') == 'success')
        logger.info(f"批量处理完成: {success_count}/{total} 成功")
        
        return results
    
    def _process_single_task(
        self,
        task: Dict,
        embedding_function: Callable
    ) -> Dict:
        """
        处理单个任务（带重试和限流）
        
        Args:
            task: 任务字典
            embedding_function: 向量生成函数
        
        Returns:
            结果字典
        """
        task_id = task.get('id')
        text = task.get('text')
        metadata = task.get('metadata')
        
        # 控制API调用频率
        thread_id = threading.current_thread().ident
        if thread_id in self.last_call_time:
            elapsed = time.time() - self.last_call_time[thread_id]
            if elapsed < self.delay_between_calls:
                time.sleep(self.delay_between_calls - elapsed)
        
        # 重试逻辑
        last_error = None
        for attempt in range(self.max_retries):
            try:
                self.last_call_time[thread_id] = time.time()
                embedding = embedding_function(text)
                
                return {
                    'id': task_id,
                    'status': 'success',
                    'embedding': embedding,
                    'metadata': metadata
                }
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = (attempt + 1) * 0.5  # 指数退避
                    logger.warning(f"任务 {task_id} 失败（尝试 {attempt + 1}/{self.max_retries}），{wait_time}秒后重试")
                    time.sleep(wait_time)
                else:
                    logger.error(f"任务 {task_id} 最终失败: {str(e)}")
        
        return {
            'id': task_id,
            'status': 'failed',
            'error': str(last_error),
            'metadata': metadata
        }
    
    def process_chapters(
        self,
        chapters: List[Dict],
        embedding_service,
        store_function: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        批量处理章节向量生成和存储
        
        Args:
            chapters: 章节列表，每个章节包含：
                - chapter_id: 章节ID
                - content: 章节内容
                - novel_id: 小说ID（可选）
            embedding_service: EmbeddingService实例
            store_function: 存储函数（可选），接受 (chapter_id, novel_id, content, embedding)
            progress_callback: 进度回调（可选）
        
        Returns:
            结果列表
        """
        # 准备任务
        tasks = []
        for chapter in chapters:
            tasks.append({
                'id': chapter.get('chapter_id'),
                'text': chapter.get('content', ''),
                'metadata': {
                    'chapter_id': chapter.get('chapter_id'),
                    'novel_id': chapter.get('novel_id')
                }
            })
        
        # 批量处理
        results = self.process_batch(
            tasks=tasks,
            embedding_function=lambda text: embedding_service.generate_embedding(text),
            progress_callback=progress_callback
        )
        
        # 存储结果（如果提供了存储函数）
        if store_function:
            for result in results:
                if result.get('status') == 'success':
                    metadata = result.get('metadata', {})
                    try:
                        store_function(
                            metadata.get('chapter_id'),
                            metadata.get('novel_id'),
                            tasks[results.index(result)].get('text'),
                            result.get('embedding')
                        )
                    except Exception as e:
                        logger.error(f"存储失败 {metadata.get('chapter_id')}: {str(e)}")
                        result['storage_error'] = str(e)
        
        return results


# 辅助函数
def create_batch_tasks_from_chapters(
    chapters: List[Dict],
    include_content: bool = True
) -> List[Dict]:
    """
    从章节列表创建批量任务
    
    Args:
        chapters: 章节列表
        include_content: 是否包含内容（如果False，只生成任务结构）
    
    Returns:
        任务列表
    """
    tasks = []
    for chapter in chapters:
        task = {
            'id': chapter.get('chapter_id') or chapter.get('id'),
            'text': chapter.get('content', '') if include_content else '',
            'metadata': {
                'chapter_id': chapter.get('chapter_id') or chapter.get('id'),
                'novel_id': chapter.get('novel_id'),
                'chapter_title': chapter.get('title')
            }
        }
        tasks.append(task)
    return tasks


def batch_generate_embeddings(
    texts: List[str],
    embedding_service,
    max_workers: int = 3,
    delay: float = 0.5,
    progress_callback: Optional[Callable] = None
) -> List[Dict]:
    """
    批量生成向量（简化接口）
    
    Args:
        texts: 文本列表
        embedding_service: EmbeddingService实例
        max_workers: 最大并发数
        delay: API调用间隔
        progress_callback: 进度回调
    
    Returns:
        结果列表，每个结果包含 'text', 'embedding', 'status'
    """
    processor = BatchEmbeddingProcessor(
        max_workers=max_workers,
        delay_between_calls=delay
    )
    
    tasks = [{'id': i, 'text': text, 'metadata': {}} for i, text in enumerate(texts)]
    
    results = processor.process_batch(
        tasks=tasks,
        embedding_function=lambda text: embedding_service.generate_embedding(text),
        progress_callback=progress_callback
    )
    
    # 转换为简化格式
    return [
        {
            'text': tasks[r.get('id')].get('text'),
            'embedding': r.get('embedding'),
            'status': r.get('status'),
            'error': r.get('error')
        }
        for r in results
    ]


