"""Gemini API 服务适配器（调用微服务）"""
import logging
from typing import Optional, AsyncGenerator
from services.ai.ai_service_client import AIServiceClient
from core.config import AI_SERVICE_URL, AI_SERVICE_PROVIDER

# 初始化微服务客户端
_ai_client = AIServiceClient(base_url=AI_SERVICE_URL, provider=AI_SERVICE_PROVIDER)
logger = logging.getLogger(__name__)

# ==================== 适配器函数 ====================
# 保持原有函数签名，调用微服务


async def generate_full_outline(
    title: str,
    genre: str,
    synopsis: str,
    progress_callback=None
) -> dict:
    """生成完整大纲（适配器）"""
    logger.info(f"[AI Service Adapter] 生成完整大纲: {title}")
    return await _ai_client.generate_full_outline(title, genre, synopsis, progress_callback)


async def generate_volume_outline_stream(
    novel_title: str,
    full_outline: str,
    volume_title: str,
    volume_summary: str,
    characters: list,
    volume_index: int
):
    """生成卷详细大纲（流式，适配器）"""
    logger.info(f"[AI Service Adapter] 流式生成卷大纲: {volume_title}")
    async for chunk in _ai_client.generate_volume_outline_stream(
        novel_title=novel_title,
        full_outline=full_outline,
        volume_title=volume_title,
        volume_summary=volume_summary,
        characters=characters,
        volume_index=volume_index
    ):
        yield chunk


async def generate_volume_outline(
    novel_title: str,
    full_outline: str,
    volume_title: str,
    volume_summary: str,
    characters: list,
    volume_index: int,
    progress_callback=None
) -> str:
    """生成卷详细大纲（非流式，适配器）"""
    logger.info(f"[AI Service Adapter] 生成卷大纲: {volume_title}")
    return await _ai_client.generate_volume_outline(
        novel_title=novel_title,
        full_outline=full_outline,
        volume_title=volume_title,
        volume_summary=volume_summary,
        characters=characters,
        volume_index=volume_index,
        progress_callback=progress_callback
    )


async def generate_chapter_outline(
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
    """生成章节列表（适配器）"""
    logger.info(f"[AI Service Adapter] 生成章节列表: {volume_title}")
    return await _ai_client.generate_chapter_outline(
        novel_title=novel_title,
        genre=genre,
        full_outline=full_outline,
        volume_title=volume_title,
        volume_summary=volume_summary,
        volume_outline=volume_outline,
        characters=characters,
        volume_index=volume_index,
        chapter_count=chapter_count,
        previous_volumes_info=previous_volumes_info,
        future_volumes_info=future_volumes_info
    )


async def write_chapter_content_stream(
    novel_title: str,
    genre: str,
    synopsis: str,
    chapter_title: str,
    chapter_summary: str,
    chapter_prompt_hints: str,
    characters: list,
    world_settings: list,
    previous_chapters_context: Optional[str] = None,
    novel_id: Optional[str] = None,
    current_chapter_id: Optional[str] = None,
    db_session=None,
    forced_previous_chapter_context: Optional[str] = None
):
    """流式生成章节内容（适配器，保留向量检索逻辑）"""
    logger.info(f"[AI Service Adapter] 流式生成章节: {chapter_title}")

    # ==================== 在主应用中进行向量检索 ====================
    # 保留原逻辑（第 602-651 行）
    if novel_id and db_session:
        try:
            from services.analysis.consistency_checker import ConsistencyChecker
            from services.analysis.content_similarity_checker import ContentSimilarityChecker

            # 可选：在生成前进行相似度检查（仅警告，不阻止生成）
            try:
                similarity_checker = ContentSimilarityChecker()
                similarity_result = similarity_checker.check_before_generation(
                    db=db_session,
                    novel_id=novel_id,
                    chapter_title=chapter_title,
                    chapter_summary=chapter_summary,
                    exclude_chapter_ids=[current_chapter_id] if current_chapter_id else None,
                    similarity_threshold=0.8
                )
                if similarity_result.get("has_similar_content"):
                    logger.warning(f"⚠️  相似度警告: {similarity_result.get('warnings', [])}")
            except Exception as e:
                logger.warning(f"⚠️  相似度检查失败（继续生成）: {str(e)}")

            # 获取智能上下文（只获取当前卷及之前卷的章节）
            checker = ConsistencyChecker()
            smart_context = checker.get_relevant_context_text(
                db=db_session,
                novel_id=novel_id,
                current_chapter_title=chapter_title,
                current_chapter_summary=chapter_summary,
                exclude_chapter_ids=[current_chapter_id] if current_chapter_id else None,
                max_chapters=5
            )

            if smart_context and smart_context.strip():
                # 优先使用强制上下文（当前章节内容）
                if forced_previous_chapter_context and forced_previous_chapter_context.strip():
                    # 将强制上下文和智能上下文合并
                    previous_chapters_context = f"{forced_previous_chapter_context}\n\n【相关前文参考】（基于向量相似度智能推荐的其他相关章节）：\n{smart_context}"
                else:
                    previous_chapters_context = smart_context

                logger.info(f"✅ 使用智能上下文检索，找到 {len(smart_context.split('---'))} 个相关章节")
        except Exception as e:
            # 如果向量检索失败，使用原始上下文，不影响主流程
            logger.warning(f"⚠️  智能上下文检索失败，使用原始上下文: {str(e)}")

    # 调用微服务
    async for chunk in _ai_client.write_chapter_content_stream(
        novel_title=novel_title,
        genre=genre,
        synopsis=synopsis,
        chapter_title=chapter_title,
        chapter_summary=chapter_summary,
        chapter_prompt_hints=chapter_prompt_hints,
        characters=characters,
        world_settings=world_settings,
        previous_chapters_context=previous_chapters_context
    ):
        yield chunk


async def write_chapter_content(
    novel_title: str,
    genre: str,
    synopsis: str,
    chapter_title: str,
    chapter_summary: str,
    chapter_prompt_hints: str,
    characters: list,
    world_settings: list,
    previous_chapters_context: Optional[str] = None,
    novel_id: Optional[str] = None,
    current_chapter_id: Optional[str] = None,
    db_session=None,
    progress_callback=None,
    forced_previous_chapter_context: Optional[str] = None
) -> str:
    """生成章节内容（非流式，适配器，保留向量检索逻辑）"""
    logger.info(f"[AI Service Adapter] 生成章节内容: {chapter_title}")

    # ==================== 在主应用中进行向量检索 ====================
    # 保留原逻辑（第 786-828 行）
    if novel_id and db_session:
        try:
            from services.analysis.consistency_checker import ConsistencyChecker
            from services.analysis.content_similarity_checker import ContentSimilarityChecker

            # 可选：在生成前进行相似度检查（仅警告，不阻止生成）
            try:
                similarity_checker = ContentSimilarityChecker()
                similarity_result = similarity_checker.check_before_generation(
                    db=db_session,
                    novel_id=novel_id,
                    chapter_title=chapter_title,
                    chapter_summary=chapter_summary,
                    exclude_chapter_ids=[current_chapter_id] if current_chapter_id else None,
                    similarity_threshold=0.8
                )
                if similarity_result.get("has_similar_content"):
                    logger.warning(f"⚠️  相似度警告: {similarity_result.get('warnings', [])}")
            except Exception as e:
                logger.warning(f"⚠️  相似度检查失败（继续生成）: {str(e)}")

            # 获取智能上下文
            checker = ConsistencyChecker()
            smart_context = checker.get_relevant_context_text(
                db=db_session,
                novel_id=novel_id,
                current_chapter_title=chapter_title,
                current_chapter_summary=chapter_summary,
                exclude_chapter_ids=[current_chapter_id] if current_chapter_id else None,
                max_chapters=5
            )

            if smart_context and smart_context.strip():
                # 优先使用强制上下文（当前章节内容）
                if forced_previous_chapter_context and forced_previous_chapter_context.strip():
                    # 将强制上下文和智能上下文合并
                    previous_chapters_context = f"{forced_previous_chapter_context}\n\n【相关前文参考】（基于向量相似度智能推荐的其他相关章节）：\n{smart_context}"
                else:
                    previous_chapters_context = smart_context

                logger.info(f"✅ 使用智能上下文检索，找到 {len(smart_context.split('---'))} 个相关章节")
        except Exception as e:
            # 如果向量检索失败，使用原始上下文，不影响主流程
            logger.warning(f"⚠️  智能上下文检索失败，使用原始上下文: {str(e)}")

    # 调用微服务
    return await _ai_client.write_chapter_content(
        novel_title=novel_title,
        genre=genre,
        synopsis=synopsis,
        chapter_title=chapter_title,
        chapter_summary=chapter_summary,
        chapter_prompt_hints=chapter_prompt_hints,
        characters=characters,
        world_settings=world_settings,
        previous_chapters_context=previous_chapters_context,
        progress_callback=progress_callback
    )


async def summarize_chapter_content(
    chapter_title: str,
    chapter_content: str,
    max_len: int = 400
) -> str:
    """生成章节摘要（适配器）"""
    logger.info(f"[AI Service Adapter] 生成章节摘要: {chapter_title}")
    return await _ai_client.summarize_chapter_content(
        chapter_title=chapter_title,
        chapter_content=chapter_content,
        max_len=max_len
    )


async def generate_characters(
    title: str,
    genre: str,
    synopsis: str,
    outline: str,
    progress_callback=None
) -> list:
    """生成角色列表（适配器）"""
    logger.info(f"[AI Service Adapter] 生成角色列表: {title}")
    return await _ai_client.generate_characters(
        title=title,
        genre=genre,
        synopsis=synopsis,
        outline=outline,
        progress_callback=progress_callback
    )


async def generate_character_relations(
    title: str,
    genre: str,
    synopsis: str,
    outline: str,
    characters: list,
    progress_callback=None
) -> list:
    """生成角色关系（适配器）"""
    logger.info(f"[AI Service Adapter] 生成角色关系: {title}")
    return await _ai_client.generate_character_relations(
        title=title,
        genre=genre,
        synopsis=synopsis,
        outline=outline,
        characters=characters,
        progress_callback=progress_callback
    )


async def generate_world_settings(
    title: str,
    genre: str,
    synopsis: str,
    outline: str,
    progress_callback=None
) -> list:
    """生成世界观设定（适配器）"""
    logger.info(f"[AI Service Adapter] 生成世界观设定: {title}")
    return await _ai_client.generate_world_settings(
        title=title,
        genre=genre,
        synopsis=synopsis,
        outline=outline,
        progress_callback=progress_callback
    )


async def generate_timeline_events(
    title: str,
    genre: str,
    synopsis: str,
    outline: str,
    progress_callback=None
) -> list:
    """生成时间线事件（适配器）"""
    logger.info(f"[AI Service Adapter] 生成时间线事件: {title}")
    return await _ai_client.generate_timeline_events(
        title=title,
        genre=genre,
        synopsis=synopsis,
        outline=outline,
        progress_callback=progress_callback
    )


async def generate_foreshadowings_from_outline(
    title: str,
    genre: str,
    synopsis: str,
    outline: str,
    progress_callback=None
) -> list:
    """从大纲生成伏笔（适配器）"""
    logger.info(f"[AI Service Adapter] 从大纲生成伏笔: {title}")
    return await _ai_client.generate_foreshadowings_from_outline(
        title=title,
        genre=genre,
        synopsis=synopsis,
        outline=outline,
        progress_callback=progress_callback
    )


async def modify_outline_by_dialogue(
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
    """通过对话修改大纲（适配器）"""
    logger.info(f"[AI Service Adapter] 修改大纲: {title}")
    return await _ai_client.modify_outline_by_dialogue(
        title=title,
        genre=genre,
        synopsis=synopsis,
        current_outline=current_outline,
        characters=characters,
        world_settings=world_settings,
        timeline=timeline,
        user_message=user_message,
        progress_callback=progress_callback
    )


async def extract_foreshadowings_from_chapter(
    title: str,
    genre: str,
    chapter_title: str,
    chapter_content: str,
    existing_foreshadowings: list = None
) -> list:
    """从章节提取伏笔（适配器）"""
    logger.info(f"[AI Service Adapter] 从章节提取伏笔: {chapter_title}")
    return await _ai_client.extract_foreshadowings_from_chapter(
        title=title,
        genre=genre,
        chapter_title=chapter_title,
        chapter_content=chapter_content,
        existing_foreshadowings=existing_foreshadowings
    )


async def extract_next_chapter_hook(
    title: str,
    genre: str,
    chapter_title: str,
    chapter_content: str,
    next_chapter_title: Optional[str] = None,
    next_chapter_summary: Optional[str] = None
) -> str:
    """提取下一章钩子（适配器）"""
    logger.info(f"[AI Service Adapter] 提取下一章钩子: {chapter_title}")
    return await _ai_client.extract_next_chapter_hook(
        title=title,
        genre=genre,
        chapter_title=chapter_title,
        chapter_content=chapter_content,
        next_chapter_title=next_chapter_title,
        next_chapter_summary=next_chapter_summary
    )
