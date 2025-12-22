
import React from 'react';
import { AppView } from '../types';
import { 
  LayoutDashboard, 
  BookText, 
  PenTool, 
  Users, 
  Globe, 
  History,
  Lightbulb
} from 'lucide-react';

interface MobileNavProps {
  activeView: AppView;
  setActiveView: (view: AppView) => void;
}

const MobileNav: React.FC<MobileNavProps> = ({ activeView, setActiveView }) => {
  const navItems = [
    { id: 'dashboard' as AppView, label: '仪表板', icon: LayoutDashboard },
    { id: 'outline' as AppView, label: '大纲', icon: BookText },
    { id: 'writing' as AppView, label: '写作', icon: PenTool },
    { id: 'characters' as AppView, label: '角色', icon: Users },
    { id: 'world' as AppView, label: '世界观', icon: Globe },
    { id: 'timeline' as AppView, label: '时间线', icon: History },
    { id: 'foreshadowings' as AppView, label: '伏笔', icon: Lightbulb },
  ];

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-40 safe-area-inset-bottom">
      <div className="flex justify-around items-center h-16">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              className={`
                flex flex-col items-center justify-center 
                min-w-[60px] h-full
                transition-colors duration-200
                ${isActive 
                  ? 'text-indigo-600' 
                  : 'text-slate-500 active:text-indigo-600'
                }
              `}
              aria-label={item.label}
            >
              <Icon 
                size={22} 
                strokeWidth={isActive ? 2.5 : 2}
                className="mb-1"
              />
              <span className={`text-xs font-medium ${isActive ? 'text-indigo-600' : 'text-slate-600'}`}>
                {item.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};

export default MobileNav;

