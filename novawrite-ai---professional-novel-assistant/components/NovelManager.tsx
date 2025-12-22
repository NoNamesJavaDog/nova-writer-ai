import React, { useState } from 'react';
import { Novel } from '../types';
import { BookOpen, Plus, Trash2, Edit2, Check, X } from 'lucide-react';

interface NovelManagerProps {
  novels: Novel[];
  currentNovelId: string;
  onSelectNovel: (novelId: string) => void;
  onCreateNovel: () => void;
  onUpdateNovel: (novelId: string, updates: Partial<Novel>) => void;
  onDeleteNovel: (novelId: string) => void;
  onClose: () => void;
}

const NovelManager: React.FC<NovelManagerProps> = ({
  novels,
  currentNovelId,
  onSelectNovel,
  onCreateNovel,
  onUpdateNovel,
  onDeleteNovel,
  onClose
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const handleStartEdit = (novel: Novel) => {
    setEditingId(novel.id);
    setEditTitle(novel.title);
  };

  const handleSaveEdit = (novelId: string) => {
    if (editTitle.trim()) {
      onUpdateNovel(novelId, { title: editTitle.trim() });
    }
    setEditingId(null);
    setEditTitle('');
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditTitle('');
  };

  const handleDelete = (novelId: string) => {
    if (window.confirm('确定要删除这本小说吗？此操作无法撤销。')) {
      onDeleteNovel(novelId);
      if (editingId === novelId) {
        setEditingId(null);
      }
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div 
        className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="p-6 border-b flex items-center justify-between">
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <BookOpen size={24} className="text-indigo-600" />
            作品管理
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X size={20} className="text-slate-500" />
          </button>
        </div>

        {/* 作品列表 */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-3">
            {novels.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                <BookOpen size={48} className="mx-auto mb-4 opacity-50" />
                <p>还没有作品，点击下方按钮创建第一本小说</p>
              </div>
            ) : (
              novels.map((novel) => (
                <div
                  key={novel.id}
                  className={`p-4 border rounded-lg transition-all ${
                    novel.id === currentNovelId
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-slate-200 hover:border-slate-300 bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      {editingId === novel.id ? (
                        <div className="flex items-center gap-2">
                          <input
                            type="text"
                            value={editTitle}
                            onChange={(e) => setEditTitle(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleSaveEdit(novel.id);
                              if (e.key === 'Escape') handleCancelEdit();
                            }}
                            className="flex-1 px-2 py-1 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            autoFocus
                          />
                          <button
                            onClick={() => handleSaveEdit(novel.id)}
                            className="p-1 text-green-600 hover:bg-green-50 rounded"
                          >
                            <Check size={16} />
                          </button>
                          <button
                            onClick={handleCancelEdit}
                            className="p-1 text-red-600 hover:bg-red-50 rounded"
                          >
                            <X size={16} />
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-3">
                          <div className="flex-1 min-w-0">
                            <h3 className="font-semibold text-slate-800 truncate">
                              {novel.title || '未命名小说'}
                            </h3>
                            <div className="flex items-center gap-4 mt-1 text-xs text-slate-500">
                              <span>类型: {novel.genre || '未设置'}</span>
                              <span>卷数: {novel.volumes?.length || 0}</span>
                              <span>章节: {novel.volumes?.reduce((sum, v) => sum + (v.chapters?.length || 0), 0) || 0}</span>
                            </div>
                          </div>
                          {novel.id === currentNovelId && (
                            <span className="px-2 py-1 bg-indigo-600 text-white text-xs font-semibold rounded">
                              当前作品
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                    {editingId !== novel.id && (
                      <div className="flex items-center gap-2 ml-4">
                        <button
                          onClick={() => handleStartEdit(novel)}
                          className="p-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                          title="编辑标题"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          onClick={() => handleDelete(novel.id)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="删除作品"
                          disabled={novels.length === 1}
                        >
                          <Trash2 size={16} />
                        </button>
                        {novel.id !== currentNovelId && (
                          <button
                            onClick={() => onSelectNovel(novel.id)}
                            className="px-3 py-1.5 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 transition-colors"
                          >
                            切换
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 底部操作 */}
        <div className="p-6 border-t bg-slate-50">
          <button
            onClick={onCreateNovel}
            className="w-full px-4 py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2"
          >
            <Plus size={20} />
            创建新作品
          </button>
        </div>
      </div>
    </div>
  );
};

export default NovelManager;

