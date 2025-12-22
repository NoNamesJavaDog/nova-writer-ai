
import React, { useState } from 'react';
import { Novel, WorldSetting } from '../types';
import { Plus, Trash2, Globe, Save } from 'lucide-react';

interface WorldViewProps {
  novel: Novel;
  updateNovel: (updates: Partial<Novel>) => void;
}

const WorldView: React.FC<WorldViewProps> = ({ novel, updateNovel }) => {
  const [editingId, setEditingId] = useState<string | null>(null);

  const addSetting = () => {
    const newSetting: WorldSetting = {
      id: Date.now().toString(),
      title: '新世界观设定',
      category: '地理',
      description: ''
    };
    updateNovel({ worldSettings: [...novel.worldSettings, newSetting] });
    setEditingId(newSetting.id);
  };

  const updateSetting = (id: string, updates: Partial<WorldSetting>) => {
    updateNovel({
      worldSettings: novel.worldSettings.map(s => s.id === id ? { ...s, ...updates } : s)
    });
  };

  const deleteSetting = (id: string) => {
    updateNovel({
      worldSettings: novel.worldSettings.filter(s => s.id !== id)
    });
  };

  return (
    <div className="max-w-4xl mx-auto py-4 md:py-8 px-4 md:px-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 md:mb-8">
        <div>
          <h2 className="text-xl md:text-2xl font-bold text-slate-800">世界观构建</h2>
          <p className="text-xs md:text-sm text-slate-500">定义您设定中的规则、地点和传说。</p>
        </div>
        <button 
          onClick={addSetting}
          className="flex items-center justify-center gap-2 bg-indigo-600 text-white px-4 py-2.5 md:py-2 rounded-lg font-semibold hover:bg-indigo-700 active:bg-indigo-800 transition-colors min-h-[44px] md:min-h-0"
        >
          <Plus size={18} /> <span>添加条目</span>
        </button>
      </div>

      <div className="space-y-4">
        {novel.worldSettings.map((setting) => (
          <div key={setting.id} className="bg-white border rounded-xl overflow-hidden">
            {editingId === setting.id ? (
              <div className="p-4 md:p-6 space-y-4">
                <div className="flex flex-col sm:flex-row gap-3 md:gap-4">
                  <input 
                    className="flex-1 text-base md:text-lg font-bold border-b focus:outline-none min-h-[44px] md:min-h-0 px-1"
                    value={setting.title}
                    onChange={(e) => updateSetting(setting.id, { title: e.target.value })}
                  />
                  <select 
                    className="p-2.5 md:p-2 border rounded-lg text-sm md:text-xs min-h-[44px] md:min-h-0"
                    value={setting.category}
                    onChange={(e) => updateSetting(setting.id, { category: e.target.value as WorldSetting['category'] })}
                  >
                    <option>地理</option>
                    <option>社会</option>
                    <option>魔法/科技</option>
                    <option>历史</option>
                    <option>其他</option>
                  </select>
                </div>
                <textarea 
                  className="w-full p-3 bg-slate-50 border rounded-lg text-base md:text-sm focus:outline-none min-h-[150px]"
                  placeholder="描述您世界的这个方面..."
                  value={setting.description}
                  onChange={(e) => updateSetting(setting.id, { description: e.target.value })}
                />
                <div className="flex flex-col sm:flex-row justify-end gap-2">
                  <button onClick={() => deleteSetting(setting.id)} className="px-4 py-2.5 md:py-2 text-red-600 hover:bg-red-50 active:bg-red-100 rounded-lg text-sm font-bold transition-colors min-h-[44px] md:min-h-0">删除</button>
                  <button onClick={() => setEditingId(null)} className="px-6 py-2.5 md:py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-700 active:bg-indigo-800 transition-colors min-h-[44px] md:min-h-0">保存条目</button>
                </div>
              </div>
            ) : (
              <div 
                className="p-4 md:p-6 cursor-pointer hover:bg-slate-50 active:bg-slate-100 transition-colors flex gap-4 md:gap-6"
                onClick={() => setEditingId(setting.id)}
              >
                <div className="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center shrink-0">
                  <Globe className="text-indigo-600" size={24} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="font-bold text-slate-800">{setting.title}</h3>
                    <span className="px-2 py-0.5 bg-slate-100 text-slate-500 text-[10px] rounded font-bold uppercase tracking-wider">{setting.category}</span>
                  </div>
                  <p className="text-sm text-slate-500 line-clamp-2">{setting.description || "尚未提供描述。"}</p>
                </div>
              </div>
            )}
          </div>
        ))}

        {novel.worldSettings.length === 0 && (
          <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-slate-300">
            <Globe className="text-slate-200 mx-auto mb-4" size={48} />
            <p className="text-slate-400 font-medium italic">您的世界目前还是一张白纸。</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorldView;
