import React, { useEffect, useRef, useState } from 'react';
import type { Novel } from '../types';
import { agentApi } from '../services/apiService';

interface AgentConsoleProps {
  novel: Novel;
}

type ChatRole = 'user' | 'agent' | 'system';

interface ChatMessage {
  id: string;
  role: ChatRole;
  text: string;
  agent?: string;
}

interface StreamEventPayload {
  stage?: string;
  text?: string;
  status?: string;
  attempt?: number;
  issues?: string[];
  score?: number;
  run_id?: string;
  message?: string;
  chapter_id?: string;
}

const stageLabels: Record<string, string> = {
  director: '导演',
  writer: '写作',
  critic: '批评',
  archivist: '档案',
  flow: '流程',
};

const createId = () => `${Date.now()}-${Math.random().toString(16).slice(2)}`;

const AgentConsole: React.FC<AgentConsoleProps> = ({ novel }) => {
  const [message, setMessage] = useState('');
  const [selectedVolumeId, setSelectedVolumeId] = useState('');
  const [selectedChapterId, setSelectedChapterId] = useState('');
  const [provider, setProvider] = useState(() => {
    try {
      return localStorage.getItem('agent_provider') || 'gemini';
    } catch {
      return 'gemini';
    }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [lastFlowRunId, setLastFlowRunId] = useState<string | null>(null);
  const [lastFlowStage, setLastFlowStage] = useState<string | null>(null);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const isPlaceholderNovel = novel?.id === '1';
  const endRef = useRef<HTMLDivElement | null>(null);
  const stageMessageMap = useRef<Record<string, string>>({});

  const volumes = novel?.volumes || [];
  const selectedVolume = volumes.find((volume) => volume.id === selectedVolumeId) || null;
  const chapters = selectedVolume?.chapters || [];

  const getStageLabel = (stage?: string) => {
    if (!stage) return '智能体';
    return stageLabels[stage] || stage;
  };

  const findChapterTitle = (chapterId?: string) => {
    if (!chapterId) return '';
    for (const volume of volumes) {
      const chapter = volume.chapters.find((item) => item.id === chapterId);
      if (chapter) {
        return chapter.title || '';
      }
    }
    return '';
  };

  const extractStageFromRun = (item: any) => {
    if (!item?.output) return null;
    try {
      const parsed = JSON.parse(item.output);
      return parsed.stage || null;
    } catch {
      return null;
    }
  };

  const loadHistory = async () => {
    if (!novel?.id || isPlaceholderNovel) return;
    try {
      const res = await agentApi.history(novel.id, 20);
      setHistory(res?.items || []);
      let foundPending = false;
      if (Array.isArray(res?.items)) {
        const candidates = res.items.filter((item: any) => item.agent === 'flow');
        const latest = candidates.find((item: any) => item.status && item.status !== 'completed');
        if (latest?.id) {
          const stage = extractStageFromRun(latest);
          setLastFlowRunId(latest.id);
          setLastFlowStage(stage);
          setNotice(`检测到未完成的流程：${stage ? getStageLabel(stage) : '等待恢复'}`);
          foundPending = true;
        }
      }
      if (!foundPending) {
        setNotice(null);
      }
    } catch (err: any) {
      setError(err?.message || '加载历史失败');
    }
  };

  const appendMessage = (next: ChatMessage) => {
    setMessages((prev) => [...prev, next]);
  };

  const updateMessage = (id: string, updater: (current: ChatMessage) => ChatMessage) => {
    setMessages((prev) => prev.map((item) => (item.id === id ? updater(item) : item)));
  };

  const loadChatHistory = async () => {
    if (!novel?.id || isPlaceholderNovel) return;
    try {
      const res = await agentApi.chatHistory(novel.id, 200);
      const items = Array.isArray(res?.items) ? res.items : [];
      const base: ChatMessage[] = [
        {
          id: 'welcome',
          role: 'system',
          text: '欢迎来到智能小说写作 Agent，对话会自动触发多角色流程。',
        },
      ];
      const mapped = items.map((item: any) => ({
        id: item.id,
        role: item.role as ChatRole,
        text: item.content || '',
        agent: item.agent ? stageLabels[item.agent] || item.agent : undefined,
      }));
      setMessages([...base, ...mapped]);
    } catch (err: any) {
      setError(err?.message || '加载对话记录失败');
    }
  };

  const upsertStageMessage = (stage: string, text: string) => {
    const existingId = stageMessageMap.current[stage];
    if (existingId) {
      updateMessage(existingId, (item) => ({ ...item, text }));
      return;
    }
    const id = createId();
    stageMessageMap.current[stage] = id;
    appendMessage({ id, role: 'agent', text, agent: getStageLabel(stage) });
  };

  const appendStageChunk = (stage: string, chunk: string) => {
    const existingId = stageMessageMap.current[stage];
    if (existingId) {
      updateMessage(existingId, (item) => ({ ...item, text: `${item.text}${chunk}` }));
      return;
    }
    const id = createId();
    stageMessageMap.current[stage] = id;
    appendMessage({ id, role: 'agent', text: chunk, agent: getStageLabel(stage) });
  };

  const parseSseEvent = (raw: string) => {
    const lines = raw.split(/\r?\n/);
    let event = 'message';
    const dataLines: string[] = [];
    for (const line of lines) {
      if (line.startsWith('event:')) {
        event = line.slice(6).trim();
      }
      if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trim());
      }
    }
    const dataString = dataLines.join('\n');
    if (!dataString) return { event, data: null };
    try {
      return { event, data: JSON.parse(dataString) };
    } catch {
      return { event, data: dataString };
    }
  };

  const consumeSse = async (
    response: Response,
    onEvent: (event: string, data: StreamEventPayload | string | null) => void
  ) => {
    if (!response.body) {
      throw new Error('Stream response has no body');
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let index;
      while ((index = buffer.indexOf('\n\n')) >= 0) {
        const rawEvent = buffer.slice(0, index).trim();
        buffer = buffer.slice(index + 2);
        if (!rawEvent) continue;
        const parsed = parseSseEvent(rawEvent);
        onEvent(parsed.event, parsed.data);
      }
    }
  };

  const streamFlow = async (content: string) => {
    if (!novel?.id || isPlaceholderNovel) return;
    setLoading(true);
    setError(null);
    setNotice(null);
    stageMessageMap.current = {};
    setLastFlowRunId(null);
    setLastFlowStage(null);
    setCurrentRunId(null);
    try {
      const response = await agentApi.flowStream({
        novel_id: novel.id,
        message: content,
        volume_id: selectedVolumeId || undefined,
        chapter_id: selectedChapterId || undefined,
        max_retries: 1,
        critic_threshold: 70,
        summarize_chapters: true,
        overwrite_summaries: false,
        provider,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `请求失败: ${response.status}`);
      }

      await consumeSse(response, (event, data) => {
        if (!data) return;
        if (event === 'status' && typeof data === 'object') {
          if (data.status === 'saved' && data.chapter_id) {
            const title = findChapterTitle(data.chapter_id);
            appendMessage({
              id: createId(),
              role: 'system',
              text: `已保存到章节：${title || data.chapter_id}`,
            });
            return;
          }
          const stage = data.stage || 'agent';
          const stageLabel = getStageLabel(stage);
          const statusText = data.status === 'retry' ? '重试' : '执行';
          if (data.run_id) {
            setCurrentRunId(data.run_id);
            setLastFlowRunId(data.run_id);
            setLastFlowStage(stage || null);
          }
          appendMessage({
            id: createId(),
            role: 'system',
            text: `流程更新：${stageLabel} · ${statusText}${data.attempt ? ` · 第${data.attempt}次` : ''}`,
          });
          return;
        }
        if (event === 'chunk' && typeof data === 'object' && data.text) {
          appendStageChunk(data.stage || 'flow', data.text);
          return;
        }
        if (event === 'stage_output' && typeof data === 'object') {
          const stage = data.stage || 'flow';
          upsertStageMessage(stage, data.text || '');
          return;
        }
        if (event === 'done' && typeof data === 'object') {
          setNotice(`流程完成 · 评分 ${data.score ?? '-'}`);
          setLastFlowRunId(null);
          setLastFlowStage(null);
          setCurrentRunId(null);
          loadHistory();
          setLoading(false);
        }
        if (event === 'error' && typeof data === 'object') {
          const msg = data.message || data.text || data.status || '流程执行失败';
          setError(msg);
          appendMessage({ id: createId(), role: 'system', text: `流程错误：${msg}` });
          if (data.run_id) {
            setLastFlowRunId(data.run_id);
            setLastFlowStage(data.stage || null);
            setCurrentRunId(null);
          }
          setLoading(false);
        }
        if (event === 'cancelled' && typeof data === 'object') {
          setNotice('流程已停止');
          appendMessage({ id: createId(), role: 'system', text: '已中止当前流程' });
          if (data.run_id) {
            setLastFlowRunId(data.run_id);
            setLastFlowStage(data.stage || null);
          }
          setCurrentRunId(null);
          setLoading(false);
        }
      });
    } catch (err: any) {
      const msg = err?.message || '流程请求失败';
      setError(msg);
      appendMessage({ id: createId(), role: 'system', text: `流程错误：${msg}` });
    } finally {
      setLoading(false);
    }
  };

  const resumeFlow = async () => {
    if (!lastFlowRunId || loading) return;
    setLoading(true);
    setError(null);
    setNotice(null);
    appendMessage({
      id: createId(),
      role: 'system',
      text: `继续流程：${lastFlowStage ? getStageLabel(lastFlowStage) : '上次未完成步骤'}...`,
    });
    setCurrentRunId(lastFlowRunId);
    try {
      const response = await agentApi.flowResumeStream({ run_id: lastFlowRunId, provider });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `请求失败: ${response.status}`);
      }
      await consumeSse(response, (event, data) => {
        if (!data) return;
        if (event === 'status' && typeof data === 'object') {
          if (data.status === 'saved' && data.chapter_id) {
            const title = findChapterTitle(data.chapter_id);
            appendMessage({
              id: createId(),
              role: 'system',
              text: `已保存到章节：${title || data.chapter_id}`,
            });
            return;
          }
          const stage = data.stage || 'agent';
          const stageLabel = getStageLabel(stage);
          const statusText = data.status === 'retry' ? '重试' : '执行';
          if (data.run_id) {
            setCurrentRunId(data.run_id);
            setLastFlowRunId(data.run_id);
            setLastFlowStage(stage || null);
          }
          appendMessage({
            id: createId(),
            role: 'system',
            text: `流程更新：${stageLabel} · ${statusText}${data.attempt ? ` · 第${data.attempt}次` : ''}`,
          });
          return;
        }
        if (event === 'chunk' && typeof data === 'object' && data.text) {
          appendStageChunk(data.stage || 'flow', data.text);
          return;
        }
        if (event === 'stage_output' && typeof data === 'object') {
          const stage = data.stage || 'flow';
          upsertStageMessage(stage, data.text || '');
          return;
        }
        if (event === 'done' && typeof data === 'object') {
          setNotice(`流程完成 · 评分 ${data.score ?? '-'}`);
          setLastFlowRunId(null);
          setLastFlowStage(null);
          setCurrentRunId(null);
          loadHistory();
          setLoading(false);
        }
        if (event === 'error' && typeof data === 'object') {
          const msg = data.message || data.text || data.status || '流程执行失败';
          setError(msg);
          appendMessage({ id: createId(), role: 'system', text: `流程错误：${msg}` });
          if (data.run_id) {
            setLastFlowRunId(data.run_id);
            setLastFlowStage(data.stage || null);
            setCurrentRunId(null);
          }
          setLoading(false);
        }
        if (event === 'cancelled' && typeof data === 'object') {
          setNotice('流程已停止');
          appendMessage({ id: createId(), role: 'system', text: '已中止当前流程' });
          if (data.run_id) {
            setLastFlowRunId(data.run_id);
            setLastFlowStage(data.stage || null);
          }
          setCurrentRunId(null);
          setLoading(false);
        }
      });
    } catch (err: any) {
      const msg = err?.message || '流程请求失败';
      setError(msg);
      appendMessage({ id: createId(), role: 'system', text: `流程错误：${msg}` });
      setLoading(false);
    } finally {
      setLoading(false);
    }
  };

  const stopRun = async () => {
    if (!currentRunId) return;
    setNotice('正在停止流程...');
    try {
      await agentApi.cancelRun({ run_id: currentRunId });
    } catch (err: any) {
      setError(err?.message || '停止失败');
    }
  };

  const handleSend = async () => {
    const trimmed = message.trim();
    if (!trimmed) {
      setError('请输入内容');
      return;
    }
    appendMessage({ id: createId(), role: 'user', text: trimmed });
    setMessage('');
    await streamFlow(trimmed);
  };

  useEffect(() => {
    loadHistory();
    loadChatHistory();
  }, [novel?.id]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <div
      className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white/70 p-6"
      style={{
        '--agent-ink': '#111213',
        '--agent-cream': '#f7efe3',
        '--agent-accent': '#ff7a3d',
        '--agent-accent-2': '#1f7a8c',
        '--agent-glow': '#ffd29d',
      } as React.CSSProperties}
    >
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-24 -top-24 h-64 w-64 rounded-full bg-[radial-gradient(circle_at_center,rgba(255,122,61,0.35),transparent_65%)]" />
        <div className="absolute -right-24 top-8 h-72 w-72 rounded-full bg-[radial-gradient(circle_at_center,rgba(31,122,140,0.3),transparent_60%)]" />
        <div className="absolute bottom-0 left-1/3 h-64 w-64 rounded-full bg-[radial-gradient(circle_at_center,rgba(255,210,157,0.35),transparent_70%)]" />
      </div>

      <div className="relative z-10 grid grid-cols-1 gap-6 lg:grid-cols-[1.3fr_0.7fr]">
        <section className="flex flex-col gap-4">
          <header className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p
                className="text-xs uppercase tracking-[0.3em] text-[color:var(--agent-accent-2)]"
                style={{ fontFamily: '"Space Grotesk", sans-serif' }}
              >
                对话控制台
              </p>
              <h2
                className="text-2xl font-semibold text-[color:var(--agent-ink)]"
                style={{ fontFamily: '"Fraunces", "Noto Serif SC", serif' }}
              >
                智能小说写作 Agent
              </h2>
              <p className="text-sm text-slate-600">以对话驱动多角色协作写作与归档。</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600">
                {loading ? '生成中...' : '就绪'}
              </span>
              <span className="rounded-full bg-[color:var(--agent-ink)] px-3 py-1 text-xs text-[color:var(--agent-cream)]">
                {novel?.title || '未选择作品'}
              </span>
            </div>
          </header>

          {(error || notice) && (
            <div className="flex flex-col gap-2 text-sm">
              {error && <div className="rounded-xl bg-red-50 px-4 py-2 text-red-700">{error}</div>}
              {notice && (
                <div className="rounded-xl bg-white/80 px-4 py-2 text-slate-700">{notice}</div>
              )}
            </div>
          )}

          <div className="flex h-[70vh] max-h-[720px] min-h-[420px] flex-col rounded-2xl border border-slate-200 bg-white/80 px-4 py-5 shadow-[0_12px_30px_rgba(15,23,42,0.08)]">
            <div className="flex-1 space-y-4 overflow-y-auto pr-2">
              {messages.map((item) => (
                <div
                  key={item.id}
                  className={`flex ${item.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                      item.role === 'user'
                        ? 'bg-[color:var(--agent-accent)] text-white'
                        : item.role === 'agent'
                        ? 'bg-[color:var(--agent-ink)] text-[color:var(--agent-cream)]'
                        : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {item.role !== 'user' && item.agent && (
                      <div className="mb-1 text-xs uppercase tracking-[0.2em] text-white/70">
                        {item.agent}
                      </div>
                    )}
                    <div className="whitespace-pre-wrap">{item.text}</div>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="max-w-[70%] rounded-2xl bg-[color:var(--agent-ink)]/90 px-4 py-3 text-sm text-[color:var(--agent-cream)]">
                    <div className="mb-1 text-xs uppercase tracking-[0.2em] text-white/70">智能体</div>
                    正在生成内容...
                  </div>
                </div>
              )}
              <div ref={endRef} />
            </div>

            <div className="mt-4 rounded-2xl border border-slate-200 bg-white px-4 py-3">
              <div className="mb-3 grid grid-cols-1 gap-2 md:grid-cols-2">
                <select
                  value={selectedVolumeId}
                  onChange={(e) => {
                    setSelectedVolumeId(e.target.value);
                    setSelectedChapterId('');
                  }}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
                >
                  <option value="">选择卷（可选）</option>
                  {volumes.map((volume, index) => (
                    <option key={volume.id} value={volume.id}>
                      第{index + 1}卷 · {volume.title}
                    </option>
                  ))}
                </select>
                <select
                  value={selectedChapterId}
                  onChange={(e) => setSelectedChapterId(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
                  disabled={!selectedVolume}
                >
                  <option value="">选择章（可选）</option>
                  {chapters.map((chapter, index) => (
                    <option key={chapter.id} value={chapter.id}>
                      第{index + 1}章 · {chapter.title}
                    </option>
                  ))}
                </select>
              </div>
              <div className="mb-3">
                <label className="mb-1 block text-xs text-slate-500">Model</label>
                <select
                  value={provider}
                  onChange={(e) => {
                    const value = e.target.value;
                    setProvider(value);
                    try {
                      localStorage.setItem('agent_provider', value);
                    } catch {
                      // ignore storage errors
                    }
                  }}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
                >
                  <option value="deepseek">DeepSeek</option>
                  <option value="gemini">Gemini</option>
                </select>
              </div>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                className="min-h-[96px] w-full resize-none bg-transparent text-sm text-slate-700 outline-none"
                placeholder="输入你的写作需求，Enter 发送，Shift+Enter 换行"
              />
              <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                <div className="text-xs text-slate-500">支持流式输出与流程控制</div>
                <button
                  onClick={loading ? stopRun : handleSend}
                  className={`rounded-full px-5 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[color:var(--agent-cream)] transition ${
                    loading ? 'bg-[color:var(--agent-accent-2)]' : 'bg-[color:var(--agent-ink)]'
                  } hover:opacity-90`}
                >
                  {loading ? (
                    <span className="inline-flex items-center gap-2">
                      <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                      生成中
                    </span>
                  ) : (
                    '发送'
                  )}
                </button>
              </div>
            </div>
          </div>
        </section>

        <aside className="flex flex-col gap-4">
          <div className="rounded-2xl border border-slate-200 bg-white/85 p-4">
            <div className="mb-3 flex items-center justify-between">
              <div className="text-sm font-semibold text-slate-800">流程记录</div>
              <button
                onClick={loadHistory}
                className="rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-500 hover:bg-slate-50"
                disabled={loading}
              >
                刷新
              </button>
            </div>
            <div className="max-h-72 space-y-3 overflow-y-auto text-xs text-slate-600">
              {history.length === 0 ? (
                <div className="rounded-lg border border-dashed border-slate-200 px-3 py-4 text-center text-slate-400">
                  暂无记录
                </div>
              ) : (
                history.map((item) => (
                  <div key={item.id} className="rounded-xl border border-slate-100 bg-white px-3 py-2">
                    <div className="text-[10px] uppercase tracking-[0.2em] text-slate-400">
                      {item.agent}
                    </div>
                    <div className="mt-1 line-clamp-2 text-slate-600">
                      {item.input_text || item.input || ''}
                    </div>
                  </div>
                ))
              )}
            </div>
            {currentRunId && (
              <button
                onClick={stopRun}
                className="mt-3 w-full rounded-full border border-slate-200 px-3 py-2 text-xs text-slate-700 hover:bg-slate-50"
                disabled={!loading}
              >
                停止当前流程
              </button>
            )}
            {lastFlowRunId && (
              <button
                onClick={resumeFlow}
                className="mt-3 w-full rounded-full border border-slate-200 px-3 py-2 text-xs text-slate-700 hover:bg-slate-50"
                disabled={loading}
              >
                继续未完成流程
              </button>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
};

export default AgentConsole;
