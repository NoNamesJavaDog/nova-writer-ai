"""Gemini API 服务模块"""
import os
import json
from typing import Optional, AsyncGenerator
from google import genai
from config import GEMINI_API_KEY

# 初始化 Gemini 客户端
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY 未配置，请在 .env 文件中设置")

client = genai.Client(api_key=GEMINI_API_KEY)

# 超时时间：5分钟（300秒）
API_TIMEOUT_MS = 300000


def generate_full_outline(
    title: str,
    genre: str,
    synopsis: str
) -> dict:
    """生成完整大纲和卷结构"""
    try:
        # 生成完整大纲
        outline_prompt = f"""作为一名资深小说家，请为标题为《{title}》的小说创作一份完整的故事大纲。
类型：{genre}。
初始创意：{synopsis}。
请提供多幕结构、关键情节转折，以及从开头到结尾的逻辑发展。"""
        
        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=outline_prompt,
            config={
                "temperature": 0.8,
                "max_output_tokens": 8192,
            }
        )
        
        full_outline = response.text if response.text else ""
        
        # 生成卷结构
        volumes_prompt = f"""基于以下完整大纲，将故事划分为多个卷（通常3-5卷）。
完整大纲：{full_outline[:2000]}

请为每个卷生成标题和简要描述。仅返回 JSON 数组，每个对象包含：
- "title"（卷标题）
- "summary"（卷的简要描述，50-100字）"""
        
        volumes_response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=volumes_prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.7,
            }
        )
        
        volumes_data = None
        if volumes_response.text:
            try:
                volumes_data = json.loads(volumes_response.text)
                if not isinstance(volumes_data, list):
                    volumes_data = None
            except:
                volumes_data = None
        
        return {
            "outline": full_outline,
            "volumes": volumes_data
        }
    except Exception as e:
        raise Exception(f"生成大纲失败: {str(e)}")


def generate_volume_outline_stream(
    novel_title: str,
    full_outline: str,
    volume_title: str,
    volume_summary: str,
    characters: list,
    volume_index: int
):
    """生成卷详细大纲（流式）"""
    try:
        characters_text = "、".join([f"{c.get('name', '')}（{c.get('role', '')}）" for c in characters[:5]]) if characters else "暂无"
        
        volume_prompt = f"""基于以下信息，为《{novel_title}》的第 {volume_index + 1} 卷《{volume_title}》生成详细大纲。

完整小说大纲：{full_outline[:1500]}

本卷信息：
标题：{volume_title}
{f'描述：{volume_summary}' if volume_summary else ''}

角色：{characters_text}

请生成本卷的详细大纲，包括：
1. 本卷的主要情节线
2. 关键事件和转折点
3. 角色在本卷中的发展
4. 本卷的起承转合结构

重要：请根据总纲中本卷的内容量，规划本卷的字数和章节数。
- 分析本卷在总纲中的情节复杂度、事件数量和内容量
- 估算本卷的合理字数范围（通常每卷15-30万字）
- 根据字数规划章节数（通常每章1.5-2.5万字）
- 确保章节数量合理，既能充分展开情节，又不会过于冗长

请在大纲末尾明确标注：
【字数规划】：XX-XX万字（例如：18-22万字）
【章节规划】：XX章（例如：12章，必须是具体数字，不要范围）"""
        
        stream = client.models.generate_content_stream(
            model="gemini-3-pro-preview",
            contents=volume_prompt,
            config={
                "temperature": 0.8,
                "max_output_tokens": 8192,
            }
        )
        
        for chunk in stream:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        raise Exception(f"生成卷大纲失败: {str(e)}")


def generate_chapter_outline(
    novel_title: str,
    genre: str,
    full_outline: str,
    volume_title: str,
    volume_summary: str,
    volume_outline: str,
    characters: list,
    volume_index: int,
    chapter_count: Optional[int] = None
) -> list:
    """生成章节列表"""
    try:
        characters_text = "、".join([f"{c.get('name', '')}（{c.get('role', '')}）" for c in characters[:5]]) if characters else "暂无"
        
        # 提取字数规划和章节规划
        word_count_info = ""
        if volume_outline:
            import re
            word_match = re.search(r'【字数规划】：\s*(\d+)[-~]?(\d+)?\s*万字', volume_outline)
            if word_match:
                min_w = word_match.group(1)
                max_w = word_match.group(2) if word_match.group(2) else min_w
                word_count_info = f"\n字数规划：{min_w}-{max_w}万字" if max_w != min_w else f"\n字数规划：{min_w}万字"
        
        chapter_count_instruction = ""
        if chapter_count:
            chapter_count_instruction = f"请为本卷生成 {chapter_count} 个章节。"
        else:
            chapter_count_instruction = """请仔细分析本卷的详细大纲，根据以下原则确定合适的章节数量并生成章节列表：
章节数量应该：
1. 优先参考卷大纲中标注的【章节规划】（如果存在）
2. 根据卷大纲的内容复杂度合理分配
3. 确保每个章节有足够的内容和情节发展（通常每章1.5-2.5万字）
4. 如果大纲中明确提到了章节数，请参考该数量
5. 如果大纲中没有明确提到，请根据情节结构合理分配（通常每章对应一个主要事件或情节转折点）
6. 章节数量应在合理范围内（建议6-30章）"""
        
        volume_desc = f"卷描述：{volume_summary[:200]}" if volume_summary else ""
        volume_outline_text = f"卷详细大纲：{volume_outline[:1500]}" if volume_outline else ""
        
        prompt = f"""基于以下小说信息，为第 {volume_index + 1} 卷《{volume_title}》生成章节列表：
标题：{novel_title}
类型：{genre}
完整大纲：{full_outline[:800]}

本卷信息：
{volume_desc}
{volume_outline_text}{word_count_info}

角色：{characters_text}

{chapter_count_instruction}

仅返回 JSON 数组，每个对象包含以下键："title"（标题）、"summary"（摘要）、"aiPromptHints"（AI提示）。"""
        
        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.7,
            }
        )
        
        if not response.text:
            raise Exception("API 返回空响应")
        
        chapters = json.loads(response.text)
        if not isinstance(chapters, list):
            raise Exception("返回的数据格式不正确")
        
        return chapters
        
    except Exception as e:
        raise Exception(f"生成章节列表失败: {str(e)}")


def write_chapter_content_stream(
    novel_title: str,
    genre: str,
    synopsis: str,
    chapter_title: str,
    chapter_summary: str,
    chapter_prompt_hints: str,
    characters: list,
    world_settings: list
):
    """生成章节内容（流式）"""
    try:
        characters_text = "；".join([f"{c.get('name', '')}：{c.get('personality', '')}" for c in characters]) if characters else "暂无"
        world_text = "；".join([f"{w.get('title', '')}：{w.get('description', '')}" for w in world_settings]) if world_settings else "暂无"
        
        prompt = f"""请为小说《{novel_title}》创作一个完整的章节。
章节标题：{chapter_title}
情节摘要：{chapter_summary}
写作提示：{chapter_prompt_hints}

上下文：
完整小说简介：{synopsis}
涉及角色：{characters_text}
世界观规则：{world_text}

请以高文学品质、沉浸式描述和引人入胜的对话来创作。仅输出章节正文内容。"""
        
        stream = client.models.generate_content_stream(
            model="gemini-3-pro-preview",
            contents=prompt,
            config={
                "temperature": 0.9,
                "max_output_tokens": 16384,
            }
        )
        
        for chunk in stream:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        raise Exception(f"生成章节内容失败: {str(e)}")


def generate_characters(
    title: str,
    genre: str,
    synopsis: str,
    outline: str
) -> list:
    """生成角色列表"""
    try:
        prompt = f"""基于以下小说信息，生成主要角色列表（3-8个角色）：
标题：{title}
类型：{genre}
简介：{synopsis}
大纲：{outline[:1000]}

请为每个角色生成详细信息。仅返回 JSON 数组，每个对象包含以下键：
- "name"（姓名）
- "age"（年龄）
- "role"（角色定位，如：主角、反派、配角等）
- "personality"（性格特征）
- "background"（背景故事）
- "goals"（目标和动机）"""
        
        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.7,
            }
        )
        
        if not response.text:
            raise Exception("API 返回空响应")
        
        characters = json.loads(response.text)
        if not isinstance(characters, list):
            raise Exception("返回的数据格式不正确")
        
        return characters
        
    except Exception as e:
        raise Exception(f"生成角色列表失败: {str(e)}")


def generate_world_settings(
    title: str,
    genre: str,
    synopsis: str,
    outline: str
) -> list:
    """生成世界观设定"""
    try:
        prompt = f"""基于以下小说信息，生成世界观设定列表（5-10个设定）：
标题：{title}
类型：{genre}
简介：{synopsis}
大纲：{outline[:1000]}

请为每个设定生成详细信息。仅返回 JSON 数组，每个对象包含以下键：
- "title"（设定标题）
- "category"（分类：地理、社会、魔法/科技、历史、其他）
- "description"（详细描述）"""
        
        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.7,
            }
        )
        
        if not response.text:
            raise Exception("API 返回空响应")
        
        settings = json.loads(response.text)
        if not isinstance(settings, list):
            raise Exception("返回的数据格式不正确")
        
        return settings
        
    except Exception as e:
        raise Exception(f"生成世界观设定失败: {str(e)}")


def generate_timeline_events(
    title: str,
    genre: str,
    synopsis: str,
    outline: str
) -> list:
    """生成时间线事件"""
    try:
        prompt = f"""基于以下小说信息，生成重要时间线事件列表（5-10个事件）：
标题：{title}
类型：{genre}
简介：{synopsis}
大纲：{outline[:1000]}

请为每个事件生成详细信息。仅返回 JSON 数组，每个对象包含以下键：
- "time"（时间/年代）
- "event"（事件标题）
- "impact"（事件影响和后果）"""
        
        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.7,
            }
        )
        
        if not response.text:
            raise Exception("API 返回空响应")
        
        events = json.loads(response.text)
        if not isinstance(events, list):
            raise Exception("返回的数据格式不正确")
        
        return events
        
    except Exception as e:
        raise Exception(f"生成时间线事件失败: {str(e)}")


def generate_foreshadowings_from_outline(
    title: str,
    genre: str,
    synopsis: str,
    outline: str
) -> list:
    """从大纲中生成伏笔"""
    try:
        prompt = f"""基于以下小说信息，生成伏笔列表（5-15个伏笔）：
标题：{title}
类型：{genre}
简介：{synopsis}
大纲：{outline[:2000]}

请分析故事大纲，识别其中的伏笔线索。伏笔是指在故事早期埋下的线索，会在后期得到呼应或揭示。

仅返回 JSON 数组，每个对象包含以下键：
- "content"（伏笔内容描述，50-150字）"""
        
        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.7,
            }
        )
        
        if not response.text:
            raise Exception("API 返回空响应")
        
        foreshadowings = json.loads(response.text)
        if not isinstance(foreshadowings, list):
            raise Exception("返回的数据格式不正确")
        
        return foreshadowings
        
    except Exception as e:
        raise Exception(f"生成伏笔失败: {str(e)}")


def extract_foreshadowings_from_chapter(
    title: str,
    genre: str,
    chapter_title: str,
    chapter_content: str,
    existing_foreshadowings: list = None
) -> list:
    """从章节内容中提取伏笔"""
    try:
        existing_text = ""
        if existing_foreshadowings:
            existing_text = "\n已存在的伏笔：\n" + "\n".join([f"- {f.get('content', '')[:100]}" for f in existing_foreshadowings[:10]])
        
        prompt = f"""基于以下章节内容，提取新出现的伏笔线索（0-5个）：
小说标题：{title}
类型：{genre}
章节标题：{chapter_title}
章节内容：{chapter_content[:3000]}
{existing_text}

请仔细分析章节内容，识别：
1. 新出现的可疑线索、未解之谜
2. 角色的暗示性话语或行为
3. 环境中的特殊细节
4. 看似无意但可能有深意的情节设置

注意：
- 只提取明显可以作为伏笔的内容
- 避免与已有伏笔重复
- 如果章节中没有新的伏笔线索，返回空数组

仅返回 JSON 数组，每个对象包含以下键：
- "content"（伏笔内容描述，50-150字）"""
        
        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.7,
            }
        )
        
        if not response.text:
            raise Exception("API 返回空响应")
        
        foreshadowings = json.loads(response.text)
        if not isinstance(foreshadowings, list):
            raise Exception("返回的数据格式不正确")
        
        return foreshadowings
        
    except Exception as e:
        raise Exception(f"提取伏笔失败: {str(e)}")

