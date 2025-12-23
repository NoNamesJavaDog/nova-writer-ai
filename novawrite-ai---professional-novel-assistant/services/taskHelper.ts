// 任务辅助函数 - 用于等待任务完成并获取结果
import { startPolling, Task } from './taskService';

/**
 * 等待任务完成并返回结果
 */
export const waitForTask = <T = any>(
  taskId: string
): Promise<T> => {
  return new Promise<T>((resolve, reject) => {
    startPolling(taskId, {
      onProgress: (task: Task) => {
        // 进度更新时可以在这里处理
        console.log(`任务 ${taskId} 进度: ${task.progress}% - ${task.progress_message}`);
      },
      onComplete: (task: Task) => {
        if (task.result) {
          resolve(task.result as T);
        } else {
          reject(new Error('任务完成但结果为空'));
        }
      },
      onError: (task: Task) => {
        reject(new Error(task.error_message || '任务执行失败'));
      },
    });
  });
};

