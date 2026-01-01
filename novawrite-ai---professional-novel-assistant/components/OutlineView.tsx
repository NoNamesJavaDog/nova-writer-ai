
import React, { useState } from 'react';
import { Novel, Chapter, Volume } from '../types';
import { Sparkles, Plus, Trash2, ListTree, BookOpen, FileText, MessageCircle } from 'lucide-react';
import { writeChapterContent } from '../services/geminiService';
import Console, { LogEntry } from './Console';
import OutlineChat from './OutlineChat';

interface OutlineViewProps {
  novel: Novel;
  updateNovel: (updates: Partial<Novel>) => void;
  loadNovels?: () => Promise<void>;  // 添加重新加载函数
}

const OutlineView: React.FC<OutlineViewProps> = ({ novel, updateNovel, loadNovels }) => {
  const [loading, setLoading] = useState(false);
  const [loadingVolumeIdx, setLoadingVolumeIdx] = useState<number | null>(null);
  const [loadingAllVolumeOutlines, setLoadingAllVolumeOutlines] = useState(false);
  const [loadingAllChapters, setLoadingAllChapters] = useState(false);
  const [expandedVolumeIdx, setExpandedVolumeIdx] = useState<number | null>(null);
  const [chapterCountInput, setChapterCountInput] = useState<{ [key: number]: string }>({});
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [showConsole, setShowConsole] = useState(false);
  const [consoleMinimized, setConsoleMinimized] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [writingVolumeIdx, setWritingVolumeIdx] = useState<number | null>(null); // 正在批量写作的卷索引
  const [writingProgress, setWritingProgress] = useState<{ current: number; total: number } | null>(null); // 写作进度

  // 添加日志
  const addLog = (type: LogEntry['type'], message: string) => {
    const logEntry: LogEntry = {
      id: `log-${Date.now()}-${Math.random()}`,
      timestamp: Date.now(),
      type,
      message
    };
    setLogs(prev => [...prev, logEntry]);
    const consoleMethod = type === 'error' ? 'error' : type === 'warning' ? 'warn' : 'log';
    console[consoleMethod](message);
  };

  // 追加流式内容到最后一个日志条目
  const appendStreamChunk = (chunk: string) => {
    if (!chunk) return;
    setLogs(prev => {
      const lastLog = prev[prev.length - 1];
      if (lastLog && lastLog.type === 'stream') {
        // 如果最后一条是流式日志，追加内容
        return [...prev.slice(0, -1), { ...lastLog, message: lastLog.message + chunk }];
      } else {
        // 否则创建新的流式日志条目
        const streamLog: LogEntry = {
          id: `stream-${Date.now()}-${Math.random()}`,
          timestamp: Date.now(),
          type: 'stream',
          message: chunk
        };
        return [...prev, streamLog];
      }
    });
  };

  // 清空日志
  const clearLogs = () => {
    setLogs([]);
  };

  // 生成卷的详细大纲
  const handleGenVolumeOutline = async (volumeIndex: number) => {
    if (!novel.fullOutline || !novel.title) {
      alert("请先生成完整大纲！");
      return;
    }
    
    if (!novel.volumes || volumeIndex >= novel.volumes.length || volumeIndex < 0) {
      alert("错误：卷信息无效");
      return;
    }
    
    if (loadingVolumeIdx !== null) {
      return;
    }
    
    setLoadingVolumeIdx(volumeIndex);
    setShowConsole(true);
    setConsoleMinimized(false);
    clearLogs();
    
    try {
      const volume = novel.volumes[volumeIndex];
      addLog('step', `🚀 正在调用后端生成第 ${volumeIndex + 1} 卷《${volume.title}》的详细大纲...`);
      addLog('info', '💡 所有业务逻辑在后端完成，数据将直接保存到数据库');
      
      // 调用后端任务API
      const { apiRequest } = await import('../services/apiService');
      const taskResult = await apiRequest<{task_id: string; status: string; message: string}>(
        `/api/novels/${novel.id}/volumes/${volumeIndex}/generate-outline`,
        { method: 'POST' }
      );
      
      if (!taskResult.task_id) {
        throw new Error('任务创建失败：未返回任务ID');
      }
      
      addLog('success', `✅ 任务已创建 (ID: ${taskResult.task_id})`);
      addLog('info', '⏳ 正在后台生成，请等待...');
      
      // 轮询任务状态
      const taskServiceModule = await import('../services/taskService');
      const { startPolling } = taskServiceModule;
      
      await new Promise<void>((resolve, reject) => {
        startPolling(taskResult.task_id, {
          onProgress: (task) => {
            const progress = task.progress || 0;
            const message = task.progress_message || '处理中...';
            addLog('info', `⏳ ${progress}% - ${message}`);
          },
          onComplete: async (task) => {
            addLog('success', '✅ 卷大纲生成完成！后端已自动保存');
            addLog('info', '🔄 正在重新加载最新数据...');
            
            // 重新加载小说数据（后端已经保存）
            if (loadNovels) {
              await loadNovels();
              addLog('success', '✅ 数据加载完成！');
            }
            
            resolve();
          },
          onError: (task) => {
            addLog('error', `❌ 任务失败: ${task.error_message || '未知错误'}`);
            reject(new Error(task.error_message || '任务执行失败'));
          },
        });
      });
      
    } catch (err: any) {
      addLog('error', `❌ 生成失败: ${err?.message || '未知错误'}`);
      alert(`生成卷大纲失败：${err?.message || '未知错误'}`);
    } finally {
      setLoadingVolumeIdx(null);
    }
  };

  // 一键生成所有卷的详细大纲（后端任务：可选跳过已有卷大纲）
  const handleGenAllVolumeOutlines = async () => {
    if (!novel.id) {
      alert("小说ID无效");
      return;
    }

    if (!novel.fullOutline || !novel.title) {
      alert("请先生成完整大纲！");
      return;
    }

    if (!novel.volumes || novel.volumes.length === 0) {
      alert("还没有卷结构，无法生成卷大纲");
      return;
    }

    if (loadingAllVolumeOutlines || loadingVolumeIdx !== null) {
      return;
    }

    const force = window.confirm('是否覆盖已存在的卷大纲？\n\n选择“确定”：全部重新生成并覆盖\n选择“取消”：只生成缺失卷大纲的卷');

    setLoadingAllVolumeOutlines(true);
    setShowConsole(true);
    setConsoleMinimized(false);
    clearLogs();

    try {
      addLog('step', `✨ 正在创建“一键生成全部卷大纲”任务...`);
      addLog('info', `📚 卷数量: ${novel.volumes.length}；模式: ${force ? '覆盖已有' : '仅补全缺失'}`);

      const { apiRequest } = await import('../services/apiService');
      const params = force ? `?force=true` : '';
      const taskResult = await apiRequest<{task_id: string; status: string; message: string}>(
        `/api/novels/${novel.id}/generate-all-volume-outlines${params}`,
        { method: 'POST' }
      );

      if (!taskResult.task_id) {
        throw new Error('任务创建失败：未返回任务ID');
      }

      addLog('success', `✅ 任务已创建 (ID: ${taskResult.task_id})`);
      addLog('info', '⏳ 正在后台生成，请等待...');

      const taskServiceModule = await import('../services/taskService');
      const { startPolling } = taskServiceModule;

      await new Promise<void>((resolve, reject) => {
        startPolling(taskResult.task_id, {
          onProgress: (task) => {
            const progress = task.progress || 0;
            const message = task.progress_message || '处理中...';
            addLog('info', `📈 ${progress}% - ${message}`);
          },
          onComplete: async () => {
            addLog('success', '✅ 全部卷大纲生成完成！后端已自动保存');
            addLog('info', '🔄 正在重新加载最新数据...');
            if (loadNovels) {
              await loadNovels();
              addLog('success', '✅ 数据加载完成！');
            }
            resolve();
          },
          onError: (task) => {
            addLog('error', `❌ 任务失败: ${task.error_message || '未知错误'}`);
            reject(new Error(task.error_message || '任务执行失败'));
          },
        });
      });
    } catch (err: any) {
      addLog('error', `❌ 生成失败: ${err?.message || '未知错误'}`);
      alert(`一键生成卷大纲失败：${err?.message || '未知错误'}`);
    } finally {
      setLoadingAllVolumeOutlines(false);
    }
  };

  // 一键生成所有卷的章节列表（连贯且尽量不重复）
  const handleGenAllChapters = async () => {
    if (!novel.id) {
      alert("小说ID无效");
      return;
    }

    if (!novel.fullOutline || !novel.title) {
      alert("请先生成完整大纲！");
      return;
    }

    if (!novel.volumes || novel.volumes.length === 0) {
      alert("还没有卷结构，无法生成章节列表");
      return;
    }

    if (loadingAllChapters || loadingVolumeIdx !== null || loadingAllVolumeOutlines) {
      return;
    }

    const force = window.confirm('是否覆盖已存在的章节列表？\n\n选择“确定”：全部重新生成并覆盖\n选择“取消”：只生成没有章节的卷');

    const chapterCountText = window.prompt('每卷章节数（1-50，留空则自动决定）：', '');
    let chapterCount: number | undefined;
    if (chapterCountText && chapterCountText.trim()) {
      const parsed = parseInt(chapterCountText.trim(), 10);
      if (!isNaN(parsed) && parsed >= 1 && parsed <= 50) {
        chapterCount = parsed;
      } else {
        alert("章节数量必须是 1-50 之间的数字");
        return;
      }
    }

    setLoadingAllChapters(true);
    setShowConsole(true);
    setConsoleMinimized(false);
    clearLogs();

    try {
      addLog('step', `✨ 正在创建“一键生成全部章节列表”任务...`);
      addLog('info', `📚 卷数量: ${novel.volumes.length}；模式: ${force ? '覆盖已有' : '仅补全缺失'}`);
      if (chapterCount) {
        addLog('info', `📌 每卷章节数: ${chapterCount}`);
      } else {
        addLog('info', '📌 每卷章节数: 自动决定');
      }

      const { apiRequest } = await import('../services/apiService');
      const params = new URLSearchParams();
      if (force) params.set('force', 'true');
      if (chapterCount) params.set('chapter_count', String(chapterCount));
      const qs = params.toString() ? `?${params.toString()}` : '';

      const taskResult = await apiRequest<{task_id: string; status: string; message: string}>(
        `/api/novels/${novel.id}/generate-all-chapters${qs}`,
        { method: 'POST' }
      );

      if (!taskResult.task_id) {
        throw new Error('任务创建失败：未返回任务ID');
      }

      addLog('success', `✅ 任务已创建 (ID: ${taskResult.task_id})`);
      addLog('info', '⏳ 正在后台生成，请等待...');

      const taskServiceModule = await import('../services/taskService');
      const { startPolling } = taskServiceModule;

      await new Promise<void>((resolve, reject) => {
        startPolling(taskResult.task_id, {
          onProgress: (task) => {
            const progress = task.progress || 0;
            const message = task.progress_message || '处理中...';
            addLog('info', `📈 ${progress}% - ${message}`);
          },
          onComplete: async () => {
            addLog('success', '✅ 全部章节列表生成完成！后端已自动保存');
            addLog('info', '🔄 正在重新加载最新数据...');
            if (loadNovels) {
              await loadNovels();
              addLog('success', '✅ 数据加载完成！');
            }
            resolve();
          },
          onError: (task) => {
            addLog('error', `❌ 任务失败: ${task.error_message || '未知错误'}`);
            reject(new Error(task.error_message || '任务执行失败'));
          },
        });
      });
    } catch (err: any) {
      addLog('error', `❌ 生成失败: ${err?.message || '未知错误'}`);
      alert(`一键生成章节列表失败：${err?.message || '未知错误'}`);
    } finally {
      setLoadingAllChapters(false);
    }
  };

  // 生成指定卷的章节列表
  const handleGenChapters = async (volumeIndex: number) => {
    if (!novel.id) {
      alert("小说ID无效");
      return;
    }
    
    if (!novel.volumes || volumeIndex >= novel.volumes.length) {
      alert("错误：卷信息无效");
      return;
    }
    
    if (loadingVolumeIdx !== null) {
      return;
    }
    
    // 解析章节数量（如果用户指定了）
    let chapterCount: number | undefined;
    const inputValue = chapterCountInput[volumeIndex];
    if (inputValue && inputValue.trim()) {
      const parsed = parseInt(inputValue.trim(), 10);
      if (!isNaN(parsed) && parsed > 0 && parsed <= 50) {
        chapterCount = parsed;
      } else {
        alert("章节数量必须是 1-50 之间的数字");
        return;
      }
    }
    
    setLoadingVolumeIdx(volumeIndex);
    setShowConsole(true);
    setConsoleMinimized(false);
    clearLogs();
    
    try {
      const volume = novel.volumes[volumeIndex];
      addLog('step', `🚀 正在调用后端生成第 ${volumeIndex + 1} 卷《${volume.title}》的章节列表...`);
      addLog('info', '💡 所有业务逻辑在后端完成，数据将直接保存到数据库');
      if (!volume.outline || !volume.outline.trim()) {
        addLog('warning', '⚠️ 当前卷还没有“卷详细大纲”，直接生成章节容易出现串卷/重复；后端会自动补全卷大纲后再生成章节。');
      }
      if (chapterCount) {
        addLog('info', `📊 指定章节数量: ${chapterCount} 章`);
      }
      
      // 调用后端任务API
      const { apiRequest } = await import('../services/apiService');
      const params = chapterCount ? `?chapter_count=${chapterCount}` : '';
      const taskResult = await apiRequest<{task_id: string; status: string; message: string}>(
        `/api/novels/${novel.id}/volumes/${volumeIndex}/generate-chapters${params}`,
        { method: 'POST' }
      );
      
      if (!taskResult.task_id) {
        throw new Error('任务创建失败：未返回任务ID');
      }
      
      addLog('success', `✅ 任务已创建 (ID: ${taskResult.task_id})`);
      addLog('info', '⏳ 正在后台生成，请等待...');
      
      // 轮询任务状态
      const taskServiceModule = await import('../services/taskService');
      const { startPolling } = taskServiceModule;
      
      await new Promise<void>((resolve, reject) => {
        startPolling(taskResult.task_id, {
          onProgress: (task) => {
            const progress = task.progress || 0;
            const message = task.progress_message || '处理中...';
            addLog('info', `⏳ ${progress}% - ${message}`);
          },
          onComplete: async (task) => {
            addLog('success', '✅ 章节列表生成完成！后端已自动保存');
            addLog('info', '🔄 正在重新加载最新数据...');
            
            // 重新加载小说数据（后端已经保存）
            if (loadNovels) {
              await loadNovels();
              addLog('success', '✅ 数据加载完成！');
            }
            
            resolve();
          },
          onError: (task) => {
            addLog('error', `❌ 任务失败: ${task.error_message || '未知错误'}`);
            reject(new Error(task.error_message || '任务执行失败'));
          },
        });
      });
      
    } catch (err: any) {
      addLog('error', `❌ 生成失败: ${err?.message || '未知错误'}`);
      alert(`生成章节失败：${err?.message || '未知错误'}`);
    } finally {
      setLoadingVolumeIdx(null);
    }
  };

  // 一键写作本卷所有章节（优化版：支持同步向量存储和智能延迟）
  const handleWriteAllChapters = async (volumeIndex: number) => {
    if (!novel.volumes || volumeIndex >= novel.volumes.length) {
      alert('卷信息无效');
      return;
    }
    
    const volume = novel.volumes[volumeIndex];
    if (!volume.chapters || volume.chapters.length === 0) {
      alert('请先生成章节列表！');
      return;
    }
    
    // 筛选出没有内容的章节（需要生成的章节）
    const chaptersToWrite = volume.chapters
      .map((ch, idx) => ({ chapter: ch, index: idx }))
      .filter(({ chapter }) => !chapter.content || !chapter.content.trim());
    
    if (chaptersToWrite.length === 0) {
      alert('本卷所有章节都已生成内容！');
      return;
    }
    
    const chaptersWithContent = volume.chapters.length - chaptersToWrite.length;
    if (chaptersWithContent > 0) {
      addLog('info', `ℹ️ 本卷已有 ${chaptersWithContent} 个章节有内容，将跳过这些章节`);
    }
    
    setWritingVolumeIdx(volumeIndex);
    setWritingProgress({ current: 0, total: chaptersToWrite.length });
    setShowConsole(true);
    setConsoleMinimized(false);
    clearLogs();
    
    // 新增：预热向量存储（为已有内容的章节）
    if (chaptersWithContent > 0) {
      addLog('step', '🔥 预热向量存储：为已有章节建立语义索引...');
      const { chapterApi } = await import('../services/apiService');
      let preheatedCount = 0;
      for (let i = 0; i < volume.chapters.length; i++) {
        const chapter = volume.chapters[i];
        if (chapter.content && chapter.content.trim() && chapter.id) {
          try {
            await chapterApi.storeEmbeddingSync(chapter.id);
            preheatedCount++;
          } catch (err) {
            // 预热失败不影响主流程，只记录日志
            console.warn(`预热章节 ${i + 1} 向量失败:`, err);
          }
        }
      }
      addLog('success', `✅ 向量预热完成：已为 ${preheatedCount} 个章节建立语义索引`);
      addLog('info', '💡 现在开始批量生成，AI将能够获取更准确的上下文');
    }
    
    try {
      addLog('step', `🚀 开始批量生成第 ${volumeIndex + 1} 卷《${volume.title}》的未写作章节...`);
      addLog('info', `📚 共 ${chaptersToWrite.length} 个章节需要生成（跳过 ${chaptersWithContent} 个已有内容的章节）`);
      addLog('info', '🧠 智能延迟策略：前3章间隔3秒（建立上下文），后续章节间隔1.5秒');
      
      const updatedVolumes = [...novel.volumes];
      let successCount = 0;
      let failCount = 0;
      let skippedCount = 0;
      const { chapterApi } = await import('../services/apiService');
      
      // 逐章生成（只生成没有内容的章节）
      for (let i = 0; i < volume.chapters.length; i++) {
        const chapter = volume.chapters[i];
        
        // 检查章节是否已有内容
        if (chapter.content && chapter.content.trim()) {
          skippedCount++;
          addLog('info', `⏭️ [${i + 1}/${volume.chapters.length}] 跳过第 ${i + 1} 章《${chapter.title}》（已有内容）`);
          continue;
        }
        
        // 计算当前进度（基于需要生成的章节）
        const currentProgress = chaptersToWrite.findIndex(({ index }) => index === i) + 1;
        setWritingProgress({ current: currentProgress, total: chaptersToWrite.length });
        
        try {
          addLog('step', `📝 [${currentProgress}/${chaptersToWrite.length}] 正在生成第 ${i + 1} 章《${chapter.title}》...`);
          
          // 创建流式传输回调
          const onChunk = (chunk: string, isComplete: boolean) => {
            if (isComplete) {
              addLog('success', `✅ 第 ${i + 1} 章内容生成完成！`);
            } else if (chunk) {
              appendStreamChunk(chunk);
            }
          };
          
          const content = await writeChapterContent(novel, i, volumeIndex, onChunk);
          
          if (content && content.trim()) {
            // 更新章节内容
            updatedVolumes[volumeIndex].chapters[i].content = content;
            updateNovel({ volumes: updatedVolumes });
            successCount++;
            addLog('info', `📄 第 ${i + 1} 章内容长度: ${content.length} 字符`);
            
            // 新增：同步存储向量（确保下一章能获取到上下文）
            if (chapter.id) {
              addLog('step', `🔄 正在存储第 ${i + 1} 章的语义向量...`);
              try {
                const result = await chapterApi.storeEmbeddingSync(chapter.id);
                if (result.stored) {
                  addLog('success', `✅ 第 ${i + 1} 章向量存储成功！`);
                } else {
                  addLog('info', `ℹ️ 第 ${i + 1} 章向量存储跳过：${result.message}`);
                }
              } catch (storeErr: any) {
                addLog('warning', `⚠️ 第 ${i + 1} 章向量存储失败: ${storeErr?.message || '未知错误'}`);
                addLog('info', '💡 继续生成下一章（向量将在后台异步存储）');
              }
            }
          } else {
            throw new Error('生成的内容为空');
          }
          
          // 智能延迟策略：前3章间隔3秒，后续1.5秒
          if (currentProgress < chaptersToWrite.length) {
            const delay = currentProgress <= 3 ? 3000 : 1500;
            addLog('info', `⏳ 等待 ${delay / 1000} 秒后继续生成下一章...`);
            await new Promise(resolve => setTimeout(resolve, delay));
          }
        } catch (err: any) {
          failCount++;
          addLog('error', `❌ 第 ${i + 1} 章生成失败: ${err?.message || '未知错误'}`);
          // 继续生成下一章，不中断整个流程
        }
      }
      
      // 最终统计
      addLog('success', `\n🎉 批量生成完成！`);
      addLog('info', `✅ 成功: ${successCount} 章`);
      if (skippedCount > 0) {
        addLog('info', `⏭️ 跳过: ${skippedCount} 章（已有内容）`);
      }
      if (failCount > 0) {
        addLog('warning', `⚠️ 失败: ${failCount} 章`);
        addLog('info', '💡 可以单独重新生成失败的章节');
      }
      
      const summaryMessage = `批量生成完成！\n成功: ${successCount} 章\n${skippedCount > 0 ? `跳过: ${skippedCount} 章（已有内容）\n` : ''}${failCount > 0 ? `失败: ${failCount} 章` : ''}`;
      alert(summaryMessage);
    } catch (err: any) {
      addLog('error', `❌ 批量生成过程中出现错误: ${err?.message || '未知错误'}`);
      alert(`批量生成失败：${err?.message || '未知错误'}`);
    } finally {
      setWritingVolumeIdx(null);
      setWritingProgress(null);
    }
  };

  // 添加新卷
  const handleAddVolume = () => {
    const currentVolumes = novel.volumes || [];
    const newVolume: Volume = {
      id: `vol-${Date.now()}`,
      title: `第${currentVolumes.length + 1}卷`,
      summary: '',
      outline: '',
      chapters: []
    };
    updateNovel({ volumes: [...currentVolumes, newVolume] });
  };

  return (
    <div className="max-w-6xl mx-auto py-4 md:py-8 px-4 md:px-6 space-y-4 md:space-y-6">
      {/* 完整大纲区域 */}
      <section className="bg-white p-4 md:p-6 rounded-xl border shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <h3 className="font-bold text-lg md:text-xl text-slate-800 flex items-center gap-2">
            <ListTree size={20} className="text-indigo-600" />
            完整故事结构
          </h3>
          <button
            onClick={() => setShowChat(true)}
            className="px-4 py-2.5 md:py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 active:bg-indigo-800 transition-all flex items-center justify-center gap-2 min-h-[44px] md:min-h-0"
            title="通过对话修改大纲"
          >
            <MessageCircle size={16} />
            <span>对话修改大纲</span>
          </button>
        </div>
        <textarea 
          value={novel.fullOutline}
          onChange={(e) => updateNovel({ fullOutline: e.target.value })}
          rows={12}
          placeholder="尚未生成大纲..."
          className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none text-sm font-mono leading-relaxed bg-slate-50"
        />
      </section>

      {/* 卷列表区域 */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2">
            <BookOpen size={18} className="text-indigo-600" />
            卷结构 ({novel.volumes?.length || 0})
          </h3>
          <div className="flex items-center gap-2">
            <button
              onClick={handleGenAllVolumeOutlines}
              disabled={loadingAllVolumeOutlines || loadingAllChapters || loadingVolumeIdx !== null || !novel.fullOutline || !novel.volumes || novel.volumes.length === 0}
              className="px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 disabled:bg-slate-200 disabled:text-slate-400 transition-all flex items-center gap-2"
              title="一键生成全部卷的详细大纲（可选择是否覆盖已有卷大纲）"
            >
              {loadingAllVolumeOutlines ? (
                <>
                  <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  生成中...
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  一键生成卷大纲
                </>
              )}
            </button>
            <button
              onClick={handleGenAllChapters}
              disabled={loadingAllChapters || loadingAllVolumeOutlines || loadingVolumeIdx !== null || !novel.fullOutline || !novel.volumes || novel.volumes.length === 0}
              className="px-4 py-2 bg-green-600 text-white text-sm font-semibold rounded-lg hover:bg-green-700 disabled:bg-slate-200 disabled:text-slate-400 transition-all flex items-center gap-2"
              title="一键生成所有卷的章节列表（按卷顺序生成，尽量确保连贯且不重复）"
            >
              {loadingAllChapters ? (
                <>
                  <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  生成中...
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  一键生成章节列表
                </>
              )}
            </button>
            <button
              onClick={handleAddVolume}
              className="px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 transition-all flex items-center gap-2"
            >
              <Plus size={16} />
              添加卷
            </button>
          </div>
        </div>

        {!novel.volumes || novel.volumes.length === 0 ? (
          <div className="bg-white p-8 rounded-xl border border-dashed text-center">
            <p className="text-slate-400">还没有卷。请先在仪表板生成完整大纲，或手动添加卷。</p>
          </div>
        ) : (
          <div className="space-y-4">
            {novel.volumes.map((volume, volumeIdx) => (
              <div key={volume.id} className="bg-white rounded-xl border shadow-sm overflow-hidden">
                {/* 卷头部 */}
                <div 
                  className="p-4 bg-slate-50 border-b cursor-pointer hover:bg-slate-100 transition-colors"
                  onClick={() => setExpandedVolumeIdx(expandedVolumeIdx === volumeIdx ? null : volumeIdx)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1">
                      <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center font-bold text-indigo-700">
                        {volumeIdx + 1}
                      </div>
                      <div className="flex-1">
                        <input
                          type="text"
                          value={volume.title || ''}
                          onChange={(e) => {
                            if (!novel.volumes || volumeIdx >= novel.volumes.length) return;
                            const updated = [...novel.volumes];
                            updated[volumeIdx].title = e.target.value;
                            updateNovel({ volumes: updated });
                          }}
                          onClick={(e) => e.stopPropagation()}
                          className="text-lg font-bold text-slate-800 bg-transparent border-none focus:outline-none focus:ring-0 p-0 w-full"
                        />
                        {volume.summary && (
                          <p className="text-xs text-slate-500 mt-1 line-clamp-1">{volume.summary}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-400">
                        {volume.chapters?.length || 0} 章
                      </span>
                    </div>
                  </div>
                </div>

                {/* 卷内容（展开时显示） */}
                {expandedVolumeIdx === volumeIdx && (
                  <div className="p-6 space-y-4">
                    {/* 卷描述编辑 */}
                    <div>
                      <label className="block text-xs font-medium text-slate-600 mb-1">卷描述</label>
                      <textarea
                        value={volume.summary || ''}
                        onChange={(e) => {
                          if (!novel.volumes || volumeIdx >= novel.volumes.length) return;
                          const updated = [...novel.volumes];
                          updated[volumeIdx].summary = e.target.value;
                          updateNovel({ volumes: updated });
                        }}
                        rows={2}
                        placeholder="简要描述本卷的内容..."
                        className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                      />
                    </div>

                    {/* 卷详细大纲 */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <label className="block text-xs font-medium text-slate-600">卷详细大纲</label>
                        <button
                          onClick={() => handleGenVolumeOutline(volumeIdx)}
                          disabled={loadingVolumeIdx === volumeIdx || !novel.fullOutline}
                          className="px-3 py-1 bg-indigo-600 text-white text-xs font-semibold rounded-md hover:bg-indigo-700 disabled:bg-slate-200 disabled:text-slate-400 transition-all flex items-center gap-1"
                        >
                          {loadingVolumeIdx === volumeIdx ? (
                            <>
                              <span className="inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                              生成中...
                            </>
                          ) : (
                            <>
                              <FileText size={12} />
                              生成卷大纲
                            </>
                          )}
                        </button>
                      </div>
                      <textarea
                        value={volume.outline || ''}
                        onChange={(e) => {
                          if (!novel.volumes || volumeIdx >= novel.volumes.length) return;
                          const updated = [...novel.volumes];
                          updated[volumeIdx].outline = e.target.value;
                          updateNovel({ volumes: updated });
                        }}
                        rows={6}
                        placeholder={volume.outline ? '' : '点击"生成卷大纲"按钮生成详细大纲，或手动输入...'}
                        className="w-full px-3 py-2 border rounded-lg text-sm font-mono leading-relaxed bg-slate-50 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                      />
                    </div>

                    {/* 章节列表 */}
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-bold text-slate-700">
                          章节列表 ({volume.chapters?.length || 0})
                          {writingVolumeIdx === volumeIdx && writingProgress && (
                            <span className="ml-2 text-xs text-indigo-600 font-normal">
                              (正在生成: {writingProgress.current}/{writingProgress.total})
                            </span>
                          )}
                        </h4>
                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            min="1"
                            max="50"
                            placeholder="章节数（可选）"
                            value={chapterCountInput[volumeIdx] || ''}
                            onChange={(e) => setChapterCountInput(prev => ({ ...prev, [volumeIdx]: e.target.value }))}
                            disabled={loadingVolumeIdx === volumeIdx || writingVolumeIdx === volumeIdx}
                            className="w-24 px-2 py-1.5 text-xs border rounded-md focus:ring-2 focus:ring-indigo-500 focus:outline-none disabled:bg-slate-100 disabled:text-slate-400"
                            title="指定要生成的章节数量（1-50），留空则自动决定"
                          />
                          <button
                            onClick={() => handleGenChapters(volumeIdx)}
                            disabled={loadingVolumeIdx === volumeIdx || writingVolumeIdx === volumeIdx || !novel.fullOutline || !novel.title}
                            className="px-3 py-1.5 bg-indigo-600 text-white text-xs font-semibold rounded-md hover:bg-indigo-700 disabled:bg-slate-200 disabled:text-slate-400 transition-all flex items-center gap-1"
                          >
                            {loadingVolumeIdx === volumeIdx ? (
                              <>
                                <span className="inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                                生成中...
                              </>
                            ) : (
                              <>
                                <Sparkles size={12} />
                                生成章节
                              </>
                            )}
                          </button>
                          {volume.chapters && volume.chapters.length > 0 && (
                            <button
                              onClick={() => handleWriteAllChapters(volumeIdx)}
                              disabled={writingVolumeIdx === volumeIdx || loadingVolumeIdx === volumeIdx}
                              className="px-3 py-1.5 bg-green-600 text-white text-xs font-semibold rounded-md hover:bg-green-700 disabled:bg-slate-200 disabled:text-slate-400 transition-all flex items-center gap-1"
                              title="一键生成本卷所有章节的内容"
                            >
                              {writingVolumeIdx === volumeIdx ? (
                                <>
                                  <span className="inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                                  写作中 {writingProgress ? `(${writingProgress.current}/${writingProgress.total})` : ''}
                                </>
                              ) : (
                                <>
                                  <FileText size={12} />
                                  一键写作本卷
                                </>
                              )}
                            </button>
                          )}
                        </div>
                      </div>
                      
                      {!volume.chapters || volume.chapters.length === 0 ? (
                        <p className="text-xs text-slate-400 italic text-center py-4">暂无章节。点击"生成章节"按钮生成章节列表。</p>
                      ) : (
                        <div className="space-y-2 max-h-[300px] overflow-y-auto">
                          {volume.chapters.map((ch, chIdx) => (
                            <div key={ch.id} className="p-3 bg-slate-50 border rounded-lg text-xs hover:border-indigo-300 transition-colors">
                              <div className="flex justify-between items-start mb-1">
                                <span className="font-bold text-slate-700">
                                  第 {(novel.volumes?.slice(0, volumeIdx).reduce((acc, v) => acc + (v.chapters?.length || 0), 0) || 0) + chIdx + 1} 章: {ch.title}
                                </span>
                              </div>
                              <p className="text-slate-500 line-clamp-2 mb-1">{ch.summary}</p>
                              {ch.aiPromptHints && (
                                <p className="text-slate-400 text-[10px] italic line-clamp-1">提示: {ch.aiPromptHints}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 生成控制台 */}
      <Console
        logs={logs}
        showConsole={showConsole}
        consoleMinimized={consoleMinimized}
        onClose={() => setShowConsole(false)}
        onMinimize={setConsoleMinimized}
        onClear={clearLogs}
      />

      {/* 对话修改大纲弹窗 */}
      {showChat && (
        <OutlineChat
          novel={novel}
          updateNovel={updateNovel}
          onClose={() => setShowChat(false)}
          loadNovels={loadNovels}
        />
      )}
    </div>
  );
};

export default OutlineView;
