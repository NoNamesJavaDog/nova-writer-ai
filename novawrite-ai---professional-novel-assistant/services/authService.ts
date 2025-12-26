// 用户认证服务 - 使用后端API
// 完全移除对 User 类型的依赖，使用内联类型定义

// 类型定义
type LoginData = {
  username_or_email: string;
  password: string;
  captcha_id?: string;
  captcha_code?: string;
};

type RegisterData = {
  username: string;
  email: string;
  password: string;
};

type CaptchaResponse = {
  captcha_id: string;
  image: string;
};

type LoginStatusResponse = {
  requires_captcha: boolean;
  locked: boolean;
  lock_message?: string;
};

// 使用内联类型定义，避免引用 User 类型
type LoginResponse = {
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
};

// 使用相对路径，由 Nginx 代理到后端
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// 获取存储的访问令牌
const getToken = (): string | null => {
  return localStorage.getItem('access_token');
};

// 设置访问令牌
const setToken = (token: string): void => {
  localStorage.setItem('access_token', token);
};

// 设置刷新令牌
const setRefreshToken = (token: string): void => {
  localStorage.setItem('refresh_token', token);
};

// 清除所有令牌
const clearAllTokens = (): void => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

// 通用 API 请求函数（独立实现，避免循环依赖）
const apiRequest = async <T>(endpoint: string, options: RequestInit = {}): Promise<T> => {
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
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `请求失败: ${response.status} ${response.statusText}`);
  }
  
  // 204 No Content 响应没有 body
  if (response.status === 204) {
    return null as T;
  }
  
  return response.json();
};

// 导出验证码相关函数
export const getCaptcha = async (): Promise<CaptchaResponse> => {
  return apiRequest<CaptchaResponse>('/api/auth/captcha', {
    method: 'GET',
  });
};

export const checkLoginStatus = async (usernameOrEmail: string): Promise<LoginStatusResponse> => {
  return apiRequest<LoginStatusResponse>(`/api/auth/login-status?username_or_email=${encodeURIComponent(usernameOrEmail)}`, {
    method: 'GET',
  });
};

const STORAGE_KEY_CURRENT_USER = 'nova_write_current_user'; // 当前登录用户（缓存）

// 定义用户类型别名
type UserType = LoginResponse['user'];

// 获取当前登录用户（从缓存）
export const getCurrentUser = (): UserType | null => {
  const saved = localStorage.getItem(STORAGE_KEY_CURRENT_USER);
  if (saved) {
    try {
      return JSON.parse(saved) as UserType;
    } catch {
      return null;
    }
  }
  return null;
};

// 设置当前用户到缓存
const setCurrentUserCache = (user: UserType | null): void => {
  if (user) {
    localStorage.setItem(STORAGE_KEY_CURRENT_USER, JSON.stringify(user));
  } else {
    localStorage.removeItem(STORAGE_KEY_CURRENT_USER);
  }
};

// 注册新用户
export const register = async (username: string, email: string, password: string): Promise<UserType> => {
  const data: RegisterData = { username, email, password };
  try {
    const response: LoginResponse = await apiRequest<LoginResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    
    if (response.access_token) {
      setToken(response.access_token);
    }
    if (response.refresh_token) {
      setRefreshToken(response.refresh_token);
    }
    
    setCurrentUserCache(response.user);
    return response.user;
  } catch (error: any) {
    throw new Error(error.message || '注册失败，请重试');
  }
};

// 登录
export const login = async (
  usernameOrEmail: string, 
  password: string, 
  captchaId?: string, 
  captchaCode?: string
): Promise<UserType> => {
  const data: LoginData = {
    username_or_email: usernameOrEmail,
    password: password,
    captcha_id: captchaId,
    captcha_code: captchaCode
  };
  
  try {
    const response: LoginResponse = await apiRequest<LoginResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    
    if (response.access_token) {
      setToken(response.access_token);
    }
    if (response.refresh_token) {
      setRefreshToken(response.refresh_token);
    }
    
    setCurrentUserCache(response.user);
    return response.user;
  } catch (error: any) {
    throw new Error(error.message || '登录失败，请检查用户名和密码');
  }
};

// 登出
export const logout = (): void => {
  clearAllTokens();
  setCurrentUserCache(null);
};

// 检查是否已登录
export const isAuthenticated = (): boolean => {
  return getToken() !== null;
};

// 刷新当前用户信息（从服务器获取最新信息）
export const refreshCurrentUser = async (): Promise<UserType | null> => {
  try {
    const user: UserType = await apiRequest<UserType>('/api/auth/me');
    setCurrentUserCache(user);
    return user;
  } catch (error) {
    // 如果获取失败，可能是token过期，清除缓存
    setCurrentUserCache(null);
    return null;
  }
};
