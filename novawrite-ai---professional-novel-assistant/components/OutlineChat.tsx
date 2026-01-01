import React, { useState, useRef, useEffect } from 'react';
import { Novel } from '../types';
import { MessageCircle, Send, X, Bot, User } from 'lucide-react';
import { modifyOutlineByDialogue } from '../services/geminiService';
import { startPolling } from '../services/taskService';
import Console, { LogEntry } from './Console';

interface OutlineChatProps {
  novel: Novel;
  updateNovel: (updates: Partial<Novel>) => void;
  onClose: () => void;
  loadNovels?: () => Promise<void>;  // 添加重新加载函数
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

const OutlineChat: React.FC<OutlineChatProps> = ({ novel, updateNovel, onClose, loadNovels }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [showConsole, setShowConsole] = useState(false);
  const [consoleMinimized, setConsoleMinimized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    // 初始化欢迎消息
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: `你好！我是你的小说编辑助手。我可以帮你通过对话的方式修改《${novel.title || '未命名小说'}》的大纲，并自动更新相关的角色、世界观和时间线设定。\n\n你可以告诉我想要如何修改大纲，比如：\n- "我想让主角在第二卷时变得更加强大"\n- "增加一个反派角色，他在第三卷出现"\n- "修改世界观，添加魔法体系"\n- "调整时间线，让某个事件提前发生"`,
      timestamp: Date.now()
    }]);
  }, [novel.title]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    
    const userMessage = input.trim();
    setInput('');
    
    // 添加用户消息
    const userMsg: Message = {
      id: `msg-${Date.now()}-user`,
      role: 'user',
      content: userMessage,
      timestamp: Date.now()
    };
    setMessages(prev => [...prev, userMsg]);
    
    setLoading(true);
    setShowConsole(true);
    setConsoleMinimized(false);
    clearLogs();
    
    try {
      addLog('step', '🤖 分析用户修改请求...');
      addLog('info', `📝 用户请求: ${userMessage}`);
      
      // 显示提示词
      const modifyPrompt = `你是一名资深小说编辑，用户想要修改小说《${novel.title}》的大纲。

当前小说信息：
类型：${novel.genre}
简介：${novel.synopsis}
当前大纲：${novel.fullOutline.substring(0, 2000)}${novel.fullOutline.length > 2000 ? '...' : ''}

角色列表：${novel.characters.map(c => `${c.name}（${c.role}）：${c.personality}`).join('；') || '暂无'}

世界观设定：${novel.worldSettings.map(w => `${w.title}（${w.category}）：${w.description}`).join('；') || '暂无'}

时间线事件：${novel.timeline.map(t => `[${t.time}] ${t.event}`).join('；') || '暂无'}

用户修改请求：${userMessage}

请根据用户的修改请求，生成修改后的内容。`;
      
      addLog('info', '📋 提示词 (对话修改大纲):');
      addLog('info', '─'.repeat(60));
      modifyPrompt.split('\n').slice(0, 10).forEach(line => {
        addLog('info', `   ${line.trim()}`);
      });
      addLog('info', '   ...');
      addLog('info', '─'.repeat(60));
      
      addLog('step', '🚀 创建修改任务...');
      
      // 创建任务
      const taskResult = await modifyOutlineByDialogue(novel, userMessage);
      
      if (!taskResult.taskId) {
        throw new Error('任务创建失败：未返回任务ID');
      }
      
      addLog('info', `✅ 任务已创建 (ID: ${taskResult.taskId})，正在后台执行...`);
      addLog('info', '💡 您可以离开此页面，任务将继续在后台执行');
      
      // 等待任务完成（带进度更新）
      addLog('step', '⏳ 等待任务完成...');
      
      // 自定义任务等待，以便显示进度
      await new Promise<void>((resolve, reject) => {
        startPolling(taskResult.taskId, {
          onProgress: (task) => {
            // 更新进度消息
            if (task.progress_message) {
              const progressMsg = `⏳ ${task.progress}% - ${task.progress_message}`;
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
          onComplete: async (task) => {
            addLog('success', '✅ 大纲修改完成！后端已自动保存');
            addLog('info', '🔄 正在重新加载最新数据...');
            
            // 重新加载小说数据（后端已经保存）
            if (loadNovels) {
              await loadNovels();
              addLog('success', '✅ 数据加载完成！');
            }
            
            resolve();
          },
          onError: (task) => {
            reject(new Error(task.error_message || '任务执行失败'));
          },
        });
      });
      
      // AI助手回复
      const assistantMsg: Message = {
        id: `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: '大纲修改完成！所有更改已自动保存到数据库。',
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, assistantMsg]);
      
      addLog('success', '🎉 修改完成，控制台将在3秒后自动关闭');
      setTimeout(() => {
        setShowConsole(false);
      }, 3000);
      
    } catch (error: any) {
      const errorMessage = error?.message || '未知错误';
      addLog('error', `❌ 修改失败: ${errorMessage}`);
      
      // 构建更详细的错误提示
      let detailedErrorMessage = `抱歉，修改大纲时出现错误。\n\n${errorMessage}\n\n`;
      
      if (errorMessage.includes('网络连接失败') || errorMessage.includes('Failed to fetch')) {
        detailedErrorMessage += '💡 网络问题解决步骤：\n\n';
        detailedErrorMessage += '【重要】浏览器端需要系统级代理配置：\n\n';
        detailedErrorMessage += '方法 1：配置 Windows 系统代理（推荐）\n';
        detailedErrorMessage += '  1. 打开"设置" → "网络和 Internet" → "代理"\n';
        detailedErrorMessage += '  2. 开启"使用代理服务器"\n';
        detailedErrorMessage += '  3. 地址：127.0.0.1，端口：7899\n';
        detailedErrorMessage += '  4. 保存后完全关闭浏览器（所有窗口）\n';
        detailedErrorMessage += '  5. 重新打开浏览器并重试\n\n';
        detailedErrorMessage += '方法 2：使用浏览器代理扩展\n';
        detailedErrorMessage += '  1. 安装 SwitchyOmega 扩展（Chrome/Edge）\n';
        detailedErrorMessage += '  2. 配置 HTTP 代理：127.0.0.1:7899\n';
        detailedErrorMessage += '  3. 应用到所有网站\n\n';
        detailedErrorMessage += '方法 3：检查代理软件\n';
        detailedErrorMessage += '  1. 确认代理软件正在运行\n';
        detailedErrorMessage += '  2. 确认端口是 7899\n';
        detailedErrorMessage += '  3. 确认代理规则允许访问 Google API\n\n';
        detailedErrorMessage += '⚠️ 注意：Node.js 的 HTTP_PROXY 环境变量对浏览器请求无效！';
      } else if (errorMessage.includes('API Key')) {
        detailedErrorMessage += '💡 API Key 问题解决建议：\n';
        detailedErrorMessage += '1. 检查项目根目录是否有 .env.local 文件\n';
        detailedErrorMessage += '2. 确认文件中有：GEMINI_API_KEY=your_key\n';
        detailedErrorMessage += '3. 重启开发服务器（npm run dev）';
      } else if (errorMessage.includes('超时') || errorMessage.includes('timeout')) {
        detailedErrorMessage += '💡 超时问题解决建议：\n';
        detailedErrorMessage += '1. 尝试简化你的修改请求\n';
        detailedErrorMessage += '2. 检查网络连接是否稳定\n';
        detailedErrorMessage += '3. 稍后重试';
      } else {
        detailedErrorMessage += '💡 请尝试：\n';
        detailedErrorMessage += '1. 检查你的请求是否清晰明确\n';
        detailedErrorMessage += '2. 查看控制台获取详细错误信息\n';
        detailedErrorMessage += '3. 稍后重试';
      }
      
      const errorMsg: Message = {
        id: `msg-${Date.now()}-error`,
        role: 'assistant',
        content: detailedErrorMessage,
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div 
        className="bg-white rounded-xl shadow-2xl w-full max-w-4xl h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="p-4 border-b flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageCircle size={24} className="text-indigo-600" />
            <h2 className="text-xl font-bold text-slate-800">对话修改大纲</h2>
            <span className="text-sm text-slate-500">《{novel.title || '未命名小说'}》</span>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X size={20} className="text-slate-500" />
          </button>
        </div>

        {/* 消息列表 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                msg.role === 'user' ? 'bg-indigo-600' : 'bg-slate-600'
              }`}>
                {msg.role === 'user' ? (
                  <User size={18} className="text-white" />
                ) : (
                  <Bot size={18} className="text-white" />
                )}
              </div>
              <div className={`flex-1 max-w-[80%] ${msg.role === 'user' ? 'text-right' : ''}`}>
                <div className={`inline-block p-3 rounded-lg ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-slate-800 border'
                }`}>
                  <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center shrink-0">
                <Bot size={18} className="text-white" />
              </div>
              <div className="bg-white p-3 rounded-lg border">
                <div className="flex items-center gap-2 text-slate-600 text-sm">
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  <span className="ml-2">正在思考和修改...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 输入框 */}
        <div className="p-4 border-t bg-white">
          <div className="flex gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="告诉我你想如何修改大纲..."
              rows={2}
              className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none resize-none text-sm"
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <Send size={18} />
            </button>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            提示：按 Enter 发送，Shift+Enter 换行
          </p>
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
    </div>
  );
};

export default OutlineChat;

