// Gemini API 服务 - 通过后端 API 调用
import { Novel, Character, WorldSetting, TimelineEvent } from "../types";
import { apiFetch, apiRequest } from "./apiService";

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

// 生成完整大纲和卷结构（任务模式）
export const generateFullOutline = async (
  title: string,
  genre: string,
  synopsis: string,
  novelId: string,
  onChunk?: StreamChunkCallback
): Promise<{ outline: string; volumes: any[] | null; taskId?: string }> => {
  try {
    // 创建任务
    const taskResponse = await apiRequest<{ task_id: string; status: string; message: string }>(
      "/api/ai/generate-outline",
      {
        method: "POST",
        body: JSON.stringify({ title, genre, synopsis, novel_id: novelId }),
      }
    );

    // 如果返回了 task_id，说明是异步任务模式
    if (taskResponse.task_id) {
      return {
        outline: '',
        volumes: null,
        taskId: taskResponse.task_id,
      };
    }

    // 兼容旧的同步模式（不应该到达这里）
    return {
      outline: '',
      volumes: null,
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
    const response = await apiFetch(`/api/ai/generate-volume-outline`, {
      method: "POST",
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

// 获取前文章节上下文（用于避免重复内容）
const getPreviousChaptersContext = (
  novel: Novel,
  chapterIndex: number,
  volumeIndex: number,
  maxChapters: number = 3  // 默认传递前3章
): string => {
  const chapters = novel.volumes[volumeIndex].chapters;
  if (chapterIndex === 0) return ""; // 第一章没有前文
  
  // 获取前面几章（最多maxChapters章）
  const startIdx = Math.max(0, chapterIndex - maxChapters);
  const previousChapters = chapters.slice(startIdx, chapterIndex);
  
  return previousChapters.map((ch, idx) => {
    const actualIdx = startIdx + idx;
    let context = `第${actualIdx + 1}章《${ch.title}》`;
    
    if (ch.content && ch.content.trim()) {
      // 如果有内容，提取摘要（取前800字 + 结尾200字，或者直接截取1000字）
      const content = ch.content;
      let summary = "";
      
      if (content.length <= 1000) {
        summary = content;
      } else {
        // 开头800字 + 结尾200字，保证连贯性
        summary = content.substring(0, 800) + "\n[...]\n" + content.substring(content.length - 200);
      }
      context += `：\n${summary}`;
    } else if (ch.summary) {
      // 如果没有内容但有摘要，使用摘要
      context += `摘要：${ch.summary}`;
    }
    
    return context;
  }).join("\n\n---\n\n");
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

    // 注意：后端现在会自动使用向量相似度智能选择相关章节作为上下文
    // 如果提供了 novel_id，后端会忽略 previous_chapters_context 参数
    // 保留此调用作为备用（当后端无法获取 novel_id 时）
    const previousChaptersContext = getPreviousChaptersContext(novel, chapterIndex, volumeIndex, 3);

    const response = await apiFetch(`/api/ai/write-chapter`, {
      method: "POST",
      body: JSON.stringify({
        novel_title: novel.title,
        novel_id: novel.id,  // 传递 novel_id，后端会使用向量相似度智能选择相关章节
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
        previous_chapters_context: previousChaptersContext || undefined,  // 备用上下文（后端会自动使用智能上下文）
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
  try {
    const response = await apiRequest<{ expanded_text: string }>(
      "/api/ai/expand-text",
      {
        method: "POST",
        body: JSON.stringify({ text, context }),
      }
    );
    return response.expanded_text;
  } catch (error: any) {
    throw new Error(`扩展文本失败: ${error.message || "未知错误"}`);
  }
};

// 润色文本
export const polishText = async (text: string) => {
  try {
    const response = await apiRequest<{ polished_text: string }>(
      "/api/ai/polish-text",
      {
        method: "POST",
        body: JSON.stringify({ text }),
      }
    );
    return response.polished_text;
  } catch (error: any) {
    throw new Error(`润色文本失败: ${error.message || "未知错误"}`);
  }
};

// 生成角色列表（任务模式）
export const generateCharacters = async (
  title: string,
  genre: string,
  synopsis: string,
  outline: string,
  novelId: string
): Promise<{ taskId?: string; characters?: any[] }> => {
  try {
    const response = await apiRequest<{ task_id: string; status: string; message: string } | any[]>(
      "/api/ai/generate-characters",
      {
        method: "POST",
        body: JSON.stringify({ title, genre, synopsis, outline, novel_id: novelId }),
      }
    );

    // 如果返回了 task_id，说明是异步任务模式
    if (response && typeof response === 'object' && 'task_id' in response) {
      return { taskId: (response as any).task_id };
    }

    // 兼容旧的同步模式（不应该到达这里）
    return { characters: response as any[] };
  } catch (error: any) {
    throw new Error(`生成角色列表失败: ${error.message || "未知错误"}`);
  }
};

// 生成世界观设定（任务模式）
export const generateWorldSettings = async (
  title: string,
  genre: string,
  synopsis: string,
  outline: string,
  novelId: string
): Promise<{ taskId?: string; settings?: any[] }> => {
  try {
    const response = await apiRequest<{ task_id: string; status: string; message: string } | any[]>(
      "/api/ai/generate-world-settings",
      {
        method: "POST",
        body: JSON.stringify({ title, genre, synopsis, outline, novel_id: novelId }),
      }
    );

    // 如果返回了 task_id，说明是异步任务模式
    if (response && typeof response === 'object' && 'task_id' in response) {
      return { taskId: (response as any).task_id };
    }

    // 兼容旧的同步模式（不应该到达这里）
    return { settings: response as any[] };
  } catch (error: any) {
    throw new Error(`生成世界观设定失败: ${error.message || "未知错误"}`);
  }
};

// 生成时间线事件（任务模式）
export const generateTimelineEvents = async (
  title: string,
  genre: string,
  synopsis: string,
  outline: string,
  novelId: string
): Promise<{ taskId?: string; events?: any[] }> => {
  try {
    const response = await apiRequest<{ task_id: string; status: string; message: string } | any[]>(
      "/api/ai/generate-timeline-events",
      {
        method: "POST",
        body: JSON.stringify({ title, genre, synopsis, outline, novel_id: novelId }),
      }
    );

    // 如果返回了 task_id，说明是异步任务模式
    if (response && typeof response === 'object' && 'task_id' in response) {
      return { taskId: (response as any).task_id };
    }

    // 兼容旧的同步模式（不应该到达这里）
    return { events: response as any[] };

    return events;
  } catch (error: any) {
    throw new Error(`生成时间线事件失败: ${error.message || "未知错误"}`);
  }
};

// 生成伏笔（从大纲，任务模式）
export const generateForeshadowings = async (
  title: string,
  genre: string,
  synopsis: string,
  outline: string,
  novelId: string
): Promise<{ taskId?: string; foreshadowings?: any[] }> => {
  try {
    const response = await apiRequest<{ task_id: string; status: string; message: string } | any[]>(
      "/api/ai/generate-foreshadowings",
      {
        method: "POST",
        body: JSON.stringify({ title, genre, synopsis, outline, novel_id: novelId }),
      }
    );

    // 如果返回了 task_id，说明是异步任务模式
    if (response && typeof response === 'object' && 'task_id' in response) {
      return { taskId: (response as any).task_id };
    }

    // 兼容旧的同步模式（不应该到达这里）
    return { foreshadowings: response as any[] };
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

// 通过对话修改大纲并联动更新相关设定（任务模式）
export const modifyOutlineByDialogue = async (
  novel: Novel,
  userMessage: string
): Promise<{ taskId?: string; result?: any }> => {
  try {
    if (!novel.id) {
      throw new Error("小说ID不存在");
    }

    const response = await apiRequest<{ task_id: string; status: string; message: string }>(
      "/api/ai/modify-outline-by-dialogue",
      {
        method: "POST",
        body: JSON.stringify({
          novel_id: novel.id,
          user_message: userMessage,
        }),
      }
    );

    // 如果返回了 task_id，说明是异步任务模式
    if (response.task_id) {
      return { taskId: response.task_id };
    }

    // 兼容旧的同步模式（不应该到达这里）
    return {};
  } catch (error: any) {
    throw new Error(`修改大纲失败: ${error.message || "未知错误"}`);
  }
};
