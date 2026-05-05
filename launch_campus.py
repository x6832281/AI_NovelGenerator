# launch_campus.py
# -*- coding: utf-8 -*-
"""
校园青春回忆·爱情与遗憾 —— AI小说写作智能体 一键启动脚本

融合写作风格：村上春树底色 × 八月长安内容策略 × 太宰治刀锋
分层体系：
  ★★★ 第一层·底色：挪威的森林（村上春树）——全文统一语调
  ★★  第二层·策略：最好的我们（八月长安）——选材与事件设计
  ★★  第三层·刀锋：人间失格（太宰治）——关键情感高潮
  ★   第四层·调料：平凡的世界/匆匆那年/穆斯林的葬礼

用法：
    python launch_campus.py

首次运行会自动：
  1. 将校园青春风格提示词注入提示词模块
  2. 加载 config_campus.json 配置（如不存在则自动创建）
  3. 自动导入 knowledge/ 目录下的写作风格知识文件到向量库
  4. 启动 GUI 工作台
"""

import os
import sys
import json
import shutil
import importlib
import logging


def list_project_files(base_dir: str, prefix: str = "") -> None:
    """递归列出项目文件结构"""
    files = []
    dirs = []
    
    for entry in os.listdir(base_dir):
        entry_path = os.path.join(base_dir, entry)
        if entry.startswith(".") or entry == "__pycache__" or entry.endswith(".pyc") or entry.endswith(".bak") or entry == "app.log":
            continue
        if os.path.isdir(entry_path):
            dirs.append(entry)
        else:
            files.append(entry)
    
    for file in sorted(files):
        print(f"     {prefix}+-- {file}")
    
    for i, dir_name in enumerate(sorted(dirs)):
        print(f"     {prefix}+-- {dir_name}/")
        new_prefix = prefix + "|   " if i < len(dirs) - 1 else prefix + "    "
        list_project_files(os.path.join(base_dir, dir_name), new_prefix)


def auto_import_knowledge_files(base_dir: str, config: dict) -> bool:
    """
    自动导入 knowledge/ 目录下的写作风格文件到向量库。
    仅在以下条件全部满足时执行：
    1. filepath 已配置且目录存在
    2. embedding API key 已配置
    3. 向量库为空或不存在
    """
    knowledge_dir = os.path.join(base_dir, "knowledge")
    if not os.path.exists(knowledge_dir):
        print("  [SKIP] 未找到 knowledge/ 目录，跳过知识库导入")
        return False

    knowledge_files = [f for f in os.listdir(knowledge_dir) if f.endswith(".txt")]
    if not knowledge_files:
        print("  [SKIP] knowledge/ 目录下无 .txt 文件")
        return False

    filepath = config.get("other_params", {}).get("filepath", "")
    if not filepath or not os.path.exists(filepath):
        print("  [SKIP] 项目输出目录(filepath)未配置或不存在，跳过自动导入")
        print("         请在 GUI 中设置项目路径后，手动导入知识库文件")
        return False

    last_emb_fmt = config.get("last_embedding_interface_format", "OpenAI")
    emb_configs = config.get("embedding_configs", {})
    emb_cfg = emb_configs.get(last_emb_fmt, {})
    emb_api_key = emb_cfg.get("api_key", "")
    if not emb_api_key:
        print("  [SKIP] Embedding API Key 未配置，跳过自动导入")
        print("         请在 GUI 中配置 Embedding API Key 后，手动导入知识库文件")
        return False

    try:
        sys.path.insert(0, base_dir)
        from embedding_adapters import create_embedding_adapter
        from novel_generator.vectorstore_utils import load_vector_store, get_vectorstore_dir
        from novel_generator.knowledge import import_knowledge_file

        embedding_adapter = create_embedding_adapter(
            emb_cfg.get("interface_format", "OpenAI"),
            emb_api_key,
            emb_cfg.get("base_url", ""),
            emb_cfg.get("model_name", "")
        )
        store = load_vector_store(embedding_adapter, filepath)
        if store:
            try:
                count = store._collection.count()
                if count > 0:
                    print(f"  [SKIP] 向量库已包含 {count} 条记录，跳过自动导入")
                    return False
            except Exception:
                pass

        print(f"\n  [AutoImport] 正在自动导入 {len(knowledge_files)} 个知识文件到向量库...")
        imported = 0
        for kf in knowledge_files:
            kf_path = os.path.join(knowledge_dir, kf)
            try:
                import_knowledge_file(
                    embedding_api_key=emb_api_key,
                    embedding_url=emb_cfg.get("base_url", ""),
                    embedding_interface_format=emb_cfg.get("interface_format", "OpenAI"),
                    embedding_model_name=emb_cfg.get("model_name", ""),
                    file_path=kf_path,
                    filepath=filepath
                )
                imported += 1
                print(f"     [OK] {kf}")
            except Exception as e:
                print(f"     [FAIL] {kf}: {e}")
                logging.warning(f"Auto-import failed for {kf}: {e}")

        if imported > 0:
            print(f"  [OK] 成功导入 {imported}/{len(knowledge_files)} 个知识文件")
            return True
        else:
            print("  [WARN] 所有知识文件导入失败")
            return False

    except Exception as e:
        print(f"  [WARN] 自动导入过程出错: {e}")
        logging.warning(f"Auto-import knowledge error: {e}")
        return False


def setup_campus_environment():
    """
    设置校园青春创作环境：
    1. 注入校园提示词到 prompt_definitions 模块
    2. 确保使用 config_campus.json 配置
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # ── 步骤1: 注入校园风格提示词 ──
    print("=" * 60)
    print("  [Graduation] 校园青春回忆 · AI 小说写作智能体")
    print("  风格：村上春树底色 x 八月长安内容策略 x 太宰治刀锋")
    print("=" * 60)

    try:
        import prompt_definitions
        source = importlib.import_module("prompt_definitions_campus")
        importlib.reload(source)

        injected_count = 0
        for attr in dir(source):
            if not attr.startswith("__"):
                setattr(prompt_definitions, attr, getattr(source, attr))
                injected_count += 1

        print(f"  [OK] 已注入 {injected_count} 个校园青春风格提示词")
        print(f"  [Book] 第一层·底色：《挪威的森林》（村上春树）")
        print(f"  [Book] 第二层·策略：《最好的我们》（八月长安）")
        print(f"  [Book] 第三层·刀锋：《人间失格》（太宰治）")
        print(f"  [Book] 第四层·调料：《平凡的世界》《匆匆那年》《穆斯林的葬礼》")
        print(f"  [Model] 支持模型：DeepSeek V3 / GPT 5 / Gemini 2.5 Flash / MiMo V2.5 Pro")
    except Exception as e:
        print(f"  [WARN] 提示词注入警告: {e}")
        print("  将使用默认提示词继续运行...")

    # ── 步骤2: 检查知识库文件 ──
    knowledge_dir = os.path.join(base_dir, "knowledge")
    if os.path.exists(knowledge_dir):
        knowledge_files = os.listdir(knowledge_dir)
        print(f"\n  [Doc] 写作风格知识库 ({len(knowledge_files)} 个文件):")
        for f in knowledge_files:
            print(f"       > {f}")

    # ── 步骤3: 配置文件处理 ──
    config_campus = os.path.join(base_dir, "config_campus.json")
    config_default = os.path.join(base_dir, "config.json")

    if not os.path.exists(config_campus):
        print(f"\n  [WARN] 未找到 config_campus.json，正在自动创建...")
        create_default_campus_config(config_campus)

    # 备份原有 config.json（如果存在且与校园配置不同）
    if os.path.exists(config_default):
        with open(config_default, "r", encoding="utf-8") as f:
            old_config = json.load(f)
        old_topic = old_config.get("other_params", {}).get("topic", "")
        if "校园" not in old_topic and "春上" not in old_topic:
            backup_path = config_default + ".bak"
            shutil.copy2(config_default, backup_path)
            print(f"\n  [Save] 已备份原配置到: {backup_path}")

    # 用校园配置覆盖当前配置
    shutil.copy2(config_campus, config_default)
    print(f"  [OK] 已加载校园青春故事配置")

    # ── 步骤3.5: 自动导入知识库 ──
    with open(config_campus, "r", encoding="utf-8") as f:
        campus_config = json.load(f)
    auto_import_knowledge_files(base_dir, campus_config)

    # ── 步骤4: 显示项目文件列表 ──
    print("\n" + "=" * 60)
    print("  [Dir] 项目文件结构:")
    print("  ─────────────────────────────────────────────")
    list_project_files(base_dir)

    print("\n" + "=" * 60)
    print("  [Launch] 启动 GUI 工作台...")
    print("  [Tip] 提示: 启动后请先配置 API Key, 再开始创作!")
    print("  [Tip] 知识库文件将在配置完成后自动导入到向量库")
    print("=" * 60 + "\n")


def create_default_campus_config(config_path: str):
    """创建默认的校园青春小说配置"""
    default_config = {
        "last_interface_format": "OpenAI",
        "last_embedding_interface_format": "OpenAI",
        "llm_configs": {
            "DeepSeek V3": {
                "api_key": "",
                "base_url": "https://api.deepseek.com/v1",
                "model_name": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": 8192,
                "timeout": 600,
                "interface_format": "OpenAI",
            },
            "GPT 5": {
                "api_key": "",
                "base_url": "https://api.openai.com/v1",
                "model_name": "gpt-5",
                "temperature": 0.7,
                "max_tokens": 32768,
                "timeout": 600,
                "interface_format": "OpenAI",
            },
            "Gemini 2.5 Flash": {
                "api_key": "",
                "base_url": "https://generativelanguage.googleapis.com/v1beta",
                "model_name": "gemini-2.5-flash",
                "temperature": 0.7,
                "max_tokens": 32768,
                "timeout": 600,
                "interface_format": "Gemini",
            },
            "MiMo V2.5 Pro": {
                "api_key": "",
                "base_url": "https://token-plan-cn.xiaomimimo.com/v1",
                "model_name": "mimo-v2.5-pro",
                "temperature": 0.7,
                "max_tokens": 32000,
                "timeout": 600,
                "interface_format": "OpenAI",
            },
        },
        "embedding_configs": {
            "OpenAI": {
                "api_key": "",
                "base_url": "https://api.openai.com/v1",
                "model_name": "text-embedding-ada-002",
                "retrieval_k": 4,
                "interface_format": "OpenAI",
            },
            "Gemini": {
                "api_key": "",
                "base_url": "https://generativelanguage.googleapis.com/v1beta",
                "model_name": "gemini-embedding-2",
                "retrieval_k": 4,
                "interface_format": "Gemini",
            },
        },
        "other_params": {
            "topic": "广西大学物理工程专业，同专业两个班天天一起上课却从未交流。大四考研，空旷的考研教室只有三个人——林晚、苏雨、陈北。她偷偷养了一只兔子叫团子，三个人的秘密。林晚考上成都西南交大，苏雨落榜。第二年苏雨二战考研，考完笔试来成都找他，他们一起去了峨眉山、九寨沟，那是林晚人生中很多'第一次'。苏雨考上哈尔滨工程大学，两人正式异地相恋。林晚很穷很自卑，坐60小时硬座去看她，在零下28度的破旧公寓里煮面。后来吵架越来越多，某次争吵后彻底沉默，默认分手。十五年后，林晚成家立业，孩子两岁，偶尔想起她，仍有遗憾。",
            "genre": "校园青春文学·爱情与遗憾",
            "num_chapters": 36,
            "word_number": 3000,
            "filepath": "",
            "chapter_num": "1",
            "user_guidance": "这是一部以村上春树《挪威的森林》为文字底色的长篇校园青春小说。采用分层融合风格体系：第一层（底色）村上春树——克制的深情、短句呼吸感、感官精确、意象系统、潜台词对话；第二层（内容策略）八月长安《最好的我们》——'小事大写'的选材哲学、暗恋的精确解剖、配角的质感；第三层（刀锋）太宰治《人间失格》——仅在关键情感高潮处使用自我解剖和温柔绝望；第四层（辅助）路遥的社会观察、九夜茴的年代标记、霍达的信物意象。叙事采用第一人称回顾视角（林晚），以十五年后的目光回望大学岁月和那段刻骨铭心的异地恋。故事分四部：第一部广西（相识与暗恋，考研教室与兔子团子），第二部成都（重逢与表白，峨眉山九寨沟西安之旅），第三部哈尔滨（异地恋的甜蜜与消磨，60小时硬座，零下28度，自卑与争吵，默认分手），第四部余生（十五年后的回望与释然）。核心情感：相爱与分离，遗憾但释然。不追求强情节，追求情感的累积与释放。主题关键词：考研教室、兔子、六十小时硬座、零下二十八度、九寨沟的水、隧道与光、朋友圈灰色横线。",
            "characters_involved": "林晚, 苏雨, 陈北",
            "key_items": "兔子团子, 考研教室的日光灯, 六十小时的硬座火车票, 九寨沟的照片, 苏雨织的兔子小毛衣, 壶口瀑布前她说的那句没听清的话",
            "scene_location": "广西大学物理楼考研教室(空旷、日光灯嗡嗡响、窗外永远绿着的树), 成都西南交通大学(阴冷潮湿的冬天), 峨眉山(雾中的山路), 九寨沟(蓝得不像真的水), 西安(兵马俑、壶口瀑布、延安), 哈尔滨工程大学附近破旧公寓(暖气时有时无、墙皮脱落), 哈尔滨火车站出站口(零下28度、她在雪地里等), 成都(雨天的窗户)",
            "time_constraint": "2010年代，从大四考研到十五年后成家立业，主要集中在考研那年到研究生毕业的四五年间",
        },
        "choose_configs": {
            "prompt_draft_llm": "MiMo V2.5 Pro",
            "chapter_outline_llm": "MiMo V2.5 Pro",
            "architecture_llm": "MiMo V2.5 Pro",
            "final_chapter_llm": "MiMo V2.5 Pro",
            "consistency_review_llm": "MiMo V2.5 Pro",
        },
        "proxy_setting": {
            "proxy_url": "127.0.0.1",
            "proxy_port": "",
            "enabled": False,
        },
        "webdav_config": {
            "webdav_url": "",
            "webdav_username": "",
            "webdav_password": "",
        },
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(default_config, f, ensure_ascii=False, indent=4)
    print(f"  ✅ 已创建默认配置: {config_path}")


def main():
    """启动校园青春小说写作智能体"""
    # 切换到项目目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    # 设置校园创作环境
    setup_campus_environment()

    # 启动 GUI
    try:
        import customtkinter as ctk
        from ui import NovelGeneratorGUI

        app = ctk.CTk()
        gui = NovelGeneratorGUI(app)
        app.mainloop()
    except ImportError as e:
        print(f"\n❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
