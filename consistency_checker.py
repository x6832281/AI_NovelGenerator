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

三、质感层检查（路遥·细节与质朴感）：
  1. 是否有"不评价只呈现"的细节描写？（用具体细节代替抽象评价）
  2. 是否有经济差距/家庭压力的暗线？（通过选择而非旁白呈现）
  3. 是否有中国校园特有的感官细节？（粉笔灰/食堂菜香/塑胶跑道/暖气片/油墨味）
  4. 情感爆发前是否有足够的日常铺垫？（路遥式耐心）

四、年代标记检查（八月长安·时代感）：
  1. 是否有具体的年代标记？（2011-2026年间的具体事件/产品/文化现象）
  2. 年代标记是否自然融入场景？（应为背景噪音而非新闻编年史）
  3. 是否有信物意象的运用？（霍达式情感载体）

五、禁止项检查：
  1. 是否出现网络用语（如"yyds""绝绝子""emo了"）？
  2. 是否出现过度口语化的表达（如"哈哈哈哈""好家伙"）？
  3. 是否出现过于华丽的形容词堆砌？
  4. 是否有不自然的情感跳跃？（情感变化应如潮汐般缓慢）

六、镜头语言与时间操控检查（村上高级技法）：
  1. 是否运用了镜头语言？（推镜头聚焦细节/拉镜头疏离旁观/慢镜头延长瞬间/焦点转移从物到人/长镜头全景扫描）
  2. 时间处理是否有弹性？（压缩跳过平淡/膨胀延长关键瞬间/预见性回忆暗示命运/重复变奏同一场景不同版本）
  3. 是否存在时间线混乱？（时间操控应在读者可理解范围内）

七、开头与结尾技法检查：
  1. 章节开头是否避免了"那天早上""清晨醒来"等平庸起笔？（推荐"从中间开始"：直接进入场景的第二拍）
  2. 章节结尾是否有余韵？（推荐画面定格/问题悬置/意象落点，避免总结性金句或说教式升华）
  3. 结尾是否呼应了本章核心意象？

八、意象系统与沉默留白检查：
  1. 核心意象（如考研兔子/考研教室/硬座车厢/哈尔滨的雪）是否在本章有延续或变化？
  2. 意象是否随情节发展产生新的含义层次？（意象应动态变化而非静态重复）
  3. 重要情感场景是否留出了沉默空间？（不急着解释，让读者自己感受）
  4. 留白是否适度？（过少则窒息，过多则断裂）

九、异地恋场景技法检查：
  1. 异地沟通场景是否避免了流水账式对话？（电话/微信场景应有潜台词和未说出的话）
  2. 距离感是否通过感官缺失来呈现？（如"听得到声音却闻不到气息"）
  3. 是否有各自生活的平行蒙太奇？（两地同时发生的日常形成对照）
  4. 相见/分离场景是否有足够的仪式感和克制？

十、默认分手叙事技法检查：
  1. 分手过程是否避免了戏剧化争吵？（默认分手的核心是"没有争吵，只是渐渐不联系"）
  2. 是否通过日常细节的消失来暗示关系淡化？（消息变短/电话变少/不再分享日常）
  3. 叙事语调是否保持克制？（事后回望时不应有怨恨或控诉，而是平静的遗憾）
  4. 是否留有开放性？（不急于给出"为什么分手"的明确答案）
"""

CONSISTENCY_PROMPT = """\
你是一位严谨的现实主义青春小说审校编辑，需要从两个维度检查最新章节：
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
- 质感层（路遥）：是否有"不评价只呈现"的细节？经济现实/家庭暗线/感官细节是否到位？
- 年代标记（八月）：2011-2026年时代事件是否自然融入？信物意象是否延续？
- 镜头与时间：是否运用了镜头语言？时间处理是否有弹性？
- 开头与结尾：开头是否避免平庸起笔？结尾是否有余韵？
- 意象与留白：核心意象是否延续变化？重要场景是否有沉默空间？
- 异地恋技法：沟通场景是否有潜台词？距离感是否通过感官缺失呈现？
- 默认分手技法：是否避免戏剧化争吵？语调是否克制？
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
        "我靠", "我天", "妈呀", "救命", "笑死", "裂开",
        "无语子", "下头", "上头", "社死", "摆烂", "卷王",
        "内卷", "躺平", "栓Q", "芭比Q", "真香", "暴风哭泣"
    ]
    found_slang = [s for s in banned_slang if s in chapter_text]
    if found_slang:
        issues["网络用语/过度口语"] = found_slang

    cliche_metaphors = [
        "心如刀割", "泪如雨下", "肝肠寸断", "撕心裂肺",
        "痛不欲生", "心碎了一地", "心在滴血", "刻骨铭心",
        "海誓山盟", "天长地久", "至死不渝", "一见钟情",
        "热泪盈眶", "百感交集", "思绪万千", "感慨万千",
        "黯然神伤", "潸然泪下", "潸然泪下", "泣不成声",
        "柔情蜜意", "含情脉脉", "情意绵绵", "如胶似漆"
    ]
    found_cliche = [m for m in cliche_metaphors if m in chapter_text]
    if found_cliche:
        issues["陈旧比喻/直白抒情"] = found_cliche

    direct_emotion = [
        "我很难过", "我非常伤心", "我心碎了", "我崩溃了",
        "我很痛苦", "我绝望了", "我哭了", "我忍不住哭了",
        "我感到无比", "心中充满了", "内心深处的悲伤",
        "我的眼眶湿润了", "泪水模糊了", "眼泪不争气",
        "我真的很想你", "我好想你啊", "我太难过了",
        "我伤心极了", "我痛苦万分", "我悲痛欲绝",
        "一种说不出的难过", "说不出的悲伤", "难以言喻的痛苦"
    ]
    found_direct = [e for e in direct_emotion if e in chapter_text]
    if found_direct:
        issues["直白情感宣泄"] = found_direct

    dazai_markers = [
        "抱歉", "不配", "面具", "生而为人",
        "果然如此", "果然还是", "不理解", "不明白为什么",
        "对不起", "我这样的人", "不值得", "可笑",
        "丑角", "小丑", "伪装", "假装"
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

    # --- 新增检测项 ---

    dialogue_lines = []
    for l in chapter_text.split("\n"):
        s = l.strip()
        if s and (s[0] in ("\u201c", "\u300c", '"')):
            dialogue_lines.append(s)
    total_chars = len(chapter_text)
    if total_chars > 0:
        dialogue_chars = sum(len(l) for l in dialogue_lines)
        dialogue_ratio = dialogue_chars / total_chars
        if dialogue_ratio > 0.45:
            issues["对话比例过高"] = [f"对话占比 {dialogue_ratio:.0%}，超过45%，可能缺乏叙述描写的平衡"]

        non_dialogue = chapter_text
        for l in dialogue_lines:
            non_dialogue = non_dialogue.replace(l, "")
        sensory_words = {
            "视觉": ["看到", "望着", "目光", "视线", "映入", "眼前", "阳光", "灯光", "阴影", "光线", "月光", "颜色", "红色", "白色", "蓝色", "昏暗", "明亮"],
            "听觉": ["听到", "声音", "响", "安静", "寂静", "嘈杂", "音乐", "歌", "脚步声", "风声", "雨声", "铃声", "说话声", "鸟鸣"],
            "嗅觉": ["闻到", "气味", "香味", "味道", "气息", "清香", "臭味", "烟味", "雨后的", "泥土味", "食物的"],
            "触觉": ["摸到", "触感", "冰冷", "温暖", "温热", "粗糙", "光滑", "潮湿", "干燥", "柔软", "僵硬", "刺痛", "发麻"],
        }
        sensory_stats = {}
        for sense, words in sensory_words.items():
            count = sum(1 for w in words if w in non_dialogue)
            sensory_stats[sense] = count
        used_senses = sum(1 for v in sensory_stats.values() if v > 0)
        if used_senses < 2:
            issues["感官描写不足"] = [f"非对话部分仅涉及 {used_senses} 种感官({', '.join(s for s, c in sensory_stats.items() if c > 0) or '无'})，建议至少调动3种感官"]

        periods = chapter_text.count("。")
        commas = chapter_text.count("，")
        if commas > 0 and periods / commas < 0.4:
            issues["句号密度不足"] = [f"句号 {periods} 个 vs 逗号 {commas} 个（比率 {periods/commas:.2f}），句号应多于逗号才有村上式呼吸感"]

    flat_openings = ["那天早上", "清晨醒来", "早上起床", "新的一天", "阳光照进", "闹钟响了", "又是新的一天", "时光飞逝", "不知不觉", "日子一天天"]
    text_start = chapter_text[:200]
    found_flat = [o for o in flat_openings if o in text_start]
    if found_flat:
        issues["开头平庸"] = [f"章节开头200字内出现: {', '.join(found_flat)}，建议'从中间开始'直接进入场景"]

    summary_endings = ["人生就是这样", "这就是成长", "我们终于明白", "也许这就是", "我终于懂了", "原来一切", "生活还得继续", "日子还得过", "一切都会好起来的", "明天会更好"]
    text_end = chapter_text[-300:]
    found_summary = [e for e in summary_endings if e in text_end]
    if found_summary:
        issues["结尾说教"] = [f"章节结尾出现总结性金句: {', '.join(found_summary)}，建议用画面定格或意象落点替代"]

    core_images = ["考研教室", "考研兔子", "奶黄包", "螺蛳粉", "硬座", "哈尔滨", "张杰", "苏月", "猫南北", "大汪"]
    found_images = [img for img in core_images if img in chapter_text]
    if not found_images:
        issues["核心意象缺失"] = ["本章未出现任何核心意象（考研教室/考研兔子/硬座/哈尔滨/奶黄包/螺蛳粉/猫南北/大汪），建议至少融入一个"]

    return issues


def detect_dazai_blade(chapter_text: str) -> dict:
    """
    检测章节中是否使用了太宰治式"刀锋"技法。
    返回 {"used": bool, "signals": list, "intensity": str}
    """
    if not chapter_text:
        return {"used": False, "signals": [], "intensity": "none"}

    signals = []

    self_hate_phrases = [
        "恶心", "虚伪", "骗子", "懦弱", "可悲", "不配", "丑陋",
        "肮脏", "卑鄙", "可笑", "窝囊", "废物", "没用",
        "我这样的人", "像我这样", "不值得", "没有资格",
        "装", "演", "假装", "面具", "伪装"
    ]
    found_hate = [p for p in self_hate_phrases if p in chapter_text]
    if found_hate:
        signals.append(f"自我厌恶/面具: {', '.join(found_hate[:3])}")

    over_aware_phrases = [
        "过度", "每一个动作", "意识到自己", "审视自己",
        "从旁观者的角度", "第三者视角", "跳出来看",
        "可笑的是", "讽刺的是", "荒谬的是",
        "我清楚地知道", "我明白自己"
    ]
    found_aware = [p for p in over_aware_phrases if p in chapter_text]
    if found_aware:
        signals.append(f"过度自我意识: {', '.join(found_aware[:3])}")

    blade_moments = [
        "赤裸", "剥开", "解剖", "撕裂", "暴露",
        "最真实的想法", "不敢说出口", "心底深处",
        "阴暗", "黑暗面", "另一面"
    ]
    found_blade = [p for p in blade_moments if p in chapter_text]
    if found_blade:
        signals.append(f"刀锋时刻: {', '.join(found_blade[:3])}")

    is_used = len(signals) >= 2

    if len(signals) >= 3:
        intensity = "heavy"
    elif len(signals) >= 2:
        intensity = "moderate"
    elif len(signals) == 1:
        intensity = "light"
    else:
        intensity = "none"

    return {
        "used": is_used,
        "signals": signals,
        "intensity": intensity
    }
