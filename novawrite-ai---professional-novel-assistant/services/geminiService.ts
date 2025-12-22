// Gemini API 服务 - 通过后端 API 调用
import { Novel, Character, WorldSetting, TimelineEvent } from "../types";
import { apiRequest } from "./apiService";

// 流式传输回调函数类型
export type StreamChunkCallback = (chunk: string, isComplete: boolean) => void;

// 处理 Server-Sent Events 流式响应
async function processStreamResponse(
  response: Response,
  onChunk?: StreamChunkCallback
): Promise<string> {
  if (!response.body) {
    throw new Error("响应体为空");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let fullText = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        if (onChunk) {
          onChunk("", true);
        }
        break;
      }

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.substring(6));
            if (data.chunk) {
              fullText += data.chunk;
              if (onChunk) {
                onChunk(data.chunk, false);
              }
            }
            if (data.done) {
              if (onChunk) {
                onChunk("", true);
              }
              return fullText;
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  return fullText;
}

// 生成完整大纲和卷结构
export const generateFullOutline = async (
  title: string,
  genre: string,
  synopsis: string,
  onChunk?: StreamChunkCallback
) => {
  try {
    const response = await apiRequest<{ outline: string; volumes: any[] | null }>(
      "/api/ai/generate-outline",
      {
        method: "POST",
        body: JSON.stringify({ title, genre, synopsis }),
      }
    );

    return {
      outline: response.outline,
      volumes: response.volumes,
    };
  } catch (error: any) {
    throw new Error(`生成大纲失败: ${error.message || "未知错误"}`);
  }
};

// 生成单个卷的详细大纲
export const generateVolumeOutline = async (
  novel: Novel,
  volumeIndex: number,
  onChunk?: StreamChunkCallback
) => {
  if (!novel.title || !novel.fullOutline) {
    throw new Error("需要完整的小说标题和大纲");
  }

  if (!novel.volumes || volumeIndex >= novel.volumes.length) {
    throw new Error("卷索引无效");
  }

  const volume = novel.volumes[volumeIndex];

  try {
    const token = localStorage.getItem("access_token");
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

    const response = await fetch(`${API_BASE_URL}/api/ai/generate-volume-outline`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        novel_title: novel.title,
        full_outline: novel.fullOutline,
        volume_title: volume.title,
        volume_summary: volume.summary || "",
        characters: novel.characters.map((c) => ({
          name: c.name,
          role: c.role,
        })),
        volume_index: volumeIndex,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `请求失败: ${response.status}`);
    }

    if (onChunk) {
      return await processStreamResponse(response, onChunk);
    } else {
      // 非流式模式，读取所有数据
      let fullText = "";
      await processStreamResponse(response, (chunk) => {
        fullText += chunk;
      });
      return fullText;
    }
  } catch (error: any) {
    throw new Error(`生成卷大纲失败: ${error.message || "未知错误"}`);
  }
};

// 生成章节列表
export const generateChapterOutline = async (
  novel: Novel,
  volumeIndex: number = 0,
  chapterCount?: number
) => {
  if (!novel.title) {
    throw new Error("小说标题不能为空");
  }

  if (!novel.fullOutline) {
    throw new Error("完整大纲不能为空");
  }

  if (!novel.volumes || volumeIndex >= novel.volumes.length) {
    throw new Error("卷索引无效");
  }

  const volume = novel.volumes[volumeIndex];

  try {
    const chapters = await apiRequest<any[]>(
      "/api/ai/generate-chapter-outline",
      {
        method: "POST",
        body: JSON.stringify({
          novel_title: novel.title,
          genre: novel.genre,
          full_outline: novel.fullOutline,
          volume_title: volume.title,
          volume_summary: volume.summary || "",
          volume_outline: volume.outline || "",
          characters: novel.characters.map((c) => ({
            name: c.name,
            role: c.role,
          })),
          volume_index: volumeIndex,
          chapter_count: chapterCount,
        }),
      }
    );

    return chapters;
  } catch (error: any) {
    throw new Error(`生成章节列表失败: ${error.message || "未知错误"}`);
  }
};

// 生成章节内容
export const writeChapterContent = async (
  novel: Novel,
  chapterIndex: number,
  volumeIndex: number,
  onChunk?: StreamChunkCallback
) => {
  try {
    const chapter = novel.volumes[volumeIndex].chapters[chapterIndex];
    const token = localStorage.getItem("access_token");
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

    const response = await fetch(`${API_BASE_URL}/api/ai/write-chapter`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        novel_title: novel.title,
        genre: novel.genre,
        synopsis: novel.synopsis || "",
        chapter_title: chapter.title,
        chapter_summary: chapter.summary || "",
        chapter_prompt_hints: chapter.aiPromptHints || "",
        characters: novel.characters.map((c) => ({
          name: c.name,
          personality: c.personality,
        })),
        world_settings: novel.worldSettings.map((w) => ({
          title: w.title,
          description: w.description,
        })),
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `请求失败: ${response.status}`);
    }

    if (onChunk) {
      return await processStreamResponse(response, onChunk);
    } else {
      let fullText = "";
      await processStreamResponse(response, (chunk) => {
        fullText += chunk;
      });
      return fullText;
    }
  } catch (error: any) {
    throw new Error(`生成章节内容失败: ${error.message || "未知错误"}`);
  }
};

// 生成下一章节内容（考虑前文上下文）
export const writeNextChapterContent = async (
  novel: Novel,
  currentChapterIndex: number,
  volumeIndex: number,
  onChunk?: StreamChunkCallback
) => {
  if (currentChapterIndex + 1 >= novel.volumes[volumeIndex].chapters.length) {
    throw new Error("没有下一章节，请先在大纲页面生成章节列表");
  }

  const nextChapterIndex = currentChapterIndex + 1;
  return writeChapterContent(novel, nextChapterIndex, volumeIndex, onChunk);
};

// 扩展文本
export const expandText = async (text: string, context: string) => {
  // TODO: 在后端实现此功能
  throw new Error("扩展文本功能暂未实现");
};

// 润色文本
export const polishText = async (text: string) => {
  // TODO: 在后端实现此功能
  throw new Error("润色文本功能暂未实现");
};

// 生成角色列表
export const generateCharacters = async (
  title: string,
  genre: string,
  synopsis: string,
  outline: string
) => {
  try {
    const characters = await apiRequest<any[]>(
      "/api/ai/generate-characters",
      {
        method: "POST",
        body: JSON.stringify({ title, genre, synopsis, outline }),
      }
    );

    return characters;
  } catch (error: any) {
    throw new Error(`生成角色列表失败: ${error.message || "未知错误"}`);
  }
};

// 生成世界观设定
export const generateWorldSettings = async (
  title: string,
  genre: string,
  synopsis: string,
  outline: string
) => {
  try {
    const settings = await apiRequest<any[]>(
      "/api/ai/generate-world-settings",
      {
        method: "POST",
        body: JSON.stringify({ title, genre, synopsis, outline }),
      }
    );

    return settings;
  } catch (error: any) {
    throw new Error(`生成世界观设定失败: ${error.message || "未知错误"}`);
  }
};

// 生成时间线事件
export const generateTimelineEvents = async (
  title: string,
  genre: string,
  synopsis: string,
  outline: string
) => {
  try {
    const events = await apiRequest<any[]>(
      "/api/ai/generate-timeline-events",
      {
        method: "POST",
        body: JSON.stringify({ title, genre, synopsis, outline }),
      }
    );

    return events;
  } catch (error: any) {
    throw new Error(`生成时间线事件失败: ${error.message || "未知错误"}`);
  }
};

// 生成伏笔（从大纲）
export const generateForeshadowings = async (
  title: string,
  genre: string,
  synopsis: string,
  outline: string
) => {
  try {
    const foreshadowings = await apiRequest<any[]>(
      "/api/ai/generate-foreshadowings",
      {
        method: "POST",
        body: JSON.stringify({ title, genre, synopsis, outline }),
      }
    );

    return foreshadowings;
  } catch (error: any) {
    throw new Error(`生成伏笔失败: ${error.message || "未知错误"}`);
  }
};

// 从章节内容提取伏笔
export const extractForeshadowingsFromChapter = async (
  title: string,
  genre: string,
  chapterTitle: string,
  chapterContent: string,
  existingForeshadowings: any[] = []
) => {
  try {
    const foreshadowings = await apiRequest<any[]>(
      "/api/ai/extract-foreshadowings-from-chapter",
      {
        method: "POST",
        body: JSON.stringify({
          title,
          genre,
          chapter_title: chapterTitle,
          chapter_content: chapterContent,
          existing_foreshadowings: existingForeshadowings,
        }),
      }
    );

    return foreshadowings;
  } catch (error: any) {
    throw new Error(`提取伏笔失败: ${error.message || "未知错误"}`);
  }
};

// 通过对话修改大纲并联动更新相关设定
export const modifyOutlineByDialogue = async (
  novel: Novel,
  userMessage: string,
  onChunk?: StreamChunkCallback
) => {
  // TODO: 在后端实现此功能
  throw new Error("对话修改大纲功能暂未实现");
};
