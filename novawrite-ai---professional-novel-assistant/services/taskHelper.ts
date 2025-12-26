// 任务辅助函数
import { apiRequest } from './apiService';
import type { Task } from './taskService';

/**
 * 等待任务完成并返回结果
 * @param taskId 任务ID
 * @param timeout 超时时间（毫秒），默认 5 分钟
 * @returns 任务结果
 */
export async function waitForTask<T = any>(
  taskId: string,
  timeout: number = 5 * 60 * 1000
): Promise<T> {
  const startTime = Date.now();
  const pollInterval = 2000; // 每2秒轮询一次

  while (true) {
    // 检查超时
    if (Date.now() - startTime > timeout) {
      throw new Error(`任务等待超时: ${taskId}`);
    }

    // 获取任务状态
    const task = await apiRequest<Task>(`/api/tasks/${taskId}`);

    if (task.status === 'completed') {
      if (task.result) {
        return task.result as T;
      } else {
        throw new Error('任务完成但结果为空');
      }
    }

    if (task.status === 'failed') {
      throw new Error(task.error_message || '任务执行失败');
    }

    // 如果任务还在运行或等待中，继续轮询
    if (task.status === 'running' || task.status === 'pending') {
      await new Promise(resolve => setTimeout(resolve, pollInterval));
      continue;
    }

    // 未知状态
    throw new Error(`任务状态异常: ${task.status}`);
  }
}

