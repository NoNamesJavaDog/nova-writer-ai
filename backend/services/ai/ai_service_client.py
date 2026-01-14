"""AI 微服务客户端"""
import json
import logging
from typing import Optional, AsyncGenerator
import httpx

logger = logging.getLogger(__name__)


class AIServiceClient:
    """AI 微服务客户端"""

    def __init__(self, base_url: str, timeout: int = 300, provider: str = "gemini"):
        """
        初始化客户端

        Args:
            base_url: 微服务基础 URL
            timeout: 请求超时时间（秒）
            provider: AI 提供商（gemini/openai等）
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.provider = provider
        logger.info(f"✅ AI 微服务客户端初始化: {self.base_url}, provider={self.provider}")

    def _get_headers(self) -> dict:
        """获取请求头"""
        return {
            "Content-Type": "application/json",
            "X-Provider": self.provider
        }

    async def _post_json(self, path: str, payload: dict) -> dict:
        client = httpx.AsyncClient(timeout=self.timeout)
        try:
            response = await client.post(
                f"{self.base_url}{path}",
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        finally:
            try:
                await client.aclose()
            except RuntimeError:
                # Ignore uvloop transport-close errors during cleanup.
                pass

    async def close(self):
        """关闭客户端"""
        return

    # ==================== 大纲生成 ====================

    async def generate_full_outline(
        self,
        title: str,
        genre: str,
        synopsis: str,
        progress_callback=None
    ) -> dict:
        """
        生成完整大纲

        Args:
            title: 小说标题
            genre: 小说类型
            synopsis: 简介
            progress_callback: 进度回调（保留但不使用）

        Returns:
            {"outline": str, "volumes": list}
        """
        try:
            logger.info(f"[AI Service] 生成完整大纲: {title}")

            return await self._post_json(
                "/api/v1/outline/generate-full",
                {
                    "title": title,
                    "genre": genre,
                    "synopsis": synopsis
                }
            )

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成完整大纲失败: {error_msg}")
        except httpx.RequestError as e:
            error_msg = f"请求错误: {str(e)}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成完整大纲失败: {error_msg}")
        except Exception as e:
            logger.error(f"[AI Service] 未知错误: {str(e)}")
            raise Exception(f"生成完整大纲失败: {str(e)}")

    async def generate_volume_outline_stream(
        self,
        novel_title: str,
        full_outline: str,
        volume_title: str,
        volume_summary: str,
        characters: list,
        volume_index: int
    ) -> AsyncGenerator[str, None]:
        """
        流式生成卷详细大纲

        Args:
            novel_title: 小说标题
            full_outline: 完整大纲
            volume_title: 卷标题
            volume_summary: 卷简介
            characters: 角色列表
            volume_index: 卷索引

        Yields:
            SSE 格式数据
        """
        try:
            logger.info(f"[AI Service] 流式生成卷大纲: {volume_title}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/v1/outline/generate-volume-stream",
                    json={
                        "novel_title": novel_title,
                        "full_outline": full_outline,
                        "volume_title": volume_title,
                        "volume_summary": volume_summary,
                        "characters": characters,
                        "volume_index": volume_index
                    },
                    headers=self._get_headers()
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            yield line + "\n"

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(f"[AI Service] {error_msg}")
            error_data = json.dumps({"error": f"生成卷大纲失败: {error_msg}"})
            yield f"data: {error_data}\n\n"
        except httpx.RequestError as e:
            error_msg = f"请求错误: {str(e)}"
            logger.error(f"[AI Service] {error_msg}")
            error_data = json.dumps({"error": f"生成卷大纲失败: {error_msg}"})
            yield f"data: {error_data}\n\n"
        except Exception as e:
            logger.error(f"[AI Service] 未知错误: {str(e)}")
            error_data = json.dumps({"error": f"生成卷大纲失败: {str(e)}"})
            yield f"data: {error_data}\n\n"

    async def generate_volume_outline(
        self,
        novel_title: str,
        full_outline: str,
        volume_title: str,
        volume_summary: str,
        characters: list,
        volume_index: int,
        progress_callback=None
    ) -> str:
        """
        生成卷详细大纲（非流式）

        Args:
            novel_title: 小说标题
            full_outline: 完整大纲
            volume_title: 卷标题
            volume_summary: 卷简介
            characters: 角色列表
            volume_index: 卷索引
            progress_callback: 进度回调（保留但不使用）

        Returns:
            卷大纲文本
        """
        try:
            logger.info(f"[AI Service] 生成卷大纲: {volume_title}")

            result = await self._post_json(
                "/api/v1/outline/generate-volume",
                {
                    "novel_title": novel_title,
                    "full_outline": full_outline,
                    "volume_title": volume_title,
                    "volume_summary": volume_summary,
                    "characters": characters,
                    "volume_index": volume_index
                }
            )
            return result.get("outline", "")

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成卷大纲失败: {error_msg}")
        except httpx.RequestError as e:
            error_msg = f"请求错误: {str(e)}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成卷大纲失败: {error_msg}")
        except Exception as e:
            logger.error(f"[AI Service] 未知错误: {str(e)}")
            raise Exception(f"生成卷大纲失败: {str(e)}")

    async def modify_outline_by_dialogue(
        self,
        title: str,
        genre: str,
        synopsis: str,
        current_outline: str,
        characters: list,
        world_settings: list,
        timeline: list,
        user_message: str,
        progress_callback=None
    ) -> dict:
        """
        通过对话修改大纲

        Args:
            title: 小说标题
            genre: 小说类型
            synopsis: 简介
            current_outline: 当前大纲
            characters: 角色列表
            world_settings: 世界观设定
            timeline: 时间线
            user_message: 用户消息
            progress_callback: 进度回调（保留但不使用）

        Returns:
            修改结果字典
        """
        try:
            logger.info(f"[AI Service] 修改大纲: {title}")

            return await self._post_json(
                "/api/v1/outline/modify-by-dialogue",
                {
                    "title": title,
                    "genre": genre,
                    "synopsis": synopsis,
                    "current_outline": current_outline,
                    "characters": characters,
                    "world_settings": world_settings,
                    "timeline": timeline,
                    "user_message": user_message
                }
            )

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"修改大纲失败: {error_msg}")
        except httpx.RequestError as e:
            error_msg = f"请求错误: {str(e)}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"修改大纲失败: {error_msg}")
        except Exception as e:
            logger.error(f"[AI Service] 未知错误: {str(e)}")
            raise Exception(f"修改大纲失败: {str(e)}")

    # ==================== 章节生成 ====================

    async def generate_chapter_outline(
        self,
        novel_title: str,
        genre: str,
        full_outline: str,
        volume_title: str,
        volume_summary: str,
        volume_outline: str,
        characters: list,
        volume_index: int,
        chapter_count: Optional[int] = None,
        previous_volumes_info: Optional[list] = None,
        future_volumes_info: Optional[list] = None
    ) -> list:
        """
        生成章节列表

        Args:
            novel_title: 小说标题
            genre: 小说类型
            full_outline: 完整大纲
            volume_title: 卷标题
            volume_summary: 卷简介
            volume_outline: 卷大纲
            characters: 角色列表
            volume_index: 卷索引
            chapter_count: 章节数量
            previous_volumes_info: 前面卷的信息
            future_volumes_info: 后续卷的信息

        Returns:
            章节列表
        """
        try:
            logger.info(f"[AI Service] 生成章节列表: {volume_title}")

            result = await self._post_json(
                "/api/v1/chapter/generate-outline",
                {
                    "novel_title": novel_title,
                    "genre": genre,
                    "full_outline": full_outline,
                    "volume_title": volume_title,
                    "volume_summary": volume_summary,
                    "volume_outline": volume_outline,
                    "characters": characters,
                    "volume_index": volume_index,
                    "chapter_count": chapter_count,
                    "previous_volumes_info": previous_volumes_info,
                    "future_volumes_info": future_volumes_info
                }
            )
            return result.get("chapters", [])

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成章节列表失败: {error_msg}")
        except httpx.RequestError as e:
            error_msg = f"请求错误: {str(e)}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成章节列表失败: {error_msg}")
        except Exception as e:
            logger.error(f"[AI Service] 未知错误: {str(e)}")
            raise Exception(f"生成章节列表失败: {str(e)}")

    async def write_chapter_content_stream(
        self,
        novel_title: str,
        genre: str,
        synopsis: str,
        chapter_title: str,
        chapter_summary: str,
        chapter_prompt_hints: str,
        characters: list,
        world_settings: list,
        previous_chapters_context: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式生成章节内容

        Args:
            novel_title: 小说标题
            genre: 小说类型
            synopsis: 简介
            chapter_title: 章节标题
            chapter_summary: 章节摘要
            chapter_prompt_hints: 写作提示
            characters: 角色列表
            world_settings: 世界观设定
            previous_chapters_context: 前文上下文

        Yields:
            SSE 格式数据
        """
        try:
            logger.info(f"[AI Service] 流式生成章节内容: {chapter_title}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/v1/chapter/write-content-stream",
                    json={
                        "novel_title": novel_title,
                        "genre": genre,
                        "synopsis": synopsis,
                        "chapter_title": chapter_title,
                        "chapter_summary": chapter_summary,
                        "chapter_prompt_hints": chapter_prompt_hints,
                        "characters": characters,
                        "world_settings": world_settings,
                        "previous_chapters_context": previous_chapters_context
                    },
                    headers=self._get_headers()
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            yield line + "\n"

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(f"[AI Service] {error_msg}")
            error_data = json.dumps({"error": f"生成章节内容失败: {error_msg}"})
            yield f"data: {error_data}\n\n"
        except httpx.RequestError as e:
            error_msg = f"请求错误: {str(e)}"
            logger.error(f"[AI Service] {error_msg}")
            error_data = json.dumps({"error": f"生成章节内容失败: {error_msg}"})
            yield f"data: {error_data}\n\n"
        except Exception as e:
            logger.error(f"[AI Service] 未知错误: {str(e)}")
            error_data = json.dumps({"error": f"生成章节内容失败: {str(e)}"})
            yield f"data: {error_data}\n\n"

    async def write_chapter_content(
        self,
        novel_title: str,
        genre: str,
        synopsis: str,
        chapter_title: str,
        chapter_summary: str,
        chapter_prompt_hints: str,
        characters: list,
        world_settings: list,
        previous_chapters_context: Optional[str] = None,
        progress_callback=None
    ) -> str:
        """
        生成章节内容（非流式）

        Args:
            novel_title: 小说标题
            genre: 小说类型
            synopsis: 简介
            chapter_title: 章节标题
            chapter_summary: 章节摘要
            chapter_prompt_hints: 写作提示
            characters: 角色列表
            world_settings: 世界观设定
            previous_chapters_context: 前文上下文
            progress_callback: 进度回调（保留但不使用）

        Returns:
            章节内容
        """
        try:
            logger.info(f"[AI Service] 生成章节内容: {chapter_title}")

            result = await self._post_json(
                "/api/v1/chapter/write-content",
                {
                    "novel_title": novel_title,
                    "genre": genre,
                    "synopsis": synopsis,
                    "chapter_title": chapter_title,
                    "chapter_summary": chapter_summary,
                    "chapter_prompt_hints": chapter_prompt_hints,
                    "characters": characters,
                    "world_settings": world_settings,
                    "previous_chapters_context": previous_chapters_context
                }
            )
            return result.get("content", "")

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成章节内容失败: {error_msg}")
        except httpx.RequestError as e:
            error_msg = f"请求错误: {str(e)}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成章节内容失败: {error_msg}")
        except Exception as e:
            logger.error(f"[AI Service] 未知错误: {str(e)}")
            raise Exception(f"生成章节内容失败: {str(e)}")

    async def summarize_chapter_content(
        self,
        chapter_title: str,
        chapter_content: str,
        max_len: int = 400
    ) -> str:
        """
        生成章节摘要

        Args:
            chapter_title: 章节标题
            chapter_content: 章节内容
            max_len: 最大长度

        Returns:
            摘要文本
        """
        try:
            logger.info(f"[AI Service] 生成章节摘要: {chapter_title}")

            result = await self._post_json(
                "/api/v1/chapter/summarize",
                {
                    "chapter_title": chapter_title,
                    "chapter_content": chapter_content,
                    "max_len": max_len
                }
            )
            return result.get("summary", "")

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成章节摘要失败: {error_msg}")
        except httpx.RequestError as e:
            error_msg = f"请求错误: {str(e)}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成章节摘要失败: {error_msg}")
        except Exception as e:
            logger.error(f"[AI Service] 未知错误: {str(e)}")
            raise Exception(f"生成章节摘要失败: {str(e)}")

    # ==================== 分析服务 ====================

    async def generate_characters(
        self,
        title: str,
        genre: str,
        synopsis: str,
        outline: str,
        progress_callback=None
    ) -> list:
        """
        生成角色列表

        Args:
            title: 小说标题
            genre: 小说类型
            synopsis: 简介
            outline: 大纲
            progress_callback: 进度回调（保留但不使用）

        Returns:
            角色列表
        """
        try:
            logger.info(f"[AI Service] 生成角色列表: {title}")

            result = await self._post_json(
                "/api/v1/analysis/generate-characters",
                {
                    "title": title,
                    "genre": genre,
                    "synopsis": synopsis,
                    "outline": outline
                }
            )
            return result.get("characters", [])

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成角色列表失败: {error_msg}")
        except httpx.RequestError as e:
            error_msg = f"请求错误: {str(e)}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成角色列表失败: {error_msg}")
        except Exception as e:
            logger.error(f"[AI Service] 未知错误: {str(e)}")
            raise Exception(f"生成角色列表失败: {str(e)}")

    async def generate_world_settings(
        self,
        title: str,
        genre: str,
        synopsis: str,
        outline: str,
        progress_callback=None
    ) -> list:
        """
        生成世界观设定

        Args:
            title: 小说标题
            genre: 小说类型
            synopsis: 简介
            outline: 大纲
            progress_callback: 进度回调（保留但不使用）

        Returns:
            世界观设定列表
        """
        try:
            logger.info(f"[AI Service] 生成世界观设定: {title}")

            result = await self._post_json(
                "/api/v1/analysis/generate-world-settings",
                {
                    "title": title,
                    "genre": genre,
                    "synopsis": synopsis,
                    "outline": outline
                }
            )
            if isinstance(result, list):
                return result
            return result.get("world_settings") or result.get("settings") or []

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成世界观设定失败: {error_msg}")
        except httpx.RequestError as e:
            error_msg = f"请求错误: {str(e)}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成世界观设定失败: {error_msg}")
        except Exception as e:
            logger.error(f"[AI Service] 未知错误: {str(e)}")
            raise Exception(f"生成世界观设定失败: {str(e)}")

    async def generate_character_relations(
        self,
        title: str,
        genre: str,
        synopsis: str,
        outline: str,
        characters: list,
        progress_callback=None
    ) -> list:
        """
        生成角色关系

        Args:
            title: 小说标题
            genre: 小说类型
            synopsis: 简介
            outline: 大纲
            characters: 角色列表
            progress_callback: 进度回调（保留但不使用）

        Returns:
            角色关系列表
        """
        try:
            logger.info(f"[AI Service] 生成角色关系: {title}")

            result = await self._post_json(
                "/api/v1/analysis/generate-character-relations",
                {
                    "title": title,
                    "genre": genre,
                    "synopsis": synopsis,
                    "outline": outline,
                    "characters": characters,
                }
            )
            if isinstance(result, list):
                return result
            return result.get("relations") or []

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成角色关系失败: {error_msg}")
        except httpx.RequestError as e:
            error_msg = f"请求错误: {str(e)}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成角色关系失败: {error_msg}")
        except Exception as e:
            logger.error(f"[AI Service] 未知错误: {str(e)}")
            raise Exception(f"生成角色关系失败: {str(e)}")

    async def generate_timeline_events(
        self,
        title: str,
        genre: str,
        synopsis: str,
        outline: str,
        progress_callback=None
    ) -> list:
        """
        生成时间线事件

        Args:
            title: 小说标题
            genre: 小说类型
            synopsis: 简介
            outline: 大纲
            progress_callback: 进度回调（保留但不使用）

        Returns:
            时间线事件列表
        """
        try:
            logger.info(f"[AI Service] 生成时间线事件: {title}")

            result = await self._post_json(
                "/api/v1/analysis/generate-timeline",
                {
                    "title": title,
                    "genre": genre,
                    "synopsis": synopsis,
                    "outline": outline
                }
            )
            return result.get("events", [])

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成时间线事件失败: {error_msg}")
        except httpx.RequestError as e:
            error_msg = f"请求错误: {str(e)}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成时间线事件失败: {error_msg}")
        except Exception as e:
            logger.error(f"[AI Service] 未知错误: {str(e)}")
            raise Exception(f"生成时间线事件失败: {str(e)}")

    async def generate_foreshadowings_from_outline(
        self,
        title: str,
        genre: str,
        synopsis: str,
        outline: str,
        progress_callback=None
    ) -> list:
        """
        从大纲生成伏笔

        Args:
            title: 小说标题
            genre: 小说类型
            synopsis: 简介
            outline: 大纲
            progress_callback: 进度回调（保留但不使用）

        Returns:
            伏笔列表
        """
        try:
            logger.info(f"[AI Service] 生成伏笔: {title}")

            result = await self._post_json(
                "/api/v1/analysis/generate-foreshadowings",
                {
                    "title": title,
                    "genre": genre,
                    "synopsis": synopsis,
                    "outline": outline,
                    "full_outline": outline
                }
            )
            return result.get("foreshadowings", [])

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成伏笔失败: {error_msg}")
        except httpx.RequestError as e:
            error_msg = f"请求错误: {str(e)}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"生成伏笔失败: {error_msg}")
        except Exception as e:
            logger.error(f"[AI Service] 未知错误: {str(e)}")
            raise Exception(f"生成伏笔失败: {str(e)}")

    async def extract_foreshadowings_from_chapter(
        self,
        title: str,
        genre: str,
        chapter_title: str,
        chapter_content: str,
        existing_foreshadowings: list = None
    ) -> list:
        """
        从章节提取伏笔

        Args:
            title: 小说标题
            genre: 小说类型
            chapter_title: 章节标题
            chapter_content: 章节内容
            existing_foreshadowings: 已有伏笔

        Returns:
            伏笔列表
        """
        try:
            logger.info(f"[AI Service] 提取章节伏笔: {chapter_title}")

            result = await self._post_json(
                "/api/v1/analysis/extract-foreshadowings",
                {
                    "title": title,
                    "genre": genre,
                    "chapter_title": chapter_title,
                    "chapter_content": chapter_content,
                    "existing_foreshadowings": existing_foreshadowings or []
                }
            )
            return result.get("foreshadowings", [])

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"提取章节伏笔失败: {error_msg}")
        except httpx.RequestError as e:
            error_msg = f"请求错误: {str(e)}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"提取章节伏笔失败: {error_msg}")
        except Exception as e:
            logger.error(f"[AI Service] 未知错误: {str(e)}")
            raise Exception(f"提取章节伏笔失败: {str(e)}")

    async def extract_next_chapter_hook(
        self,
        title: str,
        genre: str,
        chapter_title: str,
        chapter_content: str,
        next_chapter_title: Optional[str] = None,
        next_chapter_summary: Optional[str] = None
    ) -> str:
        """
        提取下一章钩子

        Args:
            title: 小说标题
            genre: 小说类型
            chapter_title: 章节标题
            chapter_content: 章节内容
            next_chapter_title: 下一章标题
            next_chapter_summary: 下一章摘要

        Returns:
            钩子文本
        """
        try:
            logger.info(f"[AI Service] 提取下一章钩子: {chapter_title}")

            result = await self._post_json(
                "/api/v1/analysis/extract-chapter-hook",
                {
                    "title": title,
                    "genre": genre,
                    "chapter_title": chapter_title,
                    "chapter_content": chapter_content,
                    "next_chapter_title": next_chapter_title,
                    "next_chapter_summary": next_chapter_summary
                }
            )
            return result.get("hook", "")

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"提取下一章钩子失败: {error_msg}")
        except httpx.RequestError as e:
            error_msg = f"请求错误: {str(e)}"
            logger.error(f"[AI Service] {error_msg}")
            raise Exception(f"提取下一章钩子失败: {error_msg}")
        except Exception as e:
            logger.error(f"[AI Service] 未知错误: {str(e)}")
            raise Exception(f"提取下一章钩子失败: {str(e)}")
