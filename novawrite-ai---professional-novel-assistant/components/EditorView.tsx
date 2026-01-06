import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Novel, Chapter } from '../types';
import { 
  Sparkles, 
  Wand2, 
  ChevronRight, 
  ChevronLeft, 
  BookOpen, 
  Feather,
  CheckCircle2,
  RefreshCcw,
  ArrowRight,
  Plus,
  X,
  ChevronDown,
  List,
  Copy,
  Download
} from 'lucide-react';
import { writeChapterContent, expandText, polishText, extractForeshadowingsFromChapter } from '../services/geminiService';
import { foreshadowingApi, chapterApi } from '../services/apiService';
import Console, { LogEntry } from './Console';

interface EditorViewProps {
  novel: Novel;
  updateNovel: (updates: Partial<Novel>) => void;
  activeVolumeIdx: number;
  activeChapterIdx: number | null;
  setActiveChapterIdx: (idx: number | null) => void;
  setActiveVolumeIdx?: (idx: number) => void;
  loadNovels?: () => Promise<void>;
}

const EditorView: React.FC<EditorViewProps> = ({ 
  novel, 
  updateNovel, 
  activeVolumeIdx, 
  activeChapterIdx, 
  setActiveChapterIdx,
  setActiveVolumeIdx,
  loadNovels
}) => {
  const [isWriting, setIsWriting] = useState(false);
  const [selectedText, setSelectedText] = useState("");
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [showConsole, setShowConsole] = useState(false);
  const [consoleMinimized, setConsoleMinimized] = useState(false);
  const [showMobileChapterMenu, setShowMobileChapterMenu] = useState(false);
  const isMountedRef = useRef(true);
  const loadingChaptersRef = useRef<Set<string>>(new Set()); // 记录正在加载的章节ID，避免重复请求

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

  // 将流式内容追加到最后一条日志条目
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

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Debug: log menu visibility changes.
  useEffect(() => {
    if (showMobileChapterMenu) {
      console.log("Menu visible", showMobileChapterMenu);
    }
  }, [showMobileChapterMenu]);

  // 使用原生DOM事件作为最后的备用方案
  useEffect(() => {
    const btn = document.getElementById('mobile-chapter-select-btn');
    if (btn) {
      const handleClick = () => {
        setShowMobileChapterMenu(prev => !prev);
      };
      btn.addEventListener('click', handleClick);
      btn.addEventListener('touchend', handleClick);
      return () => {
        btn.removeEventListener('click', handleClick);
        btn.removeEventListener('touchend', handleClick);
      };
    }
  }, []);

  // 当切换章节时，如果章节内容为空，则从后端获取最新内容
  useEffect(() => {
    if (activeChapterIdx === null || activeVolumeIdx === null) return;
    
    const volume = novel.volumes[activeVolumeIdx];
    if (!volume || !volume.id) return;
    
    const chapter = volume.chapters[activeChapterIdx];
    if (!chapter || !chapter.id) return;
    
    // 如果章节内容为空，尝试从后端获取
    // 使用 volume.id 作为 key，避免同一卷的多个章节重复请求
    const volumeKey = volume.id;
    if ((!chapter.content || !chapter.content.trim()) && !loadingChaptersRef.current.has(volumeKey)) {
      loadingChaptersRef.current.add(volumeKey);
      
      const loadChapterContent = async () => {
        try {
          // 获取整个卷的所有章节（包括内容），这样可以一次性更新所有章节
          const chaptersWithContent = await chapterApi.getAll(volume.id);
          
          // 更新本地 novel 对象中的章节内容
          const updatedVolumes = [...novel.volumes];
          const currentVolume = updatedVolumes[activeVolumeIdx];
          
          // 将后端返回的章节内容更新到本地
          chaptersWithContent.forEach(backendChapter => {
            const localChapterIndex = currentVolume.chapters.findIndex(
              ch => ch.id === backendChapter.id
            );
            if (localChapterIndex !== -1 && backendChapter.content) {
              currentVolume.chapters[localChapterIndex].content = backendChapter.content;
            }
          });
          
          updateNovel({ volumes: updatedVolumes });
        } catch (err: any) {
          // 静默失败，不影响用户体验
          console.warn('获取章节内容失败:', err?.message || '未知错误');
        } finally {
          // 加载完成后，移除标记，允许下次重新加载（因为后端可能已经更新了内容）
          loadingChaptersRef.current.delete(volumeKey);
        }
      };
      
      loadChapterContent();
    }
  }, [activeChapterIdx, activeVolumeIdx]);

  const chapters = novel.volumes[activeVolumeIdx]?.chapters || [];
  const currentChapter = activeChapterIdx !== null && chapters[activeChapterIdx] ? chapters[activeChapterIdx] : null;
  const hasNextChapter = activeChapterIdx !== null && activeChapterIdx < chapters.length - 1;
  const nextChapterIndex = activeChapterIdx !== null ? activeChapterIdx + 1 : null;

  // Copy chapter content to clipboard.
  const handleCopyChapter = async () => {
    if (!currentChapter || !currentChapter.content) {
      alert('No chapter content to copy.');
      return;
    }

    try {
      await navigator.clipboard.writeText(currentChapter.content);
      addLog('success', 'Chapter content copied.');
      const originalTitle = document.title;
      document.title = 'Copied';
      setTimeout(() => {
        document.title = originalTitle;
      }, 1000);
    } catch (err: any) {
      console.error('Copy failed:', err);
      addLog('error', `Copy failed: ${err?.message || 'Unknown error'}`);
      alert('Copy failed, please copy manually.');
    }
  };

  // Add a new chapter.
  const handleAddChapter = () => {
    const currentVolumes = [...novel.volumes];
    const newChapter: Chapter = {
      id: `ch-${Date.now()}`,
      title: `Chapter ${chapters.length + 1}`,
      summary: '',
      aiPromptHints: '',
      content: ''
    };
    currentVolumes[activeVolumeIdx].chapters = [...chapters, newChapter];
    updateNovel({ volumes: currentVolumes });
    setActiveChapterIdx(chapters.length);
  };

  // 删除章节
  const handleDeleteChapter = (chapterIndex: number) => {
    if (!window.confirm('确定要删除此章节吗？此操作无法撤销。')) {
      return;
    }
    const currentVolumes = [...novel.volumes];
    currentVolumes[activeVolumeIdx].chapters = chapters.filter((_, idx) => idx !== chapterIndex);
    updateNovel({ volumes: currentVolumes });
    
    // 如果删除的是当前章节，切换到其他章节
    if (activeChapterIdx === chapterIndex) {
      if (currentVolumes[activeVolumeIdx].chapters.length > 0) {
        setActiveChapterIdx(Math.min(chapterIndex, currentVolumes[activeVolumeIdx].chapters.length - 1));
      } else {
        setActiveChapterIdx(null);
      }
    } else if (activeChapterIdx !== null && activeChapterIdx > chapterIndex) {
      setActiveChapterIdx(activeChapterIdx - 1);
    }
  };

  // 更新章节信息
  const handleUpdateChapter = (chapterIndex: number, updates: Partial<Chapter>) => {
    const currentVolumes = [...novel.volumes];
    currentVolumes[activeVolumeIdx].chapters[chapterIndex] = {
      ...currentVolumes[activeVolumeIdx].chapters[chapterIndex],
      ...updates
    };
    updateNovel({ volumes: currentVolumes });
  };

  // 切换卷
  const handleSwitchVolume = (volumeIndex: number) => {
    if (volumeIndex >= 0 && volumeIndex < novel.volumes.length && volumeIndex !== activeVolumeIdx) {
      if (setActiveVolumeIdx) {
        setActiveVolumeIdx(volumeIndex);
        // 切换到新卷的第一章节（如果有）
        const newVolume = novel.volumes[volumeIndex];
        if (newVolume.chapters.length > 0) {
          setActiveChapterIdx(0);
        } else {
          setActiveChapterIdx(null);
        }
      }
    }
  };

  const handleUpdateContent = (newContent: string) => {
    if (activeChapterIdx === null) return;
    const newVolumes = [...novel.volumes];
    newVolumes[activeVolumeIdx].chapters[activeChapterIdx].content = newContent;
    updateNovel({ volumes: newVolumes });
  };

  const handleDraftWithAI = async () => {
    if (activeChapterIdx === null) return;
    if (!isMountedRef.current) return;
    if (!novel.id) {
      alert("小说ID无效");
      return;
    }
    
    const volume = novel.volumes[activeVolumeIdx];
    if (!volume || !volume.id) {
      alert('卷信息无效');
      return;
    }
    
    const chapter = chapters[activeChapterIdx];
    if (!chapter || !chapter.id) {
      alert('章节信息无效');
      return;
    }
    
    setIsWriting(true);
    setShowConsole(true);
    setConsoleMinimized(false);
    clearLogs();
    
    try {
      addLog('step', `📝 生成章节内容: ${chapter.title}`);
      addLog('info', '💡 所有业务逻辑在后端完成，数据将直接保存到数据库并存储向量');
      
      // 调用后端任务API
      const { novelApi } = await import('../services/apiService');
      const taskResult = await novelApi.writeChapter(novel.id, volume.id, chapter.id);
      
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
            addLog('success', '✅ 章节内容生成完成！后端已自动保存并存储向量');
            
            // 后端已经将 result 解析为对象，直接使用即可
            const resultData: any = task.result || {};
            
            // 显示伏笔和钩子信息
            if (resultData.foreshadowings && resultData.foreshadowings.length > 0) {
              addLog('success', `✅ 已提取 ${resultData.foreshadowings.length} 个伏笔`);
              resultData.foreshadowings.forEach((f: string, idx: number) => {
                addLog('info', `   ${idx + 1}. ${f.substring(0, 50)}${f.length > 50 ? '...' : ''}`);
              });
            }
            
            if (resultData.next_chapter_hook) {
              addLog('info', `💡 下一章钩子: ${resultData.next_chapter_hook.substring(0, 50)}${resultData.next_chapter_hook.length > 50 ? '...' : ''}`);
            }
            
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
      if (!isMountedRef.current) return;
      
      addLog('error', `❌ 生成失败: ${err?.message || '未知错误'}`);
      alert(`生成章节内容失败：${err?.message || '未知错误'}`);
    } finally {
      if (isMountedRef.current) {
        setIsWriting(false);
      }
    }
  };

  const handleExpandSelection = async () => {
    if (!selectedText) return;
    if (!isMountedRef.current) return;
    
    setIsWriting(true);
    setShowConsole(true);
    setConsoleMinimized(false);
    clearLogs();
    
    try {
      addLog('step', '📝 扩展选中文本...');
      
      // 构建提示词
      const expandPrompt = `请扩展以下文本，保持原有风格，并添加更多感官细节和角色内心想法。待扩展文本：${selectedText.substring(0, 500)}${selectedText.length > 500 ? '...' : ''}
上下文：${currentChapter?.summary || ''}`;
      
      addLog('info', '🔍 提示词(扩展文本):');
      addLog('info', '─'.repeat(60));
      expandPrompt.split('\n').forEach(line => {
        addLog('info', `   ${line.trim()}`);
      });
      addLog('info', '─'.repeat(60));
      
      const expanded = await expandText(selectedText, currentChapter?.summary || "");
      if (!isMountedRef.current) return;
      
      if (expanded && expanded.trim() && currentChapter && activeChapterIdx !== null) {
        const newContent = currentChapter.content.replace(selectedText, expanded);
        handleUpdateContent(newContent);
        
        // 立即保存到数据库
        try {
          const volume = novel.volumes[activeVolumeIdx];
          const chapter = chapters[activeChapterIdx];
          await chapterApi.update(volume.id, chapter.id, {
            title: chapter.title,
            summary: chapter.summary,
            content: newContent,
            aiPromptHints: chapter.aiPromptHints,
          });
          addLog('success', '✅ 文本扩展已保存至数据库！');
        } catch (saveError: any) {
          addLog('warning', `⚠️ 保存到数据库失败: ${saveError?.message || '未知错误'}，内容已更新到本地`);
          console.error('保存扩展文本失败:', saveError);
        }
        
        addLog('success', '✅ 文本扩展成功');
      } else {
        addLog('error', '❌ 扩展失败，返回的内容为空');
        alert('扩展文本失败，返回的内容为空，请重试。');
      }
    } catch (err: any) {
      if (!isMountedRef.current) return;
      
      addLog('error', `❌ 扩展失败: ${err?.message || '未知错误'}`);
      const errorMessage = err?.message || err?.toString() || '未知错误';
      alert(`扩展文本失败，${errorMessage}`);
    } finally {
      if (isMountedRef.current) {
        setIsWriting(false);
      }
    }
  };

  const handlePolishSelection = async () => {
    if (!selectedText) return;
    if (!isMountedRef.current) return;
    
    setIsWriting(true);
    setShowConsole(true);
    setConsoleMinimized(false);
    clearLogs();
    
    try {
      addLog('step', '📝 润色选中文本...');
      
      // 构建提示词
      const polishPrompt = `请润色以下文本，提升流畅度、词汇选择和情感共鸣。不要改变原意。待润色文本：${selectedText.substring(0, 500)}${selectedText.length > 500 ? '...' : ''}`;
      
      addLog('info', '🔍 提示词(润色文本):');
      addLog('info', '─'.repeat(60));
      polishPrompt.split('\n').forEach(line => {
        addLog('info', `   ${line.trim()}`);
      });
      addLog('info', '─'.repeat(60));
      
      const polished = await polishText(selectedText);
      if (!isMountedRef.current) return;
      
      if (polished && polished.trim() && currentChapter && activeChapterIdx !== null) {
        const newContent = currentChapter.content.replace(selectedText, polished);
        handleUpdateContent(newContent);
        
        // 立即保存到数据库
        try {
          const volume = novel.volumes[activeVolumeIdx];
          const chapter = chapters[activeChapterIdx];
          await chapterApi.update(volume.id, chapter.id, {
            title: chapter.title,
            summary: chapter.summary,
            content: newContent,
            aiPromptHints: chapter.aiPromptHints,
          });
          addLog('success', '✅ 文本润色已保存至数据库！');
        } catch (saveError: any) {
          addLog('warning', `⚠️ 保存到数据库失败: ${saveError?.message || '未知错误'}，内容已更新到本地`);
          console.error('保存润色文本失败:', saveError);
        }
        
        addLog('success', '✅ 文本润色成功');
      } else {
        addLog('error', '❌ 润色失败，返回的内容为空');
        alert('润色文本失败，返回的内容为空，请重试。');
      }
    } catch (err: any) {
      if (!isMountedRef.current) return;
      
      addLog('error', `❌ 润色失败: ${err?.message || '未知错误'}`);
      const errorMessage = err?.message || err?.toString() || '未知错误';
      alert(`润色文本失败，${errorMessage}`);
    } finally {
      if (isMountedRef.current) {
        setIsWriting(false);
      }
    }
  };

  const handleGenerateNextChapter = async () => {
    if (activeChapterIdx === null || nextChapterIndex === null) return;
    if (!isMountedRef.current) return;
    if (!novel.id) {
      alert("小说ID无效");
      return;
    }
    
    const volume = novel.volumes[activeVolumeIdx];
    if (!volume || !volume.id) {
      alert('卷信息无效');
      return;
    }
    
    const currentChapter = chapters[activeChapterIdx];
    if (!currentChapter || !currentChapter.id) {
      alert('当前章节信息无效');
      return;
    }
    
    const nextChapter = chapters[nextChapterIndex];
    if (!nextChapter) {
      alert('没有下一章节');
      return;
    }
    
    setIsWriting(true);
    setShowConsole(true);
    setConsoleMinimized(false);
    clearLogs();
    
    try {
      addLog('step', `📝 生成下一章节: ${nextChapter.title}`);
      addLog('info', `📄 当前章节: ${currentChapter.title}`);
      addLog('info', `📄 下一章节: ${nextChapter.title}`);
      addLog('info', '💡 所有业务逻辑在后端完成，数据将直接保存到数据库并存储向量');
      
      // 调用后端任务API
      const { novelApi } = await import('../services/apiService');
      const taskResult = await novelApi.writeNextChapter(novel.id, volume.id, currentChapter.id);
      
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
            addLog('success', '✅ 下一章节生成完成！后端已自动保存并存储向量');

            // 后端已经将 result 解析为对象，直接使用即可
            const resultData: any = task.result || {};
            
            // 显示伏笔和钩子信息
            if (resultData.foreshadowings && resultData.foreshadowings.length > 0) {
              addLog('success', `✅ 已提取 ${resultData.foreshadowings.length} 个伏笔`);
              resultData.foreshadowings.forEach((f: string, idx: number) => {
                addLog('info', `   ${idx + 1}. ${f.substring(0, 50)}${f.length > 50 ? '...' : ''}`);
              });
            }
            
            if (resultData.next_chapter_hook) {
              addLog('info', `💡 下一章钩子: ${resultData.next_chapter_hook.substring(0, 50)}${resultData.next_chapter_hook.length > 50 ? '...' : ''}`);
            }
            
            addLog('info', '🔄 正在重新加载最新数据...');
            
            // 重新加载小说数据（后端已经保存）
            if (loadNovels) {
              await loadNovels();
              addLog('success', '✅ 数据加载完成！');
            }
            
            // 自动切换到下一章节
            setActiveChapterIdx(nextChapterIndex);
            addLog('info', `⏭️ 已自动跳转到下一章节`);
            
            resolve();
          },
          onError: (task) => {
            addLog('error', `❌ 任务失败: ${task.error_message || '未知错误'}`);
            reject(new Error(task.error_message || '任务执行失败'));
          },
        });
      });
      
    } catch (err: any) {
      if (!isMountedRef.current) return;
      
      addLog('error', `❌ 生成失败: ${err?.message || '未知错误'}`);
      alert(`生成下一章节失败：${err?.message || '未知错误'}`);
    } finally {
      if (isMountedRef.current) {
        setIsWriting(false);
      }
    }
  };

  const onSelectText = () => {
    const text = window.getSelection()?.toString();
    if (text) setSelectedText(text);
  };

  // 导出章节内容为TXT文件
  const handleExportChapter = () => {
    if (!currentChapter || !currentChapter.content) {
      alert('当前章节没有内容，无法导出');
      return;
    }

    const content = `${currentChapter.title}\n\n${currentChapter.content}`;
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentChapter.title}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // 导出整本小说为TXT文件
  const handleExportNovel = () => {
    if (!novel.volumes || novel.volumes.length === 0) {
      alert('没有内容可以导出');
      return;
    }

    let content = `${novel.title}\n\n`;
    if (novel.synopsis) {
      content += `简介：\n${novel.synopsis}\n\n`;
    }
    if (novel.fullOutline) {
      content += `完整大纲：\n${novel.fullOutline}\n\n`;
    }
    content += '='.repeat(50) + '\n\n';

    novel.volumes.forEach((volume, volIdx) => {
      content += `\n第${volIdx + 1}卷：${volume.title}\n`;
      if (volume.summary) {
        content += `卷简介：${volume.summary}\n`;
      }
      content += '='.repeat(50) + '\n\n';

      volume.chapters.forEach((chapter, chIdx) => {
        if (chapter.content && chapter.content.trim()) {
          content += `\n第${chIdx + 1}章：${chapter.title}\n\n`;
          content += chapter.content;
          content += '\n\n' + '-'.repeat(50) + '\n\n';
        }
      });
    });

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${novel.title || '未命名小说'}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <>
      {/* 移动端章节选择器 - 放在最前面，确保总是渲染 */}
      <div 
        className="lg:hidden"
        id="mobile-chapter-select-container"
        style={{ 
          position: 'fixed',
          top: '56px',
          left: 0,
          right: 0,
          padding: '8px 16px',
          backgroundColor: 'white',
          borderBottom: '1px solid #e2e8f0',
          zIndex: 9999
        }}
      >
        <div
          id="mobile-chapter-select-btn"
          onClick={() => {
            console.log('✅ 按钮被点击了');
            setShowMobileChapterMenu(prev => !prev);
          }}
          onTouchEnd={(e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('✅ 按钮被触摸了');
            setShowMobileChapterMenu(prev => !prev);
          }}
          style={{ 
            width: '100%',
            minHeight: '44px',
            padding: '12px',
            backgroundColor: '#f1f5f9',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            cursor: 'pointer',
            touchAction: 'manipulation'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: 0 }}>
            <List size={16} />
            <span style={{ fontSize: '14px', fontWeight: 600, color: '#334155', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {activeChapterIdx !== null && currentChapter ? `${activeChapterIdx + 1}. ${currentChapter.title}` : '选择章节'}
            </span>
          </div>
          <ChevronDown size={16} style={{ transform: showMobileChapterMenu ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }} />
        </div>
      </div>
      
    <div className="flex h-full overflow-hidden flex-col lg:flex-row">
      {/* Chapter Sidebar - 移动端隐藏，使用顶部导航或按钮 */}
      <div className="hidden lg:flex w-80 border-r bg-white shrink-0 flex-col">
        <div className="p-4 border-b bg-slate-50">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
              <BookOpen size={16} /> 章节列表
            </h3>
            <button
              onClick={handleAddChapter}
              className="p-1.5 text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
              title="添加新章节"
            >
              <Plus size={16} />
            </button>
          </div>
          <div className="text-xs text-slate-500">
            当前卷：{novel.volumes[activeVolumeIdx]?.title || `第${activeVolumeIdx + 1} 卷`}
          </div>
        </div>
        
        {/* 卷列表（如果有由多卷） */}
        {novel.volumes.length > 1 && (
          <div className="p-2 border-b bg-slate-50">
            <div className="text-xs font-semibold text-slate-500 mb-1">切换卷：</div>
            <div className="flex flex-wrap gap-1">
              {novel.volumes.map((vol, volIdx) => (
                <button
                  key={vol.id}
                  onClick={() => handleSwitchVolume(volIdx)}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    volIdx === activeVolumeIdx
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white text-slate-600 hover:bg-slate-100 border'
                  }`}
                  title={`第${volIdx + 1} 卷：${vol.title} (${vol.chapters.length} 章)`}
                >
                  {volIdx + 1}
                </button>
              ))}
            </div>
          </div>
        )}
        
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {chapters.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-xs text-slate-400 p-2 italic mb-3">这里没有章节</p>
              <button
                onClick={handleAddChapter}
                className="px-3 py-1.5 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2 mx-auto"
              >
                <Plus size={14} />
                添加章节
              </button>
            </div>
          ) : (
            chapters.map((ch, idx) => (
              <div
                key={ch.id}
                className={`group relative rounded-lg transition-all ${
                  activeChapterIdx === idx 
                    ? 'bg-indigo-50 border border-indigo-100' 
                    : 'bg-white border border-transparent hover:border-slate-200'
                }`}
              >
                <button
                  onClick={() => setActiveChapterIdx(idx)}
                  className="w-full text-left px-3 py-2 pr-8"
                >
                  <div className="flex justify-between items-center mb-1">
                    <span className={`text-xs font-medium truncate flex-1 ${
                      activeChapterIdx === idx ? 'text-indigo-700' : 'text-slate-700'
                    }`}>
                      {idx + 1}. {ch.title}
                    </span>
                    {ch.content.length > 0 && (
                      <CheckCircle2 size={12} className="text-green-500 shrink-0 ml-2" />
                    )}
                  </div>
                  {ch.summary && (
                    <p className="text-[10px] text-slate-500 line-clamp-1">{ch.summary}</p>
                  )}
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteChapter(idx);
                  }}
                  className="absolute top-1 right-1 p-1 opacity-0 group-hover:opacity-100 text-red-500 hover:bg-red-50 rounded transition-all"
                  title="删除章节"
                >
                  <X size={12} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      
      <div className="flex-1 flex flex-col bg-white min-w-0 relative">
        
        {currentChapter ? (
          <>
            <div className="min-h-[56px] border-b px-4 md:px-6 flex flex-col lg:flex-row lg:items-center justify-between shrink-0 pt-[60px] lg:pt-0 gap-2 lg:gap-0" style={{ position: 'relative', zIndex: 100 }}>
              <div className="flex flex-col flex-1 min-w-0 lg:min-h-[56px] lg:justify-center" style={{ position: 'relative', zIndex: 101 }}>
                {/* 桌面端章节标题输入 */}
                <input
                  type="text"
                  value={currentChapter.title}
                  onChange={(e) => handleUpdateChapter(activeChapterIdx!, { title: e.target.value })}
                  className="hidden lg:block text-base md:text-lg font-bold text-slate-800 bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-indigo-500 px-1 -ml-1 rounded truncate w-full"
                  placeholder="章节标题"
                />
                
                {/* 移动端章节下拉菜单 - 使用 Portal 渲染到 body */}
                {showMobileChapterMenu && typeof document !== 'undefined' && createPortal(
                    <>
                      <div 
                        className="fixed inset-0 z-[100] bg-black/40"
                        onClick={() => {
                          console.log('遮罩层点击，关闭菜单');
                          setShowMobileChapterMenu(false);
                        }}
                        onTouchEnd={(e) => {
                          e.preventDefault();
                          console.log('遮罩层触摸，关闭菜单');
                          setShowMobileChapterMenu(false);
                        }}
                        style={{ touchAction: 'manipulation' }}
                      />
                      <div 
                        className="fixed top-[60px] left-4 right-4 bg-white border-2 border-indigo-300 rounded-xl shadow-2xl z-[102] max-h-[calc(100vh-140px)] overflow-y-auto"
                        onClick={(e) => {
                          e.stopPropagation();
                          console.log('菜单容器点击');
                        }}
                        onTouchEnd={(e) => {
                          e.stopPropagation();
                          console.log('菜单容器触摸');
                        }}
                        style={{ 
                          touchAction: 'manipulation',
                          pointerEvents: 'auto',
                          WebkitOverflowScrolling: 'touch'
                        }}
                      >
                        {/* 卷选择（如果有由多卷） */}
                        {novel.volumes.length > 1 && (
                          <div className="p-3 border-b bg-indigo-50">
                            <div className="text-xs font-semibold text-indigo-700 mb-2">切换卷：</div>
                            <div className="flex flex-wrap gap-2">
                              {novel.volumes.map((vol, volIdx) => (
                                <button
                                  key={vol.id}
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    handleSwitchVolume(volIdx);
                                    setShowMobileChapterMenu(false);
                                  }}
                                  onTouchEnd={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    handleSwitchVolume(volIdx);
                                    setShowMobileChapterMenu(false);
                                  }}
                                  className={`px-3 py-1.5 text-sm rounded-lg transition-colors touch-manipulation font-medium ${
                                    volIdx === activeVolumeIdx
                                      ? 'bg-indigo-600 text-white shadow-md'
                                      : 'bg-white text-slate-700 hover:bg-indigo-100 active:bg-indigo-200 border border-slate-300'
                                  }`}
                                >
                                  第{volIdx + 1}卷
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* 章节列表 */}
                        <div className="p-3">
                          {chapters.length === 0 ? (
                            <div className="text-center py-4 text-sm text-slate-400">
                              这里没有章节
                            </div>
                          ) : (
                            chapters.map((ch, idx) => (
                              <button
                                key={ch.id}
                                onClick={(e) => {
                                  e.preventDefault();
                                  e.stopPropagation();
                                  console.log('章节按钮点击:', idx, ch.title);
                                  setActiveChapterIdx(idx);
                                  setShowMobileChapterMenu(false);
                                }}
                                onTouchStart={(e) => {
                                  e.stopPropagation();
                                }}
                                onTouchEnd={(e) => {
                                  e.preventDefault();
                                  e.stopPropagation();
                                  console.log('章节按钮触摸:', idx, ch.title);
                                  setActiveChapterIdx(idx);
                                  setShowMobileChapterMenu(false);
                                }}
                                onMouseDown={(e) => {
                                  e.stopPropagation();
                                }}
                                style={{ 
                                  WebkitTapHighlightColor: 'transparent',
                                  touchAction: 'manipulation',
                                  pointerEvents: 'auto',
                                  userSelect: 'none'
                                }}
                                className={`w-full text-left px-4 py-3 rounded-lg mb-2 transition-all touch-manipulation cursor-pointer ${
                                  activeChapterIdx === idx
                                    ? 'bg-indigo-100 border-2 border-indigo-500 text-indigo-900 font-semibold shadow-md'
                                    : 'bg-white border border-slate-200 hover:border-indigo-300 active:bg-slate-50 text-slate-700'
                                }`}
                              >
                                <div className="flex items-center justify-between">
                                  <span className="text-sm truncate flex-1">
                                    {idx + 1}. {ch.title}
                                  </span>
                                  {ch.content.length > 0 && (
                                    <CheckCircle2 size={14} className="text-green-500 shrink-0 ml-2" />
                                  )}
                                </div>
                                {ch.summary && (
                                  <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">{ch.summary}</p>
                                )}
                              </button>
                            ))
                          )}
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              handleAddChapter();
                              setShowMobileChapterMenu(false);
                            }}
                            onTouchEnd={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              handleAddChapter();
                              setShowMobileChapterMenu(false);
                            }}
                            className="w-full mt-2 px-3 py-2.5 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 active:bg-indigo-800 transition-colors flex items-center justify-center gap-2 touch-manipulation"
                          >
                            <Plus size={16} />
                            添加新章节
                          </button>
                        </div>
                      </div>
                    </>,
                    document.body
                  )}
                
                {/* 桌面端章节标题输入 */}
                <input
                  type="text"
                  value={currentChapter.title}
                  onChange={(e) => handleUpdateChapter(activeChapterIdx!, { title: e.target.value })}
                  className="hidden lg:block text-base md:text-lg font-bold text-slate-800 bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-indigo-500 px-1 -ml-1 rounded truncate w-full"
                  placeholder="章节标题"
                />
                <div className="flex items-center gap-4 mt-1">
                  <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">
                    字数: {currentChapter.content.split(/\s+/).filter(Boolean).length}
                  </p>
                  <span className="text-[10px] text-slate-400">
                    字符: {currentChapter.content.length}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-wrap lg:flex-nowrap">
                <button 
                  onClick={handleCopyChapter}
                  disabled={!currentChapter.content}
                  className="px-3 md:px-4 py-2 bg-slate-600 text-white text-xs font-bold rounded-lg hover:bg-slate-700 disabled:bg-slate-200 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
                  title="复制本章内容到剪贴板"
                >
                  <Copy size={14} />
                  <span className="hidden sm:inline">复制</span>
                </button>
                <button 
                  onClick={handleExportChapter}
                  disabled={!currentChapter.content}
                  className="px-3 md:px-4 py-2 bg-blue-600 text-white text-xs font-bold rounded-lg hover:bg-blue-700 disabled:bg-slate-200 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
                  title="导出本章为TXT文件"
                >
                  <Download size={14} />
                  <span className="hidden sm:inline">导出本章</span>
                  <span className="sm:hidden">导出</span>
                </button>
                <button 
                  onClick={handleExportNovel}
                  className="px-3 md:px-4 py-2 bg-purple-600 text-white text-xs font-bold rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-1.5"
                  title="导出整本小说为TXT文件"
                >
                  <Download size={14} />
                  <span className="hidden sm:inline">导出小说</span>
                  <span className="sm:hidden">全部</span>
                </button>
                <button 
                  onClick={handleDraftWithAI}
                  disabled={isWriting}
                  className="px-3 md:px-4 py-2 bg-indigo-600 text-white text-xs font-bold rounded-lg hover:bg-indigo-700 disabled:bg-slate-200 transition-colors flex items-center gap-1.5"
                >
                  {isWriting ? <RefreshCcw size={14} className="animate-spin" /> : <Sparkles size={14} />}
                  <span className="hidden sm:inline">{currentChapter.content ? "重新生成草稿" : "AI 生成草稿"}</span>
                  <span className="sm:hidden">生成</span>
                </button>
                {hasNextChapter && (
                  <button 
                    onClick={handleGenerateNextChapter}
                    disabled={isWriting || !currentChapter.content}
                    className="px-3 md:px-4 py-2 bg-green-600 text-white text-xs font-bold rounded-lg hover:bg-green-700 disabled:bg-slate-200 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
                    title={!currentChapter.content ? "请先完成当前章节生成" : "生成下一章节内容"}
                  >
                    {isWriting ? <RefreshCcw size={14} className="animate-spin" /> : <ArrowRight size={14} />}
                    <span className="hidden sm:inline">生成下一章</span>
                    <span className="sm:hidden">下一章</span>
                  </button>
                )}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto px-4 md:px-12 py-6 md:py-10 relative">
              <div className="max-w-[700px] mx-auto">
                {isWriting && (
                  <div className="absolute inset-0 bg-white/50 z-10 flex items-center justify-center backdrop-blur-[1px]">
                    <div className="bg-white p-6 rounded-2xl shadow-xl border border-indigo-100 flex flex-col items-center animate-pulse">
                      <Sparkles size={40} className="text-indigo-600 mb-4 animate-bounce" />
                      <p className="text-lg font-bold text-indigo-900">AI 正在创作中...</p>
                      <p className="text-sm text-slate-500">正在融入您的世界观设定...</p>
                    </div>
                  </div>
                )}
                
                <textarea
                  value={currentChapter.content}
                  onMouseUp={onSelectText}
                  onChange={(e) => handleUpdateContent(e.target.value)}
                  placeholder="开始创作或使用 AI 生成章节内容..."
                  className="w-full h-full min-h-[600px] resize-none focus:outline-none serif text-xl leading-relaxed text-slate-800"
                />
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center flex-col text-slate-400 bg-slate-50 p-10 text-center">
            <div className="w-16 h-16 bg-slate-200 rounded-full flex items-center justify-center mb-4">
              <Feather size={32} />
            </div>
            <h3 className="text-xl font-bold text-slate-600 mb-2">选择一个章节开始</h3>
            <p className="max-w-xs text-sm mb-4">从列表中选择一个章节，或在侧边栏视图中创建一个。</p>
            {/* 移动端：如果没有章节，显示添加按钮 */}
            <div className="lg:hidden">
              {chapters.length === 0 ? (
                <button
                  onClick={handleAddChapter}
                  className="px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2 mx-auto"
                >
                  <Plus size={16} />
                  添加第一个章节
                </button>
              ) : (
                <button
                  onClick={() => setShowMobileChapterMenu(true)}
                  className="px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2 mx-auto"
                >
                  <List size={16} />
                  选择章节
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Sidekick panel */}
      {currentChapter && (
        <div className="w-72 border-l bg-slate-50 shrink-0 flex flex-col overflow-hidden">
          <div className="p-4 border-b bg-white">
            <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
              <Wand2 size={16} className="text-indigo-600" /> AI 助手
            </h3>
          </div>
          
          <div className="flex-1 p-4 overflow-y-auto space-y-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">章节摘要</h4>
              </div>
              <textarea
                value={currentChapter.summary}
                onChange={(e) => handleUpdateChapter(activeChapterIdx!, { summary: e.target.value })}
                placeholder="章节摘要..."
                rows={3}
                className="w-full px-3 py-2 border rounded-lg text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none resize-none bg-white"
              />
            </div>

            <div className="space-y-3">
              <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">AI 提示</h4>
              <textarea
                value={currentChapter.aiPromptHints || ''}
                onChange={(e) => handleUpdateChapter(activeChapterIdx!, { aiPromptHints: e.target.value })}
                placeholder="写作提示，用于 AI 生成..."
                rows={2}
                className="w-full px-3 py-2 border rounded-lg text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none resize-none bg-white"
              />
            </div>

            <div className="space-y-3">
              <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">智能工具</h4>
              <div className="space-y-2">
                <button 
                  onClick={handleExpandSelection}
                  disabled={!selectedText || isWriting}
                  className="w-full text-left p-3 bg-white border rounded-lg hover:border-indigo-400 transition-all group disabled:opacity-50"
                >
                  <p className="text-xs font-bold text-slate-800 mb-1 flex items-center gap-2">
                    <Sparkles size={14} className="text-indigo-600" /> 扩展文本
                  </p>
                  <p className="text-[10px] text-slate-500">选择文本并点击以添加更多细节和深度。</p>
                </button>

                <button 
                  onClick={handlePolishSelection}
                  disabled={!selectedText || isWriting}
                  className="w-full text-left p-3 bg-white border rounded-lg hover:border-indigo-400 transition-all group disabled:opacity-50"
                >
                  <p className="text-xs font-bold text-slate-800 mb-1 flex items-center gap-2">
                    <Feather size={14} className="text-indigo-600" /> 润色文本
                  </p>
                  <p className="text-[10px] text-slate-500">优化词汇并提升文学质量。</p>
                </button>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">角色信息</h4>
              <div className="space-y-2">
                {novel.characters.length === 0 ? (
                  <p className="text-[10px] text-slate-400 italic">尚未添加角色。</p>
                ) : (
                  novel.characters.slice(0, 3).map(char => (
                    <div key={char.id} className="p-2 bg-white border rounded-lg text-[10px]">
                      <span className="font-bold text-slate-700">{char.name}</span>
                      <p className="text-slate-500">{char.role}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}

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
    </>
  );
};

export default EditorView;