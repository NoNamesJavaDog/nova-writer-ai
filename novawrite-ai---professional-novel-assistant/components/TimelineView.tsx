
import React, { useState } from 'react';
import { Novel, TimelineEvent } from '../types';
import { Plus, Trash2, History, Clock } from 'lucide-react';

interface TimelineViewProps {
  novel: Novel;
  updateNovel: (updates: Partial<Novel>) => void;
}

const TimelineView: React.FC<TimelineViewProps> = ({ novel, updateNovel }) => {
  // 确保timeline有默认值
  const timeline = novel.timeline || [];
  
  const addEvent = () => {
    const newEvent: TimelineEvent = {
      id: Date.now().toString(),
      time: '新日期/时代',
      event: '描述事件...',
      impact: '因此发生了什么变化？'
    };
    updateNovel({ timeline: [...timeline, newEvent] });
  };

  const updateEvent = (id: string, updates: Partial<TimelineEvent>) => {
    updateNovel({
      timeline: timeline.map(e => e.id === id ? { ...e, ...updates } : e)
    });
  };

  const deleteEvent = (id: string) => {
    updateNovel({
      timeline: timeline.filter(e => e.id !== id)
    });
  };

  return (
    <div className="max-w-3xl mx-auto py-4 md:py-8 px-4 md:px-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 md:mb-8">
        <div>
          <h2 className="text-xl md:text-2xl font-bold text-slate-800">故事时间线</h2>
          <p className="text-xs md:text-sm text-slate-500">追踪重大事件和历史里程碑。</p>
        </div>
        <button 
          onClick={addEvent}
          className="flex items-center justify-center gap-2 bg-indigo-600 text-white px-4 py-2.5 md:py-2 rounded-lg font-semibold hover:bg-indigo-700 active:bg-indigo-800 transition-colors min-h-[44px] md:min-h-0"
        >
          <Plus size={18} /> <span>添加事件</span>
        </button>
      </div>

      <div className="relative">
        <div className="absolute left-5 md:left-6 top-4 bottom-4 w-px bg-slate-200"></div>
        
        <div className="space-y-8">
          {timeline.length === 0 ? (
            <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-slate-300 ml-12">
              <History className="text-slate-200 mx-auto mb-4" size={48} />
              <p className="text-slate-400 font-medium italic">尚未记录时间线事件。</p>
            </div>
          ) : (
            timeline.map((item, idx) => (
              <div key={item.id} className="relative pl-10 md:pl-14 group">
                {/* Marker */}
                <div className="absolute left-[14px] md:left-[18px] top-1 w-2.5 h-2.5 bg-indigo-600 rounded-full ring-4 ring-indigo-100 z-10"></div>
                
                <div className="bg-white border rounded-xl p-4 md:p-6 shadow-sm group-hover:border-indigo-200 transition-colors">
                  <div className="flex items-center justify-between gap-3 md:gap-4 mb-4">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <Clock size={16} className="text-slate-400 shrink-0" />
                      <input 
                        className="bg-slate-50 px-2 py-1.5 md:py-1 rounded text-sm font-bold text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-200 min-h-[36px] md:min-h-0 flex-1"
                        value={item.time}
                        onChange={(e) => updateEvent(item.id, { time: e.target.value })}
                        placeholder="1024年..."
                      />
                    </div>
                    <button 
                      onClick={() => deleteEvent(item.id)}
                      className="opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity p-2 md:p-1.5 text-red-400 hover:text-red-600 active:text-red-700 min-h-[36px] md:min-h-0 flex items-center justify-center"
                      aria-label="删除事件"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                  <div className="space-y-3">
                    <input 
                      className="w-full text-base md:text-lg font-bold text-slate-800 focus:outline-none border-b border-transparent focus:border-slate-100 pb-1 min-h-[44px] md:min-h-0"
                      value={item.event}
                      onChange={(e) => updateEvent(item.id, { event: e.target.value })}
                      placeholder="事件标题"
                    />
                    <textarea 
                      className="w-full text-base md:text-sm text-slate-600 focus:outline-none min-h-[80px] md:min-h-[60px] resize-none"
                      value={item.impact}
                      onChange={(e) => updateEvent(item.id, { impact: e.target.value })}
                      placeholder="这对世界或角色产生了什么影响？"
                    />
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default TimelineView;
