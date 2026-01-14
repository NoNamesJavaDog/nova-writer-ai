
import React, { useEffect } from 'react';
import { AppView } from '../types';
import { 
  LayoutDashboard, 
  BookText, 
  PenTool, 
  Users, 
  Globe, 
  History,
  Settings,
  X,
  Lightbulb,
  Share2,
  Bot
} from 'lucide-react';

interface SidebarProps {
  activeView: AppView;
  setActiveView: (view: AppView) => void;
  novelTitle: string;
  isMobileOpen?: boolean;
  onMobileClose?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  activeView, 
  setActiveView, 
  novelTitle,
  isMobileOpen = false,
  onMobileClose
}) => {
  const navItems = [
    { id: 'dashboard' as AppView, label: '仪表板', icon: LayoutDashboard },
    { id: 'outline' as AppView, label: '大纲', icon: BookText },
    { id: 'agents' as AppView, label: '智能小说写作Agent', icon: Bot },
    { id: 'writing' as AppView, label: '写作', icon: PenTool },
    { id: 'characters' as AppView, label: '角色', icon: Users },
    { id: 'world' as AppView, label: '世界观', icon: Globe },
    { id: 'timeline' as AppView, label: '时间线', icon: History },
    { id: 'foreshadowings' as AppView, label: '伏笔', icon: Lightbulb },
    { id: 'graph' as AppView, label: 'Graph', icon: Share2 },
  ];

  // 移动端点击导航项后关闭抽屉
  const handleNavClick = (view: AppView) => {
    setActiveView(view);
    if (onMobileClose) {
      onMobileClose();
    }
  };

  // 移动端阻止背景滚动
  useEffect(() => {
    if (isMobileOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isMobileOpen]);

  return (
    <>
      {/* 移动端遮罩层 - 只有在移动端打开时才显示 */}
      {isMobileOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-[45] transition-opacity"
          onClick={(e) => {
            e.preventDefault();
            onMobileClose?.();
          }}
          onTouchEnd={(e) => {
            e.preventDefault();
            onMobileClose?.();
          }}
          aria-hidden="true"
        />
      )}
      
      {/* 侧边栏 */}
      <aside className={`
        fixed lg:static
        top-0 left-0 bottom-0
        w-64 bg-slate-900 text-slate-400 flex flex-col shrink-0
        transform transition-transform duration-300 ease-in-out
        ${isMobileOpen ? 'translate-x-0 z-50' : '-translate-x-full lg:translate-x-0 z-50'}
      `}>
        {/* 移动端关闭按钮 */}
        <div className="lg:hidden flex items-center justify-between p-4 border-b border-slate-800 sticky top-0 bg-slate-900 z-10">
          <div className="flex items-center gap-2 text-white">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center font-bold text-xl">N</div>
            <h1 className="text-lg font-bold tracking-tight">NovaWrite</h1>
          </div>
          <button
            onClick={onMobileClose}
            onTouchEnd={(e) => {
              e.preventDefault();
              onMobileClose?.();
            }}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 active:bg-slate-700 rounded-lg transition-colors touch-manipulation"
            aria-label="关闭菜单"
          >
            <X size={20} />
          </button>
        </div>

        {/* 桌面端标题 */}
        <div className="hidden lg:block p-6 border-b border-slate-800">
          <div className="flex items-center gap-2 text-white mb-1">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center font-bold text-xl">N</div>
            <h1 className="text-lg font-bold tracking-tight">NovaWrite</h1>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleNavClick(item.id)}
              onTouchEnd={(e) => {
                // 移动端触摸后立即关闭
                handleNavClick(item.id);
              }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors touch-manipulation ${
                activeView === item.id 
                  ? 'bg-slate-800 text-white shadow-sm' 
                  : 'hover:bg-slate-800 hover:text-slate-200 active:bg-slate-800'
              }`}
            >
              <item.icon size={18} />
              {item.label}
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium hover:bg-slate-800 hover:text-slate-200 active:bg-slate-800 transition-colors">
            <Settings size={18} />
            设置
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
