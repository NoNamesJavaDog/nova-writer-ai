
import React, { useState, useEffect, useRef } from 'react';
// 先导入类型，避免循环依赖
import type { Novel, AppView, Character, WorldSetting, TimelineEvent, Volume, Chapter, User } from './types';
// 先导入服务，避免在组件初始化时执行
import { getCurrentUser, logout, refreshCurrentUser } from './services/authService';
import { novelApi, currentNovelApi, setOnTokenExpired } from './services/apiService';
// 然后导入组件
import Sidebar from './components/Sidebar';
import MobileNav from './components/MobileNav';
import Dashboard from './components/Dashboard';
import OutlineView from './components/OutlineView';
import EditorView from './components/EditorView';
import CharacterView from './components/CharacterView';
import WorldView from './components/WorldView';
import TimelineView from './components/TimelineView';
import ForeshadowingView from './components/ForeshadowingView';
import NovelManager from './components/NovelManager';
import Login from './components/Login';
import UserSettings from './components/UserSettings';
import { BookText, PenTool, Users, Globe, History, LayoutDashboard, BookOpen, ChevronDown, User as UserIcon, LogOut, Settings, Menu } from 'lucide-react';

const INITIAL_NOVEL: Novel = {
  id: '1',
  title: '',
  genre: '奇幻',
  synopsis: '',
  fullOutline: '',
  volumes: [{ id: 'v1', title: '第一卷', chapters: [] }],
  characters: [],
  worldSettings: [],
  timeline: [],
  foreshadowings: []
};

const App: React.FC = () => {
  // 认证状态
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [showUserSettings, setShowUserSettings] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [loading, setLoading] = useState(false);

  // 作品列表和当前作品ID
  const [novels, setNovels] = useState<Novel[]>([]);
  const [currentNovelId, setCurrentNovelId] = useState<string>('');

  // 从localStorage恢复视图状态（使用函数来获取，确保每次都能读取最新值）
  const getStoredView = (): AppView => {
    const saved = localStorage.getItem('nova_write_active_view');
    return (saved as AppView) || 'dashboard';
  };
  const [activeView, setActiveView] = useState<AppView>(getStoredView);
  
  const getStoredVolumeIdx = (): number => {
    const saved = localStorage.getItem('nova_write_active_volume_idx');
    return saved ? parseInt(saved, 10) : 0;
  };
  const [activeVolumeIdx, setActiveVolumeIdx] = useState(getStoredVolumeIdx);
  
  const getStoredChapterIdx = (): number | null => {
    const saved = localStorage.getItem('nova_write_active_chapter_idx');
    return saved ? parseInt(saved, 10) : null;
  };
  const [activeChapterIdx, setActiveChapterIdx] = useState<number | null>(getStoredChapterIdx);
  const [showNovelManager, setShowNovelManager] = useState(false);
  
  // 移动端侧边栏状态
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // 获取当前作品
  const currentNovel = novels.find(n => n.id === currentNovelId) || novels[0] || INITIAL_NOVEL;

  // 使用 ref 跟踪组件是否已挂载
  const isMountedRef = useRef(true);

  // 设置 token 过期回调
  useEffect(() => {
    setOnTokenExpired(() => {
      // Token 过期时，清除用户状态并跳转到登录页
      logout();
      setCurrentUser(null);
      setNovels([]);
      setCurrentNovelId('');
      // 清除用户缓存
      localStorage.removeItem('nova_write_current_user');
    });
  }, []);


  // 从API加载小说列表
  const loadNovels = async () => {
    if (!currentUser || !isMountedRef.current) return;
    
    setLoading(true);
    try {
      const loadedNovels = await novelApi.getAll();
      
      // 检查组件是否仍然挂载
      if (!isMountedRef.current) return;
      
      if (loadedNovels.length > 0) {
        setNovels(loadedNovels);
        
        // 获取当前选择的小说ID
        const currentNovelIdFromApi = await currentNovelApi.get();
        
        // 再次检查组件是否仍然挂载
        if (!isMountedRef.current) return;
        
        if (currentNovelIdFromApi && loadedNovels.find(n => n.id === currentNovelIdFromApi)) {
          setCurrentNovelId(currentNovelIdFromApi);
        } else {
          setCurrentNovelId(loadedNovels[0].id);
          // 保存当前小说ID到后端
          await currentNovelApi.set(loadedNovels[0].id);
        }
      } else {
        // 如果没有小说，创建一个默认的
        const newNovel = await novelApi.create({
          title: '新作品',
          genre: '奇幻',
          synopsis: '',
          fullOutline: '',
        });
        
        // 再次检查组件是否仍然挂载
        if (!isMountedRef.current) return;
        
        setNovels([newNovel]);
        setCurrentNovelId(newNovel.id);
        await currentNovelApi.set(newNovel.id);
      }
    } catch (error: any) {
      // 只有在组件仍然挂载时才显示错误
      if (isMountedRef.current) {
        console.error('加载小说列表失败:', error);
        alert(`加载失败: ${error.message || '未知错误'}`);
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  };

  // 组件挂载时，从localStorage恢复视图状态（只执行一次）
  // 注意：由于useState初始化时已经读取了localStorage，这里主要是为了确保状态同步
  useEffect(() => {
    // 强制从localStorage读取并应用（覆盖可能的默认值）
    const savedView = localStorage.getItem('nova_write_active_view') as AppView;
    console.log('🔍 恢复视图状态 - localStorage中的值:', savedView, '当前activeView:', activeView);
    if (savedView && savedView !== activeView) {
      console.log('✅ 设置activeView为:', savedView);
      setActiveView(savedView);
    } else if (!savedView) {
      console.log('⚠️ localStorage中没有保存的视图，使用默认值dashboard');
    } else {
      console.log('ℹ️ activeView已经是正确的值:', activeView);
    }
    const savedVolumeIdx = localStorage.getItem('nova_write_active_volume_idx');
    if (savedVolumeIdx) {
      const volumeIdx = parseInt(savedVolumeIdx, 10);
      if (!isNaN(volumeIdx)) {
        setActiveVolumeIdx(volumeIdx);
      }
    }
    const savedChapterIdx = localStorage.getItem('nova_write_active_chapter_idx');
    if (savedChapterIdx) {
      const chapterIdx = parseInt(savedChapterIdx, 10);
      if (!isNaN(chapterIdx)) {
        setActiveChapterIdx(chapterIdx);
      }
    }
  }, []); // 只在组件挂载时执行一次

  // 初始化：加载当前用户
  useEffect(() => {
    isMountedRef.current = true;
    
    // 延迟加载用户信息，避免初始化顺序问题
    const user = getCurrentUser();
    if (user) {
      setCurrentUser(user);
    }
    
    // 清理函数：组件卸载时标记为未挂载
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // 当用户切换时，重新加载数据
  useEffect(() => {
    if (currentUser) {
      loadNovels();
    } else {
      setNovels([]);
      setCurrentNovelId('');
    }
  }, [currentUser]);

  // 保存activeView到localStorage
  useEffect(() => {
    localStorage.setItem('nova_write_active_view', activeView);
  }, [activeView]);

  // 保存activeVolumeIdx到localStorage
  useEffect(() => {
    localStorage.setItem('nova_write_active_volume_idx', activeVolumeIdx.toString());
  }, [activeVolumeIdx]);

  // 保存activeChapterIdx到localStorage
  useEffect(() => {
    if (activeChapterIdx !== null) {
      localStorage.setItem('nova_write_active_chapter_idx', activeChapterIdx.toString());
    } else {
      localStorage.removeItem('nova_write_active_chapter_idx');
    }
  }, [activeChapterIdx]);

  // 更新当前作品（异步保存到API）
  const updateNovel = async (updates: Partial<Novel>) => {
    if (!currentNovelId || !isMountedRef.current) return;
    
    // 使用函数式更新来获取最新的状态并构建更新的小说数据
    let updatedNovel: Novel | null = null;
    setNovels(prev => {
      const currentNovel = prev.find(n => n.id === currentNovelId);
      if (currentNovel) {
        updatedNovel = { ...currentNovel, ...updates };
        return prev.map(n => 
          n.id === currentNovelId ? updatedNovel! : n
        );
      }
      return prev;
    });
    
    // 异步保存到API
    if (updatedNovel && isMountedRef.current) {
      try {
        // 使用syncFull来完整同步小说数据
        const savedNovel = await novelApi.syncFull(updatedNovel);
        
        // 检查组件是否仍然挂载
        if (isMountedRef.current) {
          // 更新本地状态为服务器返回的最新数据
          setNovels(prev => prev.map(n => 
            n.id === currentNovelId ? savedNovel : n
          ));
        }
      } catch (error: any) {
        // 只有在组件仍然挂载时才记录错误
        if (isMountedRef.current) {
          console.error('保存小说失败:', error);
          // 如果保存失败，可以显示错误提示，但不回滚本地状态（保持乐观更新）
        }
      }
    }
  };

  // 创建新作品
  const handleCreateNovel = async () => {
    try {
      const newNovel = await novelApi.create({
        title: `新作品 ${novels.length + 1}`,
        genre: '奇幻',
        synopsis: '',
        fullOutline: '',
      });
      setNovels(prev => [...prev, newNovel]);
      setCurrentNovelId(newNovel.id);
      await currentNovelApi.set(newNovel.id);
      setShowNovelManager(false);
      setActiveView('dashboard');
      // 重置卷和章节索引
      setActiveVolumeIdx(0);
      setActiveChapterIdx(null);
    } catch (error: any) {
      console.error('创建小说失败:', error);
      alert(`创建失败: ${error.message || '未知错误'}`);
    }
  };

  // 选择作品
  const handleSelectNovel = async (novelId: string) => {
    try {
      setCurrentNovelId(novelId);
      await currentNovelApi.set(novelId);
      setShowNovelManager(false);
      // 不再强制跳转到dashboard，保持当前视图
      // setActiveView('dashboard');
      // 保持当前的卷和章节索引，不重置
      // setActiveVolumeIdx(0);
      // setActiveChapterIdx(null);
    } catch (error: any) {
      console.error('设置当前小说失败:', error);
    }
  };

  // 更新作品
  const handleUpdateNovel = async (novelId: string, updates: Partial<Novel>) => {
    try {
      // 先更新本地状态
      setNovels(prev => prev.map(n => 
        n.id === novelId ? { ...n, ...updates } : n
      ));
      
      // 保存到API
      const currentNovelData = novels.find(n => n.id === novelId);
      if (currentNovelData) {
        const updatedNovel = { ...currentNovelData, ...updates };
        const savedNovel = await novelApi.syncFull(updatedNovel);
        setNovels(prev => prev.map(n => 
          n.id === novelId ? savedNovel : n
        ));
      }
    } catch (error: any) {
      console.error('更新小说失败:', error);
      alert(`更新失败: ${error.message || '未知错误'}`);
    }
  };

  // 删除作品
  const handleDeleteNovel = async (novelId: string) => {
    if (novels.length <= 1) {
      alert('至少需要保留一本作品');
      return;
    }
    
    try {
      await novelApi.delete(novelId);
      
      // 如果删除的是当前作品，先切换到其他作品
      if (novelId === currentNovelId) {
        const remaining = novels.filter(n => n.id !== novelId);
        if (remaining.length > 0) {
          setCurrentNovelId(remaining[0].id);
          await currentNovelApi.set(remaining[0].id);
        }
      }
      
      // 从本地状态中删除
      setNovels(prev => prev.filter(n => n.id !== novelId));
    } catch (error: any) {
      console.error('删除小说失败:', error);
      alert(`删除失败: ${error.message || '未知错误'}`);
    }
  };

  // 处理登录成功
  const handleLoginSuccess = async () => {
    const user = await refreshCurrentUser();
    setCurrentUser(user);
    // 数据会在 useEffect 中自动加载
  };

  // 处理登出
  const handleLogout = () => {
    logout();
    setCurrentUser(null);
    setShowUserMenu(false);
    // 重置数据
    setNovels([]);
    setCurrentNovelId('');
  };

  // 如果未登录，显示登录页面
  if (!currentUser) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  const renderView = () => {
    switch (activeView) {
      case 'dashboard':
        return <Dashboard novel={currentNovel} updateNovel={updateNovel} onStartWriting={() => setActiveView('outline')} />;
      case 'outline':
        return <OutlineView novel={currentNovel} updateNovel={updateNovel} />;
      case 'writing':
        return (
          <EditorView 
            novel={currentNovel} 
            updateNovel={updateNovel} 
            activeVolumeIdx={activeVolumeIdx}
            activeChapterIdx={activeChapterIdx}
            setActiveChapterIdx={setActiveChapterIdx}
            setActiveVolumeIdx={setActiveVolumeIdx}
          />
        );
      case 'characters':
        return <CharacterView novel={currentNovel} updateNovel={updateNovel} />;
      case 'world':
        return <WorldView novel={currentNovel} updateNovel={updateNovel} />;
      case 'timeline':
        return <TimelineView novel={currentNovel} updateNovel={updateNovel} />;
      case 'foreshadowings':
        return <ForeshadowingView novel={currentNovel} updateNovel={updateNovel} />;
      default:
        return <Dashboard novel={currentNovel} updateNovel={updateNovel} onStartWriting={() => setActiveView('outline')} />;
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* 侧边栏 - 桌面端固定显示，移动端通过抽屉控制 */}
      <Sidebar 
        activeView={activeView} 
        setActiveView={setActiveView} 
        novelTitle={currentNovel.title || "未命名小说"}
        isMobileOpen={isMobileSidebarOpen}
        onMobileClose={() => setIsMobileSidebarOpen(false)}
      />
      <main className="flex-1 flex flex-col min-w-0 relative lg:ml-0 overflow-hidden">
        {loading && (
          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-4 flex items-center gap-3">
              <span className="inline-block w-5 h-5 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></span>
              <span className="text-slate-700">加载中...</span>
            </div>
          </div>
        )}
        <header className="h-14 border-b bg-white flex items-center justify-between px-4 md:px-6 shrink-0">
          {/* 移动端菜单按钮 */}
          <button
            onClick={() => setIsMobileSidebarOpen(true)}
            className="lg:hidden p-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors mr-2"
            aria-label="打开菜单"
          >
            <Menu size={20} />
          </button>
          
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <span className="hidden sm:inline text-sm font-medium text-slate-500">NovaWrite AI</span>
            <span className="hidden sm:inline text-slate-300">/</span>
            <span className="text-sm font-bold text-slate-800 truncate">
              {currentNovel.title || "新项目"}
            </span>
          </div>
          <div className="flex items-center gap-2 md:gap-3">
            {/* 作品选择器 - 移动端仅显示图标 */}
            <div className="relative">
              <button
                onClick={() => setShowNovelManager(true)}
                className="px-2 md:px-3 py-1.5 bg-white border border-slate-300 text-slate-700 text-xs font-semibold rounded-md hover:bg-slate-50 active:bg-slate-100 transition-colors flex items-center gap-1 md:gap-2 min-h-[36px]"
                aria-label="选择作品"
              >
                <BookOpen size={14} />
                <span className="hidden sm:inline max-w-[120px] truncate">
                  {currentNovel.title || "未命名小说"}
                </span>
                <ChevronDown size={14} className="hidden sm:block" />
              </button>
            </div>
            <button 
              onClick={() => setActiveView('writing')}
              className="px-2 md:px-3 py-1.5 bg-indigo-600 text-white text-xs font-semibold rounded-md hover:bg-indigo-700 active:bg-indigo-800 transition-colors flex items-center gap-1 md:gap-2 min-h-[36px]"
            >
              <PenTool size={14} />
              <span className="hidden sm:inline">继续写作</span>
            </button>
            
            {/* 用户菜单 */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="px-3 py-1.5 bg-white border border-slate-300 text-slate-700 text-xs font-semibold rounded-md hover:bg-slate-50 transition-colors flex items-center gap-2"
              >
                <UserIcon size={14} />
                <span className="max-w-[100px] truncate">{currentUser.username}</span>
                <ChevronDown size={14} />
              </button>
              
              {showUserMenu && (
                <>
                  <div 
                    className="fixed inset-0 z-10" 
                    onClick={() => setShowUserMenu(false)}
                  />
                  <div className="absolute right-0 mt-2 w-48 bg-white border border-slate-200 rounded-lg shadow-lg z-20 py-1">
                    <button
                      onClick={() => {
                        setShowUserSettings(true);
                        setShowUserMenu(false);
                      }}
                      className="w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                    >
                      <Settings size={16} />
                      用户设置
                    </button>
                    <button
                      onClick={() => {
                        handleLogout();
                        setShowUserMenu(false);
                      }}
                      className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                    >
                      <LogOut size={16} />
                      登出
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </header>
        <div className="flex-1 overflow-y-auto overflow-x-hidden pb-16 lg:pb-0 overscroll-contain">
          {renderView()}
        </div>
      </main>
      
      {/* 移动端底部导航栏 */}
      <MobileNav 
        activeView={activeView} 
        setActiveView={setActiveView}
      />
      
      {/* 作品管理弹窗 */}
      {showNovelManager && (
        <NovelManager
          novels={novels}
          currentNovelId={currentNovelId}
          onSelectNovel={handleSelectNovel}
          onCreateNovel={handleCreateNovel}
          onUpdateNovel={handleUpdateNovel}
          onDeleteNovel={handleDeleteNovel}
          onClose={() => setShowNovelManager(false)}
        />
      )}
      
      {/* 用户设置弹窗 */}
      {showUserSettings && (
        <UserSettings
          onClose={() => setShowUserSettings(false)}
          onLogout={handleLogout}
        />
      )}
    </div>
  );
};

export default App;
