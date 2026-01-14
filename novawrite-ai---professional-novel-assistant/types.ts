// 用户相关类型（放在最前面，避免循环依赖）
export interface User {
  id: string;
  username: string;
  email: string;
  createdAt: number;
  lastLoginAt?: number;
}

export interface Character {
  id: string;
  name: string;
  age: string;
  role: string;
  personality: string;
  background: string;
  goals: string;
}

export interface WorldSetting {
  id: string;
  title: string;
  description: string;
  category: '地理' | '社会' | '魔法/科技' | '历史' | '其他';
}

export interface TimelineEvent {
  id: string;
  time: string;
  event: string;
  impact: string;
}

export interface Chapter {
  id: string;
  title: string;
  summary: string;
  content: string;
  aiPromptHints: string;
  isGenerating?: boolean;
  hasContent?: boolean;  // 章节是否有内容（用于判断，避免加载完整内容）
}

export interface Volume {
  id: string;
  title: string;
  summary?: string; // 卷的简要描述
  outline?: string; // 卷的详细大纲
  chapters: Chapter[];
}

export interface Foreshadowing {
  id: string;
  content: string;
  chapterId?: string;  // 伏笔产生的章节ID，可为空（大纲阶段生成）
  resolvedChapterId?: string;  // 闭环章节ID
  isResolved: string;  // "true" 或 "false"
}

export interface Novel {
  id: string;
  title: string;
  genre: string;
  synopsis: string;
  fullOutline: string;
  volumes: Volume[];
  characters: Character[];
  worldSettings: WorldSetting[];
  timeline: TimelineEvent[];
  foreshadowings: Foreshadowing[];
}

export type AppView = 'dashboard' | 'outline' | 'writing' | 'characters' | 'world' | 'timeline' | 'foreshadowings' | 'graph' | 'agents';

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
