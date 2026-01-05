// API 服务 - 封装所有后端 API 调用
// 使用 type 导入类型，避免在模块初始化时执行代码
import type { Novel, Character, WorldSetting, TimelineEvent, Foreshadowing, Volume, Chapter, User } from '../types';

// 使用相对路径，由 Nginx 代理到后端
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// 统一的 Token 存储：优先 sessionStorage，启动时迁移 legacy localStorage
const TOKEN_KEY = 'access_token';
const REFRESH_KEY = 'refresh_token';

const migrateLocalToSession = () => {
  try {
    const legacyAccess = localStorage.getItem(TOKEN_KEY);
    const legacyRefresh = localStorage.getItem(REFRESH_KEY);
    if (legacyAccess) {
      sessionStorage.setItem(TOKEN_KEY, legacyAccess);
      localStorage.removeItem(TOKEN_KEY);
    }
    if (legacyRefresh) {
      sessionStorage.setItem(REFRESH_KEY, legacyRefresh);
      localStorage.removeItem(REFRESH_KEY);
    }
  } catch {
    // ignore storage errors
  }
};

// 获取存储的访问令牌
const getToken = (): string | null => {
  migrateLocalToSession();
  return sessionStorage.getItem(TOKEN_KEY);
};

// 获取存储的刷新令牌
const getRefreshToken = (): string | null => {
  migrateLocalToSession();
  return sessionStorage.getItem(REFRESH_KEY);
};

// 设置访问令牌
const setToken = (token: string): void => {
  sessionStorage.setItem(TOKEN_KEY, token);
};

// 设置刷新令牌
const setRefreshToken = (token: string): void => {
  sessionStorage.setItem(REFRESH_KEY, token);
};

// 清除访问令牌
const clearToken = (): void => {
  sessionStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(TOKEN_KEY);
};

// 清除刷新令牌
const clearRefreshToken = (): void => {
  sessionStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(REFRESH_KEY);
};

// 清除所有令牌
const clearAllTokens = (): void => {
  clearToken();
  clearRefreshToken();
};

// Token 过期回调函数
let onTokenExpiredCallback: (() => void) | null = null;

// 设置 token 过期回调
export const setOnTokenExpired = (callback: () => void): void => {
  onTokenExpiredCallback = callback;
};

// 刷新访问令牌
let isRefreshing = false;
let refreshPromise: Promise<LoginResponse | null> | null = null;

const refreshAccessToken = async (): Promise<LoginResponse | null> => {
  // 如果正在刷新，等待当前的刷新请求完成
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        return null;
      }

      const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        clearAllTokens();
        return null;
      }

      const data: LoginResponse = await response.json();
      setToken(data.access_token);
      setRefreshToken(data.refresh_token);
      return data;
    } catch (error) {
      clearAllTokens();
      return null;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
};

// 通用 fetch（支持 401 自动刷新），用于流式接口等需要拿到 Response 的场景
export async function apiFetch(
  endpoint: string,
  options: RequestInit = {},
  retryOn401: boolean = true
): Promise<Response> {
  const token = getToken();

  const headers: HeadersInit = {
    ...(options.headers || {}),
  };

  // 仅在未显式设置时补充 Content-Type，避免覆盖 FormData 等
  if (!('Content-Type' in (headers as any))) {
    (headers as any)['Content-Type'] = 'application/json';
  }

  if (token) {
    (headers as any)['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status !== 401 || !retryOn401) {
    return response;
  }

  const refreshed = await refreshAccessToken();
  if (!refreshed) {
    clearAllTokens();
    if (onTokenExpiredCallback) {
      onTokenExpiredCallback();
    }
    throw new Error('登录已过期，请重新登录');
  }

  const retryHeaders: HeadersInit = {
    ...(options.headers || {}),
    'Authorization': `Bearer ${refreshed.access_token}`,
  };
  if (!('Content-Type' in (retryHeaders as any))) {
    (retryHeaders as any)['Content-Type'] = 'application/json';
  }

  const retryResponse = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: retryHeaders,
  });

  if (retryResponse.status === 401) {
    clearAllTokens();
    if (onTokenExpiredCallback) {
      onTokenExpiredCallback();
    }
    throw new Error('登录已过期，请重新登录');
  }

  return retryResponse;
}

// 通用 API 请求函数
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  retryOn401: boolean = true
): Promise<T> {
  const token = getToken();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    if (response.status === 401 && retryOn401) {
      // 尝试刷新令牌
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        // 使用新的访问令牌重试请求
        const newHeaders: HeadersInit = {
          'Content-Type': 'application/json',
          ...options.headers,
          'Authorization': `Bearer ${refreshed.access_token}`,
        };
        
        const retryResponse = await fetch(`${API_BASE_URL}${endpoint}`, {
          ...options,
          headers: newHeaders,
        });
        
        if (!retryResponse.ok) {
          if (retryResponse.status === 401) {
            clearAllTokens();
            // 触发 token 过期回调
            if (onTokenExpiredCallback) {
              onTokenExpiredCallback();
            }
            throw new Error('登录已过期，请重新登录');
          }
          const errorData = await retryResponse.json().catch(() => ({}));
          throw new Error(errorData.detail || `请求失败: ${retryResponse.status} ${retryResponse.statusText}`);
        }
        
        // 204 No Content 响应没有 body
        if (retryResponse.status === 204) {
          return null as T;
        }
        
        return retryResponse.json();
      } else {
        // 刷新失败，清除令牌
        clearAllTokens();
        // 触发 token 过期回调
        if (onTokenExpiredCallback) {
          onTokenExpiredCallback();
        }
        throw new Error('登录已过期，请重新登录');
      }
    }
    
    if (response.status === 401) {
      clearAllTokens();
      // 触发 token 过期回调
      if (onTokenExpiredCallback) {
        onTokenExpiredCallback();
      }
      throw new Error('登录已过期，请重新登录');
    }
    
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `请求失败: ${response.status} ${response.statusText}`);
  }
  
  // 204 No Content 响应没有 body
  if (response.status === 204) {
    return null as T;
  }
  
  return response.json();
}

// ==================== 认证相关 ====================

// 使用内联类型定义，避免在模块级别引用 User 类型
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: string;
    username: string;
    email: string;
    createdAt: number;
    lastLoginAt?: number;
  };
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
}

export interface LoginData {
  username_or_email: string;
  password: string;
  captcha_id?: string;
  captcha_code?: string;
}

export interface CaptchaResponse {
  captcha_id: string;
  image: string;
}

export interface LoginStatusResponse {
  requires_captcha: boolean;
  locked: boolean;
  lock_message?: string;
}

export const authApi = {
  // 注册
  register: async (data: RegisterData): Promise<LoginResponse> => {
    const response = await apiRequest<LoginResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }, false); // 注册接口不需要重试
    
    if (response.access_token) {
      setToken(response.access_token);
    }
    if (response.refresh_token) {
      setRefreshToken(response.refresh_token);
    }
    return response;
  },
  
  // 获取验证码
  getCaptcha: async (): Promise<CaptchaResponse> => {
    return apiRequest<CaptchaResponse>('/api/auth/captcha', {
      method: 'GET',
    }, false);
  },
  
  // 检查登录状态（是否需要验证码等）
  checkLoginStatus: async (usernameOrEmail: string): Promise<LoginStatusResponse> => {
    return apiRequest<LoginStatusResponse>(`/api/auth/login-status?username_or_email=${encodeURIComponent(usernameOrEmail)}`, {
      method: 'GET',
    }, false);
  },
  
  // 登录
  login: async (data: LoginData): Promise<LoginResponse> => {
    const response = await apiRequest<LoginResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    }, false); // 登录接口不需要重试
    
    if (response.access_token) {
      setToken(response.access_token);
    }
    if (response.refresh_token) {
      setRefreshToken(response.refresh_token);
    }
    return response;
  },
  
  // 刷新令牌
  refresh: async (refreshToken: string): Promise<LoginResponse> => {
    const response = await apiRequest<LoginResponse>('/api/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    }, false); // 刷新接口不需要重试
    
    if (response.access_token) {
      setToken(response.access_token);
    }
    if (response.refresh_token) {
      setRefreshToken(response.refresh_token);
    }
    return response;
  },
  
  // 获取当前用户信息
  getCurrentUser: async (): Promise<LoginResponse['user']> => {
    return apiRequest<LoginResponse['user']>('/api/auth/me');
  },
  
  // 登出
  logout: (): void => {
    clearAllTokens();
  },
  
  // 检查是否已登录
  isAuthenticated: (): boolean => {
    return getToken() !== null;
  },
};

// ==================== 小说相关 ====================

// 转换前端 Novel 格式到后端格式
// 注意：后端现在接受 camelCase 格式，此函数主要用于兼容
function novelToApi(novel: Novel): any {
  return {
    title: novel.title,
    genre: novel.genre,
    synopsis: novel.synopsis || '',
    fullOutline: novel.fullOutline || '',  // 后端接受 camelCase
    full_outline: novel.fullOutline || '',  // 兼容 snake_case
  };
}

// 转换后端 Novel 格式到前端格式
// 注意：后端现在返回 camelCase 格式，此函数主要用于兼容和过滤空值
function apiToNovel(apiNovel: any): Novel {
  if (!apiNovel) {
    throw new Error('apiNovel is null or undefined');
  }
  
  // 后端已返回 camelCase，但需要处理可能的空值和数组过滤
  return {
    id: apiNovel.id || apiNovel.id || '',
    title: apiNovel.title || '',
    genre: apiNovel.genre || '',
    synopsis: apiNovel.synopsis || '',
    fullOutline: apiNovel.fullOutline || apiNovel.full_outline || '',
    volumes: (Array.isArray(apiNovel.volumes) ? apiNovel.volumes : [])
      .filter((v: any) => v && v.id)
      .map((v: any) => ({
        id: v.id,
        title: v.title || '',
        summary: v.summary || '',
        outline: v.outline || '',
        chapters: (Array.isArray(v.chapters) ? v.chapters : [])
          .filter((c: any) => c && c.id)
          .map((c: any) => ({
            id: c.id,
            title: c.title || '',
            summary: c.summary || '',
            content: c.content || '',
            aiPromptHints: c.aiPromptHints || c.ai_prompt_hints || '',
          })),
      })),
    characters: (Array.isArray(apiNovel.characters) ? apiNovel.characters : [])
      .filter((c: any) => c && c.id)
      .map((c: any) => ({
        id: c.id,
        name: c.name || '',
        age: c.age || '',
        role: c.role || '',
        personality: c.personality || '',
        background: c.background || '',
        goals: c.goals || '',
      })),
    worldSettings: (Array.isArray(apiNovel.worldSettings) ? apiNovel.worldSettings : Array.isArray(apiNovel.world_settings) ? apiNovel.world_settings : [])
      .filter((w: any) => w && w.id)
      .map((w: any) => ({
        id: w.id,
        title: w.title || '',
        description: w.description || '',
        category: w.category as any,
      })),
    timeline: (Array.isArray(apiNovel.timeline) ? apiNovel.timeline : Array.isArray(apiNovel.timelineEvents) ? apiNovel.timelineEvents : Array.isArray(apiNovel.timeline_events) ? apiNovel.timeline_events : [])
      .filter((t: any) => t && t.id)
      .map((t: any) => ({
        id: t.id,
        time: t.time || '',
        event: t.event || '',
        impact: t.impact || '',
      })),
    foreshadowings: (Array.isArray(apiNovel.foreshadowings) ? apiNovel.foreshadowings : [])
      .filter((f: any) => f && f.id)
      .map((f: any) => ({
        id: f.id,
        content: f.content || '',
        chapterId: f.chapterId || f.chapter_id || undefined,
        resolvedChapterId: f.resolvedChapterId || f.resolved_chapter_id || undefined,
        isResolved: f.isResolved || f.is_resolved || 'false',
      })),
  };
}

export const novelApi = {
  // 获取所有小说
  getAll: async (): Promise<Novel[]> => {
    const response = await apiRequest<any[]>('/api/novels');
    return response.map(apiToNovel);
  },
  
  // 获取单个小说
  getById: async (novelId: string): Promise<Novel> => {
    const response = await apiRequest<any>(`/api/novels/${novelId}`);
    return apiToNovel(response);
  },
  
  // 创建小说
  create: async (novel: Partial<Novel>): Promise<Novel> => {
    const response = await apiRequest<any>('/api/novels', {
      method: 'POST',
      body: JSON.stringify(novelToApi(novel as Novel)),
    });
    return apiToNovel(response);
  },
  
  // 更新小说基本信息
  update: async (novelId: string, updates: Partial<Novel>): Promise<Novel> => {
    const response = await apiRequest<any>(`/api/novels/${novelId}`, {
      method: 'PUT',
      body: JSON.stringify({
        title: updates.title,
        genre: updates.genre,
        synopsis: updates.synopsis,
        full_outline: updates.fullOutline,
      }),
    });
    return apiToNovel(response);
  },
  
  // 删除小说
  delete: async (novelId: string): Promise<void> => {
    await apiRequest(`/api/novels/${novelId}`, {
      method: 'DELETE',
    });
  },

  // 一键写作某卷全部未写作章节（后端任务）
  writeVolumeChapters: async (novelId: string, volumeId: string, fromStart: boolean = false): Promise<{ task_id: string }> => {
    const params = fromStart ? '?from_start=true' : '';
    return apiRequest<{ task_id: string }>(`/api/novels/${novelId}/volumes/${volumeId}/write-all-chapters${params}`, {
      method: 'POST',
    });
  },
  
  // 完整同步小说（包括所有子项）
  // 注意：现在使用后端的同步接口，更高效且保证数据一致性
  syncFull: async (novel: Novel): Promise<Novel> => {
    try {
      // 使用后端同步接口
      const response = await apiRequest<any>(`/api/novels/${novel.id}/sync`, {
        method: 'POST',
        body: JSON.stringify({
          title: novel.title,
          genre: novel.genre,
          synopsis: novel.synopsis,
          fullOutline: novel.fullOutline,
          volumes: novel.volumes,
          characters: novel.characters,
          worldSettings: novel.worldSettings,
          timeline: novel.timeline,
          foreshadowings: novel.foreshadowings
        }),
      });
      return apiToNovel(response);
    } catch (error) {
      console.error('同步小说失败:', error);
      throw error;
    }
  },
  
  // 旧版同步方法（已废弃，保留用于兼容）
  // 注意：为避免初始化顺序问题，直接调用新的 syncFull 方法
  syncFull_old: async (novel: Novel): Promise<Novel> => {
    // 直接委托给 syncFull 方法，避免循环依赖
    return novelApi.syncFull(novel);
  },
};

// ==================== 卷相关 ====================

export const volumeApi = {
  getAll: async (novelId: string): Promise<Volume[]> => {
    const response = await apiRequest<any[]>(`/api/novels/${novelId}/volumes`);
    if (!Array.isArray(response)) return [];
    return response.filter(v => v && v.id).map(v => ({
      id: v.id,
      title: v.title || '',
      summary: v.summary || '',
      outline: v.outline || '',
      chapters: (Array.isArray(v.chapters) ? v.chapters : [])
        .filter((c: any) => c && c.id)
        .map((c: any) => ({
          id: c.id,
          title: c.title || '',
          summary: c.summary || '',
          content: c.content || '',
          aiPromptHints: c.ai_prompt_hints || '',
        })),
    }));
  },
  
  create: async (novelId: string, volume: Partial<Volume>): Promise<Volume> => {
    const response = await apiRequest<any>(`/api/novels/${novelId}/volumes`, {
      method: 'POST',
      body: JSON.stringify({
        title: volume.title,
        summary: volume.summary,
        outline: volume.outline,
      }),
    });
    return {
      id: response.id,
      title: response.title,
      summary: response.summary || '',
      outline: response.outline || '',
      chapters: [],
    };
  },
  
  update: async (novelId: string, volumeId: string, updates: Partial<Volume>): Promise<Volume> => {
    const response = await apiRequest<any>(`/api/novels/${novelId}/volumes/${volumeId}`, {
      method: 'PUT',
      body: JSON.stringify({
        title: updates.title,
        summary: updates.summary,
        outline: updates.outline,
      }),
    });
    return {
      id: response.id,
      title: response.title,
      summary: response.summary || '',
      outline: response.outline || '',
      chapters: [],
    };
  },
  
  delete: async (novelId: string, volumeId: string): Promise<void> => {
    await apiRequest(`/api/novels/${novelId}/volumes/${volumeId}`, {
      method: 'DELETE',
    });
  },
};

// ==================== 章节相关 ====================

export const chapterApi = {
  getAll: async (volumeId: string): Promise<Chapter[]> => {
    // 注意：需要通过卷获取章节
    const response = await apiRequest<any[]>(`/api/volumes/${volumeId}/chapters`);
    if (!Array.isArray(response)) return [];
    return response
      .filter(c => c && c.id)
      .map(c => ({
        id: c.id,
        title: c.title || '',
        summary: c.summary || '',
        content: c.content || '',
        aiPromptHints: c.ai_prompt_hints || '',
      }));
  },
  
  create: async (volumeId: string, chapter: Partial<Chapter>): Promise<Chapter> => {
    const response = await apiRequest<any[]>(`/api/volumes/${volumeId}/chapters`, {
      method: 'POST',
      body: JSON.stringify([{
        title: chapter.title,
        summary: chapter.summary,
        content: chapter.content,
        ai_prompt_hints: chapter.aiPromptHints,
      }]),
    });
    const created = response[0];
    return {
      id: created.id,
      title: created.title,
      summary: created.summary || '',
      content: created.content || '',
      aiPromptHints: created.ai_prompt_hints || '',
    };
  },
  
  createBatch: async (volumeId: string, chapters: Partial<Chapter>[]): Promise<Chapter[]> => {
    const response = await apiRequest<any[]>(`/api/volumes/${volumeId}/chapters`, {
      method: 'POST',
      body: JSON.stringify((Array.isArray(chapters) ? chapters : []).filter(c => c).map(c => ({
        title: c.title || '',
        summary: c.summary || '',
        content: c.content || '',
        ai_prompt_hints: c.aiPromptHints || '',
      }))),
    });
    if (!Array.isArray(response)) return [];
    return response.filter(c => c && c.id).map(c => ({
      id: c.id,
      title: c.title || '',
      summary: c.summary || '',
      content: c.content || '',
      aiPromptHints: c.ai_prompt_hints || '',
    }));
  },
  
  update: async (volumeId: string, chapterId: string, updates: Partial<Chapter>): Promise<Chapter> => {
    const response = await apiRequest<any>(`/api/volumes/${volumeId}/chapters/${chapterId}`, {
      method: 'PUT',
      body: JSON.stringify({
        title: updates.title,
        summary: updates.summary,
        content: updates.content,
        ai_prompt_hints: updates.aiPromptHints,
      }),
    });
    return {
      id: response.id,
      title: response.title,
      summary: response.summary || '',
      content: response.content || '',
      aiPromptHints: response.ai_prompt_hints || '',
    };
  },
  
  delete: async (volumeId: string, chapterId: string): Promise<void> => {
    await apiRequest(`/api/volumes/${volumeId}/chapters/${chapterId}`, {
      method: 'DELETE',
    });
  },
  
  reorder: async (volumeId: string, chapterIds: string[]): Promise<void> => {
    await apiRequest(`/api/volumes/${volumeId}/chapters/reorder`, {
      method: 'POST',
      body: JSON.stringify(chapterIds),
    });
  },
  
  // 同步存储章节向量（阻塞直到完成）
  storeEmbeddingSync: async (chapterId: string): Promise<{success: boolean; stored: boolean; message: string}> => {
    const response = await apiRequest<any>(`/api/chapters/${chapterId}/store-embedding-sync`, {
      method: 'POST',
    });
    return {
      success: response.success || false,
      stored: response.stored || false,
      message: response.message || '',
    };
  },
};

// ==================== 角色相关 ====================

export const characterApi = {
  getAll: async (novelId: string): Promise<Character[]> => {
    const response = await apiRequest<any[]>(`/api/novels/${novelId}/characters`);
    if (!Array.isArray(response)) return [];
    return response.filter(c => c && c.id).map(c => ({
      id: c.id,
      name: c.name || '',
      age: c.age || '',
      role: c.role || '',
      personality: c.personality || '',
      background: c.background || '',
      goals: c.goals || '',
    }));
  },
  
  create: async (novelId: string, characters: Partial<Character>[]): Promise<Character[]> => {
    const response = await apiRequest<any[]>(`/api/novels/${novelId}/characters`, {
      method: 'POST',
      body: JSON.stringify((Array.isArray(characters) ? characters : []).filter(c => c).map(c => ({
        name: c.name,
        age: c.age,
        role: c.role,
        personality: c.personality,
        background: c.background,
        goals: c.goals,
      }))),
    });
    if (!Array.isArray(response)) return [];
    return response.filter(c => c && c.id).map(c => ({
      id: c.id,
      name: c.name || '',
      age: c.age || '',
      role: c.role || '',
      personality: c.personality || '',
      background: c.background || '',
      goals: c.goals || '',
    }));
  },
  
  update: async (novelId: string, characterId: string, updates: Partial<Character>): Promise<Character> => {
    const response = await apiRequest<any>(`/api/novels/${novelId}/characters/${characterId}`, {
      method: 'PUT',
      body: JSON.stringify({
        name: updates.name,
        age: updates.age,
        role: updates.role,
        personality: updates.personality,
        background: updates.background,
        goals: updates.goals,
      }),
    });
    return {
      id: response.id,
      name: response.name,
      age: response.age || '',
      role: response.role || '',
      personality: response.personality || '',
      background: response.background || '',
      goals: response.goals || '',
    };
  },
  
  delete: async (novelId: string, characterId: string): Promise<void> => {
    await apiRequest(`/api/novels/${novelId}/characters/${characterId}`, {
      method: 'DELETE',
    });
  },
};

// ==================== 世界观相关 ====================

export const worldSettingApi = {
  getAll: async (novelId: string): Promise<WorldSetting[]> => {
    const response = await apiRequest<any[]>(`/api/novels/${novelId}/world-settings`);
    if (!Array.isArray(response)) return [];
    return response.filter(w => w && w.id).map(w => ({
      id: w.id,
      title: w.title || '',
      description: w.description || '',
      category: w.category as any,
    }));
  },
  
  create: async (novelId: string, worldSettings: Partial<WorldSetting>[]): Promise<WorldSetting[]> => {
    const response = await apiRequest<any[]>(`/api/novels/${novelId}/world-settings`, {
      method: 'POST',
      body: JSON.stringify((Array.isArray(worldSettings) ? worldSettings : []).filter(w => w).map(w => ({
        title: w.title,
        description: w.description,
        category: w.category,
      }))),
    });
    if (!Array.isArray(response)) return [];
    return response.filter(w => w && w.id).map(w => ({
      id: w.id,
      title: w.title || '',
      description: w.description || '',
      category: w.category as any,
    }));
  },
  
  update: async (novelId: string, worldSettingId: string, updates: Partial<WorldSetting>): Promise<WorldSetting> => {
    const response = await apiRequest<any>(`/api/novels/${novelId}/world-settings/${worldSettingId}`, {
      method: 'PUT',
      body: JSON.stringify({
        title: updates.title,
        description: updates.description,
        category: updates.category,
      }),
    });
    return {
      id: response.id,
      title: response.title,
      description: response.description,
      category: response.category as any,
    };
  },
  
  delete: async (novelId: string, worldSettingId: string): Promise<void> => {
    await apiRequest(`/api/novels/${novelId}/world-settings/${worldSettingId}`, {
      method: 'DELETE',
    });
  },
};

// ==================== 时间线相关 ====================

export const timelineApi = {
  getAll: async (novelId: string): Promise<TimelineEvent[]> => {
    const response = await apiRequest<any[]>(`/api/novels/${novelId}/timeline`);
    if (!Array.isArray(response)) return [];
    return response.filter(t => t && t.id).map(t => ({
      id: t.id,
      time: t.time || '',
      event: t.event || '',
      impact: t.impact || '',
    }));
  },
  
  create: async (novelId: string, timelineEvents: Partial<TimelineEvent>[]): Promise<TimelineEvent[]> => {
    const response = await apiRequest<any[]>(`/api/novels/${novelId}/timeline`, {
      method: 'POST',
      body: JSON.stringify((Array.isArray(timelineEvents) ? timelineEvents : []).filter(t => t).map(t => ({
        time: t.time,
        event: t.event,
        impact: t.impact,
      }))),
    });
    if (!Array.isArray(response)) return [];
    return response.filter(t => t && t.id).map(t => ({
      id: t.id,
      time: t.time || '',
      event: t.event || '',
      impact: t.impact || '',
    }));
  },
  
  update: async (novelId: string, timelineEventId: string, updates: Partial<TimelineEvent>): Promise<TimelineEvent> => {
    const response = await apiRequest<any>(`/api/novels/${novelId}/timeline/${timelineEventId}`, {
      method: 'PUT',
      body: JSON.stringify({
        time: updates.time,
        event: updates.event,
        impact: updates.impact,
      }),
    });
    return {
      id: response.id,
      time: response.time,
      event: response.event,
      impact: response.impact || '',
    };
  },
  
  delete: async (novelId: string, timelineEventId: string): Promise<void> => {
    await apiRequest(`/api/novels/${novelId}/timeline/${timelineEventId}`, {
      method: 'DELETE',
    });
  },
};

// ==================== 伏笔相关 ====================

export const foreshadowingApi = {
  getAll: async (novelId: string): Promise<Foreshadowing[]> => {
    const response = await apiRequest<any[]>(`/api/novels/${novelId}/foreshadowings`);
    if (!Array.isArray(response)) return [];
    return response.filter(f => f && f.id).map(f => ({
      id: f.id,
      content: f.content || '',
      chapterId: f.chapter_id || undefined,
      resolvedChapterId: f.resolved_chapter_id || undefined,
      isResolved: f.is_resolved || "false",
    }));
  },
  
  create: async (novelId: string, foreshadowings: Partial<Foreshadowing>[]): Promise<Foreshadowing[]> => {
    const response = await apiRequest<any[]>(`/api/novels/${novelId}/foreshadowings`, {
      method: 'POST',
      body: JSON.stringify((Array.isArray(foreshadowings) ? foreshadowings : []).filter(f => f).map(f => ({
        content: f.content,
        chapter_id: f.chapterId || null,
        resolved_chapter_id: f.resolvedChapterId || null,
        is_resolved: f.isResolved || "false",
      }))),
    });
    if (!Array.isArray(response)) return [];
    return response.filter(f => f && f.id).map(f => ({
      id: f.id,
      content: f.content || '',
      chapterId: f.chapter_id || undefined,
      resolvedChapterId: f.resolved_chapter_id || undefined,
      isResolved: f.is_resolved || "false",
    }));
  },
  
  update: async (novelId: string, foreshadowingId: string, updates: Partial<Foreshadowing>): Promise<Foreshadowing> => {
    const response = await apiRequest<any>(`/api/novels/${novelId}/foreshadowings/${foreshadowingId}`, {
      method: 'PUT',
      body: JSON.stringify({
        content: updates.content,
        chapter_id: updates.chapterId || null,
        resolved_chapter_id: updates.resolvedChapterId || null,
        is_resolved: updates.isResolved || "false",
      }),
    });
    return {
      id: response.id,
      content: response.content,
      chapterId: response.chapter_id || undefined,
      resolvedChapterId: response.resolved_chapter_id || undefined,
      isResolved: response.is_resolved || "false",
    };
  },
  
  delete: async (novelId: string, foreshadowingId: string): Promise<void> => {
    await apiRequest(`/api/novels/${novelId}/foreshadowings/${foreshadowingId}`, {
      method: 'DELETE',
    });
  },
};

// ==================== 当前小说ID ====================

interface CurrentNovelResponse {
  novel_id: string | null;
}

export const currentNovelApi = {
  get: async (): Promise<string | null> => {
    const response = await apiRequest<{ novel_id: string | null }>('/api/current-novel');
    return response.novel_id;
  },
  
  set: async (novelId: string): Promise<void> => {
    await apiRequest<CurrentNovelResponse>('/api/current-novel', {
      method: 'PUT',
      body: JSON.stringify({ novel_id: novelId }),
    });
  },
};

