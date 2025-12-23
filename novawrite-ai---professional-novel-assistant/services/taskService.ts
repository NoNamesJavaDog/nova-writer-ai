// 任务管理服务 - 处理后台任务状态查询和轮询
import { apiRequest } from './apiService';

export interface Task {
  id: string;
  novel_id: string;
  task_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number; // 0-100
  progress_message?: string;
  result?: any;
  error_message?: string;
  created_at: number;
  updated_at: number;
  started_at?: number;
  completed_at?: number;
}

export interface TaskPollCallback {
  onProgress?: (task: Task) => void;
  onComplete?: (task: Task) => void;
  onError?: (task: Task) => void;
}

// 轮询间隔（毫秒）
const POLL_INTERVAL = 2000; // 2秒

// 活跃的轮询器
const activePollers: Map<string, NodeJS.Timeout> = new Map();

/**
 * 获取任务状态
 */
export const getTask = async (taskId: string): Promise<Task> => {
  try {
    return await apiRequest<Task>(`/api/tasks/${taskId}`, {
      method: 'GET',
    });
  } catch (error: any) {
    throw new Error(`获取任务状态失败: ${error.message || '未知错误'}`);
  }
};

/**
 * 获取小说的任务列表
 */
export const getNovelTasks = async (
  novelId: string,
  status?: string
): Promise<Task[]> => {
  try {
    const url = status
      ? `/api/novels/${novelId}/tasks?status=${status}`
      : `/api/novels/${novelId}/tasks`;
    return await apiRequest<Task[]>(url, {
      method: 'GET',
    });
  } catch (error: any) {
    throw new Error(`获取任务列表失败: ${error.message || '未知错误'}`);
  }
};

/**
 * 获取当前用户的活跃任务
 */
export const getActiveTasks = async (): Promise<Task[]> => {
  try {
    return await apiRequest<Task[]>('/api/tasks/active', {
      method: 'GET',
    });
  } catch (error: any) {
    throw new Error(`获取活跃任务失败: ${error.message || '未知错误'}`);
  }
};

/**
 * 开始轮询任务状态
 */
export const startPolling = (
  taskId: string,
  callback: TaskPollCallback
): void => {
  // 如果已经有轮询器在运行，先停止它
  stopPolling(taskId);

  const poll = async () => {
    try {
      const task = await getTask(taskId);

      // 调用进度回调
      if (callback.onProgress) {
        callback.onProgress(task);
      }

      // 如果任务完成
      if (task.status === 'completed') {
        stopPolling(taskId);
        if (callback.onComplete) {
          callback.onComplete(task);
        }
        return;
      }

      // 如果任务失败
      if (task.status === 'failed') {
        stopPolling(taskId);
        if (callback.onError) {
          callback.onError(task);
        }
        return;
      }

      // 如果任务仍在运行或等待中，继续轮询
      if (task.status === 'pending' || task.status === 'running') {
        const timeout = setTimeout(poll, POLL_INTERVAL);
        activePollers.set(taskId, timeout);
      }
    } catch (error) {
      console.error(`轮询任务 ${taskId} 失败:`, error);
      // 出错时停止轮询
      stopPolling(taskId);
      if (callback.onError) {
        callback.onError({
          id: taskId,
          novel_id: '',
          task_type: '',
          status: 'failed',
          progress: 0,
          error_message: '轮询失败',
          created_at: Date.now(),
          updated_at: Date.now(),
        } as Task);
      }
    }
  };

  // 立即执行一次
  poll();
};

/**
 * 停止轮询任务状态
 */
export const stopPolling = (taskId: string): void => {
  const timeout = activePollers.get(taskId);
  if (timeout) {
    clearTimeout(timeout);
    activePollers.delete(taskId);
  }
};

/**
 * 停止所有轮询
 */
export const stopAllPolling = (): void => {
  activePollers.forEach((timeout) => clearTimeout(timeout));
  activePollers.clear();
};

