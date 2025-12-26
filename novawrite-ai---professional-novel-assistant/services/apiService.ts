// API 服务 - 封装所有后端 API 调用
// 使用 type 导入类型，避免在模块初始化时执行代码
import type { Novel, Character, WorldSetting, TimelineEvent, Foreshadowing, Volume, Chapter, User } from '../types';

// 使用相对路径，由 Nginx 代理到后端
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// 获取存储的访问令牌
const getToken = (): string | null => {
  return localStorage.getItem('access_token');
};

// 获取存储的刷新令牌
const getRefreshToken = (): string | null => {
  return localStorage.getItem('refresh_token');
};

// 设置访问令牌
const setToken = (token: string): void => {
  localStorage.setItem('access_token', token);
};

// 设置刷新令牌
const setRefreshToken = (token: string): void => {
  localStorage.setItem('refresh_token', token);
};

// 清除访问令牌
const clearToken = (): void => {
  localStorage.removeItem('access_token');
};

// 清除刷新令牌
const clearRefreshToken = (): void => {
  localStorage.removeItem('refresh_token');
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
  syncFull_old: async (novel: Novel): Promise<Novel> => {
    try {
      // 1. 更新基本信息
      await novelApi.update(novel.id, novel);
      
      // 2. 同步卷和章节（简化：只更新存在的，新增的通过批量API处理）
      const existingVolumes = (await volumeApi.getAll(novel.id)) || [];
      const existingVolumeIds = new Set(existingVolumes.filter(v => v && v.id).map(v => v.id));
      const novelVolumes = (novel.volumes && Array.isArray(novel.volumes)) ? novel.volumes : [];
      
      for (const volume of novelVolumes) {
        if (existingVolumeIds.has(volume.id)) {
          // 更新现有卷
          await volumeApi.update(novel.id, volume.id, {
            title: volume.title,
            summary: volume.summary,
            outline: volume.outline,
          });
          
          // 同步章节（获取现有章节）
          const existingChapters = (await chapterApi.getAll(volume.id)) || [];
          const existingChapterIds = new Set(existingChapters.filter(c => c && c.id).map(c => c.id));
          const volumeChapters = (volume.chapters && Array.isArray(volume.chapters)) ? volume.chapters : [];
          const frontendChapterIds = new Set(volumeChapters.filter(c => c && c.id).map(c => c.id));
          
          // 更新或创建章节
          for (const chapter of volumeChapters) {
            if (existingChapterIds.has(chapter.id)) {
              await chapterApi.update(volume.id, chapter.id, {
                title: chapter.title,
                summary: chapter.summary,
                content: chapter.content,
                aiPromptHints: chapter.aiPromptHints,
              });
            } else {
              // 新章节通过批量创建
              await chapterApi.create(volume.id, {
                title: chapter.title,
                summary: chapter.summary,
                content: chapter.content,
                aiPromptHints: chapter.aiPromptHints,
              });
            }
          }
          
          // 删除前端列表中不存在但在数据库中仍然存在的章节
          for (const existingChapter of existingChapters) {
            if (!frontendChapterIds.has(existingChapter.id)) {
              await chapterApi.delete(volume.id, existingChapter.id);
            }
          }
          
          // 重新排序章节：按照前端传入的顺序
          if (volumeChapters.length > 0) {
            const chapterIds = volumeChapters.filter(ch => ch && ch.id).map(ch => ch.id);
            await chapterApi.reorder(volume.id, chapterIds);
          }
        } else {
          // 创建新卷
          const newVolume = await volumeApi.create(novel.id, {
            title: volume.title,
            summary: volume.summary,
            outline: volume.outline,
          });
          
          // 批量创建章节
          const volumeChaptersForNew = (volume.chapters && Array.isArray(volume.chapters)) ? volume.chapters : [];
          if (volumeChaptersForNew.length > 0) {
            await chapterApi.createBatch(newVolume.id, volumeChaptersForNew.filter(ch => ch).map(ch => ({
              title: ch.title,
              summary: ch.summary,
              content: ch.content,
              aiPromptHints: ch.aiPromptHints,
            })));
          }
        }
      }
      
      // 删除不在前端列表中的卷（包括其所有章节）
      for (const existingVolume of existingVolumes) {
        if (existingVolume && existingVolume.id && !novelVolumes.some(v => v && v.id === existingVolume.id)) {
          // 先删除卷下的所有章节
          const volumeChapters = (await chapterApi.getAll(existingVolume.id)) || [];
          for (const chapter of volumeChapters) {
            if (chapter && chapter.id) {
              await chapterApi.delete(existingVolume.id, chapter.id);
            }
          }
          // 然后删除卷
          await volumeApi.delete(novel.id, existingVolume.id);
        }
      }
      
      // 3. 同步角色
      const existingCharacters = (await characterApi.getAll(novel.id)) || [];
      const novelCharacters = (novel.characters && Array.isArray(novel.characters)) ? novel.characters : [];
      const novelCharacterIds = new Set(novelCharacters.filter(c => c && c.id).map(c => c.id));
      
      // 删除不在列表中的角色
      for (const existing of existingCharacters) {
        if (existing && existing.id && !novelCharacterIds.has(existing.id)) {
          await characterApi.delete(novel.id, existing.id);
        }
      }
      
      // 更新或创建角色
      const charactersToCreate: Partial<Character>[] = [];
      for (const character of novelCharacters) {
        if (!character || !character.id) continue;
        const existing = existingCharacters.find(c => c && c.id === character.id);
        if (existing) {
          await characterApi.update(novel.id, character.id, character);
        } else {
          charactersToCreate.push(character);
        }
      }
      if (charactersToCreate.length > 0) {
        await characterApi.create(novel.id, charactersToCreate);
      }
      
      // 4. 同步世界观设定
      const existingWorldSettings = (await worldSettingApi.getAll(novel.id)) || [];
      const novelWorldSettings = (novel.worldSettings && Array.isArray(novel.worldSettings)) ? novel.worldSettings : [];
      const novelWorldSettingIds = new Set(novelWorldSettings.filter(w => w && w.id).map(w => w.id));
      
      for (const existing of existingWorldSettings) {
        if (existing && existing.id && !novelWorldSettingIds.has(existing.id)) {
          await worldSettingApi.delete(novel.id, existing.id);
        }
      }
      
      const worldSettingsToCreate: Partial<WorldSetting>[] = [];
      for (const worldSetting of novelWorldSettings) {
        if (!worldSetting || !worldSetting.id) continue;
        const existing = existingWorldSettings.find(w => w && w.id === worldSetting.id);
        if (existing) {
          await worldSettingApi.update(novel.id, worldSetting.id, worldSetting);
        } else {
          worldSettingsToCreate.push(worldSetting);
        }
      }
      if (worldSettingsToCreate.length > 0) {
        await worldSettingApi.create(novel.id, worldSettingsToCreate);
      }
      
      // 5. 同步时间线
      const existingTimeline = (await timelineApi.getAll(novel.id)) || [];
      const novelTimeline = (novel.timeline && Array.isArray(novel.timeline)) ? novel.timeline : [];
      const novelTimelineIds = new Set(novelTimeline.filter(t => t && t.id).map(t => t.id));
      
      for (const existing of existingTimeline) {
        if (existing && existing.id && !novelTimelineIds.has(existing.id)) {
          await timelineApi.delete(novel.id, existing.id);
        }
      }
      
      const timelineToCreate: Partial<TimelineEvent>[] = [];
      for (const timelineEvent of novelTimeline) {
        if (!timelineEvent || !timelineEvent.id) continue;
        const existing = existingTimeline.find(t => t && t.id === timelineEvent.id);
        if (existing) {
          await timelineApi.update(novel.id, timelineEvent.id, timelineEvent);
        } else {
          timelineToCreate.push(timelineEvent);
        }
      }
      if (timelineToCreate.length > 0) {
        await timelineApi.create(novel.id, timelineToCreate);
      }
      
      // 6. 同步伏笔
      const existingForeshadowings = (await foreshadowingApi.getAll(novel.id)) || [];
      const novelForeshadowings = (novel.foreshadowings && Array.isArray(novel.foreshadowings)) ? novel.foreshadowings : [];
      const novelForeshadowingIds = new Set(novelForeshadowings.filter(f => f && f.id).map(f => f.id));
      
      // 删除不在列表中的伏笔
      for (const existing of existingForeshadowings) {
        if (existing && existing.id && !novelForeshadowingIds.has(existing.id)) {
          await foreshadowingApi.delete(novel.id, existing.id);
        }
      }
      
      // 更新或创建伏笔
      const foreshadowingsToCreate: Partial<Foreshadowing>[] = [];
      for (const foreshadowing of novelForeshadowings) {
        if (!foreshadowing || !foreshadowing.id) continue;
        const existing = existingForeshadowings.find(f => f && f.id === foreshadowing.id);
        if (existing) {
          await foreshadowingApi.update(novel.id, foreshadowing.id, foreshadowing);
        } else {
          foreshadowingsToCreate.push(foreshadowing);
        }
      }
      if (foreshadowingsToCreate.length > 0) {
        await foreshadowingApi.create(novel.id, foreshadowingsToCreate);
      }
      
      // 返回最新的小说数据
      return novelApi.getById(novel.id);
    } catch (error) {
      console.error('同步小说失败:', error);
      throw error;
    }
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

