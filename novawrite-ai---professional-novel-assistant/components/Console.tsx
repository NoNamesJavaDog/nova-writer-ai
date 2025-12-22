import React, { useEffect, useRef } from 'react';
import { Terminal, X, Minimize2, Maximize2 } from 'lucide-react';

export interface LogEntry {
  id: string;
  timestamp: number;
  type: 'info' | 'success' | 'warning' | 'error' | 'step' | 'stream';
  message: string;
}

interface ConsoleProps {
  logs: LogEntry[];
  showConsole: boolean;
  consoleMinimized: boolean;
  onClose: () => void;
  onMinimize: (minimized: boolean) => void;
  onClear: () => void;
}

const Console: React.FC<ConsoleProps> = ({
  logs,
  showConsole,
  consoleMinimized,
  onClose,
  onMinimize,
  onClear
}) => {
  const consoleEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    if (consoleEndRef.current && showConsole && !consoleMinimized) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, showConsole, consoleMinimized]);

  // 格式化时间戳
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  if (!showConsole) return null;

  return (
    <div 
      className={`fixed ${consoleMinimized ? 'bottom-0 right-4' : 'bottom-4 right-4 left-4 md:left-auto md:w-[600px]'} bg-slate-900 text-slate-100 rounded-lg shadow-2xl border border-slate-700 flex flex-col transition-all duration-300 z-50`} 
      style={{ maxHeight: consoleMinimized ? '50px' : '400px' }}
    >
      {/* 控制台头部 */}
      <div className="flex items-center justify-between p-3 border-b border-slate-700 bg-slate-800 rounded-t-lg">
        <div className="flex items-center gap-2">
          <Terminal size={16} className="text-indigo-400" />
          <span className="text-sm font-semibold text-slate-200">生成控制台</span>
          {logs.length > 0 && (
            <span className="px-2 py-0.5 bg-slate-700 text-xs rounded text-slate-300">
              {logs.length} 条日志
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onClear}
            disabled={logs.length === 0}
            className="px-2 py-1 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="清空日志"
          >
            清空
          </button>
          <button
            onClick={() => onMinimize(!consoleMinimized)}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700 rounded transition-colors"
            title={consoleMinimized ? "展开" : "最小化"}
          >
            {consoleMinimized ? <Maximize2 size={14} /> : <Minimize2 size={14} />}
          </button>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-700 rounded transition-colors"
            title="关闭"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* 日志内容区域 */}
      {!consoleMinimized && (
        <div className="flex-1 overflow-y-auto p-3 font-mono text-xs space-y-1">
          {logs.length === 0 ? (
            <div className="text-slate-500 text-center py-8">
              <Terminal size={32} className="mx-auto mb-2 opacity-50" />
              <p>等待生成开始...</p>
            </div>
          ) : (
            logs.map((log) => {
              let className = 'text-slate-300';
              let prefix = '';
              
              switch (log.type) {
                case 'success':
                  className = 'text-green-400';
                  prefix = '✓';
                  break;
                case 'error':
                  className = 'text-red-400';
                  prefix = '✗';
                  break;
                case 'warning':
                  className = 'text-yellow-400';
                  prefix = '⚠';
                  break;
                case 'step':
                  className = 'text-indigo-400 font-semibold';
                  prefix = '→';
                  break;
                case 'stream':
                  className = 'text-cyan-400';
                  prefix = '▸';
                  break;
                default:
                  prefix = '·';
              }

              return (
                <div key={log.id} className={`${className} flex items-start gap-2 py-1`}>
                  <span className="text-slate-600 shrink-0 w-16 text-right">{formatTime(log.timestamp)}</span>
                  <span className="shrink-0 w-4">{prefix}</span>
                  <span className="flex-1 break-words">{log.message}</span>
                </div>
              );
            })
          )}
          <div ref={consoleEndRef} />
        </div>
      )}
    </div>
  );
};

export default Console;

