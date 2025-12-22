// 用户认证服务 - 使用后端API
import { User } from '../types';
import { authApi, LoginData, RegisterData } from './apiService';

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
    const response = await authApi.register(data);
    setCurrentUserCache(response.user);
    return response.user;
  } catch (error: any) {
    throw new Error(error.message || '注册失败，请重试');
  }
};

// 登录
export const login = async (usernameOrEmail: string, password: string): Promise<User> => {
  const data: LoginData = {
    username_or_email: usernameOrEmail,
    password: password
  };
  
  try {
    const response = await authApi.login(data);
    setCurrentUserCache(response.user);
    return response.user;
  } catch (error: any) {
    throw new Error(error.message || '登录失败，请检查用户名和密码');
  }
};

// 登出
export const logout = (): void => {
  authApi.logout();
  setCurrentUserCache(null);
  // 清除所有令牌已在 authApi.logout() 中处理
};

// 检查是否已登录
export const isAuthenticated = (): boolean => {
  return authApi.isAuthenticated();
};

// 刷新当前用户信息（从服务器获取最新信息）
export const refreshCurrentUser = async (): Promise<User | null> => {
  try {
    const user = await authApi.getCurrentUser();
    setCurrentUserCache(user);
    return user;
  } catch (error) {
    // 如果获取失败，可能是token过期，清除缓存
    setCurrentUserCache(null);
    return null;
  }
};
