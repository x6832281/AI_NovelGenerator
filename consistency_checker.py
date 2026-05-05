# consistency_checker.py
# -*- coding: utf-8 -*-
from llm_adapters import create_llm_adapter
import logging
import re

logging.basicConfig(
    filename='app.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

CAMPUS_STYLE_RULES = """
【风格一致性检查规则 —— 村上春树底色 · 分层融合体系】

一、底色层检查（村上春树·必须全文统一）：
  1. 句子节奏：是否保持短句为主、句号多于逗号的呼吸感？
  2. 比喻修辞：是否出现陈旧比喻（如"心如刀割""泪如雨下"）？应该用具体场景替代
  3. 克制深情：是否出现直白的情感宣泄（如"我很难过""心碎了"）？应该用行动和沉默表达
  4. 感官精确：重要场景是否至少动用了三种感官描写？
  5. 对话风格：对话是否简洁且有潜台词？是否出现冗长的直白对白？

二、刀锋层检查（太宰治·频率控制）：
  1. 本章是否出现了太宰式笔法？（自我解剖、温柔绝望、句子突然变长变密）
  2. 如果出现，是否超过一处？（每章最多一处）
  3. 出现场景是否符合要求？（独处自省/面具裂开/信任破碎/告别）
  4. 太宰式笔法是否侵入了日常叙事段落？（不应该）

三、内容策略检查（八月长安·选材）：
  1. 是否有"小事大写"的选材？（换座位/占座/食堂排队等日常事件）
  2. 是否有过度戏剧化的情节？（车祸/绝症/第三者等校园青春不应有的桥段）
  3. 暗恋描写是否含蓄而精确？（应该通过行为而非直白语言表达）

四、辅助层检查：
  1. 是否有具体的年代标记？（歌名/电影/手机型号/流行语）
  2. 是否有经济差距/家庭压力的社会观察细节？
  3. 是否有信物意象的运用？

五、禁止项检查：
  1. 是否出现网络用语（如"yyds""绝绝子""emo了"）？
  2. 是否出现过度口语化的表达（如"哈哈哈哈""好家伙"）？
  3. 是否出现过于华丽的形容词堆砌？
  4. 是否有不自然的情感跳跃？（情感变化应如潮汐般缓慢）
"""

CONSISTENCY_PROMPT = """\
你是一位严谨的校园青春小说审校编辑，需要从两个维度检查最新章节：
A. 剧情一致性（设定/角色/时间线/伏笔）
B. 风格一致性（分层融合风格体系的遵守情况）

═══ 小说设定 ═══
{novel_setting}

═══ 角色状态 ═══
{character_state}

═══ 前文摘要 ═══
{global_summary}

═══ 未解决冲突/剧情要点 ═══
{plot_arcs}

═══ 最新章节内容 ═══
{chapter_text}

═══ 风格检查规则 ═══
{style_rules}

请按以下格式输出检查结果：

【A. 剧情一致性】
- 冲突项（如有）：列出具体冲突
- 被忽略的伏笔（如有）：列出需要推进的伏笔
- 若无问题：无明显冲突

【B. 风格一致性】
- 底色层（村上）：是否保持统一语调？有无违反项？
- 刀锋层（太宰）：本章是否使用了太宰式笔法？频率是否合规？
- 内容策略（八月）：选材是否符合"小事大写"哲学？
- 禁止项：是否有网络用语/过度口语化/华丽堆砌？
- 若无问题：风格一致性良好

【C. 综合建议】（如有需要改进的地方，给出1-3条具体建议）
"""


def check_consistency(
    novel_setting: str,
    character_state: str,
    global_summary: str,
    chapter_text: str,
    api_key: str,
    base_url: str,
    model_name: str,
    temperature: float = 0.3,
    plot_arcs: str = "",
    interface_format: str = "OpenAI",
    max_tokens: int = 2048,
    timeout: int = 600,
    enable_style_check: bool = True
) -> str:
    """
    检查章节的剧情一致性和风格一致性。
    enable_style_check: 是否启用风格一致性检查（校园模式默认开启）
    """
    if not novel_setting:
        novel_setting = "（设定信息未提供）"
    if not plot_arcs:
        plot_arcs = "（无记录）"

    style_rules = CAMPUS_STYLE_RULES if enable_style_check else "（风格检查已禁用）"

    prompt = CONSISTENCY_PROMPT.format(
        novel_setting=novel_setting,
        character_state=character_state,
        global_summary=global_summary,
        plot_arcs=plot_arcs,
        chapter_text=chapter_text,
        style_rules=style_rules
    )

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )

    logging.info(f"[ConsistencyChecker] 开始检查，章节长度: {len(chapter_text)} 字")

    response = llm_adapter.invoke(prompt)
    if not response:
        return "审校Agent无回复"

    logging.info(f"[ConsistencyChecker] 检查完成，响应长度: {len(response)} 字")
    return response


def quick_style_scan(chapter_text: str) -> dict:
    """
    无需LLM的快速风格扫描，检测明显的风格违规。
    返回 {issue_type: [issues]} 字典。
    """
    issues = {}

    banned_slang = [
        "yyds", "绝绝子", "emo了", "破防了", "DNA动了", "家人们",
        "集美", "老铁", "666", "奥利给", "干饭人", "打工人",
        "哈哈哈哈", "哈哈哈哈哈", "好家伙", "绝了", "牛逼", "卧槽",
        "我靠", "我天", "妈呀", "救命", "笑死", "裂开"
    ]
    found_slang = [s for s in banned_slang if s in chapter_text]
    if found_slang:
        issues["网络用语/过度口语"] = found_slang

    cliche_metaphors = [
        "心如刀割", "泪如雨下", "肝肠寸断", "撕心裂肺",
        "痛不欲生", "心碎了一地", "心在滴血", "刻骨铭心",
        "海誓山盟", "天长地久", "至死不渝", "一见钟情"
    ]
    found_cliche = [m for m in cliche_metaphors if m in chapter_text]
    if found_cliche:
        issues["陈旧比喻/直白抒情"] = found_cliche

    direct_emotion = [
        "我很难过", "我非常伤心", "我心碎了", "我崩溃了",
        "我很痛苦", "我绝望了", "我哭了", "我忍不住哭了"
    ]
    found_direct = [e for e in direct_emotion if e in chapter_text]
    if found_direct:
        issues["直白情感宣泄"] = found_direct

    dazai_markers = [
        "抱歉", "不配", "面具", "生而为人",
        "果然如此", "果然还是", "不理解", "不明白为什么"
    ]
    dazai_count = sum(1 for m in dazai_markers if m in chapter_text)
    if dazai_count >= 3:
        issues["太宰式笔法疑似过频"] = [f"检测到 {dazai_count} 个太宰式标记词"]

    paragraphs = [p.strip() for p in chapter_text.split("\n\n") if p.strip()]
    long_sentences = 0
    for p in paragraphs:
        for sent in p.split("。"):
            if len(sent) > 80:
                long_sentences += 1
    if long_sentences > len(paragraphs) * 0.5 and len(paragraphs) > 3:
        issues["句子过长"] = [f"有 {long_sentences} 个超长句(>80字)，可能缺乏村上式呼吸感"]

    return issues
