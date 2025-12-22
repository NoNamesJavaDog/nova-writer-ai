
import React, { useState } from 'react';
import { Novel, Character } from '../types';
import { Plus, Trash2, UserPlus, Save } from 'lucide-react';

interface CharacterViewProps {
  novel: Novel;
  updateNovel: (updates: Partial<Novel>) => void;
}

const CharacterView: React.FC<CharacterViewProps> = ({ novel, updateNovel }) => {
  const [editingId, setEditingId] = useState<string | null>(null);

  const addCharacter = () => {
    const newChar: Character = {
      id: Date.now().toString(),
      name: '新角色',
      age: '',
      role: '主角',
      personality: '',
      background: '',
      goals: ''
    };
    updateNovel({ characters: [...novel.characters, newChar] });
    setEditingId(newChar.id);
  };

  const updateCharacter = (id: string, updates: Partial<Character>) => {
    updateNovel({
      characters: novel.characters.map(c => c.id === id ? { ...c, ...updates } : c)
    });
  };

  const deleteCharacter = (id: string) => {
    updateNovel({
      characters: novel.characters.filter(c => c.id !== id)
    });
  };

  return (
    <div className="max-w-6xl mx-auto py-4 md:py-8 px-4 md:px-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 md:mb-8">
        <div>
          <h2 className="text-xl md:text-2xl font-bold text-slate-800">角色库</h2>
          <p className="text-xs md:text-sm text-slate-500">管理您的角色阵容、动机和档案。</p>
        </div>
        <button 
          onClick={addCharacter}
          className="flex items-center justify-center gap-2 bg-indigo-600 text-white px-4 py-2.5 md:py-2 rounded-lg font-semibold hover:bg-indigo-700 active:bg-indigo-800 transition-colors min-h-[44px] md:min-h-0"
        >
          <UserPlus size={18} /> <span>新角色</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
        {novel.characters.map((char) => (
          <div 
            key={char.id} 
            className={`bg-white rounded-xl border transition-all ${
              editingId === char.id ? 'ring-2 ring-indigo-500 shadow-lg' : 'hover:shadow-md'
            }`}
          >
            {editingId === char.id ? (
              <div className="p-5 space-y-4">
                <input 
                  autoFocus
                  className="w-full text-lg font-bold border-b pb-1 focus:outline-none"
                  value={char.name}
                  onChange={(e) => updateCharacter(char.id, { name: e.target.value })}
                />
                <div className="grid grid-cols-2 gap-2">
                  <input 
                    placeholder="年龄" 
                    className="p-2 bg-slate-50 rounded border text-xs"
                    value={char.age}
                    onChange={(e) => updateCharacter(char.id, { age: e.target.value })}
                  />
                  <input 
                    placeholder="角色" 
                    className="p-2 bg-slate-50 rounded border text-xs"
                    value={char.role}
                    onChange={(e) => updateCharacter(char.id, { role: e.target.value })}
                  />
                </div>
                <textarea 
                  placeholder="性格与特征" 
                  rows={2}
                  className="w-full p-2 bg-slate-50 rounded border text-xs"
                  value={char.personality}
                  onChange={(e) => updateCharacter(char.id, { personality: e.target.value })}
                />
                <textarea 
                  placeholder="目标与动机" 
                  rows={2}
                  className="w-full p-2 bg-slate-50 rounded border text-xs"
                  value={char.goals}
                  onChange={(e) => updateCharacter(char.id, { goals: e.target.value })}
                />
                <div className="flex gap-2">
                  <button 
                    onClick={() => setEditingId(null)}
                    className="flex-1 py-2.5 md:py-2 bg-indigo-600 text-white rounded-lg text-xs font-bold flex items-center justify-center gap-2 min-h-[44px] md:min-h-0 active:bg-indigo-700"
                  >
                    <Save size={14} /> 完成
                  </button>
                  <button 
                    onClick={() => deleteCharacter(char.id)}
                    className="px-4 md:px-3 py-2.5 md:py-2 bg-red-50 text-red-600 rounded-lg text-xs hover:bg-red-100 active:bg-red-200 min-h-[44px] md:min-h-0 flex items-center justify-center"
                    aria-label="删除角色"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ) : (
              <div 
                onClick={() => setEditingId(char.id)}
                className="p-5 cursor-pointer"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center text-xl font-bold text-slate-400">
                    {char.name.charAt(0)}
                  </div>
                  <span className="px-2 py-1 bg-indigo-50 text-indigo-700 text-[10px] font-bold rounded uppercase">
                    {char.role}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-slate-800 mb-1">{char.name}</h3>
                <p className="text-xs text-slate-500 mb-4">{char.personality || "尚未描述性格。"}</p>
                <div className="flex items-center gap-2 text-[10px] font-medium text-slate-400">
                  <span className="flex items-center gap-1"><span className="w-1 h-1 bg-slate-300 rounded-full"></span> 年龄: {char.age || '未知'}</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {novel.characters.length === 0 && (
        <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-slate-300">
          <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <UserPlus className="text-slate-300" size={32} />
          </div>
          <p className="text-slate-500 font-medium">开始添加您的主角或反派角色。</p>
        </div>
      )}
    </div>
  );
};

export default CharacterView;
