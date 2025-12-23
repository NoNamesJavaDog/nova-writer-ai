
import React, { useState } from 'react';
import { Novel, Foreshadowing, Volume } from '../types';
import { Plus, Trash2, CheckCircle2, Circle, BookOpen, Link as LinkIcon } from 'lucide-react';
import { foreshadowingApi } from '../services/apiService';

interface ForeshadowingViewProps {
  novel: Novel;
  updateNovel: (updates: Partial<Novel>) => void;
}

const ForeshadowingView: React.FC<ForeshadowingViewProps> = ({ novel, updateNovel }) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingForeshadowing, setEditingForeshadowing] = useState<Partial<Foreshadowing>>({});
  
  // 确保 novel 和必要的属性存在
  if (!novel) {
    return (
      <div className="max-w-5xl mx-auto py-8 px-6">
        <div className="text-center py-20">
          <p className="text-slate-400">加载中...</p>
        </div>
      </div>
    );
  }

  // 获取章节标题
  const getChapterTitle = (chapterId?: string): string => {
    if (!chapterId) return '大纲阶段';
    const volumes = novel.volumes || [];
    for (const volume of volumes) {
      const chapters = volume.chapters || [];
      const chapter = chapters.find(c => c.id === chapterId);
      if (chapter) {
        const volumeIndex = volumes.indexOf(volume) + 1;
        const chapterIndex = chapters.findIndex(c => c.id === chapterId) + 1;
        return `第${volumeIndex}卷 第${chapterIndex}章：${chapter.title}`;
      }
    }
    return '未知章节';
  };

  // 获取所有章节选项
  const getAllChapters = (): Array<{ id: string; title: string; volumeTitle: string; volumeIndex: number; chapterIndex: number }> => {
    const chapters: Array<{ id: string; title: string; volumeTitle: string; volumeIndex: number; chapterIndex: number }> = [];
    const volumes = novel.volumes || [];
    volumes.forEach((volume, volumeIndex) => {
      const volumeChapters = volume.chapters || [];
      volumeChapters.forEach((chapter, chapterIndex) => {
        chapters.push({
          id: chapter.id,
          title: chapter.title,
          volumeTitle: volume.title,
          volumeIndex: volumeIndex + 1,
          chapterIndex: chapterIndex + 1
        });
      });
    });
    return chapters;
  };

  const addForeshadowing = () => {
    const newForeshadowing: Foreshadowing = {
      id: Date.now().toString(),
      content: '新伏笔',
      isResolved: 'false'
    };
    const currentForeshadowings = novel.foreshadowings || [];
    updateNovel({ foreshadowings: [...currentForeshadowings, newForeshadowing] });
    setEditingId(newForeshadowing.id);
    setEditingForeshadowing(newForeshadowing);
  };

  const updateForeshadowing = async (id: string, updates: Partial<Foreshadowing>) => {
    try {
      await foreshadowingApi.update(novel.id, id, updates);
      const currentForeshadowings = novel.foreshadowings || [];
      updateNovel({
        foreshadowings: currentForeshadowings.map(f => f.id === id ? { ...f, ...updates } : f)
      });
      setEditingId(null);
    } catch (error: any) {
      console.error('更新伏笔失败:', error);
      alert(`更新失败: ${error.message || '未知错误'}`);
    }
  };

  const deleteForeshadowing = async (id: string) => {
    if (!confirm('确定要删除这个伏笔吗？')) return;
    try {
      await foreshadowingApi.delete(novel.id, id);
      const currentForeshadowings = novel.foreshadowings || [];
      updateNovel({
        foreshadowings: currentForeshadowings.filter(f => f.id !== id)
      });
    } catch (error: any) {
      console.error('删除伏笔失败:', error);
      alert(`删除失败: ${error.message || '未知错误'}`);
    }
  };

  const toggleResolved = async (foreshadowing: Foreshadowing) => {
    const newIsResolved = foreshadowing.isResolved === 'true' ? 'false' : 'true';
    await updateForeshadowing(foreshadowing.id, { isResolved: newIsResolved });
  };

  const chapters = getAllChapters();
  
  // 确保 foreshadowings 数组存在
  const foreshadowings = novel.foreshadowings || [];

  return (
    <div className="max-w-5xl mx-auto py-4 md:py-8 px-4 md:px-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 md:mb-8">
        <div>
          <h2 className="text-xl md:text-2xl font-bold text-slate-800">伏笔管理</h2>
          <p className="text-xs md:text-sm text-slate-500">追踪故事的伏笔线索及其闭环状态。</p>
        </div>
        <button 
          onClick={addForeshadowing}
          className="flex items-center justify-center gap-2 bg-indigo-600 text-white px-4 py-2.5 md:py-2 rounded-lg font-semibold hover:bg-indigo-700 active:bg-indigo-800 transition-colors min-h-[44px] md:min-h-0"
        >
          <Plus size={18} /> <span>添加伏笔</span>
        </button>
      </div>

      <div className="space-y-4">
        {foreshadowings.map((foreshadowing) => {
          const isResolved = foreshadowing.isResolved === 'true';
          const sourceChapterTitle = getChapterTitle(foreshadowing.chapterId);
          const resolvedChapterTitle = foreshadowing.resolvedChapterId ? getChapterTitle(foreshadowing.resolvedChapterId) : null;

          return (
            <div 
              key={foreshadowing.id} 
              className={`bg-white border rounded-xl overflow-hidden transition-all ${
                isResolved ? 'border-green-200 bg-green-50/30' : 'hover:shadow-md'
              }`}
            >
              {editingId === foreshadowing.id ? (
                <div className="p-4 md:p-6 space-y-4">
                  <textarea 
                    className="w-full p-3 bg-slate-50 border rounded-lg text-base md:text-sm focus:outline-none min-h-[100px]"
                    placeholder="描述伏笔内容..."
                    value={editingForeshadowing.content || ''}
                    onChange={(e) => setEditingForeshadowing({ ...editingForeshadowing, content: e.target.value })}
                  />
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">产生章节</label>
                      <select
                        className="w-full p-2.5 md:p-2 border rounded-lg text-sm min-h-[44px] md:min-h-0"
                        value={editingForeshadowing.chapterId || ''}
                        onChange={(e) => setEditingForeshadowing({ ...editingForeshadowing, chapterId: e.target.value || undefined })}
                      >
                        <option value="">大纲阶段</option>
                        {chapters.map(ch => (
                          <option key={ch.id} value={ch.id}>
                            第{ch.volumeIndex}卷 第{ch.chapterIndex}章：{ch.title}
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">闭环章节</label>
                      <select
                        className="w-full p-2.5 md:p-2 border rounded-lg text-sm min-h-[44px] md:min-h-0"
                        value={editingForeshadowing.resolvedChapterId || ''}
                        onChange={(e) => setEditingForeshadowing({ ...editingForeshadowing, resolvedChapterId: e.target.value || undefined })}
                      >
                        <option value="">未闭环</option>
                        {chapters.map(ch => (
                          <option key={ch.id} value={ch.id}>
                            第{ch.volumeIndex}卷 第{ch.chapterIndex}章：{ch.title}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="flex flex-col sm:flex-row justify-end gap-2">
                    <button 
                      onClick={() => {
                        setEditingId(null);
                        setEditingForeshadowing({});
                      }}
                      className="px-4 py-2.5 md:py-2 text-slate-600 hover:bg-slate-100 active:bg-slate-200 rounded-lg text-sm font-medium transition-colors min-h-[44px] md:min-h-0"
                    >
                      取消
                    </button>
                    <button 
                      onClick={() => updateForeshadowing(foreshadowing.id, editingForeshadowing)}
                      className="px-6 py-2.5 md:py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-700 active:bg-indigo-800 transition-colors min-h-[44px] md:min-h-0"
                    >
                      保存
                    </button>
                  </div>
                </div>
              ) : (
                <div className="p-4 md:p-6">
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <button
                          onClick={() => toggleResolved(foreshadowing)}
                          className="flex items-center gap-2 text-sm font-medium hover:text-indigo-600 transition-colors"
                        >
                          {isResolved ? (
                            <CheckCircle2 size={18} className="text-green-600" />
                          ) : (
                            <Circle size={18} className="text-slate-400" />
                          )}
                          <span className={isResolved ? 'text-green-600' : 'text-slate-600'}>
                            {isResolved ? '已闭环' : '未闭环'}
                          </span>
                        </button>
                      </div>
                      <p className="text-sm md:text-base text-slate-800 leading-relaxed mb-3">
                        {foreshadowing.content}
                      </p>
                      <div className="flex flex-wrap gap-4 text-xs text-slate-500">
                        <div className="flex items-center gap-1">
                          <BookOpen size={14} />
                          <span>产生于：{sourceChapterTitle}</span>
                        </div>
                        {resolvedChapterTitle && (
                          <div className="flex items-center gap-1">
                            <LinkIcon size={14} />
                            <span>闭环于：{resolvedChapterTitle}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          setEditingId(foreshadowing.id);
                          setEditingForeshadowing(foreshadowing);
                        }}
                        className="px-3 py-2 text-slate-600 hover:bg-slate-100 active:bg-slate-200 rounded-lg text-xs transition-colors"
                      >
                        编辑
                      </button>
                      <button
                        onClick={() => deleteForeshadowing(foreshadowing.id)}
                        className="px-3 py-2 text-red-600 hover:bg-red-50 active:bg-red-100 rounded-lg text-xs transition-colors"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {foreshadowings.length === 0 && (
        <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-slate-300">
          <Circle className="text-slate-200 mx-auto mb-4" size={48} />
          <p className="text-slate-400 font-medium italic">还没有伏笔记录。</p>
          <p className="text-xs text-slate-400 mt-2">伏笔会在大纲生成和章节生成时自动提取。</p>
        </div>
      )}
    </div>
  );
};

export default ForeshadowingView;


