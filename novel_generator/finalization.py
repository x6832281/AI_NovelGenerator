#novel_generator/finalization.py
# -*- coding: utf-8 -*-
"""
定稿章节和扩写章节（finalize_chapter、enrich_chapter_text）
含三级摘要体系：book_summary / part_summary / global_summary
"""
import os
import json
import logging
from llm_adapters import create_llm_adapter
from embedding_adapters import create_embedding_adapter
import prompt_definitions
from novel_generator.common import invoke_with_cleaning
from utils import read_file, clear_file_content, save_string_to_txt
from novel_generator.vectorstore_utils import update_vector_store
from consistency_checker import quick_style_scan, detect_dazai_blade
logging.basicConfig(
    filename='app.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

DEFAULT_PART_BOUNDARIES = [
    {"part": 1, "name": "考研教室·相识与暗恋", "start": 1, "end": 10, "theme": "考研教室的相遇（自始至终只有三人：陈北坐最前面、张杰坐中间、苏月坐后面几排），兔子陪伴的日常（笼子放在最后一排角落，晚上九点后关门放出来跑），暗恋的萌芽"},
    {"part": 2, "name": "成都·重逢与表白", "start": 11, "end": 20, "theme": "峨眉山九寨沟之旅，人生中很多第一次，爱情的确认"},
    {"part": 3, "name": "哈尔滨·异地与消磨", "start": 21, "end": 32, "theme": "60小时硬座，零下28度，甜蜜与争吵，默认分手"},
    {"part": 4, "name": "余生·回望与释然", "start": 33, "end": 40, "theme": "十五年后的回望，成家立业，遗憾但释然"},
]


def load_part_boundaries(filepath: str) -> list:
    boundaries_file = os.path.join(filepath, "part_boundaries.json")
    if os.path.exists(boundaries_file):
        try:
            with open(boundaries_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load part_boundaries.json: {e}")
    return DEFAULT_PART_BOUNDARIES


def get_part_for_chapter(filepath: str, chapter_number: int) -> dict:
    boundaries = load_part_boundaries(filepath)
    for part_info in boundaries:
        if part_info["start"] <= chapter_number <= part_info["end"]:
            return part_info
    return boundaries[-1] if boundaries else {
        "part": 1, "name": "默认", "start": 1, "end": 999, "theme": ""
    }


def get_total_chapters_from_blueprint(filepath: str) -> int:
    from chapter_directory_parser import parse_chapter_blueprint
    directory_file = os.path.join(filepath, "Novel_directory.txt")
    blueprint_text = read_file(directory_file)
    if blueprint_text:
        chapters = parse_chapter_blueprint(blueprint_text)
        if chapters:
            return len(chapters)
    return 43


def load_part_summaries(filepath: str) -> dict:
    part_file = os.path.join(filepath, "part_summaries.json")
    if os.path.exists(part_file):
        try:
            with open(part_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load part_summaries.json: {e}")
    return {}


def save_part_summaries(filepath: str, data: dict):
    part_file = os.path.join(filepath, "part_summaries.json")
    try:
        with open(part_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(f"Failed to save part_summaries.json: {e}")


def load_foreshadow_tracker(filepath: str) -> dict:
    tracker_file = os.path.join(filepath, "foreshadow_tracker.json")
    if os.path.exists(tracker_file):
        try:
            with open(tracker_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load foreshadow_tracker.json: {e}")
    return {"next_id": 1, "foreshadows": []}


def save_foreshadow_tracker(filepath: str, data: dict):
    tracker_file = os.path.join(filepath, "foreshadow_tracker.json")
    try:
        with open(tracker_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(f"Failed to save foreshadow_tracker.json: {e}")


def update_foreshadow_tracker(filepath: str, novel_number: int, chapter_text: str, llm_adapter) -> dict:
    tracker = load_foreshadow_tracker(filepath)
    try:
        current_foreshadows = json.dumps(tracker, ensure_ascii=False, indent=2)
        prompt = prompt_definitions.foreshadow_extract_prompt.format(
            chapter_text=chapter_text[:3000],
            current_foreshadows=current_foreshadows[:2000],
            novel_number=novel_number
        )
        response = invoke_with_cleaning(llm_adapter, prompt)
        if not response:
            return tracker

        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            return tracker

        result = json.loads(json_match.group())

        for new_fs in result.get("new_foreshadows", []):
            fs_id = f"FS-{tracker['next_id']:03d}"
            tracker["next_id"] += 1
            tracker["foreshadows"].append({
                "id": fs_id,
                "description": new_fs.get("description", ""),
                "planted_chapter": new_fs.get("planted_chapter", novel_number),
                "target_recover_chapter": new_fs.get("target_recover_chapter"),
                "status": "planted",
                "last_mentioned_chapter": novel_number,
                "related_characters": new_fs.get("related_characters", []),
                "related_items": new_fs.get("related_items", []),
                "notes": []
            })

        for update in result.get("updated_foreshadows", []):
            fs_id = update.get("id", "")
            for fs in tracker["foreshadows"]:
                if fs["id"] == fs_id:
                    fs["status"] = update.get("status", fs["status"])
                    fs["last_mentioned_chapter"] = update.get("last_mentioned_chapter", novel_number)
                    if update.get("notes"):
                        fs["notes"].append(f"Ch{novel_number}: {update['notes']}")
                    break

        save_foreshadow_tracker(filepath, tracker)
        logging.info(f"[Foreshadow] 伏笔追踪已更新 (Ch{novel_number}), 共{len(tracker['foreshadows'])}条")

    except Exception as e:
        logging.warning(f"[Foreshadow] 伏笔追踪更新失败: {e}")

    return tracker


def get_pending_foreshadows(filepath: str, current_chapter: int) -> str:
    tracker = load_foreshadow_tracker(filepath)
    pending = []
    for fs in tracker.get("foreshadows", []):
        if fs["status"] in ("planted", "mentioned"):
            age = current_chapter - fs["planted_chapter"]
            urgency = ""
            if fs.get("target_recover_chapter") and fs["target_recover_chapter"] <= current_chapter:
                urgency = " ⚠️已到期！"
            elif age > 10:
                urgency = " ⏳沉睡已久"
            pending.append(
                f"  {fs['id']}: {fs['description']} (埋于Ch{fs['planted_chapter']}, "
                f"状态:{fs['status']}, 沉睡:{age}章{urgency})"
            )
    if not pending:
        return "（暂无待回收伏笔）"
    return "待回收伏笔：\n" + "\n".join(pending)


def load_style_tracker(filepath: str) -> dict:
    tracker_file = os.path.join(filepath, "style_technique_tracker.json")
    if os.path.exists(tracker_file):
        try:
            with open(tracker_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load style_technique_tracker.json: {e}")
    return {"dazai_blade": {"total_used": 0, "chapters": []}}


def save_style_tracker(filepath: str, data: dict):
    tracker_file = os.path.join(filepath, "style_technique_tracker.json")
    try:
        with open(tracker_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(f"Failed to save style_technique_tracker.json: {e}")


def update_dazai_blade_tracker(filepath: str, novel_number: int, chapter_text: str) -> dict:
    tracker = load_style_tracker(filepath)
    detection = detect_dazai_blade(chapter_text)

    if detection["used"]:
        tracker["dazai_blade"]["total_used"] += 1
        tracker["dazai_blade"]["chapters"].append({
            "chapter": novel_number,
            "intensity": detection["intensity"],
            "signals": detection["signals"]
        })
        save_style_tracker(filepath, tracker)
        logging.info(f"[DazaiBlade] Ch{novel_number} 检测到太宰刀锋 (强度:{detection['intensity']})")

    return tracker


def get_dazai_blade_status(filepath: str, total_chapters: int = 40) -> str:
    tracker = load_style_tracker(filepath)
    used = tracker["dazai_blade"]["total_used"]
    max_allowed = max(2, int(total_chapters * 0.07))
    remaining = max_allowed - used

    if remaining <= 0:
        return f"⚠️ 太宰刀锋已使用{used}次（配额{max_allowed}次），本章禁止使用太宰式自我解剖。"
    elif remaining == 1:
        return f"⚡ 太宰刀锋已使用{used}次，仅剩{remaining}次机会，请确认本章是否为关键高潮。"
    else:
        return f"📊 太宰刀锋已使用{used}/{max_allowed}次，剩余{remaining}次。"


def finalize_chapter(
    novel_number: int,
    word_number: int,
    api_key: str,
    base_url: str,
    model_name: str,
    temperature: float,
    filepath: str,
    embedding_api_key: str,
    embedding_url: str,
    embedding_interface_format: str,
    embedding_model_name: str,
    interface_format: str,
    max_tokens: int,
    timeout: int = 600,
    auto_style_check: bool = True
):
    """
    对指定章节做最终处理：
    1. 自动风格扫描 + 修正（P0质量保障）
    2. 更新三级摘要体系（book_summary / part_summary / global_summary）
    3. 更新角色状态
    4. 插入向量库
    """
    chapters_dir = os.path.join(filepath, "chapters")
    chapter_file = os.path.join(chapters_dir, f"chapter_{novel_number}.txt")
    chapter_text = read_file(chapter_file).strip()
    if not chapter_text:
        logging.warning(f"Chapter {novel_number} is empty, cannot finalize.")
        return

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )

    # ── Step 0: 自动风格扫描 + 修正 ──
    if auto_style_check and hasattr(prompt_definitions, 'style_revision_prompt'):
        style_issues = quick_style_scan(chapter_text)
        if style_issues:
            logging.info(f"[StyleCheck] Ch{novel_number} 检测到 {len(style_issues)} 类风格违规")
            issues_text = "\n".join(
                f"- {issue_type}: {', '.join(details)}"
                for issue_type, details in style_issues.items()
            )
            try:
                revision_prompt = prompt_definitions.style_revision_prompt.format(
                    chapter_text=chapter_text,
                    style_issues=issues_text
                )
                revised_text = invoke_with_cleaning(llm_adapter, revision_prompt)
                if revised_text and len(revised_text) > len(chapter_text) * 0.5:
                    chapter_text = revised_text
                    clear_file_content(chapter_file)
                    save_string_to_txt(chapter_text, chapter_file)
                    logging.info(f"[StyleCheck] Ch{novel_number} 风格修正完成")
            except Exception as e:
                logging.warning(f"[StyleCheck] Ch{novel_number} 风格修正失败: {e}")

    # ── Step 1: 更新三级摘要体系 ──
    book_summary_file = os.path.join(filepath, "book_summary.txt")
    old_book_summary = read_file(book_summary_file)
    novel_setting_file = os.path.join(filepath, "Novel_architecture.txt")
    novel_setting = read_file(novel_setting_file)
    total_chapters = get_total_chapters_from_blueprint(filepath)
    part_info = get_part_for_chapter(filepath, novel_number)
    part_key = str(part_info["part"])
    part_summaries = load_part_summaries(filepath)
    old_part_summary = part_summaries.get(part_key, "")
    global_summary_file = os.path.join(filepath, "global_summary.txt")
    old_global_summary = read_file(global_summary_file)

    # 1a: 更新全书摘要
    try:
        prompt_book = prompt_definitions.book_summary_prompt.format(
            chapter_text=chapter_text,
            old_book_summary=old_book_summary or "（首次生成）",
            novel_setting=novel_setting[:1000] if novel_setting else "（未设定）",
            novel_number=novel_number,
            total_chapters=total_chapters
        )
        new_book_summary = invoke_with_cleaning(llm_adapter, prompt_book)
        if new_book_summary and new_book_summary.strip():
            clear_file_content(book_summary_file)
            save_string_to_txt(new_book_summary.strip(), book_summary_file)
            logging.info(f"[Summary] book_summary.txt 已更新 (Ch{novel_number})")
    except Exception as e:
        logging.warning(f"[Summary] book_summary 更新失败: {e}")

    # 1b: 更新分部摘要
    try:
        prompt_part = prompt_definitions.part_summary_prompt.format(
            part_number=part_info["part"],
            part_name=part_info["name"],
            part_start=part_info["start"],
            part_end=part_info["end"],
            part_theme=part_info["theme"],
            chapter_text=chapter_text,
            old_part_summary=old_part_summary or "（首次生成）",
            book_summary=read_file(book_summary_file) or "（尚未生成）"
        )
        new_part_summary = invoke_with_cleaning(llm_adapter, prompt_part)
        if new_part_summary and new_part_summary.strip():
            part_summaries[part_key] = new_part_summary.strip()
            save_part_summaries(filepath, part_summaries)
            logging.info(f"[Summary] part_{part_key}_summary 已更新 (Ch{novel_number})")
    except Exception as e:
        logging.warning(f"[Summary] part_summary 更新失败: {e}")

    # 1c: 更新近章摘要（原有逻辑）
    try:
        prompt_summary = prompt_definitions.summary_prompt.format(
            chapter_text=chapter_text,
            global_summary=old_global_summary
        )
        new_global_summary = invoke_with_cleaning(llm_adapter, prompt_summary)
        if new_global_summary and new_global_summary.strip():
            clear_file_content(global_summary_file)
            save_string_to_txt(new_global_summary.strip(), global_summary_file)
            logging.info(f"[Summary] global_summary.txt 已更新 (Ch{novel_number})")
    except Exception as e:
        logging.warning(f"[Summary] global_summary 更新失败: {e}")

    # ── Step 2: 更新角色状态 ──
    character_state_file = os.path.join(filepath, "character_state.txt")
    old_character_state = read_file(character_state_file)
    try:
        prompt_char_state = prompt_definitions.update_character_state_prompt.format(
            chapter_text=chapter_text,
            old_state=old_character_state
        )
        new_char_state = invoke_with_cleaning(llm_adapter, prompt_char_state)
        if new_char_state and new_char_state.strip():
            clear_file_content(character_state_file)
            save_string_to_txt(new_char_state.strip(), character_state_file)
    except Exception as e:
        logging.warning(f"[CharacterState] 更新失败: {e}")

    # ── Step 3: 更新伏笔追踪 ──
    try:
        update_foreshadow_tracker(filepath, novel_number, chapter_text, llm_adapter)
    except Exception as e:
        logging.warning(f"[Foreshadow] 伏笔追踪更新失败: {e}")

    # ── Step 4: 更新太宰刀锋计数 ──
    try:
        update_dazai_blade_tracker(filepath, novel_number, chapter_text)
    except Exception as e:
        logging.warning(f"[DazaiBlade] 太宰刀锋计数更新失败: {e}")

    # ── Step 5: 更新向量库 ──
    update_vector_store(
        embedding_adapter=create_embedding_adapter(
            embedding_interface_format,
            embedding_api_key,
            embedding_url,
            embedding_model_name
        ),
        new_chapter=chapter_text,
        filepath=filepath
    )

    logging.info(f"Chapter {novel_number} has been finalized.")


def enrich_chapter_text(
    chapter_text: str,
    word_number: int,
    api_key: str,
    base_url: str,
    model_name: str,
    temperature: float,
    interface_format: str,
    max_tokens: int,
    timeout: int=600
) -> str:
    """
    对章节文本进行扩写，使其更接近 word_number 字数，保持剧情连贯。
    """
    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )
    prompt = prompt_definitions.enrich_prompt.format(
        word_number=word_number,
        chapter_text=chapter_text
    )
    enriched_text = invoke_with_cleaning(llm_adapter, prompt)
    return enriched_text if enriched_text else chapter_text
