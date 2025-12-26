// 用户认证服务 - 使用后端API
import { User } from '../types';

// 类型定义（避免导入 apiService 的类型）
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

type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
};

// 延迟导入 authApi 以避免循环依赖
let _authApi: typeof import('./apiService').authApi | null = null;
const getAuthApi = async () => {
  if (!_authApi) {
    const apiService = await import('./apiService');
    _authApi = apiService.authApi;
  }
  return _authApi;
};

// 导出验证码相关函数
export const getCaptcha = async (): Promise<CaptchaResponse> => {
  const authApi = await getAuthApi();
  return authApi.getCaptcha();
};

export const checkLoginStatus = async (usernameOrEmail: string): Promise<LoginStatusResponse> => {
  const authApi = await getAuthApi();
  return authApi.checkLoginStatus(usernameOrEmail);
};

const STORAGE_KEY_CURRENT_USER = 'nova_write_current_user'; // 当前登录用户（缓存）

// 获取当前登录用户（从缓存）
export const getCurrentUser = (): User | null => {
  const saved = localStorage.getItem(STORAGE_KEY_CURRENT_USER);
  if (saved) {
    try {
      return JSON.parse(saved) as User;
    } catch {
      return null;
    }
  }
  return null;
};

// 设置当前用户到缓存
const setCurrentUserCache = (user: User | null): void => {
  if (user) {
    localStorage.setItem(STORAGE_KEY_CURRENT_USER, JSON.stringify(user));
  } else {
    localStorage.removeItem(STORAGE_KEY_CURRENT_USER);
  }
};

// 注册新用户
export const register = async (username: string, email: string, password: string): Promise<User> => {
  const data: RegisterData = { username, email, password };
  try {
    const authApi = await getAuthApi();
    const response = await authApi.register(data);
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
): Promise<User> => {
  const data: LoginData = {
    username_or_email: usernameOrEmail,
    password: password,
    captcha_id: captchaId,
    captcha_code: captchaCode
  };
  
  try {
    const authApi = await getAuthApi();
    const response: LoginResponse = await authApi.login(data);
    setCurrentUserCache(response.user);
    return response.user;
  } catch (error: any) {
    throw new Error(error.message || '登录失败，请检查用户名和密码');
  }
};

// 登出
export const logout = (): void => {
  // 直接清除令牌，避免循环依赖
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  setCurrentUserCache(null);
};

// 检查是否已登录
export const isAuthenticated = (): boolean => {
  // 直接检查 token，避免循环依赖
  return localStorage.getItem('access_token') !== null;
};

// 刷新当前用户信息（从服务器获取最新信息）
export const refreshCurrentUser = async (): Promise<User | null> => {
  try {
    const authApi = await getAuthApi();
    const user = await authApi.getCurrentUser();
    setCurrentUserCache(user);
    return user;
  } catch (error) {
    // 如果获取失败，可能是token过期，清除缓存
    setCurrentUserCache(null);
    return null;
  }
};
