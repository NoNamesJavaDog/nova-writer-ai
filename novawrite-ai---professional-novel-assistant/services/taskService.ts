// 任务服务 - 管理任务轮询和状态
import { apiRequest } from './apiService';

// 统一的任务接口定义
export interface Task {
  id: string;
  novel_id: string;
  task_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  progress_message?: string;
  result?: any;
  error_message?: string;
  created_at: number;
  updated_at: number;
  started_at?: number;
  completed_at?: number;
}

export interface PollingCallbacks {
  onProgress?: (task: Task) => void;
  onComplete: (task: Task) => void;
  onError: (task: Task) => void;
}

let pollingIntervals: Map<string, NodeJS.Timeout> = new Map();
let pollingErrorCounts: Map<string, number> = new Map();

/**
 * 开始轮询任务状态
 * @param taskId 任务ID
 * @param callbacks 回调函数
 * @param pollInterval 轮询间隔（毫秒），默认 2 秒
 */
export function startPolling(
  taskId: string,
  callbacks: PollingCallbacks,
  pollInterval: number = 2000
): void {
  // 如果已经在轮询，先清除
  if (pollingIntervals.has(taskId)) {
    clearInterval(pollingIntervals.get(taskId)!);
  }
  pollingErrorCounts.set(taskId, 0);

  const poll = async () => {
    try {
      const task = await apiRequest<Task>(`/api/tasks/${taskId}`);
      pollingErrorCounts.set(taskId, 0);

      if (task.status === 'completed') {
        clearInterval(pollingIntervals.get(taskId)!);
        pollingIntervals.delete(taskId);
        pollingErrorCounts.delete(taskId);
        callbacks.onComplete(task);
        return;
      }

      if (task.status === 'failed') {
        clearInterval(pollingIntervals.get(taskId)!);
        pollingIntervals.delete(taskId);
        pollingErrorCounts.delete(taskId);
        callbacks.onError(task);
        return;
      }

      // 如果任务还在运行或等待中，调用进度回调
      if ((task.status === 'running' || task.status === 'pending') && callbacks.onProgress) {
        callbacks.onProgress(task);
      }
    } catch (error: any) {
      const message = error?.message || '获取任务状态失败';

      // 登录过期时直接停止轮询
      if (message.includes('登录已过期')) {
        clearInterval(pollingIntervals.get(taskId)!);
        pollingIntervals.delete(taskId);
        pollingErrorCounts.delete(taskId);
        callbacks.onError({
          id: taskId,
          novel_id: '',
          task_type: '',
          status: 'failed',
          progress: 0,
          error_message: message,
          created_at: Date.now(),
          updated_at: Date.now(),
        } as Task);
        return;
      }

      // 网络抖动等临时错误：允许少量重试，不要立刻停止轮询
      const currentCount = (pollingErrorCounts.get(taskId) || 0) + 1;
      pollingErrorCounts.set(taskId, currentCount);
      if (currentCount < 5) {
        return;
      }

      clearInterval(pollingIntervals.get(taskId)!);
      pollingIntervals.delete(taskId);
      pollingErrorCounts.delete(taskId);
      callbacks.onError({
        id: taskId,
        novel_id: '',
        task_type: '',
        status: 'failed',
        progress: 0,
        error_message: message,
        created_at: Date.now(),
        updated_at: Date.now(),
      } as Task);
    }
  };

  // 立即执行一次
  poll();

  // 设置定时轮询
  const interval = setInterval(poll, pollInterval);
  pollingIntervals.set(taskId, interval);
}

/**
 * 停止轮询任务
 * @param taskId 任务ID
 */
export function stopPolling(taskId: string): void {
  if (pollingIntervals.has(taskId)) {
    clearInterval(pollingIntervals.get(taskId)!);
    pollingIntervals.delete(taskId);
    pollingErrorCounts.delete(taskId);
  }
}

/**
 * 获取任务详情
 * @param taskId 任务ID
 * @returns 任务对象
 */
export async function getTask(taskId: string): Promise<Task> {
  return apiRequest<Task>(`/api/tasks/${taskId}`);
}

/**
 * 获取当前用户的所有活跃任务（pending 或 running）
 * @returns 任务列表
 */
export async function getActiveTasks(): Promise<Task[]> {
  return apiRequest<Task[]>('/api/tasks/active');
}

/**
 * 获取小说的所有任务
 * @param novelId 小说ID
 * @param status 可选的状态过滤
 * @returns 任务列表
 */
export async function getNovelTasks(
  novelId: string,
  status?: 'pending' | 'running' | 'completed' | 'failed'
): Promise<Task[]> {
  const url = status
    ? `/api/tasks/novel/${novelId}?status=${status}`
    : `/api/tasks/novel/${novelId}`;
  return apiRequest<Task[]>(url);
}

