
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
}

const Dashboard: React.FC<DashboardProps> = ({ novel, updateNovel, onStartWriting }) => {
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
        const activeTasks = await taskService.getActiveTasks();
        
        // 过滤出当前小说的运行中任务
        const novelActiveTasks = activeTasks.filter(
          task => task.novel_id === novel.id && task.status === 'running'
        );
        
        if (novelActiveTasks.length > 0) {
          // 如果有运行中的任务，显示提示
          console.log(`发现 ${novelActiveTasks.length} 个正在执行的任务`);
          // 可以在这里添加UI提示，让用户知道有任务正在运行
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
      // 1. 生成大纲和卷结构（使用任务系统）
      addLog('step', '📝 步骤 1/5: 生成完整大纲和卷结构...');
      addLog('info', `📖 小说标题: 《${novel.title}》`);
      addLog('info', `📚 类型: ${novel.genre}`);
      addLog('info', `💡 创意摘要: ${novel.synopsis.substring(0, 100)}${novel.synopsis.length > 100 ? '...' : ''}`);
      addLog('info', '🚀 开始创建生成任务...');
      
      // 导入任务服务
      const { generateFullOutline } = await import('../services/geminiService');
      const taskServiceModule = await import('../services/taskService');
      const { startPolling } = taskServiceModule;
      
      // 创建任务
      const taskResult = await generateFullOutline(novel.title, novel.genre, novel.synopsis, novel.id);
      
      if (!taskResult.taskId) {
        throw new Error('任务创建失败：未返回任务ID');
      }
      
      addLog('info', `✅ 任务已创建 (ID: ${taskResult.taskId})，正在后台执行...`);
      addLog('info', '💡 您可以离开此页面，任务将继续在后台执行');
      
      // 开始轮询任务状态
      let outlineResult: { outline: string; volumes: any[] | null } | null = null;
      
      await new Promise<void>((resolve, reject) => {
        startPolling(taskResult.taskId!, {
          onProgress: (task) => {
            if (!isMountedRef.current) return;
            // 更新进度消息
            if (task.progress_message) {
              // 可以在这里更新日志显示进度
              const progressMsg = `⏳ ${task.progress}% - ${task.progress_message}`;
              // 只保留最后一条进度日志，避免日志过多
              setLogs(prev => {
                const filtered = prev.filter(log => !log.message.includes('⏳'));
                return [...filtered, {
                  id: `progress-${Date.now()}`,
                  timestamp: Date.now(),
                  type: 'info' as const,
                  message: progressMsg
                }];
              });
            }
          },
          onComplete: (task) => {
            if (!isMountedRef.current) return;
            addLog('success', '✅ 大纲生成完成！');
            
            if (task.result) {
              outlineResult = {
                outline: task.result.outline || '',
                volumes: task.result.volumes || null,
              };
            }
            resolve();
          },
          onError: (task) => {
            if (!isMountedRef.current) return;
            addLog('error', `❌ 任务失败: ${task.error_message || '未知错误'}`);
            reject(new Error(task.error_message || '任务执行失败'));
          },
        });
      });
      
      if (!outlineResult || !outlineResult.outline) {
        throw new Error('生成失败：返回的大纲为空');
      }
      
      const result = outlineResult;
      if (!result.outline || !result.outline.trim()) {
        throw new Error("生成失败：返回的大纲为空");
      }
      
      addLog('success', '✅ 完整大纲生成成功！');
      addLog('info', `📄 大纲长度: ${result.outline.length} 字符`);
      
      // 显示生成卷结构的提示词
      if (result.outline) {
        const volumesPrompt = `基于以下完整大纲，将故事划分为多个卷（通常3-5卷）。
完整大纲：${result.outline.substring(0, 2000)}

请为每个卷生成标题和简要描述。仅返回 JSON 数组，每个对象包含：
- "title"（卷标题）
- "summary"（卷的简要描述，50-100字）`;
        addLog('info', '📋 提示词 (生成卷结构):');
        addLog('info', '─'.repeat(60));
        volumesPrompt.split('\n').forEach(line => {
          addLog('info', `   ${line.trim()}`);
        });
        addLog('info', '─'.repeat(60));
      }
      
      const updates: Partial<Novel> = { fullOutline: result.outline };
      
      // 处理卷结构
      if (result.volumes && Array.isArray(result.volumes) && result.volumes.length > 0) {
        const volumes: Volume[] = result.volumes.map((v: any, i: number) => ({
          id: `vol-${Date.now()}-${i}`,
          title: v.title || `第${i + 1}卷`,
          summary: v.summary || '',
          outline: '',
          chapters: []
        }));
        updates.volumes = volumes;
        addLog('success', `✅ 已生成 ${volumes.length} 个卷结构`);
        volumes.forEach((vol, idx) => {
          addLog('info', `   ${idx + 1}. ${vol.title}`);
        });
      } else {
        // 如果没有生成卷，创建默认卷
        if (!novel.volumes || novel.volumes.length === 0) {
          updates.volumes = [{ id: 'v1', title: '第一卷', chapters: [] }];
          addLog('warning', '⚠️ 未生成卷结构，使用默认卷');
        }
      }
      
      // 2. 生成角色（如果启用）
      if (generateExtras) {
        try {
          // 生成角色
          addLog('step', '👥 步骤 2/5: 生成角色列表...');
          addLog('info', '🤔 AI 正在分析角色需求...');
          
          // 显示生成角色的提示词
          const charactersPrompt = `基于以下小说信息，生成主要角色列表（3-8个角色）：
标题：${novel.title}
类型：${novel.genre}
简介：${novel.synopsis}
大纲：${result.outline.substring(0, 1000)}

请为每个角色生成详细信息，仅返回 JSON 数组，每个对象包含：
- "name"（角色名称）
- "age"（年龄或年龄段）
- "role"（角色定位：主角、配角、反派等）
- "personality"（性格特点，50-100字）
- "background"（背景故事，100-200字）
- "goals"（角色目标或动机，50-100字）`;
          addLog('info', '📋 提示词 (生成角色):');
          addLog('info', '─'.repeat(60));
          charactersPrompt.split('\n').forEach(line => {
            addLog('info', `   ${line.trim()}`);
          });
          addLog('info', '─'.repeat(60));
          
          const charactersResult = await generateCharacters(novel.title, novel.genre, novel.synopsis, result.outline, novel.id!);
          let charactersData: any[];
          if (charactersResult.taskId) {
            addLog('info', `✅ 任务已创建 (ID: ${charactersResult.taskId})，等待完成...`);
            charactersData = await waitForTask<any[]>(charactersResult.taskId);
          } else {
            charactersData = charactersResult.characters || [];
          }
          const characters: Character[] = charactersData.map((c: any, i: number) => ({
            id: `char-${Date.now()}-${i}`,
            name: c.name || `角色${i + 1}`,
            age: c.age || '',
            role: c.role || '配角',
            personality: c.personality || '',
            background: c.background || '',
            goals: c.goals || ''
          }));
          updates.characters = characters;
          addLog('success', `✅ 已生成 ${characters.length} 个角色`);
          characters.forEach((char, idx) => {
            addLog('info', `   ${idx + 1}. ${char.name} (${char.role})`);
          });
        } catch (err: any) {
          addLog('warning', `⚠️ 生成角色失败: ${err?.message || '未知错误'}，继续其他内容...`);
        }
      }
      
      // 3. 始终生成世界观（与大纲紧密相关）
      try {
        addLog('step', generateExtras ? '🌍 步骤 3/5: 生成世界观设定...' : '🌍 步骤 2/3: 生成世界观设定...');
        addLog('info', '🤔 AI 正在构建世界观体系...');
        
        // 显示生成世界观的提示词
        const worldPrompt = `基于以下小说信息，生成世界观设定列表（5-10个设定）：
标题：${novel.title}
类型：${novel.genre}
简介：${novel.synopsis}
大纲：${result.outline.substring(0, 1000)}

请涵盖以下类别（每个类别1-3个设定）：
- 地理：世界地图、主要地点、自然环境
- 社会：政治体系、社会结构、文化习俗
- 魔法/科技：魔法体系或科技水平、特殊规则
- 历史：重要历史事件、传说故事
- 其他：独特的设定元素

仅返回 JSON 数组，每个对象包含：
- "title"（设定标题）
- "category"（类别：地理、社会、魔法/科技、历史、其他）
- "description"（详细描述，100-200字）`;
        addLog('info', '📋 提示词 (生成世界观):');
        addLog('info', '─'.repeat(60));
        worldPrompt.split('\n').forEach(line => {
          addLog('info', `   ${line.trim()}`);
        });
        addLog('info', '─'.repeat(60));
        
        const worldResult = await generateWorldSettings(novel.title, novel.genre, novel.synopsis, result.outline, novel.id!);
        let worldData: any[];
        if (worldResult.taskId) {
          addLog('info', `✅ 任务已创建 (ID: ${worldResult.taskId})，等待完成...`);
          worldData = await waitForTask<any[]>(worldResult.taskId);
        } else {
          worldData = worldResult.settings || [];
        }
        const worldSettings: WorldSetting[] = worldData.map((w: any, i: number) => ({
          id: `world-${Date.now()}-${i}`,
          title: w.title || `设定${i + 1}`,
          category: (w.category === '地理' || w.category === '社会' || w.category === '魔法/科技' || w.category === '历史' || w.category === '其他') 
            ? w.category as WorldSetting['category']
            : '其他',
          description: w.description || ''
        }));
        updates.worldSettings = worldSettings;
        addLog('success', `✅ 已生成 ${worldSettings.length} 个世界观设定`);
        worldSettings.forEach((world, idx) => {
          addLog('info', `   ${idx + 1}. ${world.title} [${world.category}]`);
        });
      } catch (err: any) {
        addLog('warning', `⚠️ 生成世界观设定失败: ${err?.message || '未知错误'}，继续其他内容...`);
      }
      
      // 4. 始终生成时间线（与大纲紧密相关）
      try {
        addLog('step', generateExtras ? '📅 步骤 4/5: 生成时间线事件...' : '📅 步骤 3/3: 生成时间线事件...');
        addLog('info', '🤔 AI 正在梳理时间线...');
        
        // 显示生成时间线的提示词
        const timelinePrompt = `基于以下小说信息，生成重要时间线事件列表（5-10个事件）：
标题：${novel.title}
类型：${novel.genre}
简介：${novel.synopsis}
大纲：${result.outline.substring(0, 1000)}

请按时间顺序列出关键事件，包括：
- 故事开始前的背景事件
- 故事中的主要转折点
- 重要角色的关键时刻
- 影响剧情走向的重大事件

仅返回 JSON 数组，每个对象包含：
- "time"（时间点或时间段）
- "event"（事件描述，50-100字）
- "impact"（事件影响，50-100字）`;
        addLog('info', '📋 提示词 (生成时间线):');
        addLog('info', '─'.repeat(60));
        timelinePrompt.split('\n').forEach(line => {
          addLog('info', `   ${line.trim()}`);
        });
        addLog('info', '─'.repeat(60));
        
        const timelineResult = await generateTimelineEvents(novel.title, novel.genre, novel.synopsis, result.outline, novel.id!);
        let timelineData: any[];
        if (timelineResult.taskId) {
          addLog('info', `✅ 任务已创建 (ID: ${timelineResult.taskId})，等待完成...`);
          addLog('info', '⏳ 正在等待任务完成（最长5分钟）...');
          timelineData = await waitForTask<any[]>(timelineResult.taskId);
          addLog('success', '✅ 时间线任务执行完成！');
        } else {
          timelineData = timelineResult.events || [];
        }
        
        if (!timelineData || timelineData.length === 0) {
          addLog('warning', '⚠️ 未生成任何时间线事件，将使用空列表');
          timelineData = [];
        }
        
        const timeline: TimelineEvent[] = timelineData.map((t: any, i: number) => ({
          id: `timeline-${Date.now()}-${i}`,
          time: t.time || '未知时间',
          event: t.event || `事件${i + 1}`,
          impact: t.impact || ''
        }));
        updates.timeline = timeline;
        addLog('success', `✅ 已生成 ${timeline.length} 个时间线事件`);
        timeline.slice(0, 5).forEach((event, idx) => {
          addLog('info', `   ${idx + 1}. [${event.time}] ${event.event}`);
        });
        if (timeline.length > 5) {
          addLog('info', `   ... 还有 ${timeline.length - 5} 个事件`);
        }
      } catch (err: any) {
        addLog('error', `❌ 生成时间线事件失败: ${err?.message || '未知错误'}`);
        addLog('warning', '⚠️ 将使用空时间线继续...');
        console.error('Timeline generation error:', err);
        updates.timeline = [];
      }
      
      // 5. 始终生成伏笔（从大纲中提取）
      try {
        addLog('step', generateExtras ? '💡 步骤 5/6: 生成伏笔线索...' : '💡 步骤 4/5: 生成伏笔线索...');
        addLog('info', '🤔 AI 正在分析大纲中的伏笔...');
        
        const foreshadowingsResult = await generateForeshadowings(novel.title, novel.genre, novel.synopsis, result.outline, novel.id!);
        let foreshadowingsData: any[];
        if (foreshadowingsResult.taskId) {
          addLog('info', `✅ 任务已创建 (ID: ${foreshadowingsResult.taskId})，等待完成...`);
          addLog('info', '⏳ 正在等待任务完成（最长5分钟）...');
          foreshadowingsData = await waitForTask<any[]>(foreshadowingsResult.taskId);
          addLog('success', '✅ 伏笔任务执行完成！');
        } else {
          foreshadowingsData = foreshadowingsResult.foreshadowings || [];
        }
        
        if (!foreshadowingsData || foreshadowingsData.length === 0) {
          addLog('warning', '⚠️ 未生成任何伏笔，将使用空列表');
          foreshadowingsData = [];
        }
        
        const foreshadowings: Foreshadowing[] = foreshadowingsData.map((f: any, i: number) => ({
          id: `foreshadowing-${Date.now()}-${i}`,
          content: f.content || `伏笔${i + 1}`,
          isResolved: 'false'
        }));
        updates.foreshadowings = foreshadowings;
        addLog('success', `✅ 已生成 ${foreshadowings.length} 个伏笔`);
        foreshadowings.slice(0, 5).forEach((f, idx) => {
          addLog('info', `   ${idx + 1}. ${f.content.substring(0, 50)}${f.content.length > 50 ? '...' : ''}`);
        });
        if (foreshadowings.length > 5) {
          addLog('info', `   ... 还有 ${foreshadowings.length - 5} 个伏笔`);
        }
      } catch (err: any) {
        addLog('error', `❌ 生成伏笔失败: ${err?.message || '未知错误'}`);
        addLog('warning', '⚠️ 将使用空伏笔列表继续...');
        console.error('Foreshadowing generation error:', err);
        updates.foreshadowings = [];
      }
      
      addLog('step', generateExtras ? '🎨 步骤 6/6: 整合所有内容...' : '🎨 步骤 5/5: 整合所有内容...');
      
      // 检查组件是否仍然挂载
      if (!isMountedRef.current) return;
      
      // 更新所有内容
      addLog('info', '💾 正在保存数据到服务器...');
      console.log('📊 准备同步的数据:', {
        timelineCount: updates.timeline?.length || 0,
        foreshadowingsCount: updates.foreshadowings?.length || 0,
        hasTimeline: !!updates.timeline,
        hasForeshadowings: !!updates.foreshadowings
      });
      
      await updateNovel(updates);
      
      // 给服务器一些时间来处理数据
      addLog('info', '⏳ 等待服务器处理数据...');
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // 重新加载当前小说以确保timeline和foreshadowings正确显示
      if (!isMountedRef.current) return;
      
      try {
        addLog('info', '🔄 正在重新加载小说数据...');
        const { novelApi } = await import('../services/apiService');
        const freshNovel = await novelApi.get(novel.id!);
        
        console.log('📊 从服务器获取的数据:', {
          timelineCount: freshNovel.timeline?.length || 0,
          foreshadowingsCount: freshNovel.foreshadowings?.length || 0,
          timeline: freshNovel.timeline,
          foreshadowings: freshNovel.foreshadowings
        });
        
        updateNovel(freshNovel);
        addLog('success', '✅ 数据已从服务器同步！');
        
        // 验证数据
        addLog('info', `📊 验证结果：`);
        addLog('info', `   - 时间线事件: ${freshNovel.timeline?.length || 0} 个`);
        addLog('info', `   - 伏笔: ${freshNovel.foreshadowings?.length || 0} 个`);
        
        if (freshNovel.timeline?.length === 0 && freshNovel.foreshadowings?.length === 0) {
          addLog('warning', '⚠️ 警告：从服务器获取的数据为空！');
          addLog('warning', '⚠️ 请检查后端日志，确认数据是否保存成功');
        }
      } catch (err: any) {
        addLog('error', `❌ 重新加载数据失败: ${err?.message || '未知错误'}`);
        console.error('重新加载失败:', err);
      }
      
      addLog('success', '🎉 所有内容生成完成！');
      addLog('info', '✨ 准备跳转到大纲页面...');
      
      // 延迟跳转，确保状态更新完成
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
      addLog('error', `API Key 状态: ${process.env.API_KEY || process.env.GEMINI_API_KEY ? '已配置' : '未配置'}`);
      
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
      detailedMessage += `当前 API Key 状态：${process.env.API_KEY || process.env.GEMINI_API_KEY ? '已配置' : '未配置'}`;
      
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
