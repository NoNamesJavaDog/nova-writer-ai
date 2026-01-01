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
    synopsis: str,
    progress_callback=None
) -> dict:
    """生成完整大纲和卷结构"""
    try:
        if progress_callback:
            progress_callback.update(10, "开始生成完整大纲...")
        
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
        
        if progress_callback:
            progress_callback.update(50, "完整大纲生成完成，开始生成卷结构...")
        
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
        
        if progress_callback:
            progress_callback.update(90, "卷结构生成完成，处理结果...")
        
        result = {
            "outline": full_outline,
            "volumes": volumes_data
        }
        
        if progress_callback:
            progress_callback.update(100, "生成完成")
        
        return result
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
- 根据字数规划章节数（每章5000-8000字，即0.5-0.8万字）
- 计算公式：章节数 = 卷总字数（万字）÷ 0.65（平均每章0.65万字）
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
                # 按照 SSE 格式返回数据
                data = json.dumps({"chunk": chunk.text})
                yield f"data: {data}\n\n"
        
        # 发送完成信号
        yield f"data: {json.dumps({'done': True})}\n\n"
                
    except Exception as e:
        # 发送错误信息
        error_data = json.dumps({"error": str(e)})
        yield f"data: {error_data}\n\n"
        raise Exception(f"生成卷大纲失败: {str(e)}")


def generate_volume_outline(
    novel_title: str,
    full_outline: str,
    volume_title: str,
    volume_summary: str,
    characters: list,
    volume_index: int,
    progress_callback=None
) -> str:
    """生成卷详细大纲（非流式，返回完整文本）"""
    try:
        if progress_callback:
            progress_callback.update(10, "开始生成卷大纲...")
        
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
- 根据字数规划章节数（每章5000-8000字，即0.5-0.8万字）
- 计算公式：章节数 = 卷总字数（万字）÷ 0.65（平均每章0.65万字）
- 确保章节数量合理，既能充分展开情节，又不会过于冗长

请在大纲末尾明确标注：
【字数规划】：XX-XX万字（例如：18-22万字）
【章节规划】：XX章（例如：12章，必须是具体数字，不要范围）"""
        
        if progress_callback:
            progress_callback.update(50, "正在调用AI生成卷大纲...")
        
        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=volume_prompt,
            config={
                "temperature": 0.8,
                "max_output_tokens": 8192,
            }
        )
        
        if not response.text:
            raise Exception("API 返回空响应")
        
        if progress_callback:
            progress_callback.update(90, "卷大纲生成完成")
        
        return response.text
                
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
2. 根据卷大纲的内容复杂度和字数规划合理分配
3. 确保每个章节有足够的内容和情节发展（每章5000-8000字，即0.5-0.8万字）
4. 如果大纲中有字数规划，按照每章5000-8000字的标准计算章节数
5. 如果大纲中明确提到了章节数，请参考该数量
6. 如果大纲中没有明确提到，请根据情节结构合理分配（通常每章对应一个主要事件或情节转折点）
7. 章节数量应在合理范围内（建议6-30章）"""
        
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
    world_settings: list,
    previous_chapters_context: Optional[str] = None,
    novel_id: Optional[str] = None,
    current_chapter_id: Optional[str] = None,
    db_session=None
):
    """生成章节内容（流式）"""
    try:
        characters_text = "；".join([f"{c.get('name', '')}：{c.get('personality', '')}" for c in characters]) if characters else "暂无"
        world_text = "；".join([f"{w.get('title', '')}：{w.get('description', '')}" for w in world_settings]) if world_settings else "暂无"
        
        # 新增：使用向量检索获取智能上下文（如果提供了 novel_id 和 db_session）
        if novel_id and db_session:
            try:
                from services.consistency_checker import ConsistencyChecker
                from services.content_similarity_checker import ContentSimilarityChecker
                
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
                        import logging
                        logging.getLogger(__name__).warning(f"⚠️  相似度警告: {similarity_result.get('warnings', [])}")
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"⚠️  相似度检查失败（继续生成）: {str(e)}")
                
                # 获取智能上下文（增加到5章以提供更丰富的上下文，避免重复）
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
                    previous_chapters_context = smart_context
                    import logging
                    logging.getLogger(__name__).info(f"✅ 使用智能上下文检索，找到 {len(smart_context.split('---'))} 个相关章节")
            except Exception as e:
                # 如果向量检索失败，使用原始上下文，不影响主流程
                import logging
                logging.getLogger(__name__).warning(f"⚠️  智能上下文检索失败，使用原始上下文: {str(e)}")
        
        # 构建前文上下文部分（增强版，更强调避免重复）
        previous_context_section = ""
        if previous_chapters_context and previous_chapters_context.strip():
            previous_context_section = f"""

【前文内容参考】（基于向量相似度智能推荐的相关章节）：
{previous_chapters_context}

🚨 【重复内容检查要求】- 必须严格遵守：
1. ❌ 绝对禁止：重复前文中已经完整描述过的场景、事件、对话
2. ❌ 绝对禁止：使用与前文相同的叙事结构、描写手法、语言风格
3. ❌ 绝对禁止：让角色重复做过的事情或说过类似的话
4. ✅ 正确做法：如需提及前文，仅用1-2句简短过渡，不展开描写
5. ✅ 正确做法：本章必须推进全新情节，展现新的冲突和发展
6. ✅ 正确做法：采用不同的叙述视角、情绪基调、描写重点
7. ✅ 正确做法：确保本章有独特的核心事件，与前文明显区分

⚠️ 注意：上述前文是通过AI语义分析自动推荐的最相关章节，请认真阅读并确保本章内容完全不同。
"""
        
        prompt = f"""请为小说《{novel_title}》创作一个完整的章节。

【章节基本信息】
- 标题：{chapter_title}
- 情节摘要：{chapter_summary}
- 写作提示：{chapter_prompt_hints}

【小说背景信息】
- 完整简介：{synopsis}
- 涉及角色：{characters_text}
- 世界观规则：{world_text}
{previous_context_section}

【创作要求】
1. 字数要求：5000-8000字（正文内容，充实饱满）
2. 情节要求：
   - 必须完整推进本章情节，有明确的开端、发展、高潮、结尾
   - 核心事件必须与前文不同，避免重复情节
   - 确保本章有独特的戏剧冲突和情感张力
3. 叙事要求：
   - 采用高文学品质的沉浸式描述
   - 对话要生动自然，符合角色性格
   - 细节描写丰富（环境、心理、动作、神态）
   - 叙事节奏张弛有度，避免平铺直叙
4. 原创性要求：
   - 场景设置必须新颖独特
   - 角色互动方式要有变化
   - 避免使用套路化的表达和桥段

⚠️ 最重要：认真阅读【前文内容参考】，确保本章内容完全原创，不与前文重复！

现在请开始创作，仅输出章节正文内容（不要输出标题）："""
        
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
                # 按照 SSE 格式返回数据
                data = json.dumps({"chunk": chunk.text})
                yield f"data: {data}\n\n"
        
        # 发送完成信号
        yield f"data: {json.dumps({'done': True})}\n\n"
                
    except Exception as e:
        # 发送错误信息
        error_data = json.dumps({"error": str(e)})
        yield f"data: {error_data}\n\n"
        raise Exception(f"生成章节内容失败: {str(e)}")


def generate_characters(
    title: str,
    genre: str,
    synopsis: str,
    outline: str,
    progress_callback=None
) -> list:
    """生成角色列表"""
    try:
        if progress_callback:
            progress_callback.update(20, "开始生成角色列表...")
        
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
        
        if progress_callback:
            progress_callback.update(50, "正在调用 AI 生成角色...")
        
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
        
        if progress_callback:
            progress_callback.update(80, "正在处理角色数据...")
        
        characters = json.loads(response.text)
        if not isinstance(characters, list):
            raise Exception("返回的数据格式不正确")
        
        if progress_callback:
            progress_callback.update(100, "角色生成完成")
        
        return characters
        
    except Exception as e:
        raise Exception(f"生成角色列表失败: {str(e)}")


def generate_world_settings(
    title: str,
    genre: str,
    synopsis: str,
    outline: str,
    progress_callback=None
) -> list:
    """生成世界观设定"""
    try:
        if progress_callback:
            progress_callback.update(20, "开始生成世界观设定...")
        
        prompt = f"""基于以下小说信息，生成世界观设定列表（5-10个设定）：
标题：{title}
类型：{genre}
简介：{synopsis}
大纲：{outline[:1000]}

请为每个设定生成详细信息。仅返回 JSON 数组，每个对象包含以下键：
- "title"（设定标题）
- "category"（分类：地理、社会、魔法/科技、历史、其他）
- "description"（详细描述）"""
        
        if progress_callback:
            progress_callback.update(50, "正在调用 AI 生成世界观...")
        
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
        
        if progress_callback:
            progress_callback.update(80, "正在处理世界观数据...")
        
        settings = json.loads(response.text)
        if not isinstance(settings, list):
            raise Exception("返回的数据格式不正确")
        
        if progress_callback:
            progress_callback.update(100, "世界观生成完成")
        
        return settings
        
    except Exception as e:
        raise Exception(f"生成世界观设定失败: {str(e)}")


def generate_timeline_events(
    title: str,
    genre: str,
    synopsis: str,
    outline: str,
    progress_callback=None
) -> list:
    """生成时间线事件"""
    try:
        if progress_callback:
            progress_callback.update(20, "开始生成时间线事件...")
        
        prompt = f"""基于以下小说信息，生成重要时间线事件列表（5-10个事件）：
标题：{title}
类型：{genre}
简介：{synopsis}
大纲：{outline[:1000]}

请为每个事件生成详细信息。仅返回 JSON 数组，每个对象包含以下键：
- "time"（时间/年代）
- "event"（事件标题）
- "impact"（事件影响和后果）"""
        
        if progress_callback:
            progress_callback.update(50, "正在调用 AI 生成时间线...")
        
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
        
        if progress_callback:
            progress_callback.update(80, "正在处理时间线数据...")
        
        events = json.loads(response.text)
        if not isinstance(events, list):
            raise Exception("返回的数据格式不正确")
        
        if progress_callback:
            progress_callback.update(100, "时间线生成完成")
        
        return events
        
    except Exception as e:
        raise Exception(f"生成时间线事件失败: {str(e)}")


def generate_foreshadowings_from_outline(
    title: str,
    genre: str,
    synopsis: str,
    outline: str,
    progress_callback=None
) -> list:
    """从大纲中生成伏笔"""
    try:
        if progress_callback:
            progress_callback.update(20, "开始生成伏笔列表...")
        
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
        
        if progress_callback:
            progress_callback.update(80, "正在处理伏笔数据...")
        
        foreshadowings = json.loads(response.text)
        if not isinstance(foreshadowings, list):
            raise Exception("返回的数据格式不正确")
        
        if progress_callback:
            progress_callback.update(100, "伏笔生成完成")
        
        return foreshadowings
        
    except Exception as e:
        raise Exception(f"生成伏笔失败: {str(e)}")


def modify_outline_by_dialogue(
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
    """通过对话修改大纲并联动更新相关设定"""
    try:
        if progress_callback:
            progress_callback.update(10, "开始分析修改请求...")
        
        # 构建提示词
        characters_text = "；".join([f"{c.get('name', '')}（{c.get('role', '')}）：{c.get('personality', '')}" for c in characters[:10]]) if characters else "暂无"
        world_text = "；".join([f"{w.get('title', '')}（{w.get('category', '')}）：{w.get('description', '')[:100]}" for w in world_settings[:10]]) if world_settings else "暂无"
        timeline_text = "；".join([f"[{t.get('time', '')}] {t.get('event', '')}" for t in timeline[:10]]) if timeline else "暂无"
        
        prompt = f"""你是一名资深小说编辑，用户想要修改小说《{title}》的大纲。

当前小说信息：
类型：{genre}
简介：{synopsis}

当前完整大纲：
{current_outline[:3000]}{'...' if len(current_outline) > 3000 else ''}

当前角色列表：
{characters_text}

当前世界观设定：
{world_text}

当前时间线事件：
{timeline_text}

用户修改请求：{user_message}

请根据用户的修改请求，生成修改后的内容。你需要：
1. 分析用户的需求，理解要修改的内容
2. 生成修改后的完整大纲（保持原有结构，只修改需要改变的部分）
3. 如果涉及到卷结构的修改，生成更新后的卷列表（JSON数组格式）
4. 如果涉及到角色的新增或修改，生成更新后的角色列表（JSON数组格式）
5. 如果涉及到世界观的修改，生成更新后的世界观设定列表（JSON数组格式）
6. 如果涉及到时间线的调整，生成更新后的时间线事件列表（JSON数组格式）
7. 生成一个变更说明列表（JSON数组，每个元素是一个变更描述字符串）

请以 JSON 格式返回，包含以下字段：
- "outline": 修改后的完整大纲（字符串）
- "volumes": 修改后的卷列表（JSON数组，可选，每个对象包含 "title" 和 "summary"）
- "characters": 修改后的角色列表（JSON数组，可选，每个对象包含 "name", "age", "role", "personality", "background", "goals"）
- "world_settings": 修改后的世界观设定列表（JSON数组，可选，每个对象包含 "title", "category", "description"）
- "timeline": 修改后的时间线事件列表（JSON数组，可选，每个对象包含 "time", "event", "impact"）
- "changes": 变更说明列表（JSON数组，每个元素是字符串）

只返回 JSON 对象，不要包含其他文字说明。"""
        
        if progress_callback:
            progress_callback.update(30, "正在调用 AI 分析并生成修改方案...")
        
        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.8,
                "max_output_tokens": 16384,
            }
        )
        
        if not response.text:
            raise Exception("API 返回空响应")
        
        if progress_callback:
            progress_callback.update(70, "正在处理生成结果...")
        
        result = json.loads(response.text)
        
        # 确保返回的数据格式正确
        if not isinstance(result, dict):
            raise Exception("返回的数据格式不正确，应为 JSON 对象")
        
        # 验证必需字段
        if "outline" not in result:
            raise Exception("返回数据中缺少 outline 字段")
        
        # 确保可选字段为列表或 None
        if "volumes" in result and result["volumes"] is not None and not isinstance(result["volumes"], list):
            result["volumes"] = None
        if "characters" in result and result["characters"] is not None and not isinstance(result["characters"], list):
            result["characters"] = None
        if "world_settings" in result and result["world_settings"] is not None and not isinstance(result["world_settings"], list):
            result["world_settings"] = None
        if "timeline" in result and result["timeline"] is not None and not isinstance(result["timeline"], list):
            result["timeline"] = None
        if "changes" not in result or not isinstance(result.get("changes"), list):
            result["changes"] = []
        
        if progress_callback:
            progress_callback.update(100, "修改方案生成完成")
        
        return result
        
    except json.JSONDecodeError as e:
        raise Exception(f"解析 JSON 响应失败: {str(e)}")
    except Exception as e:
        raise Exception(f"修改大纲失败: {str(e)}")


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

