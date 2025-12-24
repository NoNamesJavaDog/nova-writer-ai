
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
  Copy
} from 'lucide-react';
import { writeChapterContent, writeNextChapterContent, expandText, polishText, extractForeshadowingsFromChapter } from '../services/geminiService';
import { foreshadowingApi, chapterApi } from '../services/apiService';
import Console, { LogEntry } from './Console';

interface EditorViewProps {
  novel: Novel;
  updateNovel: (updates: Partial<Novel>) => void;
  activeVolumeIdx: number;
  activeChapterIdx: number | null;
  setActiveChapterIdx: (idx: number | null) => void;
  setActiveVolumeIdx?: (idx: number) => void;
}

const EditorView: React.FC<EditorViewProps> = ({ 
  novel, 
  updateNovel, 
  activeVolumeIdx, 
  activeChapterIdx, 
  setActiveChapterIdx,
  setActiveVolumeIdx
}) => {
  const [isWriting, setIsWriting] = useState(false);
  const [selectedText, setSelectedText] = useState("");
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [showConsole, setShowConsole] = useState(false);
  const [consoleMinimized, setConsoleMinimized] = useState(false);
  const [showMobileChapterMenu, setShowMobileChapterMenu] = useState(false);
  const isMountedRef = useRef(true);

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

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // 调试：监听菜单状态变化
  useEffect(() => {
    if (showMobileChapterMenu) {
      console.log('✅ 菜单应该显示了，showMobileChapterMenu:', showMobileChapterMenu);
    }
  }, [showMobileChapterMenu]);

  // 使用原生DOM事件确保按钮可点击 - 使用全局事件委托
  useEffect(() => {
    const handleGlobalClick = (e: MouseEvent | TouchEvent) => {
      const target = e.target as HTMLElement;
      const btn = document.getElementById('mobile-chapter-select-btn');
      
      // 检查点击是否在按钮或其子元素上
      if (btn && (target === btn || btn.contains(target))) {
        e.preventDefault();
        e.stopPropagation();
        console.log('✅ 全局事件委托捕获到按钮点击');
        setShowMobileChapterMenu(prev => {
          const newState = !prev;
          console.log('✅ 设置菜单状态为:', newState);
          return newState;
        });
      }
    };
    
    // 在capture阶段监听，确保优先处理
    document.addEventListener('click', handleGlobalClick, true);
    document.addEventListener('touchend', handleGlobalClick, true);
    
    return () => {
      document.removeEventListener('click', handleGlobalClick, true);
      document.removeEventListener('touchend', handleGlobalClick, true);
    };
  }, []);

  const chapters = novel.volumes[activeVolumeIdx]?.chapters || [];
  const currentChapter = activeChapterIdx !== null && chapters[activeChapterIdx] ? chapters[activeChapterIdx] : null;
  const hasNextChapter = activeChapterIdx !== null && activeChapterIdx < chapters.length - 1;
  const nextChapterIndex = activeChapterIdx !== null ? activeChapterIdx + 1 : null;

  // 复制章节内容到剪贴板
  const handleCopyChapter = async () => {
    if (!currentChapter || !currentChapter.content) {
      alert('当前章节没有内容可复制');
      return;
    }

    try {
      await navigator.clipboard.writeText(currentChapter.content);
      addLog('success', '✅ 章节内容已复制到剪贴板');
      // 显示一个临时提示
      const originalTitle = document.title;
      document.title = '✓ 已复制';
      setTimeout(() => {
        document.title = originalTitle;
      }, 1000);
    } catch (err: any) {
      console.error('复制失败:', err);
      addLog('error', `❌ 复制失败: ${err?.message || '未知错误'}`);
      alert('复制失败，请手动复制内容');
    }
  };

  // 添加新章节
  const handleAddChapter = () => {
    const currentVolumes = [...novel.volumes];
    const newChapter: Chapter = {
      id: `ch-${Date.now()}`,
      title: `新章节 ${chapters.length + 1}`,
      summary: '',
      aiPromptHints: '',
      content: ''
    };
    currentVolumes[activeVolumeIdx].chapters = [...chapters, newChapter];
    updateNovel({ volumes: currentVolumes });
    // 切换到新章节
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
        // 切换到新卷的第一个章节（如果有）
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
    
    setIsWriting(true);
    setShowConsole(true);
    setConsoleMinimized(false);
    clearLogs();
    
    try {
      const chapter = chapters[activeChapterIdx];
      addLog('step', `📝 生成章节内容: ${chapter.title}`);
      
      // 显示提示词
      const chapterPrompt = `请为小说《${novel.title}》创作一个完整的章节。
章节标题：${chapter.title}
情节摘要：${chapter.summary}
写作提示：${chapter.aiPromptHints}

上下文：
完整小说简介：${novel.synopsis}
涉及角色：${novel.characters.map(c => `${c.name}：${c.personality}`).join('；')}
世界观规则：${novel.worldSettings.map(s => `${s.title}：${s.description}`).join('；')}

请以高文学品质、沉浸式描述和引人入胜的对话来创作。仅输出章节正文内容。`;
      
      addLog('info', '📋 提示词 (生成章节内容):');
      addLog('info', '─'.repeat(60));
      chapterPrompt.split('\n').forEach(line => {
        addLog('info', `   ${line.trim()}`);
      });
      addLog('info', '─'.repeat(60));
      
      // 创建流式传输回调
      const onChunk = (chunk: string, isComplete: boolean) => {
        if (isComplete) {
          addLog('success', '\n✅ 生成完成！');
        } else if (chunk) {
          appendStreamChunk(chunk);
        }
      };
      
      const content = await writeChapterContent(novel, activeChapterIdx, activeVolumeIdx, onChunk);
      if (!isMountedRef.current) return;
      
      if (content && content.trim()) {
        // 先更新本地状态
        handleUpdateContent(content);
        
        // 立即保存到数据库
        try {
          const chapter = chapters[activeChapterIdx];
          const volume = novel.volumes[activeVolumeIdx];
          await chapterApi.update(volume.id, chapter.id, {
            title: chapter.title,
            summary: chapter.summary,
            content: content,
            aiPromptHints: chapter.aiPromptHints,
          });
          addLog('success', `✅ 章节内容已保存到数据库！`);
        } catch (saveError: any) {
          addLog('warning', `⚠️ 保存到数据库失败: ${saveError?.message || '未知错误'}，内容已更新到本地`);
          console.error('保存章节内容失败:', saveError);
        }
        
        addLog('success', `✅ 章节内容生成成功！`);
        addLog('info', `📄 内容长度: ${content.length} 字符`);
        
        // 提取本章节的伏笔
        try {
          addLog('step', '💡 提取本章节的伏笔线索...');
          const existingForeshadowings = novel.foreshadowings.map(f => ({ content: f.content }));
          const extractedForeshadowings = await extractForeshadowingsFromChapter(
            novel.title,
            novel.genre,
            chapter.title,
            content,
            existingForeshadowings
          );
          
          if (extractedForeshadowings && extractedForeshadowings.length > 0) {
            const newForeshadowings = extractedForeshadowings.map((f: any) => ({
              content: f.content || '',
              chapterId: chapter.id,
              isResolved: 'false'
            }));
            
            // 保存到后端
            const savedForeshadowings = await foreshadowingApi.create(novel.id, newForeshadowings);
            
            // 更新本地状态
            updateNovel({
              foreshadowings: [...novel.foreshadowings, ...savedForeshadowings]
            });
            
            addLog('success', `✅ 已提取 ${savedForeshadowings.length} 个伏笔`);
            savedForeshadowings.forEach((f, idx) => {
              addLog('info', `   ${idx + 1}. ${f.content.substring(0, 50)}${f.content.length > 50 ? '...' : ''}`);
            });
          } else {
            addLog('info', 'ℹ️ 本章节未发现新的伏笔线索');
          }
        } catch (err: any) {
          addLog('warning', `⚠️ 提取伏笔失败: ${err?.message || '未知错误'}，章节内容已保存`);
        }
      } else {
        addLog('error', '❌ 生成失败：返回的内容为空');
        alert('生成失败：返回的内容为空，请重试。');
      }
    } catch (err: any) {
      if (!isMountedRef.current) return;
      
      addLog('error', `❌ 生成失败: ${err?.message || '未知错误'}`);
      const errorMessage = err?.message || err?.toString() || '未知错误';
      alert(`生成章节内容失败：${errorMessage}\n\n请检查：\n1. API Key 是否正确配置\n2. 网络连接是否正常\n3. 代理设置是否正确`);
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
      
      // 显示提示词
      const expandPrompt = `请扩展以下文本，保持原有风格，并添加更多感官细节和角色内心想法。
待扩展文本：${selectedText.substring(0, 500)}${selectedText.length > 500 ? '...' : ''}
上下文：${currentChapter?.summary || ''}`;
      
      addLog('info', '📋 提示词 (扩展文本):');
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
          addLog('success', '✅ 文本扩展已保存到数据库！');
        } catch (saveError: any) {
          addLog('warning', `⚠️ 保存到数据库失败: ${saveError?.message || '未知错误'}，内容已更新到本地`);
          console.error('保存扩展文本失败:', saveError);
        }
        
        addLog('success', '✅ 文本扩展成功！');
      } else {
        addLog('error', '❌ 扩展失败：返回的内容为空');
        alert('扩展文本失败：返回的内容为空，请重试。');
      }
    } catch (err: any) {
      if (!isMountedRef.current) return;
      
      addLog('error', `❌ 扩展失败: ${err?.message || '未知错误'}`);
      const errorMessage = err?.message || err?.toString() || '未知错误';
      alert(`扩展文本失败：${errorMessage}`);
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
      
      // 显示提示词
      const polishPrompt = `请润色以下文本，提升流畅度、词汇选择和情感共鸣。不要改变原意。
待润色文本：${selectedText.substring(0, 500)}${selectedText.length > 500 ? '...' : ''}`;
      
      addLog('info', '📋 提示词 (润色文本):');
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
          addLog('success', '✅ 文本润色已保存到数据库！');
        } catch (saveError: any) {
          addLog('warning', `⚠️ 保存到数据库失败: ${saveError?.message || '未知错误'}，内容已更新到本地`);
          console.error('保存润色文本失败:', saveError);
        }
        
        addLog('success', '✅ 文本润色成功！');
      } else {
        addLog('error', '❌ 润色失败：返回的内容为空');
        alert('润色文本失败：返回的内容为空，请重试。');
      }
    } catch (err: any) {
      if (!isMountedRef.current) return;
      
      addLog('error', `❌ 润色失败: ${err?.message || '未知错误'}`);
      const errorMessage = err?.message || err?.toString() || '未知错误';
      alert(`润色文本失败：${errorMessage}`);
    } finally {
      if (isMountedRef.current) {
        setIsWriting(false);
      }
    }
  };

  const handleGenerateNextChapter = async () => {
    if (activeChapterIdx === null || nextChapterIndex === null) return;
    if (!isMountedRef.current) return;
    
    setIsWriting(true);
    setShowConsole(true);
    setConsoleMinimized(false);
    clearLogs();
    
    try {
      const nextChapter = chapters[nextChapterIndex];
      addLog('step', `📝 生成下一章节: ${nextChapter.title}`);
      addLog('info', `📖 当前章节: ${currentChapter?.title}`);
      addLog('info', `📖 下一章节: ${nextChapter.title}`);
      
      // 显示提示词
      const currentVolume = novel.volumes[activeVolumeIdx];
      const previousChapters = chapters
        .slice(Math.max(0, activeChapterIdx - 2), activeChapterIdx + 1)
        .map((ch, idx) => `第${Math.max(0, activeChapterIdx - 2) + idx + 1}章《${ch.title}》：${ch.content.substring(0, 500)}${ch.content.length > 500 ? '...' : ''}`)
        .join('\n\n');
      
      const nextChapterPrompt = `请为小说《${novel.title}》创作下一章节的内容。

小说基本信息：
类型：${novel.genre}
简介：${novel.synopsis}

当前卷信息：
卷标题：${currentVolume.title}
${currentVolume.summary ? `卷描述：${currentVolume.summary}` : ''}

前文内容（最近几章）：
${previousChapters || '（这是本卷的第一章）'}

当前章节信息：
章节标题：${currentChapter?.title}
${currentChapter?.content ? `当前章节内容预览：${currentChapter.content.substring(0, 500)}${currentChapter.content.length > 500 ? '...' : ''}` : ''}

下一章节信息（需要生成的内容）：
章节标题：${nextChapter.title}
情节摘要：${nextChapter.summary}
${nextChapter.aiPromptHints ? `写作提示：${nextChapter.aiPromptHints}` : ''}

角色信息：
${novel.characters.map(c => `${c.name}（${c.role}）：性格-${c.personality}；背景-${c.background}；目标-${c.goals}`).join('\n') || '暂无角色信息'}

世界观设定：
${novel.worldSettings.map(s => `${s.title}（${s.category}）：${s.description}`).join('\n') || '暂无世界观设定'}

要求：
1. 与前文内容保持连贯性和一致性
2. 遵循角色的性格设定和世界观规则
3. 按照下一章节的情节摘要推进故事
4. 保持高文学品质，使用沉浸式描述和引人入胜的对话
5. 仅输出章节正文内容`;
      
      addLog('info', '📋 提示词 (生成下一章节):');
      addLog('info', '─'.repeat(60));
      nextChapterPrompt.split('\n').slice(0, 20).forEach(line => {
        addLog('info', `   ${line.trim()}`);
      });
      addLog('info', '   ...');
      addLog('info', '─'.repeat(60));
      
      // 创建流式传输回调
      const onChunk = (chunk: string, isComplete: boolean) => {
        if (isComplete) {
          addLog('success', '\n✅ 生成完成！');
        } else if (chunk) {
          appendStreamChunk(chunk);
        }
      };
      
      const content = await writeNextChapterContent(novel, activeChapterIdx, activeVolumeIdx, onChunk);
      if (!isMountedRef.current) return;
      
      if (content && content.trim()) {
        // 更新下一章节的内容（本地状态）
        const newVolumes = [...novel.volumes];
        const nextChapter = newVolumes[activeVolumeIdx].chapters[nextChapterIndex];
        nextChapter.content = content;
        updateNovel({ volumes: newVolumes });
        
        // 立即保存到数据库
        try {
          const volume = novel.volumes[activeVolumeIdx];
          const nextChapterObj = chapters[nextChapterIndex];
          await chapterApi.update(volume.id, nextChapterObj.id, {
            title: nextChapterObj.title,
            summary: nextChapterObj.summary,
            content: content,
            aiPromptHints: nextChapterObj.aiPromptHints,
          });
          addLog('success', `✅ 下一章节内容已保存到数据库！`);
        } catch (saveError: any) {
          addLog('warning', `⚠️ 保存到数据库失败: ${saveError?.message || '未知错误'}，内容已更新到本地`);
          console.error('保存下一章节内容失败:', saveError);
        }
        
        // 提取下一章节的伏笔
        try {
          addLog('step', '💡 提取下一章节的伏笔线索...');
          const existingForeshadowings = novel.foreshadowings.map(f => ({ content: f.content }));
          const extractedForeshadowings = await extractForeshadowingsFromChapter(
            novel.title,
            novel.genre,
            nextChapter.title,
            content,
            existingForeshadowings
          );
          
          if (extractedForeshadowings && extractedForeshadowings.length > 0) {
            const newForeshadowings = extractedForeshadowings.map((f: any) => ({
              content: f.content || '',
              chapterId: nextChapter.id,
              isResolved: 'false'
            }));
            
            // 保存到后端
            const savedForeshadowings = await foreshadowingApi.create(novel.id, newForeshadowings);
            
            // 更新本地状态
            updateNovel({
              foreshadowings: [...novel.foreshadowings, ...savedForeshadowings]
            });
            
            addLog('success', `✅ 已提取 ${savedForeshadowings.length} 个伏笔`);
            savedForeshadowings.forEach((f, idx) => {
              addLog('info', `   ${idx + 1}. ${f.content.substring(0, 50)}${f.content.length > 50 ? '...' : ''}`);
            });
          } else {
            addLog('info', 'ℹ️ 下一章节未发现新的伏笔线索');
          }
        } catch (err: any) {
          addLog('warning', `⚠️ 提取伏笔失败: ${err?.message || '未知错误'}，章节内容已保存`);
        }
        
        // 自动切换到下一章节
        setActiveChapterIdx(nextChapterIndex);
        
        addLog('success', `✅ 下一章节生成成功！`);
        addLog('info', `📄 内容长度: ${content.length} 字符`);
        addLog('info', `🔄 已自动切换到下一章节`);
      } else {
        addLog('error', '❌ 生成失败：返回的内容为空');
        alert('生成下一章节失败：返回的内容为空，请重试。');
      }
    } catch (err: any) {
      if (!isMountedRef.current) return;
      
      addLog('error', `❌ 生成失败: ${err?.message || '未知错误'}`);
      const errorMessage = err?.message || err?.toString() || '未知错误';
      alert(`生成下一章节失败：${errorMessage}\n\n请检查：\n1. API Key 是否正确配置\n2. 网络连接是否正常\n3. 代理设置是否正确`);
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

  return (
    <div className="flex h-full overflow-hidden flex-col lg:flex-row">
      {/* Chapter Sidebar - 移动端隐藏，使用底部导航或按钮切换 */}
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
            当前卷：{novel.volumes[activeVolumeIdx]?.title || `第 ${activeVolumeIdx + 1} 卷`}
          </div>
        </div>
        
        {/* 卷列表（如果有多卷） */}
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
                  title={`第 ${volIdx + 1} 卷：${vol.title} (${vol.chapters.length} 章)`}
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
              <p className="text-xs text-slate-400 p-2 italic mb-3">还没有章节。</p>
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

      {/* Editor Area */}
      <div className="flex-1 flex flex-col bg-white min-w-0 relative">
        {/* 移动端章节选择器 - 使用最简单的方式 */}
        <div 
          className="lg:hidden fixed top-14 left-0 right-0 px-4 py-2 bg-white border-b shadow-sm z-[9999]" 
        >
          <div
            id="mobile-chapter-select-btn"
            onClick={() => {
              console.log('✅✅✅ 按钮被点击了！');
              setShowMobileChapterMenu(prev => !prev);
            }}
            onTouchEnd={(e) => {
              e.preventDefault();
              e.stopPropagation();
              console.log('✅✅✅ 按钮被触摸了！');
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
                        {/* 卷选择（如果有多卷） */}
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
                              还没有章节
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
                    title={!currentChapter.content ? "请先完成或生成当前章节" : "生成下一章节内容"}
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
                  placeholder="开始写作或使用 AI 生成章节内容..."
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
            <p className="max-w-xs text-sm mb-4">从列表中选择一个章节，或在大纲视图中创建一个。</p>
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
                placeholder="写作提示（用于 AI 生成）..."
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
                  <p className="text-[10px] text-slate-500">优化词汇并提升文笔质量。</p>
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
  );
};

export default EditorView;
