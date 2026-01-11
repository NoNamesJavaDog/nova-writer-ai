"""AI 服务提供商抽象基类"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, List, Dict, Any, Callable
from enum import Enum


class StreamMode(str, Enum):
    """流式响应模式"""
    SSE = "sse"           # Server-Sent Events
    JSON_STREAM = "json"  # JSON 流


class AIServiceProvider(ABC):
    """AI 服务提供商抽象基类

    所有 AI 提供商（Gemini、Claude、OpenAI等）都必须实现这个接口
    """

    def __init__(self, api_key: str, proxy: Optional[str] = None, **kwargs):
        """初始化 AI 服务提供商

        Args:
            api_key: API 密钥
            proxy: 代理地址（可选）
            **kwargs: 其他提供商特定的参数
        """
        self.api_key = api_key
        self.proxy = proxy
        self._configure_client()

    @abstractmethod
    def _configure_client(self):
        """配置客户端

        实现此方法来：
        - 设置代理
        - 配置超时时间
        - 初始化 API 客户端
        """
        pass

    # ==================== 大纲生成 ====================

    @abstractmethod
    async def generate_full_outline(
        self,
        title: str,
        genre: str,
        synopsis: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """生成完整大纲和卷结构

        Args:
            title: 小说标题
            genre: 小说类型/体裁
            synopsis: 简介/创意
            progress_callback: 进度回调函数（可选）

        Returns:
            {
                "outline": str,  # 完整大纲文本
                "volumes": List[Dict]  # 卷结构列表
            }
        """
        pass

    @abstractmethod
    async def generate_volume_outline_stream(
        self,
        novel_title: str,
        full_outline: str,
        volume_title: str,
        volume_summary: str,
        characters: List[Dict],
        volume_index: int
    ) -> AsyncGenerator[str, None]:
        """流式生成卷详细大纲

        Args:
            novel_title: 小说标题
            full_outline: 完整大纲
            volume_title: 卷标题
            volume_summary: 卷简介
            characters: 角色列表
            volume_index: 卷索引（从0开始）

        Yields:
            SSE 格式的字符串: "data: {json}\\n\\n"
        """
        pass

    @abstractmethod
    async def generate_volume_outline(
        self,
        novel_title: str,
        full_outline: str,
        volume_title: str,
        volume_summary: str,
        characters: List[Dict],
        volume_index: int,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """生成卷详细大纲（非流式）

        Args:
            novel_title: 小说标题
            full_outline: 完整大纲
            volume_title: 卷标题
            volume_summary: 卷简介
            characters: 角色列表
            volume_index: 卷索引（从0开始）
            progress_callback: 进度回调函数（可选）

        Returns:
            卷详细大纲文本
        """
        pass

    @abstractmethod
    async def generate_chapter_outline(
        self,
        novel_title: str,
        genre: str,
        full_outline: str,
        volume_title: str,
        volume_summary: str,
        volume_outline: str,
        characters: List[Dict],
        volume_index: int,
        chapter_count: Optional[int] = None,
        previous_volumes_info: Optional[List[Dict]] = None,
        future_volumes_info: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """生成章节列表

        Args:
            novel_title: 小说标题
            genre: 小说类型
            full_outline: 完整大纲
            volume_title: 卷标题
            volume_summary: 卷简介
            volume_outline: 卷详细大纲
            characters: 角色列表
            volume_index: 卷索引
            chapter_count: 期望的章节数（可选）
            previous_volumes_info: 之前卷的信息（可选）
            future_volumes_info: 未来卷的信息（可选）

        Returns:
            章节列表 [{"title": str, "summary": str, "prompt_hints": str}, ...]
        """
        pass

    @abstractmethod
    async def modify_outline_by_dialogue(
        self,
        outline: str,
        dialogue_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """通过对话修改大纲

        Args:
            outline: 当前大纲
            dialogue_data: 对话数据（包含用户输入和历史对话）
            progress_callback: 进度回调函数（可选）

        Returns:
            {
                "outline": str,  # 修改后的大纲
                "changes": str   # 变更说明
            }
        """
        pass

    # ==================== 章节生成 ====================

    @abstractmethod
    async def write_chapter_content_stream(
        self,
        novel_title: str,
        genre: str,
        synopsis: str,
        chapter_title: str,
        chapter_summary: str,
        chapter_prompt_hints: str,
        characters: List[Dict],
        world_settings: List[Dict],
        previous_chapters_context: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """流式生成章节内容

        Args:
            novel_title: 小说标题
            genre: 小说类型
            synopsis: 简介
            chapter_title: 章节标题
            chapter_summary: 章节简介
            chapter_prompt_hints: 章节提示（额外指导）
            characters: 角色列表
            world_settings: 世界观设定列表
            previous_chapters_context: 前面章节的上下文（可选）

        Yields:
            SSE 格式的字符串: "data: {json}\\n\\n"
        """
        pass

    @abstractmethod
    async def write_chapter_content(
        self,
        novel_title: str,
        genre: str,
        synopsis: str,
        chapter_title: str,
        chapter_summary: str,
        chapter_prompt_hints: str,
        characters: List[Dict],
        world_settings: List[Dict],
        previous_chapters_context: Optional[str] = None
    ) -> str:
        """生成章节内容（非流式）

        Args:
            同 write_chapter_content_stream

        Returns:
            章节内容文本
        """
        pass

    @abstractmethod
    async def summarize_chapter_content(
        self,
        chapter_title: str,
        chapter_content: str,
        max_len: int = 400
    ) -> str:
        """总结章节内容

        Args:
            chapter_title: 章节标题
            chapter_content: 章节内容
            max_len: 最大总结长度

        Returns:
            章节内容总结
        """
        pass

    # ==================== 元数据生成 ====================

    @abstractmethod
    async def generate_characters(
        self,
        title: str,
        genre: str,
        synopsis: str,
        outline: str,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """生成角色列表

        Args:
            title: 小说标题
            genre: 小说类型
            synopsis: 简介
            outline: 大纲
            progress_callback: 进度回调函数（可选）

        Returns:
            角色列表 [{"name": str, "role": str, "personality": str, ...}, ...]
        """
        pass

    @abstractmethod
    async def generate_world_settings(
        self,
        title: str,
        genre: str,
        synopsis: str,
        outline: str,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """生成世界观设定

        Args:
            title: 小说标题
            genre: 小说类型
            synopsis: 简介
            outline: 大纲
            progress_callback: 进度回调函数（可选）

        Returns:
            世界观列表 [{"title": str, "description": str, "category": str, ...}, ...]
        """
        pass

    @abstractmethod
    async def generate_timeline_events(
        self,
        title: str,
        genre: str,
        synopsis: str,
        outline: str,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """生成时间线事件

        Args:
            title: 小说标题
            genre: 小说类型
            synopsis: 简介
            outline: 大纲
            progress_callback: 进度回调函数（可选）

        Returns:
            时间线事件列表 [{"time": str, "event": str, "significance": str, ...}, ...]
        """
        pass

    @abstractmethod
    async def generate_foreshadowings_from_outline(
        self,
        full_outline: str,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """从大纲生成伏笔

        Args:
            full_outline: 完整大纲
            progress_callback: 进度回调函数（可选）

        Returns:
            伏笔列表 [{"content": str, "setup_location": str, "payoff_location": str, ...}, ...]
        """
        pass

    # ==================== 内容提取 ====================

    @abstractmethod
    async def extract_foreshadowings_from_chapter(
        self,
        chapter_content: str
    ) -> List[Dict]:
        """从章节提取伏笔

        Args:
            chapter_content: 章节内容

        Returns:
            伏笔列表 [{"content": str, "type": str, ...}, ...]
        """
        pass

    @abstractmethod
    async def extract_next_chapter_hook(
        self,
        chapter_content: str
    ) -> str:
        """提取章节末尾的钩子

        Args:
            chapter_content: 章节内容

        Returns:
            章节钩子文本
        """
        pass
