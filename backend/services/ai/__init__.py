"""AI 服务模块"""
from .gemini_service import (
    generate_full_outline,
    generate_volume_outline_stream,
    generate_volume_outline,
    generate_chapter_outline,
    write_chapter_content_stream,
    write_chapter_content,
    generate_characters,
    generate_world_settings,
    generate_timeline_events,
    generate_foreshadowings_from_outline,
    modify_outline_by_dialogue,
    extract_foreshadowings_from_chapter,
    extract_next_chapter_hook
)
from .chapter_writing_service import (
    write_and_save_chapter,
    prepare_chapter_writing_context,
    get_forced_previous_chapter_context,
    ChapterWritingContext
)

__all__ = [
    'generate_full_outline',
    'generate_volume_outline_stream',
    'generate_volume_outline',
    'generate_chapter_outline',
    'write_chapter_content_stream',
    'write_chapter_content',
    'generate_characters',
    'generate_world_settings',
    'generate_timeline_events',
    'generate_foreshadowings_from_outline',
    'modify_outline_by_dialogue',
    'extract_foreshadowings_from_chapter',
    'extract_next_chapter_hook',
    'write_and_save_chapter',
    'prepare_chapter_writing_context',
    'get_forced_previous_chapter_context',
    'ChapterWritingContext',
]

