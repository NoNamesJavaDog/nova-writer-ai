
import React, { useState, useEffect, useRef } from 'react';
import { Novel, Character, WorldSetting, TimelineEvent, Foreshadowing, Volume } from '../types';
import { Sparkles, ArrowRight, Users, Globe, History, Download } from 'lucide-react';
import { generateFullOutline, generateCharacters, generateWorldSettings, generateTimelineEvents, generateForeshadowings } from '../services/geminiService';
import { waitForTask } from '../services/taskHelper';
import Console, { LogEntry } from './Console';

interface DashboardProps {
  novel: Novel;
  updateNovel: (updates: Partial<Novel>) => void;
  onStartWriting: () => void;
  loadNovels?: () => Promise<void>;
}

const Dashboard: React.FC<DashboardProps> = ({ novel, updateNovel, onStartWriting, loadNovels }) => {
  const [loading, setLoading] = useState(false);
  const [generateExtras, setGenerateExtras] = useState(true); // 默认开启生成额外内容
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [showConsole, setShowConsole] = useState(false);
  const [consoleMinimized, setConsoleMinimized] = useState(false);
  const isMountedRef = useRef(true);

  useEffect(() => {
    // 组件挂载时设置为 true
    isMountedRef.current = true;
    console.log('✅ Dashboard 组件已挂载');
    
    return () => {
      // 组件卸载时设置为 false
      isMountedRef.current = false;
      console.log('❌ Dashboard 组件已卸载');
    };
  }, []);
  
  // 检查活跃任务的独立 useEffect
  useEffect(() => {
    if (!novel.id) return;
    
    const checkActiveTasks = async () => {
      try {
        // 使用 getActiveTasks 获取当前用户的所有活跃任务，然后过滤出当前小说的任务
        // 改为静态导入以避免初始化顺序问题
        const taskService = await import('../services/taskService');
        
        // 设置超时，避免因网络问题导致长时间等待
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('检查任务超时')), 5000)
        );
        
        const activeTasks = await Promise.race([
          taskService.getActiveTasks(),
          timeoutPromise
        ]) as any[];
        
        // 过滤出当前小说的大纲生成任务（运行中或等待中）
        const outlineTask = activeTasks.find(
          task => task.novel_id === novel.id && 
                  task.task_type === 'generate_complete_outline' && 
                  (task.status === 'running' || task.status === 'pending' || task.status === 'processing')
        );
        
        if (outlineTask) {
          // 恢复UI状态
          console.log(`🔄 发现正在执行的大纲生成任务: ${outlineTask.id}`);
          setShowConsole(true);
          setConsoleMinimized(false);
          setLoading(true);
          clearLogs();
          addLog('info', '🔄 检测到正在进行的大纲生成任务');
          addLog('info', `📋 任务ID: ${outlineTask.id}`);
          addLog('info', `📊 当前进度: ${outlineTask.progress || 0}%`);
          addLog('info', `💬 状态: ${outlineTask.progress_message || '处理中...'}`);
          
          // 继续轮询任务进度
          const { startPolling } = taskService;
          startPolling(outlineTask.id, {
            onProgress: (task) => {
              if (!isMountedRef.current) return;
              const progress = task.progress || 0;
              const message = task.progress_message || '处理中...';
              addLog('info', `⏳ ${progress}% - ${message}`);
            },
            onComplete: async (task) => {
              if (!isMountedRef.current) return;
              addLog('success', '✅ 完整大纲生成完成！');
              addLog('info', '🔄 正在从服务器加载最新数据...');
              if (loadNovels) {
                await loadNovels();
              }
              addLog('success', '✅ 数据加载完成！');
              addLog('info', '📊 生成内容统计：');
              addLog('info', `   - 完整大纲: ${novel.fullOutline ? '✓' : '✗'}`);
              addLog('info', `   - 卷结构: ${novel.volumes?.length || 0} 个`);
              addLog('info', `   - 角色: ${novel.characters?.length || 0} 个`);
              addLog('info', `   - 世界观: ${novel.worldSettings?.length || 0} 个`);
              addLog('info', `   - 时间线事件: ${novel.timeline?.length || 0} 个`);
              addLog('info', `   - 伏笔: ${novel.foreshadowings?.length || 0} 个`);
              addLog('success', '🎉 所有内容生成完成！');
              addLog('info', '✨ 准备跳转到大纲页面...');
              await new Promise(resolve => setTimeout(resolve, 2000));
              if (isMountedRef.current) {
                onStartWriting();
              }
            },
            onError: (task) => {
              if (!isMountedRef.current) return;
              addLog('error', `❌ 任务失败: ${task.error_message || '未知错误'}`);
              setLoading(false);
            },
          });
        }
      } catch (error: any) {
        // 静默失败，不显示错误（可能是网络问题或认证问题）
        console.debug('检查活跃任务失败（可忽略）:', error?.message || error);
      }
    };
    
    checkActiveTasks();
  }, [novel.id]);

  // 添加日志
  const addLog = (type: LogEntry['type'], message: string) => {
    const logEntry: LogEntry = {
      id: `log-${Date.now()}-${Math.random()}`,
      timestamp: Date.now(),
      type,
      message
    };
    setLogs(prev => [...prev, logEntry]);
    // 同时输出到浏览器控制台
    const consoleMethod = type === 'error' ? 'error' : type === 'warning' ? 'warn' : 'log';
    console[consoleMethod](message);
  };

  // 清空日志
  const clearLogs = () => {
    setLogs([]);
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

  // 导出全文
  const handleExportFullText = () => {
    try {
      let fullText = '';
      
      // 小说基本信息
      fullText += `《${novel.title}》\n`;
      fullText += `类型：${novel.genre}\n`;
      if (novel.synopsis) {
        fullText += `\n简介：\n${novel.synopsis}\n`;
      }
      fullText += '\n' + '='.repeat(50) + '\n\n';
      
      // 完整大纲
      if (novel.fullOutline) {
        fullText += '【完整大纲】\n\n';
        fullText += novel.fullOutline;
        fullText += '\n\n' + '='.repeat(50) + '\n\n';
      }
      
      // 所有卷和章节
      const volumes = novel.volumes || [];
      if (volumes.length > 0) {
        fullText += '【正文内容】\n\n';
        
        volumes.forEach((volume, volIdx) => {
          // 卷标题
          fullText += `\n${'='.repeat(50)}\n`;
          fullText += `第${volIdx + 1}卷：${volume.title}\n`;
          fullText += `${'='.repeat(50)}\n`;
          
          if (volume.summary) {
            fullText += `\n卷简介：${volume.summary}\n`;
          }
          
          if (volume.outline) {
            fullText += `\n卷大纲：\n${volume.outline}\n`;
          }
          
          // 章节内容
          const chapters = volume.chapters || [];
          chapters.forEach((chapter, chIdx) => {
            fullText += `\n\n${'-'.repeat(40)}\n`;
            fullText += `第${volIdx + 1}卷 第${chIdx + 1}章：${chapter.title}\n`;
            fullText += `${'-'.repeat(40)}\n`;
            
            if (chapter.summary) {
              fullText += `\n章节摘要：${chapter.summary}\n`;
            }
            
            if (chapter.content) {
              fullText += `\n${chapter.content}\n`;
            } else {
              fullText += '\n（本章节内容尚未生成）\n';
            }
          });
        });
      }
      
      // 创建下载链接
      const blob = new Blob([fullText], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${novel.title || '小说全文'}.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      addLog('success', '✅ 全文已导出！');
    } catch (err: any) {
      console.error('导出失败:', err);
      addLog('error', `❌ 导出失败: ${err?.message || '未知错误'}`);
      alert('导出失败，请稍后重试');
    }
  };

  const handleGenerateOutline = async () => {
    if (!novel.title || !novel.synopsis) {
      alert("请先提供标题和简介！");
      return;
    }
    
    if (!novel.id) {
      alert("小说ID不存在，请先保存小说！");
      return;
    }
    
    if (!isMountedRef.current) return;
    setLoading(true);
    setShowConsole(true);
    setConsoleMinimized(false);
    clearLogs();
    
    try {
      addLog('info', '📖 小说标题: 《' + novel.title + '》');
      addLog('info', '📚 类型: ' + novel.genre);
      addLog('info', '💡 简介: ' + novel.synopsis.substring(0, 100) + (novel.synopsis.length > 100 ? '...' : ''));
      addLog('step', '🚀 正在调用后端生成完整大纲（包括卷、角色、世界观、时间线、伏笔）...');
      addLog('info', '💡 所有业务逻辑在后端完成，数据将直接保存到数据库');
      
      // 调用新的后端接口
      const { apiRequest } = await import('../services/apiService');
      const taskResult = await apiRequest<{task_id: string; status: string; message: string}>(
        `/api/novels/${novel.id}/generate-complete-outline`,
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
            if (!isMountedRef.current) return;
            const progress = task.progress || 0;
            const message = task.progress_message || '处理中...';
            addLog('info', `⏳ ${progress}% - ${message}`);
          },
          onComplete: (task) => {
            if (!isMountedRef.current) return;
            addLog('success', '✅ 完整大纲生成完成！');
            resolve();
          },
          onError: (task) => {
            if (!isMountedRef.current) return;
            addLog('error', `❌ 任务失败: ${task.error_message || '未知错误'}`);
            reject(new Error(task.error_message || '任务执行失败'));
          },
        });
      });
      
      // 重新加载小说数据
      addLog('info', '🔄 正在从服务器加载最新数据...');
      
      // 调用父组件的loadNovels来重新加载所有小说
      if (loadNovels) {
        await loadNovels();
      }
      
      // 显示生成的内容统计
      addLog('success', '✅ 数据加载完成！');
      addLog('info', '📊 生成内容统计：');
      addLog('info', `   - 完整大纲: ${novel.fullOutline ? '✓' : '✗'}`);
      addLog('info', `   - 卷结构: ${novel.volumes?.length || 0} 个`);
      addLog('info', `   - 角色: ${novel.characters?.length || 0} 个`);
      addLog('info', `   - 世界观: ${novel.worldSettings?.length || 0} 个`);
      addLog('info', `   - 时间线事件: ${novel.timeline?.length || 0} 个`);
      addLog('info', `   - 伏笔: ${novel.foreshadowings?.length || 0} 个`);
      
      addLog('success', '🎉 所有内容生成完成！');
      addLog('info', '✨ 准备跳转到大纲页面...');
      
      // 延迟跳转
      await new Promise(resolve => setTimeout(resolve, 2000));
      if (isMountedRef.current) {
        onStartWriting();
      }
    } catch (err: any) {
      if (!isMountedRef.current) return;
      
      addLog('error', `❌ 生成失败: ${err?.message || '未知错误'}`);
      const errorMessage = err?.message || err?.toString() || '未知错误';
      
      // 添加详细的错误信息到日志
      addLog('error', '可能的原因：');
      addLog('error', '1. API Key 未配置或无效');
      addLog('error', '2. 网络连接问题');
      addLog('error', '3. 查看控制台获取详细信息');
      addLog('error', `API Key 状态: ${import.meta.env.VITE_GEMINI_API_KEY ? '已配置' : '未配置'}`);
      
      // 构建详细的错误提示
      let detailedMessage = `生成大纲失败：${errorMessage}\n\n`;
      detailedMessage += `可能的原因：\n`;
      detailedMessage += `1. API Key 未配置或无效\n`;
      detailedMessage += `   - 检查项目根目录是否有 .env.local 文件\n`;
      detailedMessage += `   - 确认文件中有：GEMINI_API_KEY=your_key\n`;
      detailedMessage += `   - 重启开发服务器（npm run dev）\n\n`;
      detailedMessage += `2. 网络连接问题\n`;
      detailedMessage += `   - 检查网络连接\n`;
      detailedMessage += `   - 如果使用代理，确保代理软件（127.0.0.1:7899）正在运行\n`;
      detailedMessage += `   - 浏览器可能需要配置系统代理\n\n`;
      detailedMessage += `3. 查看控制台获取详细错误信息\n\n`;
      detailedMessage += `当前 API Key 状态：${import.meta.env.VITE_GEMINI_API_KEY ? '已配置' : '未配置'}`;
      
      alert(detailedMessage);
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-6 md:py-12 px-4 md:px-6">
      <div className="mb-6 md:mb-10 text-center px-4 md:px-0">
        <h2 className="text-2xl md:text-3xl font-bold text-slate-900 mb-2">欢迎回来，作者</h2>
        <p className="text-sm md:text-base text-slate-500">让我们在 AI 的协助下创作您的下一部杰作。</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-8 px-4 md:px-0">
        <div className="bg-white p-4 md:p-6 rounded-xl border shadow-sm space-y-4">
          <h3 className="font-semibold text-lg text-slate-800">小说配置</h3>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">标题</label>
            <input 
              type="text" 
              value={novel.title}
              onChange={(e) => updateNovel({ title: e.target.value })}
              placeholder="永恒的回响"
              className="w-full px-3 py-2.5 md:py-2 text-base md:text-sm border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none min-h-[44px] md:min-h-0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">类型</label>
            <select 
              value={novel.genre}
              onChange={(e) => updateNovel({ genre: e.target.value })}
              className="w-full px-3 py-2.5 md:py-2 text-base md:text-sm border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none min-h-[44px] md:min-h-0"
            >
              <option>奇幻</option>
              <option>科幻</option>
              <option>悬疑</option>
              <option>言情</option>
              <option>惊悚</option>
              <option>历史</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">简介 / 核心创意</label>
            <textarea 
              value={novel.synopsis}
              onChange={(e) => updateNovel({ synopsis: e.target.value })}
              rows={4}
              placeholder="简要描述您的故事创意..."
              className="w-full px-3 py-2.5 md:py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none text-base md:text-sm"
            />
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-2 p-3 bg-slate-50 rounded-lg border">
              <input
                type="checkbox"
                id="generateExtras"
                checked={generateExtras}
                onChange={(e) => setGenerateExtras(e.target.checked)}
                className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
              />
              <label htmlFor="generateExtras" className="text-sm text-slate-700 cursor-pointer flex-1">
                同时生成角色列表（世界观和时间线将始终生成）
              </label>
            </div>
            <button 
              onClick={handleGenerateOutline}
              disabled={loading}
              className="w-full py-3.5 md:py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 active:bg-indigo-800 disabled:bg-slate-300 transition-all flex items-center justify-center gap-2 min-h-[48px] text-sm md:text-base"
            >
              {loading ? (
                <>
                  <Sparkles size={18} className="animate-spin" />
                  <span className="hidden sm:inline">{generateExtras ? '生成中（大纲+角色+世界观+时间线）...' : '生成大纲中...'}</span>
                  <span className="sm:hidden">{generateExtras ? '生成中...' : '生成中...'}</span>
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  <span className="hidden sm:inline">{generateExtras ? '一键生成完整设定（大纲+角色+世界观+时间线）' : '生成大纲（包含世界观和时间线）'}</span>
                  <span className="sm:hidden">{generateExtras ? '生成完整设定' : '生成大纲'}</span>
                </>
              )}
            </button>
          </div>
        </div>

        <div className="space-y-4 md:space-y-6">
          <div className="bg-white p-4 md:p-6 rounded-xl border shadow-sm">
            <h3 className="font-semibold text-base md:text-lg text-slate-800 mb-3">写作统计</h3>
            <div className="grid grid-cols-2 gap-3 md:gap-4">
              <div className="p-4 bg-slate-50 rounded-lg border">
                <p className="text-xs text-slate-500 font-medium">章节</p>
                <p className="text-2xl font-bold text-slate-800">{novel.volumes.reduce((acc, v) => acc + v.chapters.length, 0)}</p>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg border">
                <p className="text-xs text-slate-500 font-medium">角色</p>
                <p className="text-2xl font-bold text-slate-800">{novel.characters.length}</p>
              </div>
            </div>
            <div className="mt-4 md:mt-6 space-y-3">
              <button 
                onClick={handleExportFullText}
                className="w-full py-3.5 md:py-3 bg-slate-600 text-white font-semibold rounded-lg hover:bg-slate-700 active:bg-slate-800 transition-all flex items-center justify-center gap-2 min-h-[48px] text-sm md:text-base"
              >
                <Download size={18} />
                <span>导出全文</span>
              </button>
            <div className="space-y-3">
              <button 
                onClick={handleExportFullText}
                className="w-full py-3.5 md:py-3 bg-slate-600 text-white font-semibold rounded-lg hover:bg-slate-700 active:bg-slate-800 transition-all flex items-center justify-center gap-2 min-h-[48px] text-sm md:text-base"
              >
                <Download size={18} />
                <span>导出全文</span>
              </button>
              <button 
                onClick={onStartWriting}
                className="w-full py-3.5 md:py-3 border-2 border-slate-100 font-semibold rounded-lg hover:bg-slate-50 active:bg-slate-100 transition-all flex items-center justify-center gap-2 group min-h-[48px] text-sm md:text-base"
              >
                <span>跳转到编辑器</span>
                <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
            </div>
          </div>

          <div className="bg-indigo-50 p-4 md:p-6 rounded-xl border border-indigo-100">
            <h4 className="font-semibold text-sm md:text-base text-indigo-900 mb-2">专业提示</h4>
            <p className="text-xs md:text-sm text-indigo-700 leading-relaxed">
              在生成完整大纲之前，先定义您的主要角色和世界观规则。AI 将整合这些细节，创建更具个性化的故事结构！
            </p>
          </div>
        </div>
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
    </div>
  );
};

export default Dashboard;
