"""Gemini API 服务模块"""
import os
import json
import logging
from typing import Optional, AsyncGenerator
from google import genai
from core.config import GEMINI_API_KEY, GEMINI_PROXY

# 初始化 Gemini 客户端
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY 未配置，请在 .env 文件中设置")

# 配置代理（如果设置了 GEMINI_PROXY）
# Google genai 客户端使用 httpx，会读取 HTTP_PROXY 和 HTTPS_PROXY 环境变量
if GEMINI_PROXY:
    # 确保代理地址格式正确（http:// 或 https://）
    proxy_url = GEMINI_PROXY.strip()
    if not proxy_url.startswith(('http://', 'https://', 'socks5://', 'socks5h://')):
        proxy_url = f"http://{proxy_url}"
    
    os.environ['HTTP_PROXY'] = proxy_url
    os.environ['HTTPS_PROXY'] = proxy_url
    # httpx 也支持 ALL_PROXY
    os.environ['ALL_PROXY'] = proxy_url
    
    logger = logging.getLogger(__name__)
    logger.info(f"✅ Gemini API 代理已配置: {proxy_url}")
    logger.info(f"   环境变量 HTTP_PROXY={os.environ.get('HTTP_PROXY')}")
    logger.info(f"   环境变量 HTTPS_PROXY={os.environ.get('HTTPS_PROXY')}")

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

        def ensure_text_length_range(
            text: str,
            *,
            min_chars: int,
            max_chars: int,
            title: str,
            genre: str,
            synopsis: str,
            progress_callback=None
        ) -> str:
            """确保文本长度处于范围内；过短则扩写，过长则压缩。"""
            if not text:
                text = ""

            def within_range(s: str) -> bool:
                return min_chars <= len(s) <= max_chars

            # 最多做两次修正，避免死循环
            for attempt in range(2):
                if within_range(text):
                    return text

                is_too_short = len(text) < min_chars
                if progress_callback:
                    action = "扩写" if is_too_short else "压缩"
                    progress_callback.update(
                        20 + attempt * 10,
                        f"正在按字数要求{action}大纲（目标 {min_chars}-{max_chars} 字）..."
                    )

                refine_prompt = f"""你是资深小说总编剧。请对下面的大纲进行“{('扩写' if is_too_short else '压缩')}与整理”，并严格满足字数范围要求。

【硬性字数要求】
- 最终输出必须在 {min_chars}-{max_chars} 字之间（以字符数近似计算）
- 必须少于等于 {max_chars} 字

【内容要求】
- 保留并强化可指导分卷/分章的细节：因果链、转折点、角色抉择、关键事件、伏笔与回收
- 保持结构清晰（分级标题/编号列表）
- 不要输出任何解释、前后对比、或统计信息，只输出最终大纲正文

【小说信息】
标题：{title}
类型：{genre}
初始创意：{synopsis}

【当前大纲】
{text}
"""

                refine_response = client.models.generate_content(
                    model="gemini-3-pro-preview",
                    contents=refine_prompt,
                    config={
                        "temperature": 0.3,
                        "max_output_tokens": 8192,
                    },
                )

                text = refine_response.text if refine_response.text else text

            # 兜底：仍然过长则硬截断（尽量保证不超标）
            if len(text) > max_chars:
                return text[:max_chars]
            return text

        # 生成完整大纲
        outline_prompt = f"""你是一名资深小说策划与总编剧，请为小说《{title}》创作“尽可能详细、可直接指导分卷与分章”的完整大纲。

【作品信息】
类型：{genre}
一句话/初始创意：{synopsis}

【字数要求】
- 最终输出控制在 6000-10000 字之间（不得超过 10000 字）

【输出要求（越详细越好）】
1) 故事核心（不超过200字）
   - 核心矛盾、主题母题、情感主线、主角欲望与代价
2) 世界观与规则（可落地）
   - 关键设定/规则清单（至少10条），包括：边界、代价、限制、常识、潜规则
3) 主要角色档案（至少6个）
   - 角色定位、动机/恐惧、秘密、成长弧线、与主角关系、关键抉择点
4) 全书结构（多幕结构）
   - 按“序幕/第一幕/第二幕上/第二幕下/第三幕/尾声”给出：
     * 每幕目标、对抗、转折点、胜负与代价
5) 关键事件时间线
   - 以“编号+事件+参与者+因果+对后续影响”的方式列出至少25条（从开端到结局）
6) 伏笔与回收（必须可执行）
   - 伏笔清单（至少12条）：埋下位置/表现形式/回收位置/回收方式/情感或逻辑收益
7) 分卷规划（为后续生成卷大纲和章节列表服务）
   - 建议卷数：3-8卷（如果故事体量需要也可以更多，但必须解释原因）
   - 每卷写清：卷主题、主冲突、关键转折、高潮、卷结尾状态变化
   - 每卷至少给出8-15个“剧情节点”（节点=可拆成章节的事件），并标注：
     * 节点目标/冲突/结果/推进了什么人物弧线/留下或回收了什么伏笔

【重要约束】
- 大纲必须自洽、因果清晰、可直接拆分为章节，不要空泛口号
- 不要只写梗概；要写“事件链+转折点+角色抉择”
- 使用清晰的分级标题与编号列表，方便后续程序解析与引用
"""
        
        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=outline_prompt,
            config={
                "temperature": 0.75,
                "max_output_tokens": 16384,
            }
        )
        
        full_outline = response.text if response.text else ""
        full_outline = ensure_text_length_range(
            full_outline,
            min_chars=6000,
            max_chars=10000,
            title=title,
            genre=genre,
            synopsis=synopsis,
            progress_callback=progress_callback
        )
        
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
        # 检查是否是地理位置限制错误
        error_msg = str(e)
        if "location is not supported" in error_msg or "FAILED_PRECONDITION" in error_msg:
            friendly_msg = "抱歉，服务器所在地区暂不支持 Gemini API 服务。请联系管理员检查服务器配置，或考虑使用代理服务器。"
            raise Exception(f"生成大纲失败: {friendly_msg}")
        raise Exception(f"生成大纲失败: {error_msg}")


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
        
        volume_prompt = f"""你是一名资深小说策划，请为《{novel_title}》的第 {volume_index + 1} 卷《{volume_title}》生成“足够详细、可直接拆分为章节”的卷详细大纲。

【全书完整大纲（节选）】
{full_outline[:2500]}

【本卷信息】
标题：{volume_title}
{f'描述：{volume_summary}' if volume_summary else ''}

【主要角色（节选）】
{characters_text}

【输出要求（越具体越好）】
1) 本卷定位
   - 卷主题、主冲突、核心悬念、情绪曲线、与全书主线的承接点
2) 本卷结构（起承转合/多幕）
   - 至少列出：导入、第一次转折、中点、第二次转折、高潮、收束，并写清“因果与代价”
3) 本卷剧情节点清单（必须可拆章）
   - 至少12-25个节点，按顺序编号，每个节点包含：
     * 节点目标/对抗点/关键行动/结果/新的信息或反转/人物弧线变化/伏笔埋或收
4) 本卷关键场景建议（可选但建议）
   - 列出至少8个“必须出现的场景/对手戏”，写清场景目的与冲突
5) 卷末状态
   - 本卷结束时：主角/反派/世界局势分别处于什么新状态？下一卷的矛盾从哪里自然长出？

【字数与章节规划（必须给出具体数字）】
- 估算本卷合理字数范围（通常每卷15-30万字，可因类型调整）
- 章节数必须是具体数字，不要范围
- 请在末尾用固定格式输出：
【字数规划】：XX-XX万字
【章节规划】：XX章
"""
        
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
        # 检查是否是地理位置限制错误
        error_msg = str(e)
        if "location is not supported" in error_msg or "FAILED_PRECONDITION" in error_msg:
            friendly_msg = "抱歉，服务器所在地区暂不支持 Gemini API 服务。请联系管理员检查服务器配置，或考虑使用代理服务器。"
            error_data = json.dumps({"error": friendly_msg})
            yield f"data: {error_data}\n\n"
            raise Exception(f"生成卷大纲失败: {friendly_msg}")
        
        # 发送错误信息
        error_data = json.dumps({"error": error_msg})
        yield f"data: {error_data}\n\n"
        raise Exception(f"生成卷大纲失败: {error_msg}")


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
        
        volume_prompt = f"""你是一名资深小说策划，请为《{novel_title}》的第 {volume_index + 1} 卷《{volume_title}》生成“足够详细、可直接拆分为章节”的卷详细大纲。

【全书完整大纲（节选）】
{full_outline[:2500]}

【本卷信息】
标题：{volume_title}
{f'描述：{volume_summary}' if volume_summary else ''}

【主要角色（节选）】
{characters_text}

【输出要求（越具体越好）】
1) 本卷定位
   - 卷主题、主冲突、核心悬念、情绪曲线、与全书主线的承接点
2) 本卷结构（起承转合/多幕）
   - 至少列出：导入、第一次转折、中点、第二次转折、高潮、收束，并写清“因果与代价”
3) 本卷剧情节点清单（必须可拆章）
   - 至少12-25个节点，按顺序编号，每个节点包含：
     * 节点目标/对抗点/关键行动/结果/新的信息或反转/人物弧线变化/伏笔埋或收
4) 本卷关键场景建议（可选但建议）
   - 列出至少8个“必须出现的场景/对手戏”，写清场景目的与冲突
5) 卷末状态
   - 本卷结束时：主角/反派/世界局势分别处于什么新状态？下一卷的矛盾从哪里自然长出？

【字数与章节规划（必须给出具体数字）】
- 估算本卷合理字数范围（通常每卷15-30万字，可因类型调整）
- 章节数必须是具体数字，不要范围
- 请在末尾用固定格式输出：
【字数规划】：XX-XX万字
【章节规划】：XX章
"""
        
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
        # 检查是否是地理位置限制错误
        error_msg = str(e)
        if "location is not supported" in error_msg or "FAILED_PRECONDITION" in error_msg:
            friendly_msg = "抱歉，服务器所在地区暂不支持 Gemini API 服务。请联系管理员检查服务器配置，或考虑使用代理服务器。"
            raise Exception(f"生成卷大纲失败: {friendly_msg}")
        raise Exception(f"生成卷大纲失败: {error_msg}")


def generate_chapter_outline(
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
            chapter_count_instruction = f"""请为本卷生成 {chapter_count} 个章节。

【章节生成策略】
1. 首先基于卷大纲中的主线剧情生成章节（优先覆盖卷大纲中的所有主要情节点）
2. 如果主线剧情生成的章节数不足 {chapter_count} 个，请补充支线剧情章节来凑足数量
3. 支线剧情章节应该：
   - 与主线剧情相关，但不能是后续卷的内容
   - 可以是角色互动、日常描写、世界观展示、配角故事等
   - 必须在当前卷的时间线和故事范围内
   - 应该丰富故事的层次感，不要显得突兀
4. 最终生成的章节总数必须达到 {chapter_count} 个"""
        else:
            chapter_count_instruction = """请仔细分析本卷的详细大纲，根据以下原则确定合适的章节数量并生成章节列表：
章节数量应该：
1. 优先参考卷大纲中标注的【章节规划】（如果存在）
2. 根据卷大纲的内容复杂度和字数规划合理分配
3. 确保每个章节有足够的内容和情节发展（每章5000-8000字，即0.5-0.8万字）
4. 如果大纲中有字数规划，按照每章5000-8000字的标准计算章节数
5. 如果大纲中明确提到了章节数，请参考该数量
6. 如果大纲中没有明确提到，请根据情节结构合理分配（通常每章对应一个主要事件或情节转折点）
7. 如果基于主线剧情确定的章节数偏少，可以适当增加支线剧情章节（角色互动、日常描写、世界观展示等）来丰富内容
8. 章节数量应在合理范围内（建议6-30章）"""
        
        volume_desc = f"卷描述：{volume_summary[:200]}" if volume_summary else ""
        volume_outline_text = f"卷详细大纲：{volume_outline[:2500]}" if volume_outline else ""
        
        # 构建前面卷的参考信息（用于确保连贯性）
        previous_volumes_section = ""
        if volume_index > 0 and previous_volumes_info:
            previous_volumes_section = "\n【前面卷的参考信息】（用于确保情节连贯，不要重复这些内容）\n"
            for prev_vol_info in previous_volumes_info:
                prev_vol_title = prev_vol_info.get("title", "")
                prev_vol_summary = prev_vol_info.get("summary", "")
                prev_chapters = prev_vol_info.get("chapters", [])
                
                previous_volumes_section += f"\n{prev_vol_title}：\n"
                if prev_vol_summary:
                    previous_volumes_section += f"  卷描述：{prev_vol_summary[:200]}\n"
                if prev_chapters:
                    previous_volumes_section += "  已发生章节（标题 - 摘要，避免重复）：\n"
                    for ch in prev_chapters[:12]:
                        ch_title = ch.get("title", "")
                        ch_summary = (ch.get("summary", "") or "")[:120]
                        if ch_title and ch_summary:
                            previous_volumes_section += f"   - {ch_title}：{ch_summary}\n"
                        elif ch_title:
                            previous_volumes_section += f"   - {ch_title}\n"
            
            previous_volumes_section += "\n重要：你必须承接这些已发生事件，但不要重复同类冲突/同一事件的再讲一遍。\n"

        # 构建后续卷的“禁止提前”信息（用于避免串到后面卷）
        future_volumes_section = ""
        if future_volumes_info:
            future_volumes_section = "\n【后续卷规划（禁止提前使用）】\n"
            for next_vol in future_volumes_info[:3]:
                next_title = next_vol.get("title", "")
                next_summary = (next_vol.get("summary", "") or "")[:240]
                next_outline = (next_vol.get("outline", "") or "")[:500]
                if next_title:
                    future_volumes_section += f"\n{next_title}：\n"
                    if next_summary:
                        future_volumes_section += f"  规划简介：{next_summary}\n"
                    if next_outline:
                        future_volumes_section += f"  规划要点（摘要）：{next_outline}\n"
            future_volumes_section += "\n重要：以上内容仅用于“避雷”。本卷不得出现这些卷的主要事件、关键反转或结局信息。\n"
        
        prompt = f"""基于以下信息，为第 {volume_index + 1} 卷《{volume_title}》生成章节列表：

【⚠️ 严格限制】
你只能生成第 {volume_index + 1} 卷《{volume_title}》的章节列表，绝对不要包含后续卷的情节！
所有章节的内容必须严格限制在本卷的范围内，不得涉及后续卷的剧情发展或预告！

【小说基本信息】
标题：{novel_title}
类型：{genre}
{previous_volumes_section}
{future_volumes_section}
【本卷详细信息】（这是你需要生成章节的依据）
{volume_desc}
{volume_outline_text}{word_count_info}

【角色信息】
{characters_text}

【生成要求】
{chapter_count_instruction}

【重要约束】
- 每一章必须能在“卷详细大纲”中找到对应的情节点/段落依据（不允许编造后续卷事件）
- chapter.title 只能写“章节标题文本”，不要包含“第X章/第 X 章/1.”等编号前缀（编号由系统生成）
- 如果提供了【前面卷的参考信息】，第1章必须承接上一卷结尾的“状态/矛盾/悬念”，但不得复述上一卷已发生内容（最多用1-2句带过）
- 章节标题和摘要必须只涉及本卷的内容，绝对不要包含后续卷的情节
- 不得包含后续卷的剧情预告、情节铺垫或结局暗示（包括“下一卷/未来/终局/最终BOSS”等）
- 章节顺序必须体现本卷内部的递进：引入矛盾 → 升级推进 → 高潮/关键转折 → 收束
- 本卷的主要冲突应在本卷内闭合；允许留下“轻微悬念”，但不得把下一卷主线提前展开
- 每个章节都应该是本卷的独立故事单元
- 章节的结尾应该是本卷的情节收束，不要为后续卷埋下伏笔
- 如果本卷大纲中提到了后续卷的内容，请忽略它们，只关注本卷的描述
{f"- 必须与前面卷的情节保持连贯，承接前面卷的故事发展" if volume_index > 0 else ""}
{f"- 不要重复前面卷已经发生的情节和事件" if volume_index > 0 else ""}
{f"- 本卷章节应该是在前面卷基础上的自然延续和发展" if volume_index > 0 else ""}

【支线剧情使用说明】
如果主线剧情章节数量不够，可以使用以下类型的支线剧情章节来补充：
- 角色日常互动、对话场景
- 角色心理描写、回忆片段
- 世界观细节展示（环境、规则、历史等）
- 配角的故事线或背景补充
- 情感线的推进（友情、亲情、爱情等）
- 小冲突的解决或新矛盾的引入（但必须是本卷能解决的）
重要：支线剧情必须在当前卷的时间范围内，不能是后续卷的内容，也不能重复前面卷已经发生的情节。

仅返回 JSON 数组，每个对象包含以下键："title"（标题，不要带章节编号）、"summary"（摘要）、"aiPromptHints"（AI提示）。"""
        
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
    db_session=None,
    forced_previous_chapter_context: Optional[str] = None
):
    """生成章节内容（流式）"""
    try:
        characters_text = "；".join([f"{c.get('name', '')}：{c.get('personality', '')}" for c in characters]) if characters else "暂无"
        world_text = "；".join([f"{w.get('title', '')}：{w.get('description', '')}" for w in world_settings]) if world_settings else "暂无"
        
        # 获取当前卷信息（用于限制内容范围）
        current_volume_info = None
        current_volume_index = None
        if novel_id and db_session:
            try:
                from sqlalchemy.orm import Session
                from models import Chapter, Volume
                
                # 尝试通过chapter_id查找所属的卷
                if current_chapter_id:
                    chapter_obj = db_session.query(Chapter).filter(Chapter.id == current_chapter_id).first()
                    if chapter_obj:
                        volume_obj = db_session.query(Volume).filter(Volume.id == chapter_obj.volume_id).first()
                        if volume_obj:
                            current_volume_info = {
                                "title": volume_obj.title,
                                "summary": volume_obj.summary or "",
                                "outline": volume_obj.outline or "",
                                "volume_index": volume_obj.volume_order
                            }
                            current_volume_index = volume_obj.volume_order
                else:
                    # 如果沒有chapter_id，尝试通过章节标题查找（模糊匹配）
                    chapter_obj = db_session.query(Chapter).join(Volume).filter(
                        Volume.novel_id == novel_id,
                        Chapter.title.like(f"%{chapter_title}%")
                    ).first()
                    if chapter_obj:
                        volume_obj = db_session.query(Volume).filter(Volume.id == chapter_obj.volume_id).first()
                        if volume_obj:
                            current_volume_info = {
                                "title": volume_obj.title,
                                "summary": volume_obj.summary or "",
                                "outline": volume_obj.outline or "",
                                "volume_index": volume_obj.volume_order
                            }
                            current_volume_index = volume_obj.volume_order
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"⚠️  获取卷信息失败: {str(e)}")
        
        # 新增：使用向量检索获取智能上下文（如果提供了 novel_id 和 db_session）
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
                        import logging
                        logging.getLogger(__name__).warning(f"⚠️  相似度警告: {similarity_result.get('warnings', [])}")
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"⚠️  相似度检查失败（继续生成）: {str(e)}")
                
                # 获取智能上下文（只获取当前卷及之前卷的章节，避免后续卷内容干扰）
                checker = ConsistencyChecker()
                # 如果有当前卷信息，只查找当前卷及之前卷的章节
                exclude_volume_indices = None
                if current_volume_index is not None:
                    # 排除后续卷的章节（通过查询时排除volume_order > current_volume_index的章节）
                    # 这需要在find_similar_chapters中实现，暂时先获取所有，后续优化
                    pass
                
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
        
        # 优先使用强制上下文（当前章节内容）
        if forced_previous_chapter_context and forced_previous_chapter_context.strip():
            previous_context_section = f"""

{forced_previous_chapter_context}

⚠️ 重要：这是上一章的结尾内容，下一章必须自然承接这个结尾，不能出现情节跳跃或逻辑断裂。
"""
        
        # 添加向量检索的其他相关章节（作为参考）
        if previous_chapters_context and previous_chapters_context.strip():
            if previous_context_section:
                previous_context_section += f"""

【相关前文参考】（基于向量相似度智能推荐的其他相关章节）：
{previous_chapters_context}
"""
            else:
                previous_context_section = f"""

【前文内容参考】（基于向量相似度智能推荐的相关章节）：
{previous_chapters_context}
"""
        
        # 添加重复内容检查要求
        if previous_context_section:
            previous_context_section += """

🚨 【重复内容检查要求】- 必须严格遵守：
1. ❌ 绝对禁止：重复前文中已经完整描述过的场景、事件、对话
2. ❌ 绝对禁止：使用与前文相同的叙事结构、描写手法、语言风格
3. ❌ 绝对禁止：让角色重复做过的事情或说过类似的话
4. ✅ 正确做法：如需提及前文，仅用1-2句简短过渡，不展开描写
5. ✅ 正确做法：本章必须推进全新情节，展现新的冲突和发展
6. ✅ 正确做法：采用不同的叙述视角、情绪基调、描写重点
7. ✅ 正确做法：确保本章有独特的核心事件，与前文明显区分

⚠️ 注意：请认真阅读上述前文内容，确保本章内容完全原创且与前文连贯。
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
        # 检查是否是地理位置限制错误
        error_msg = str(e)
        if "location is not supported" in error_msg or "FAILED_PRECONDITION" in error_msg:
            friendly_msg = "抱歉，服务器所在地区暂不支持 Gemini API 服务。请联系管理员检查服务器配置，或考虑使用代理服务器。"
            error_data = json.dumps({"error": friendly_msg})
            yield f"data: {error_data}\n\n"
            raise Exception(f"生成章节内容失败: {friendly_msg}")
        
        # 发送错误信息
        error_data = json.dumps({"error": error_msg})
        yield f"data: {error_data}\n\n"
        raise Exception(f"生成章节内容失败: {error_msg}")


def write_chapter_content(
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
    """生成章节内容（非流式，返回完整文本）"""
    try:
        if progress_callback:
            progress_callback.update(10, "开始生成章节内容...")
        
        characters_text = "；".join([f"{c.get('name', '')}：{c.get('personality', '')}" for c in characters]) if characters else "暂无"
        world_text = "；".join([f"{w.get('title', '')}：{w.get('description', '')}" for w in world_settings]) if world_settings else "暂无"
        
        # 使用向量检索获取智能上下文（如果提供了 novel_id 和 db_session）
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
                        import logging
                        logging.getLogger(__name__).warning(f"⚠️  相似度警告: {similarity_result.get('warnings', [])}")
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"⚠️  相似度检查失败（继续生成）: {str(e)}")
                
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
                    previous_chapters_context = smart_context
                    import logging
                    logging.getLogger(__name__).info(f"✅ 使用智能上下文检索，找到 {len(smart_context.split('---'))} 个相关章节")
            except Exception as e:
                # 如果向量检索失败，使用原始上下文，不影响主流程
                import logging
                logging.getLogger(__name__).warning(f"⚠️  智能上下文检索失败，使用原始上下文: {str(e)}")
        
        # 从chapter_prompt_hints中提取上一章的钩子（如果有）
        previous_chapter_hook = ""
        if chapter_prompt_hints and "【上一章钩子】" in chapter_prompt_hints:
            hook_part = chapter_prompt_hints.split("【上一章钩子】")
            if len(hook_part) > 1:
                previous_chapter_hook = hook_part[-1].strip()
        elif chapter_prompt_hints and "【下一章钩子】" in chapter_prompt_hints:
            # 兼容旧格式
            hook_part = chapter_prompt_hints.split("【下一章钩子】")
            if len(hook_part) > 1:
                previous_chapter_hook = hook_part[-1].strip()
        
        # 构建前文上下文部分
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
        
        # 构建上一章钩子部分
        previous_hook_section = ""
        if previous_chapter_hook:
            previous_hook_section = f"""

【上一章结尾钩子】（必须承接）：
{previous_chapter_hook}

⚠️ 重要：上一章结尾留下了这个悬念/转折点，本章开头必须自然承接这个钩子，但不能直接重复上一章的结尾内容。应该：
1. 用1-2句话简短呼应上一章的钩子
2. 然后立即推进新的情节发展
3. 不要让读者感觉重复或拖沓
"""
        
        # 清理chapter_prompt_hints，移除钩子标记（钩子已经在previous_hook_section中单独处理）
        clean_prompt_hints = chapter_prompt_hints or ""
        if clean_prompt_hints:
            # 移除钩子标记，保留其他提示
            clean_prompt_hints = clean_prompt_hints.replace("【下一章钩子】", "").replace("【上一章钩子】", "").strip()
            # 清理多余的空行
            clean_prompt_hints = "\n".join([line for line in clean_prompt_hints.split("\n") if line.strip()])
        
        prompt = f"""请为小说《{novel_title}》创作一个完整的章节。

【章节基本信息】
- 标题：{chapter_title}
- 情节摘要：{chapter_summary}
{f"- 写作提示：{clean_prompt_hints}" if clean_prompt_hints else ""}
{previous_hook_section}

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
        
        if progress_callback:
            progress_callback.update(50, "正在调用AI生成章节内容...")
        
        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=prompt,
            config={
                "temperature": 0.9,
                "max_output_tokens": 16384,
            }
        )
        
        if not response.text:
            raise Exception("API 返回空响应")
        
        if progress_callback:
            progress_callback.update(90, "章节内容生成完成")
        
        return response.text
                
    except Exception as e:
        # 检查是否是地理位置限制错误
        error_msg = str(e)
        if "location is not supported" in error_msg or "FAILED_PRECONDITION" in error_msg:
            friendly_msg = "抱歉，服务器所在地区暂不支持 Gemini API 服务。请联系管理员检查服务器配置，或考虑使用代理服务器。"
            raise Exception(f"生成章节内容失败: {friendly_msg}")
        raise Exception(f"生成章节内容失败: {error_msg}")


def summarize_chapter_content(chapter_title: str, chapter_content: str, max_len: int = 400) -> str:
    """
    生成章节摘要，控制在约 max_len 字以内；失败则返回截断内容
    """
    if not chapter_content:
        return ""
    try:
        prompt = f"""请为以下章节内容生成简明摘要（200-400字），保留主要冲突、关键事件、角色状态变化。仅输出摘要文本。

章节标题：{chapter_title}
章节内容：
{chapter_content[:4000]}
"""
        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=prompt,
            config={
                "temperature": 0.25,
                "max_output_tokens": 512,
            },
        )
        summary = response.text or ""
        summary = summary.strip()
        if len(summary) > max_len:
            summary = summary[:max_len]
        return summary
    except Exception as e:
        logging.getLogger(__name__).warning(f"章节摘要生成失败，使用截断: {str(e)}")
        content = chapter_content.strip()
        if len(content) <= max_len:
            return content
        return content[:max_len - 10] + "..."


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

        def parse_requested_volume_count(message: str) -> Optional[int]:
            if not message:
                return None
            import re
            patterns = [
                r"(?:增加|新增|扩展|添加|补充|改为|改成|调整为|变为)\s*(\d{1,3})\s*(?:个)?\s*卷",
                r"(\d{1,3})\s*(?:个)?\s*卷",
            ]
            for pattern in patterns:
                match = re.search(pattern, message)
                if match:
                    try:
                        value = int(match.group(1))
                        if 1 <= value <= 200:
                            return value
                    except Exception:
                        continue
            return None

        def volumes_have_range_titles(volumes: list) -> bool:
            import re
            range_pattern = re.compile(r"(?:卷)?[一二三四五六七八九十0-9]+(?:至|到|~|～|—|-)[一二三四五六七八九十0-9]+")
            for v in volumes:
                if not isinstance(v, dict):
                    continue
                title_text = (v.get("title") or "").strip()
                if not title_text:
                    continue
                if "至" in title_text or "到" in title_text or "-" in title_text or "~" in title_text or "～" in title_text or "—" in title_text:
                    if range_pattern.search(title_text):
                        return True
            return False

        requested_volume_count = parse_requested_volume_count(user_message)
        
        # 构建提示词
        characters_text = "；".join([f"{c.get('name', '')}（{c.get('role', '')}）：{c.get('personality', '')}" for c in characters[:10]]) if characters else "暂无"
        world_text = "；".join([f"{w.get('title', '')}（{w.get('category', '')}）：{w.get('description', '')[:100]}" for w in world_settings[:10]]) if world_settings else "暂无"
        timeline_text = "；".join([f"[{t.get('time', '')}] {t.get('event', '')}" for t in timeline[:10]]) if timeline else "暂无"

        volume_count_constraint = ""
        if requested_volume_count:
            volume_count_constraint = f"""

【卷数量硬约束】
用户要求卷数为 {requested_volume_count} 卷。
如果需要输出 "volumes"，必须严格输出 {requested_volume_count} 个卷对象，不能少、不能多。
严禁把多个卷合并成一个卷名（例如“卷十一至二十”“第11-20卷”等范围卷名）。
每一卷必须是一个独立条目，title 必须是单卷名称，summary 为该卷简介（50-120字）。"""
        
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
{volume_count_constraint}

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

        # 卷列表校验与修复：避免“卷十一至二十”这种范围卷名以及卷数不符合用户要求
        if requested_volume_count:
            volumes = result.get("volumes")
            if volumes is not None and isinstance(volumes, list):
                if len(volumes) != requested_volume_count or volumes_have_range_titles(volumes):
                    if progress_callback:
                        progress_callback.update(78, "检测到卷列表不符合要求，正在自动修复卷数量/卷命名...")

                    fix_prompt = f"""用户要求把《{title}》的卷结构调整为 {requested_volume_count} 卷。

你将收到当前模型给出的卷列表（可能数量不对，或出现“卷十一至二十”这类范围卷名）。
你的任务是：输出严格满足要求的新卷列表（JSON数组）。

硬约束：
1. 必须严格输出 {requested_volume_count} 个对象
2. 每个对象必须包含 "title" 与 "summary"
3. title 必须是单卷名称，严禁范围/合并卷名（例如“第11-20卷”“卷十一至二十”等）
4. 卷与卷之间要有清晰递进，summary 50-120字

当前卷列表（待修复）：
{json.dumps(volumes, ensure_ascii=False)}

只返回 JSON 数组，不要输出其他文字。"""

                    fix_response = client.models.generate_content(
                        model="gemini-3-pro-preview",
                        contents=fix_prompt,
                        config={
                            "response_mime_type": "application/json",
                            "temperature": 0.2,
                            "max_output_tokens": 8192,
                        },
                    )

                    if not fix_response.text:
                        raise Exception("卷列表修复失败：API 返回空响应")

                    fixed_volumes = json.loads(fix_response.text)
                    if not isinstance(fixed_volumes, list):
                        raise Exception("卷列表修复失败：返回格式不是 JSON 数组")
                    if len(fixed_volumes) != requested_volume_count:
                        raise Exception(f"卷列表修复失败：期望 {requested_volume_count} 卷，实际 {len(fixed_volumes)} 卷")
                    if volumes_have_range_titles(fixed_volumes):
                        raise Exception("卷列表修复失败：仍包含范围卷名")

                    result["volumes"] = fixed_volumes
                    result["changes"].append(f"已按用户要求将卷结构规范为 {requested_volume_count} 卷，并修复卷命名/数量不一致问题")
        
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


def extract_next_chapter_hook(
    title: str,
    genre: str,
    chapter_title: str,
    chapter_content: str,
    next_chapter_title: Optional[str] = None,
    next_chapter_summary: Optional[str] = None
) -> str:
    """从章节内容中提取下一章钩子（悬念、转折点等）"""
    try:
        next_chapter_info = ""
        if next_chapter_title:
            next_chapter_info = f"\n下一章标题：{next_chapter_title}"
            if next_chapter_summary:
                next_chapter_info += f"\n下一章摘要：{next_chapter_summary}"
        
        prompt = f"""基于以下章节内容，提取本章结尾的"下一章钩子"（悬念、转折点、未解之谜等，用于吸引读者继续阅读）：

小说标题：{title}
类型：{genre}
章节标题：{chapter_title}
章节内容（最后2000字）：{chapter_content[-2000:] if len(chapter_content) > 2000 else chapter_content}
{next_chapter_info}

请分析本章结尾，提取：
1. 本章结尾留下的悬念或疑问
2. 下一章可能的转折点或冲突
3. 角色状态或情节发展的关键信息
4. 吸引读者继续阅读的钩子

要求：
- 钩子应该简洁有力（50-200字）
- 应该与下一章内容相关（如果提供了下一章信息）
- 应该能够自然引导到下一章的情节

仅返回钩子文本内容（不要包含"钩子"、"悬念"等标签词），直接输出文本："""
        
        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=prompt,
            config={
                "temperature": 0.8,
                "max_output_tokens": 500,
            }
        )
        
        if not response.text:
            return ""
        
        hook = response.text.strip()
        return hook
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"提取下一章钩子失败: {str(e)}")
        return ""

