"""任务管理服务 - 处理后台生成任务"""
import time
import json
from typing import Optional, Dict, Any, Callable
from sqlalchemy.orm import Session
from models import Task
from core.database import SessionLocal

# 全局任务执行器
_task_executor = None

def get_task_executor():
    """获取任务执行器（单例）"""
    global _task_executor
    if _task_executor is None:
        _task_executor = TaskExecutor()
    return _task_executor


class ProgressCallback:
    """进度回调类 - 用于更新任务进度"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
    
    def update(self, progress: int, message: str):
        """更新任务进度"""
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == self.task_id).first()
            if task:
                task.progress = progress
                task.progress_message = message
                task.updated_at = int(time.time() * 1000)
                db.commit()
        except Exception as e:
            print(f"更新任务进度失败: {e}")
        finally:
            db.close()


class TaskExecutor:
    """任务执行器 - 在后台线程中执行任务"""
    
    def __init__(self):
        self.executor = None
        self._initialize_executor()
    
    def _initialize_executor(self):
        """初始化执行器"""
        # 使用线程池执行任务
        import concurrent.futures
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5, thread_name_prefix="task_")
    
    def submit_task(self, task_id: str, task_func: Callable):
        """提交任务到后台执行"""
        future = self.executor.submit(self._execute_task, task_id, task_func)
        return future
    
    def submit(self, task_func: Callable):
        """直接提交任务函数到后台执行（用于已经在内部处理状态的任务）"""
        future = self.executor.submit(task_func)
        return future
    
    def _execute_task(self, task_id: str, task_func: Callable):
        """执行任务并更新状态"""
        db = SessionLocal()
        try:
            # 更新任务状态为运行中
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return
            
            task.status = "running"
            task.started_at = int(time.time() * 1000)
            task.progress = 0
            task.progress_message = "任务开始执行"
            db.commit()
            
            # 执行任务函数（函数内部会创建和使用进度回调）
            try:
                result = task_func()
                
                # 更新任务为完成状态
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.status = "completed"
                    task.completed_at = int(time.time() * 1000)
                    task.result = json.dumps(result) if result else None
                    task.progress = 100
                    task.progress_message = "任务完成"
                    db.commit()
                
            except Exception as e:
                # 更新任务为失败状态
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.status = "failed"
                    task.completed_at = int(time.time() * 1000)
                    task.error_message = str(e)
                    task.progress_message = f"任务失败: {str(e)}"
                    db.commit()
                
        except Exception as e:
            print(f"任务执行错误: {e}")
        finally:
            db.close()


def create_task(
    db: Session,
    novel_id: str,
    user_id: str,
    task_type: str,
    task_data: Dict[str, Any]
) -> Task:
    """创建新任务"""
    from auth import generate_uuid
    
    task_id = generate_uuid()
    now = int(time.time() * 1000)
    
    task = Task(
        id=task_id,
        novel_id=novel_id,
        user_id=user_id,
        task_type=task_type,
        task_data=json.dumps(task_data),
        status="pending",
        progress=0,
        progress_message="等待执行",
        created_at=now,
        updated_at=now
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task


def update_task_progress(
    db: Session,
    task_id: str,
    progress: int,
    progress_message: str,
    result: Optional[Dict[str, Any]] = None
):
    """更新任务进度"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return
    
    task.progress = progress
    task.progress_message = progress_message
    task.updated_at = int(time.time() * 1000)
    
    if result is not None:
        task.result = json.dumps(result)
    
    db.commit()


def get_task(db: Session, task_id: str) -> Optional[Task]:
    """获取任务"""
    return db.query(Task).filter(Task.id == task_id).first()


def get_novel_tasks(db: Session, novel_id: str, status: Optional[str] = None) -> list:
    """获取小说的任务列表"""
    query = db.query(Task).filter(Task.novel_id == novel_id)
    if status:
        query = query.filter(Task.status == status)
    return query.order_by(Task.created_at.desc()).all()


def get_user_active_tasks(db: Session, user_id: str) -> list:
    """获取用户的活跃任务（pending 或 running）"""
    return db.query(Task).filter(
        Task.user_id == user_id,
        Task.status.in_(["pending", "running", "processing"])
    ).order_by(Task.created_at.desc()).all()

