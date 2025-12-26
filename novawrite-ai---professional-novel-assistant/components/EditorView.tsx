
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

  // 娣诲姞鏃ュ織
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

  // 杩藉姞娴佸紡鍐呭鍒版渶鍚庝竴涓棩蹇楁潯鐩?  const appendStreamChunk = (chunk: string) => {
    if (!chunk) return;
    setLogs(prev => {
      const lastLog = prev[prev.length - 1];
      if (lastLog && lastLog.type === 'stream') {
        // 濡傛灉鏈€鍚庝竴鏉℃槸娴佸紡鏃ュ織锛岃拷鍔犲唴瀹?        return [...prev.slice(0, -1), { ...lastLog, message: lastLog.message + chunk }];
      } else {
        // 鍚﹀垯鍒涘缓鏂扮殑娴佸紡鏃ュ織鏉＄洰
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

  // 娓呯┖鏃ュ織
  const clearLogs = () => {
    setLogs([]);
  };

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // 璋冭瘯锛氱洃鍚彍鍗曠姸鎬佸彉鍖?  useEffect(() => {
    if (showMobileChapterMenu) {
      console.log('鉁?鑿滃崟搴旇鏄剧ず浜嗭紝showMobileChapterMenu:', showMobileChapterMenu);
    }
  }, [showMobileChapterMenu]);

  // 浣跨敤鍘熺敓DOM浜嬩欢浣滀负鏈€鍚庣殑澶囩敤鏂规
  useEffect(() => {
    const btn = document.getElementById('mobile-chapter-select-btn');
    if (btn) {
      const handleClick = () => {
        console.log('鉁呪渽鉁?鍘熺敓DOM鐐瑰嚮浜嬩欢瑙﹀彂锛?);
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

  const chapters = novel.volumes[activeVolumeIdx]?.chapters || [];
  const currentChapter = activeChapterIdx !== null && chapters[activeChapterIdx] ? chapters[activeChapterIdx] : null;
  const hasNextChapter = activeChapterIdx !== null && activeChapterIdx < chapters.length - 1;
  const nextChapterIndex = activeChapterIdx !== null ? activeChapterIdx + 1 : null;

  // 澶嶅埗绔犺妭鍐呭鍒板壀璐存澘
  const handleCopyChapter = async () => {
    if (!currentChapter || !currentChapter.content) {
      alert('褰撳墠绔犺妭娌℃湁鍐呭鍙鍒?);
      return;
    }

    try {
      await navigator.clipboard.writeText(currentChapter.content);
      addLog('success', '鉁?绔犺妭鍐呭宸插鍒跺埌鍓创鏉?);
      // 鏄剧ず涓€涓复鏃舵彁绀?      const originalTitle = document.title;
      document.title = '鉁?宸插鍒?;
      setTimeout(() => {
        document.title = originalTitle;
      }, 1000);
    } catch (err: any) {
      console.error('澶嶅埗澶辫触:', err);
      addLog('error', `鉂?澶嶅埗澶辫触: ${err?.message || '鏈煡閿欒'}`);
      alert('澶嶅埗澶辫触锛岃鎵嬪姩澶嶅埗鍐呭');
    }
  };

  // 娣诲姞鏂扮珷鑺?  const handleAddChapter = () => {
    const currentVolumes = [...novel.volumes];
    const newChapter: Chapter = {
      id: `ch-${Date.now()}`,
      title: `鏂扮珷鑺?${chapters.length + 1}`,
      summary: '',
      aiPromptHints: '',
      content: ''
    };
    currentVolumes[activeVolumeIdx].chapters = [...chapters, newChapter];
    updateNovel({ volumes: currentVolumes });
    // 鍒囨崲鍒版柊绔犺妭
    setActiveChapterIdx(chapters.length);
  };

  // 鍒犻櫎绔犺妭
  const handleDeleteChapter = (chapterIndex: number) => {
    if (!window.confirm('纭畾瑕佸垹闄ゆ绔犺妭鍚楋紵姝ゆ搷浣滄棤娉曟挙閿€銆?)) {
      return;
    }
    const currentVolumes = [...novel.volumes];
    currentVolumes[activeVolumeIdx].chapters = chapters.filter((_, idx) => idx !== chapterIndex);
    updateNovel({ volumes: currentVolumes });
    
    // 濡傛灉鍒犻櫎鐨勬槸褰撳墠绔犺妭锛屽垏鎹㈠埌鍏朵粬绔犺妭
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

  // 鏇存柊绔犺妭淇℃伅
  const handleUpdateChapter = (chapterIndex: number, updates: Partial<Chapter>) => {
    const currentVolumes = [...novel.volumes];
    currentVolumes[activeVolumeIdx].chapters[chapterIndex] = {
      ...currentVolumes[activeVolumeIdx].chapters[chapterIndex],
      ...updates
    };
    updateNovel({ volumes: currentVolumes });
  };

  // 鍒囨崲鍗?  const handleSwitchVolume = (volumeIndex: number) => {
    if (volumeIndex >= 0 && volumeIndex < novel.volumes.length && volumeIndex !== activeVolumeIdx) {
      if (setActiveVolumeIdx) {
        setActiveVolumeIdx(volumeIndex);
        // 鍒囨崲鍒版柊鍗风殑绗竴涓珷鑺傦紙濡傛灉鏈夛級
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
      addLog('step', `馃摑 鐢熸垚绔犺妭鍐呭: ${chapter.title}`);
      
      // 鏄剧ず鎻愮ず璇?      const chapterPrompt = `璇蜂负灏忚銆?{novel.title}銆嬪垱浣滀竴涓畬鏁寸殑绔犺妭銆?绔犺妭鏍囬锛?{chapter.title}
鎯呰妭鎽樿锛?{chapter.summary}
鍐欎綔鎻愮ず锛?{chapter.aiPromptHints}

涓婁笅鏂囷細
瀹屾暣灏忚绠€浠嬶細${novel.synopsis}
娑夊強瑙掕壊锛?{novel.characters.map(c => `${c.name}锛?{c.personality}`).join('锛?)}
涓栫晫瑙傝鍒欙細${novel.worldSettings.map(s => `${s.title}锛?{s.description}`).join('锛?)}

璇蜂互楂樻枃瀛﹀搧璐ㄣ€佹矇娴稿紡鎻忚堪鍜屽紩浜哄叆鑳滅殑瀵硅瘽鏉ュ垱浣溿€備粎杈撳嚭绔犺妭姝ｆ枃鍐呭銆俙;
      
      addLog('info', '馃搵 鎻愮ず璇?(鐢熸垚绔犺妭鍐呭):');
      addLog('info', '鈹€'.repeat(60));
      chapterPrompt.split('\n').forEach(line => {
        addLog('info', `   ${line.trim()}`);
      });
      addLog('info', '鈹€'.repeat(60));
      
      // 鍒涘缓娴佸紡浼犺緭鍥炶皟
      const onChunk = (chunk: string, isComplete: boolean) => {
        if (isComplete) {
          addLog('success', '\n鉁?鐢熸垚瀹屾垚锛?);
        } else if (chunk) {
          appendStreamChunk(chunk);
        }
      };
      
      const content = await writeChapterContent(novel, activeChapterIdx, activeVolumeIdx, onChunk);
      if (!isMountedRef.current) return;
      
      if (content && content.trim()) {
        // 鍏堟洿鏂版湰鍦扮姸鎬?        handleUpdateContent(content);
        
        // 绔嬪嵆淇濆瓨鍒版暟鎹簱
        try {
          const chapter = chapters[activeChapterIdx];
          const volume = novel.volumes[activeVolumeIdx];
          await chapterApi.update(volume.id, chapter.id, {
            title: chapter.title,
            summary: chapter.summary,
            content: content,
            aiPromptHints: chapter.aiPromptHints,
          });
          addLog('success', `鉁?绔犺妭鍐呭宸蹭繚瀛樺埌鏁版嵁搴擄紒`);
        } catch (saveError: any) {
          addLog('warning', `鈿狅笍 淇濆瓨鍒版暟鎹簱澶辫触: ${saveError?.message || '鏈煡閿欒'}锛屽唴瀹瑰凡鏇存柊鍒版湰鍦癭);
          console.error('淇濆瓨绔犺妭鍐呭澶辫触:', saveError);
        }
        
        addLog('success', `鉁?绔犺妭鍐呭鐢熸垚鎴愬姛锛乣);
        addLog('info', `馃搫 鍐呭闀垮害: ${content.length} 瀛楃`);
        
        // 鎻愬彇鏈珷鑺傜殑浼忕瑪
        try {
          addLog('step', '馃挕 鎻愬彇鏈珷鑺傜殑浼忕瑪绾跨储...');
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
            
            // 淇濆瓨鍒板悗绔?            const savedForeshadowings = await foreshadowingApi.create(novel.id, newForeshadowings);
            
            // 鏇存柊鏈湴鐘舵€?            updateNovel({
              foreshadowings: [...novel.foreshadowings, ...savedForeshadowings]
            });
            
            addLog('success', `鉁?宸叉彁鍙?${savedForeshadowings.length} 涓紡绗擿);
            savedForeshadowings.forEach((f, idx) => {
              addLog('info', `   ${idx + 1}. ${f.content.substring(0, 50)}${f.content.length > 50 ? '...' : ''}`);
            });
          } else {
            addLog('info', '鈩癸笍 鏈珷鑺傛湭鍙戠幇鏂扮殑浼忕瑪绾跨储');
          }
        } catch (err: any) {
          addLog('warning', `鈿狅笍 鎻愬彇浼忕瑪澶辫触: ${err?.message || '鏈煡閿欒'}锛岀珷鑺傚唴瀹瑰凡淇濆瓨`);
        }
      } else {
        addLog('error', '鉂?鐢熸垚澶辫触锛氳繑鍥炵殑鍐呭涓虹┖');
        alert('鐢熸垚澶辫触锛氳繑鍥炵殑鍐呭涓虹┖锛岃閲嶈瘯銆?);
      }
    } catch (err: any) {
      if (!isMountedRef.current) return;
      
      addLog('error', `鉂?鐢熸垚澶辫触: ${err?.message || '鏈煡閿欒'}`);
      const errorMessage = err?.message || err?.toString() || '鏈煡閿欒';
      alert(`鐢熸垚绔犺妭鍐呭澶辫触锛?{errorMessage}\n\n璇锋鏌ワ細\n1. API Key 鏄惁姝ｇ‘閰嶇疆\n2. 缃戠粶杩炴帴鏄惁姝ｅ父\n3. 浠ｇ悊璁剧疆鏄惁姝ｇ‘`);
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
      addLog('step', '馃摑 鎵╁睍閫変腑鏂囨湰...');
      
      // 鏄剧ず鎻愮ず璇?      const expandPrompt = `璇锋墿灞曚互涓嬫枃鏈紝淇濇寔鍘熸湁椋庢牸锛屽苟娣诲姞鏇村鎰熷畼缁嗚妭鍜岃鑹插唴蹇冩兂娉曘€?寰呮墿灞曟枃鏈細${selectedText.substring(0, 500)}${selectedText.length > 500 ? '...' : ''}
涓婁笅鏂囷細${currentChapter?.summary || ''}`;
      
      addLog('info', '馃搵 鎻愮ず璇?(鎵╁睍鏂囨湰):');
      addLog('info', '鈹€'.repeat(60));
      expandPrompt.split('\n').forEach(line => {
        addLog('info', `   ${line.trim()}`);
      });
      addLog('info', '鈹€'.repeat(60));
      
      const expanded = await expandText(selectedText, currentChapter?.summary || "");
      if (!isMountedRef.current) return;
      
      if (expanded && expanded.trim() && currentChapter && activeChapterIdx !== null) {
        const newContent = currentChapter.content.replace(selectedText, expanded);
        handleUpdateContent(newContent);
        
        // 绔嬪嵆淇濆瓨鍒版暟鎹簱
        try {
          const volume = novel.volumes[activeVolumeIdx];
          const chapter = chapters[activeChapterIdx];
          await chapterApi.update(volume.id, chapter.id, {
            title: chapter.title,
            summary: chapter.summary,
            content: newContent,
            aiPromptHints: chapter.aiPromptHints,
          });
          addLog('success', '鉁?鏂囨湰鎵╁睍宸蹭繚瀛樺埌鏁版嵁搴擄紒');
        } catch (saveError: any) {
          addLog('warning', `鈿狅笍 淇濆瓨鍒版暟鎹簱澶辫触: ${saveError?.message || '鏈煡閿欒'}锛屽唴瀹瑰凡鏇存柊鍒版湰鍦癭);
          console.error('淇濆瓨鎵╁睍鏂囨湰澶辫触:', saveError);
        }
        
        addLog('success', '鉁?鏂囨湰鎵╁睍鎴愬姛锛?);
      } else {
        addLog('error', '鉂?鎵╁睍澶辫触锛氳繑鍥炵殑鍐呭涓虹┖');
        alert('鎵╁睍鏂囨湰澶辫触锛氳繑鍥炵殑鍐呭涓虹┖锛岃閲嶈瘯銆?);
      }
    } catch (err: any) {
      if (!isMountedRef.current) return;
      
      addLog('error', `鉂?鎵╁睍澶辫触: ${err?.message || '鏈煡閿欒'}`);
      const errorMessage = err?.message || err?.toString() || '鏈煡閿欒';
      alert(`鎵╁睍鏂囨湰澶辫触锛?{errorMessage}`);
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
      addLog('step', '馃摑 娑﹁壊閫変腑鏂囨湰...');
      
      // 鏄剧ず鎻愮ず璇?      const polishPrompt = `璇锋鼎鑹蹭互涓嬫枃鏈紝鎻愬崌娴佺晠搴︺€佽瘝姹囬€夋嫨鍜屾儏鎰熷叡楦ｃ€備笉瑕佹敼鍙樺師鎰忋€?寰呮鼎鑹叉枃鏈細${selectedText.substring(0, 500)}${selectedText.length > 500 ? '...' : ''}`;
      
      addLog('info', '馃搵 鎻愮ず璇?(娑﹁壊鏂囨湰):');
      addLog('info', '鈹€'.repeat(60));
      polishPrompt.split('\n').forEach(line => {
        addLog('info', `   ${line.trim()}`);
      });
      addLog('info', '鈹€'.repeat(60));
      
      const polished = await polishText(selectedText);
      if (!isMountedRef.current) return;
      
      if (polished && polished.trim() && currentChapter && activeChapterIdx !== null) {
        const newContent = currentChapter.content.replace(selectedText, polished);
        handleUpdateContent(newContent);
        
        // 绔嬪嵆淇濆瓨鍒版暟鎹簱
        try {
          const volume = novel.volumes[activeVolumeIdx];
          const chapter = chapters[activeChapterIdx];
          await chapterApi.update(volume.id, chapter.id, {
            title: chapter.title,
            summary: chapter.summary,
            content: newContent,
            aiPromptHints: chapter.aiPromptHints,
          });
          addLog('success', '鉁?鏂囨湰娑﹁壊宸蹭繚瀛樺埌鏁版嵁搴擄紒');
        } catch (saveError: any) {
          addLog('warning', `鈿狅笍 淇濆瓨鍒版暟鎹簱澶辫触: ${saveError?.message || '鏈煡閿欒'}锛屽唴瀹瑰凡鏇存柊鍒版湰鍦癭);
          console.error('淇濆瓨娑﹁壊鏂囨湰澶辫触:', saveError);
        }
        
        addLog('success', '鉁?鏂囨湰娑﹁壊鎴愬姛锛?);
      } else {
        addLog('error', '鉂?娑﹁壊澶辫触锛氳繑鍥炵殑鍐呭涓虹┖');
        alert('娑﹁壊鏂囨湰澶辫触锛氳繑鍥炵殑鍐呭涓虹┖锛岃閲嶈瘯銆?);
      }
    } catch (err: any) {
      if (!isMountedRef.current) return;
      
      addLog('error', `鉂?娑﹁壊澶辫触: ${err?.message || '鏈煡閿欒'}`);
      const errorMessage = err?.message || err?.toString() || '鏈煡閿欒';
      alert(`娑﹁壊鏂囨湰澶辫触锛?{errorMessage}`);
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
      addLog('step', `馃摑 鐢熸垚涓嬩竴绔犺妭: ${nextChapter.title}`);
      addLog('info', `馃摉 褰撳墠绔犺妭: ${currentChapter?.title}`);
      addLog('info', `馃摉 涓嬩竴绔犺妭: ${nextChapter.title}`);
      
      // 鏄剧ず鎻愮ず璇?      const currentVolume = novel.volumes[activeVolumeIdx];
      const previousChapters = chapters
        .slice(Math.max(0, activeChapterIdx - 2), activeChapterIdx + 1)
        .map((ch, idx) => `绗?{Math.max(0, activeChapterIdx - 2) + idx + 1}绔犮€?{ch.title}銆嬶細${ch.content.substring(0, 500)}${ch.content.length > 500 ? '...' : ''}`)
        .join('\n\n');
      
      const nextChapterPrompt = `璇蜂负灏忚銆?{novel.title}銆嬪垱浣滀笅涓€绔犺妭鐨勫唴瀹广€?
灏忚鍩烘湰淇℃伅锛?绫诲瀷锛?{novel.genre}
绠€浠嬶細${novel.synopsis}

褰撳墠鍗蜂俊鎭細
鍗锋爣棰橈細${currentVolume.title}
${currentVolume.summary ? `鍗锋弿杩帮細${currentVolume.summary}` : ''}

鍓嶆枃鍐呭锛堟渶杩戝嚑绔狅級锛?${previousChapters || '锛堣繖鏄湰鍗风殑绗竴绔狅級'}

褰撳墠绔犺妭淇℃伅锛?绔犺妭鏍囬锛?{currentChapter?.title}
${currentChapter?.content ? `褰撳墠绔犺妭鍐呭棰勮锛?{currentChapter.content.substring(0, 500)}${currentChapter.content.length > 500 ? '...' : ''}` : ''}

涓嬩竴绔犺妭淇℃伅锛堥渶瑕佺敓鎴愮殑鍐呭锛夛細
绔犺妭鏍囬锛?{nextChapter.title}
鎯呰妭鎽樿锛?{nextChapter.summary}
${nextChapter.aiPromptHints ? `鍐欎綔鎻愮ず锛?{nextChapter.aiPromptHints}` : ''}

瑙掕壊淇℃伅锛?${novel.characters.map(c => `${c.name}锛?{c.role}锛夛細鎬ф牸-${c.personality}锛涜儗鏅?${c.background}锛涚洰鏍?${c.goals}`).join('\n') || '鏆傛棤瑙掕壊淇℃伅'}

涓栫晫瑙傝瀹氾細
${novel.worldSettings.map(s => `${s.title}锛?{s.category}锛夛細${s.description}`).join('\n') || '鏆傛棤涓栫晫瑙傝瀹?}

瑕佹眰锛?1. 涓庡墠鏂囧唴瀹逛繚鎸佽繛璐€у拰涓€鑷存€?2. 閬靛惊瑙掕壊鐨勬€ф牸璁惧畾鍜屼笘鐣岃瑙勫垯
3. 鎸夌収涓嬩竴绔犺妭鐨勬儏鑺傛憳瑕佹帹杩涙晠浜?4. 淇濇寔楂樻枃瀛﹀搧璐紝浣跨敤娌夋蹈寮忔弿杩板拰寮曚汉鍏ヨ儨鐨勫璇?5. 浠呰緭鍑虹珷鑺傛鏂囧唴瀹筦;
      
      addLog('info', '馃搵 鎻愮ず璇?(鐢熸垚涓嬩竴绔犺妭):');
      addLog('info', '鈹€'.repeat(60));
      nextChapterPrompt.split('\n').slice(0, 20).forEach(line => {
        addLog('info', `   ${line.trim()}`);
      });
      addLog('info', '   ...');
      addLog('info', '鈹€'.repeat(60));
      
      // 鍒涘缓娴佸紡浼犺緭鍥炶皟
      const onChunk = (chunk: string, isComplete: boolean) => {
        if (isComplete) {
          addLog('success', '\n鉁?鐢熸垚瀹屾垚锛?);
        } else if (chunk) {
          appendStreamChunk(chunk);
        }
      };
      
      const content = await writeNextChapterContent(novel, activeChapterIdx, activeVolumeIdx, onChunk);
      if (!isMountedRef.current) return;
      
      if (content && content.trim()) {
        // 鏇存柊涓嬩竴绔犺妭鐨勫唴瀹癸紙鏈湴鐘舵€侊級
        const newVolumes = [...novel.volumes];
        const nextChapter = newVolumes[activeVolumeIdx].chapters[nextChapterIndex];
        nextChapter.content = content;
        updateNovel({ volumes: newVolumes });
        
        // 绔嬪嵆淇濆瓨鍒版暟鎹簱
        try {
          const volume = novel.volumes[activeVolumeIdx];
          const nextChapterObj = chapters[nextChapterIndex];
          await chapterApi.update(volume.id, nextChapterObj.id, {
            title: nextChapterObj.title,
            summary: nextChapterObj.summary,
            content: content,
            aiPromptHints: nextChapterObj.aiPromptHints,
          });
          addLog('success', `鉁?涓嬩竴绔犺妭鍐呭宸蹭繚瀛樺埌鏁版嵁搴擄紒`);
        } catch (saveError: any) {
          addLog('warning', `鈿狅笍 淇濆瓨鍒版暟鎹簱澶辫触: ${saveError?.message || '鏈煡閿欒'}锛屽唴瀹瑰凡鏇存柊鍒版湰鍦癭);
          console.error('淇濆瓨涓嬩竴绔犺妭鍐呭澶辫触:', saveError);
        }
        
        // 鎻愬彇涓嬩竴绔犺妭鐨勪紡绗?        try {
          addLog('step', '馃挕 鎻愬彇涓嬩竴绔犺妭鐨勪紡绗旂嚎绱?..');
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
            
            // 淇濆瓨鍒板悗绔?            const savedForeshadowings = await foreshadowingApi.create(novel.id, newForeshadowings);
            
            // 鏇存柊鏈湴鐘舵€?            updateNovel({
              foreshadowings: [...novel.foreshadowings, ...savedForeshadowings]
            });
            
            addLog('success', `鉁?宸叉彁鍙?${savedForeshadowings.length} 涓紡绗擿);
            savedForeshadowings.forEach((f, idx) => {
              addLog('info', `   ${idx + 1}. ${f.content.substring(0, 50)}${f.content.length > 50 ? '...' : ''}`);
            });
          } else {
            addLog('info', '鈩癸笍 涓嬩竴绔犺妭鏈彂鐜版柊鐨勪紡绗旂嚎绱?);
          }
        } catch (err: any) {
          addLog('warning', `鈿狅笍 鎻愬彇浼忕瑪澶辫触: ${err?.message || '鏈煡閿欒'}锛岀珷鑺傚唴瀹瑰凡淇濆瓨`);
        }
        
        // 鑷姩鍒囨崲鍒颁笅涓€绔犺妭
        setActiveChapterIdx(nextChapterIndex);
        
        addLog('success', `鉁?涓嬩竴绔犺妭鐢熸垚鎴愬姛锛乣);
        addLog('info', `馃搫 鍐呭闀垮害: ${content.length} 瀛楃`);
        addLog('info', `馃攧 宸茶嚜鍔ㄥ垏鎹㈠埌涓嬩竴绔犺妭`);
      } else {
        addLog('error', '鉂?鐢熸垚澶辫触锛氳繑鍥炵殑鍐呭涓虹┖');
        alert('鐢熸垚涓嬩竴绔犺妭澶辫触锛氳繑鍥炵殑鍐呭涓虹┖锛岃閲嶈瘯銆?);
      }
    } catch (err: any) {
      if (!isMountedRef.current) return;
      
      addLog('error', `鉂?鐢熸垚澶辫触: ${err?.message || '鏈煡閿欒'}`);
      const errorMessage = err?.message || err?.toString() || '鏈煡閿欒';
      alert(`鐢熸垚涓嬩竴绔犺妭澶辫触锛?{errorMessage}\n\n璇锋鏌ワ細\n1. API Key 鏄惁姝ｇ‘閰嶇疆\n2. 缃戠粶杩炴帴鏄惁姝ｅ父\n3. 浠ｇ悊璁剧疆鏄惁姝ｇ‘`);
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

  // 瀵煎嚭绔犺妭鍐呭涓篢XT鏂囦欢
  const handleExportChapter = () => {
    if (!currentChapter || !currentChapter.content) {
      alert('褰撳墠绔犺妭娌℃湁鍐呭锛屾棤娉曞鍑?);
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

  // 瀵煎嚭鏁存湰灏忚涓篢XT鏂囦欢
  const handleExportNovel = () => {
    if (!novel.volumes || novel.volumes.length === 0) {
      alert('娌℃湁鍐呭鍙互瀵煎嚭');
      return;
    }

    let content = `${novel.title}\n\n`;
    if (novel.synopsis) {
      content += `绠€浠嬶細\n${novel.synopsis}\n\n`;
    }
    if (novel.fullOutline) {
      content += `瀹屾暣澶х翰锛歕n${novel.fullOutline}\n\n`;
    }
    content += '='.repeat(50) + '\n\n';

    novel.volumes.forEach((volume, volIdx) => {
      content += `\n绗?{volIdx + 1}鍗凤細${volume.title}\n`;
      if (volume.summary) {
        content += `鍗风畝浠嬶細${volume.summary}\n`;
      }
      content += '='.repeat(50) + '\n\n';

      volume.chapters.forEach((chapter, chIdx) => {
        if (chapter.content && chapter.content.trim()) {
          content += `\n绗?{chIdx + 1}绔狅細${chapter.title}\n\n`;
          content += chapter.content;
          content += '\n\n' + '-'.repeat(50) + '\n\n';
        }
      });
    });

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${novel.title || '鏈懡鍚嶅皬璇?}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <>
      {/* 绉诲姩绔珷鑺傞€夋嫨鍣?- 鏀惧湪鏈€鍓嶉潰锛岀‘淇濇€绘槸娓叉煋 */}
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
            console.log('鉁呪渽鉁?鎸夐挳琚偣鍑讳簡锛?);
            setShowMobileChapterMenu(prev => !prev);
          }}
          onTouchEnd={(e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('鉁呪渽鉁?鎸夐挳琚Е鎽镐簡锛?);
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
              {activeChapterIdx !== null && currentChapter ? `${activeChapterIdx + 1}. ${currentChapter.title}` : '閫夋嫨绔犺妭'}
            </span>
          </div>
          <ChevronDown size={16} style={{ transform: showMobileChapterMenu ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }} />
        </div>
      </div>
      
    <div className="flex h-full overflow-hidden flex-col lg:flex-row">
      {/* Chapter Sidebar - 绉诲姩绔殣钘忥紝浣跨敤搴曢儴瀵艰埅鎴栨寜閽垏鎹?*/}
      <div className="hidden lg:flex w-80 border-r bg-white shrink-0 flex-col">
        <div className="p-4 border-b bg-slate-50">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
              <BookOpen size={16} /> 绔犺妭鍒楄〃
            </h3>
            <button
              onClick={handleAddChapter}
              className="p-1.5 text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
              title="娣诲姞鏂扮珷鑺?
            >
              <Plus size={16} />
            </button>
          </div>
          <div className="text-xs text-slate-500">
            褰撳墠鍗凤細{novel.volumes[activeVolumeIdx]?.title || `绗?${activeVolumeIdx + 1} 鍗穈}
          </div>
        </div>
        
        {/* 鍗峰垪琛紙濡傛灉鏈夊鍗凤級 */}
        {novel.volumes.length > 1 && (
          <div className="p-2 border-b bg-slate-50">
            <div className="text-xs font-semibold text-slate-500 mb-1">鍒囨崲鍗凤細</div>
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
                  title={`绗?${volIdx + 1} 鍗凤細${vol.title} (${vol.chapters.length} 绔?`}
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
              <p className="text-xs text-slate-400 p-2 italic mb-3">杩樻病鏈夌珷鑺傘€?/p>
              <button
                onClick={handleAddChapter}
                className="px-3 py-1.5 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2 mx-auto"
              >
                <Plus size={14} />
                娣诲姞绔犺妭
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
                  title="鍒犻櫎绔犺妭"
                >
                  <X size={12} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      </div>
      
      <div className="flex-1 flex flex-col bg-white min-w-0 relative">
        
        {currentChapter ? (
          <>
            <div className="min-h-[56px] border-b px-4 md:px-6 flex flex-col lg:flex-row lg:items-center justify-between shrink-0 pt-[60px] lg:pt-0 gap-2 lg:gap-0" style={{ position: 'relative', zIndex: 100 }}>
              <div className="flex flex-col flex-1 min-w-0 lg:min-h-[56px] lg:justify-center" style={{ position: 'relative', zIndex: 101 }}>
                {/* 妗岄潰绔珷鑺傛爣棰樿緭鍏?*/}
                <input
                  type="text"
                  value={currentChapter.title}
                  onChange={(e) => handleUpdateChapter(activeChapterIdx!, { title: e.target.value })}
                  className="hidden lg:block text-base md:text-lg font-bold text-slate-800 bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-indigo-500 px-1 -ml-1 rounded truncate w-full"
                  placeholder="绔犺妭鏍囬"
                />
                
                {/* 绉诲姩绔珷鑺備笅鎷夎彍鍗?- 浣跨敤 Portal 娓叉煋鍒?body */}
                {showMobileChapterMenu && typeof document !== 'undefined' && createPortal(
                    <>
                      <div 
                        className="fixed inset-0 z-[100] bg-black/40"
                        onClick={() => {
                          console.log('閬僵灞傜偣鍑伙紝鍏抽棴鑿滃崟');
                          setShowMobileChapterMenu(false);
                        }}
                        onTouchEnd={(e) => {
                          e.preventDefault();
                          console.log('閬僵灞傝Е鎽革紝鍏抽棴鑿滃崟');
                          setShowMobileChapterMenu(false);
                        }}
                        style={{ touchAction: 'manipulation' }}
                      />
                      <div 
                        className="fixed top-[60px] left-4 right-4 bg-white border-2 border-indigo-300 rounded-xl shadow-2xl z-[102] max-h-[calc(100vh-140px)] overflow-y-auto"
                        onClick={(e) => {
                          e.stopPropagation();
                          console.log('鑿滃崟瀹瑰櫒鐐瑰嚮');
                        }}
                        onTouchEnd={(e) => {
                          e.stopPropagation();
                          console.log('鑿滃崟瀹瑰櫒瑙︽懜');
                        }}
                        style={{ 
                          touchAction: 'manipulation',
                          pointerEvents: 'auto',
                          WebkitOverflowScrolling: 'touch'
                        }}
                      >
                        {/* 鍗烽€夋嫨锛堝鏋滄湁澶氬嵎锛?*/}
                        {novel.volumes.length > 1 && (
                          <div className="p-3 border-b bg-indigo-50">
                            <div className="text-xs font-semibold text-indigo-700 mb-2">鍒囨崲鍗凤細</div>
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
                                  绗瑊volIdx + 1}鍗?                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* 绔犺妭鍒楄〃 */}
                        <div className="p-3">
                          {chapters.length === 0 ? (
                            <div className="text-center py-4 text-sm text-slate-400">
                              杩樻病鏈夌珷鑺?                            </div>
                          ) : (
                            chapters.map((ch, idx) => (
                              <button
                                key={ch.id}
                                onClick={(e) => {
                                  e.preventDefault();
                                  e.stopPropagation();
                                  console.log('绔犺妭鎸夐挳鐐瑰嚮:', idx, ch.title);
                                  setActiveChapterIdx(idx);
                                  setShowMobileChapterMenu(false);
                                }}
                                onTouchStart={(e) => {
                                  e.stopPropagation();
                                }}
                                onTouchEnd={(e) => {
                                  e.preventDefault();
                                  e.stopPropagation();
                                  console.log('绔犺妭鎸夐挳瑙︽懜:', idx, ch.title);
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
                            娣诲姞鏂扮珷鑺?                          </button>
                        </div>
                      </div>
                    </>,
                    document.body
                  )}
                
                {/* 妗岄潰绔珷鑺傛爣棰樿緭鍏?*/}
                <input
                  type="text"
                  value={currentChapter.title}
                  onChange={(e) => handleUpdateChapter(activeChapterIdx!, { title: e.target.value })}
                  className="hidden lg:block text-base md:text-lg font-bold text-slate-800 bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-indigo-500 px-1 -ml-1 rounded truncate w-full"
                  placeholder="绔犺妭鏍囬"
                />
                <div className="flex items-center gap-4 mt-1">
                  <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">
                    瀛楁暟: {currentChapter.content.split(/\s+/).filter(Boolean).length}
                  </p>
                  <span className="text-[10px] text-slate-400">
                    瀛楃: {currentChapter.content.length}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-wrap lg:flex-nowrap">
                <button 
                  onClick={handleCopyChapter}
                  disabled={!currentChapter.content}
                  className="px-3 md:px-4 py-2 bg-slate-600 text-white text-xs font-bold rounded-lg hover:bg-slate-700 disabled:bg-slate-200 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
                  title="澶嶅埗鏈珷鍐呭鍒板壀璐存澘"
                >
                  <Copy size={14} />
                  <span className="hidden sm:inline">澶嶅埗</span>
                </button>
                <button 
                  onClick={handleExportChapter}
                  disabled={!currentChapter.content}
                  className="px-3 md:px-4 py-2 bg-blue-600 text-white text-xs font-bold rounded-lg hover:bg-blue-700 disabled:bg-slate-200 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
                  title="瀵煎嚭鏈珷涓篢XT鏂囦欢"
                >
                  <Download size={14} />
                  <span className="hidden sm:inline">瀵煎嚭鏈珷</span>
                  <span className="sm:hidden">瀵煎嚭</span>
                </button>
                <button 
                  onClick={handleExportNovel}
                  className="px-3 md:px-4 py-2 bg-purple-600 text-white text-xs font-bold rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-1.5"
                  title="瀵煎嚭鏁存湰灏忚涓篢XT鏂囦欢"
                >
                  <Download size={14} />
                  <span className="hidden sm:inline">瀵煎嚭灏忚</span>
                  <span className="sm:hidden">鍏ㄩ儴</span>
                </button>
                <button 
                  onClick={handleDraftWithAI}
                  disabled={isWriting}
                  className="px-3 md:px-4 py-2 bg-indigo-600 text-white text-xs font-bold rounded-lg hover:bg-indigo-700 disabled:bg-slate-200 transition-colors flex items-center gap-1.5"
                >
                  {isWriting ? <RefreshCcw size={14} className="animate-spin" /> : <Sparkles size={14} />}
                  <span className="hidden sm:inline">{currentChapter.content ? "閲嶆柊鐢熸垚鑽夌" : "AI 鐢熸垚鑽夌"}</span>
                  <span className="sm:hidden">鐢熸垚</span>
                </button>
                {hasNextChapter && (
                  <button 
                    onClick={handleGenerateNextChapter}
                    disabled={isWriting || !currentChapter.content}
                    className="px-3 md:px-4 py-2 bg-green-600 text-white text-xs font-bold rounded-lg hover:bg-green-700 disabled:bg-slate-200 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
                    title={!currentChapter.content ? "璇峰厛瀹屾垚鎴栫敓鎴愬綋鍓嶇珷鑺? : "鐢熸垚涓嬩竴绔犺妭鍐呭"}
                  >
                    {isWriting ? <RefreshCcw size={14} className="animate-spin" /> : <ArrowRight size={14} />}
                    <span className="hidden sm:inline">鐢熸垚涓嬩竴绔?/span>
                    <span className="sm:hidden">涓嬩竴绔?/span>
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
                      <p className="text-lg font-bold text-indigo-900">AI 姝ｅ湪鍒涗綔涓?..</p>
                      <p className="text-sm text-slate-500">姝ｅ湪铻嶅叆鎮ㄧ殑涓栫晫瑙傝瀹?..</p>
                    </div>
                  </div>
                )}
                
                <textarea
                  value={currentChapter.content}
                  onMouseUp={onSelectText}
                  onChange={(e) => handleUpdateContent(e.target.value)}
                  placeholder="寮€濮嬪啓浣滄垨浣跨敤 AI 鐢熸垚绔犺妭鍐呭..."
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
            <h3 className="text-xl font-bold text-slate-600 mb-2">閫夋嫨涓€涓珷鑺傚紑濮?/h3>
            <p className="max-w-xs text-sm mb-4">浠庡垪琛ㄤ腑閫夋嫨涓€涓珷鑺傦紝鎴栧湪澶х翰瑙嗗浘涓垱寤轰竴涓€?/p>
            {/* 绉诲姩绔細濡傛灉娌℃湁绔犺妭锛屾樉绀烘坊鍔犳寜閽?*/}
            <div className="lg:hidden">
              {chapters.length === 0 ? (
                <button
                  onClick={handleAddChapter}
                  className="px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2 mx-auto"
                >
                  <Plus size={16} />
                  娣诲姞绗竴涓珷鑺?                </button>
              ) : (
                <button
                  onClick={() => setShowMobileChapterMenu(true)}
                  className="px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2 mx-auto"
                >
                  <List size={16} />
                  閫夋嫨绔犺妭
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
              <Wand2 size={16} className="text-indigo-600" /> AI 鍔╂墜
            </h3>
          </div>
          
          <div className="flex-1 p-4 overflow-y-auto space-y-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">绔犺妭鎽樿</h4>
              </div>
              <textarea
                value={currentChapter.summary}
                onChange={(e) => handleUpdateChapter(activeChapterIdx!, { summary: e.target.value })}
                placeholder="绔犺妭鎽樿..."
                rows={3}
                className="w-full px-3 py-2 border rounded-lg text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none resize-none bg-white"
              />
            </div>

            <div className="space-y-3">
              <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">AI 鎻愮ず</h4>
              <textarea
                value={currentChapter.aiPromptHints || ''}
                onChange={(e) => handleUpdateChapter(activeChapterIdx!, { aiPromptHints: e.target.value })}
                placeholder="鍐欎綔鎻愮ず锛堢敤浜?AI 鐢熸垚锛?.."
                rows={2}
                className="w-full px-3 py-2 border rounded-lg text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none resize-none bg-white"
              />
            </div>

            <div className="space-y-3">
              <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">鏅鸿兘宸ュ叿</h4>
              <div className="space-y-2">
                <button 
                  onClick={handleExpandSelection}
                  disabled={!selectedText || isWriting}
                  className="w-full text-left p-3 bg-white border rounded-lg hover:border-indigo-400 transition-all group disabled:opacity-50"
                >
                  <p className="text-xs font-bold text-slate-800 mb-1 flex items-center gap-2">
                    <Sparkles size={14} className="text-indigo-600" /> 鎵╁睍鏂囨湰
                  </p>
                  <p className="text-[10px] text-slate-500">閫夋嫨鏂囨湰骞剁偣鍑讳互娣诲姞鏇村缁嗚妭鍜屾繁搴︺€?/p>
                </button>

                <button 
                  onClick={handlePolishSelection}
                  disabled={!selectedText || isWriting}
                  className="w-full text-left p-3 bg-white border rounded-lg hover:border-indigo-400 transition-all group disabled:opacity-50"
                >
                  <p className="text-xs font-bold text-slate-800 mb-1 flex items-center gap-2">
                    <Feather size={14} className="text-indigo-600" /> 娑﹁壊鏂囨湰
                  </p>
                  <p className="text-[10px] text-slate-500">浼樺寲璇嶆眹骞舵彁鍗囨枃绗旇川閲忋€?/p>
                </button>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">瑙掕壊淇℃伅</h4>
              <div className="space-y-2">
                {novel.characters.length === 0 ? (
                  <p className="text-[10px] text-slate-400 italic">灏氭湭娣诲姞瑙掕壊銆?/p>
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

      {/* 鐢熸垚鎺у埗鍙?*/}
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
