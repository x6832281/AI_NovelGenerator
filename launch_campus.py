# launch_campus.py
# -*- coding: utf-8 -*-
"""
现实主义青春文学·爱情与遗憾 —— AI小说写作智能体 一键启动脚本

融合写作风格：村上春树底色 × 路遥质感 × 太宰治刀锋 × 八月长安年代标记
分层体系：
  ★★★ 第一层·底色：挪威的森林（村上春树）——全文统一语调 ～60%
  ★★★ 第二层·质感：平凡的世界（路遥）——细节写作与质朴感 ～25%
  ★★  第三层·刀锋：人间失格（太宰治）——关键情感高潮 ～5%
  ★   第四层·标记：年代标记（八月长安）+ 信物（霍达）～5%
  ★   第五层·自由：保留5%自由发挥空间

用法：
    python launch_campus.py

首次运行会自动：
  1. 将现实主义青春文学风格提示词注入提示词模块
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

    last_emb_fmt = config.get("last_embedding_interface_format", "阿里云百炼")
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
            emb_cfg.get("interface_format", "阿里云百炼"),
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
    设置现实主义青春文学创作环境：
    1. 注入风格提示词到 prompt_definitions 模块
    2. 确保使用 config_campus.json 配置
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # ── 步骤1: 注入风格提示词 ──
    print("=" * 60)
    print("  [Graduation] 现实主义青春文学 · AI 小说写作智能体")
    print("  风格：村上春树底色 x 路遥质感 x 太宰治刀锋 x 八月长安年代标记")
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

        print(f"  [OK] 已注入 {injected_count} 个现实主义青春文学风格提示词")
        print(f"  [Book] 第一层·底色：《挪威的森林》（村上春树）～60%")
        print(f"  [Book] 第二层·质感：《平凡的世界》（路遥）～25%")
        print(f"  [Book] 第三层·刀锋：《人间失格》（太宰治）～5%")
        print(f"  [Book] 第四层·标记：年代标记（八月长安）+ 信物（霍达）～5%")
        print(f"  [Book] 第五层·自由：保留5%自由发挥空间")
        print(f"  [Model] 支持模型：DeepSeek V4 Pro / MiMo V2.5 Pro / Claude Sonnet 4.6")
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
    old_llm_keys = {}
    old_emb_keys = {}
    if os.path.exists(config_default):
        with open(config_default, "r", encoding="utf-8") as f:
            old_config = json.load(f)
        old_topic = old_config.get("other_params", {}).get("topic", "")
        if "校园" not in old_topic and "春上" not in old_topic:
            backup_path = config_default + ".bak"
            shutil.copy2(config_default, backup_path)
            print(f"\n  [Save] 已备份原配置到: {backup_path}")

        # 保存旧的 API keys，合并到新配置
        for name, cfg in old_config.get("llm_configs", {}).items():
            if cfg.get("api_key"):
                old_llm_keys[name] = cfg["api_key"]
        for name, cfg in old_config.get("embedding_configs", {}).items():
            if cfg.get("api_key"):
                old_emb_keys[name] = cfg["api_key"]

    # 读取校园配置，合并旧的 API keys
    with open(config_campus, "r", encoding="utf-8") as f:
        campus_config = json.load(f)

    for name, cfg in campus_config.get("llm_configs", {}).items():
        if name in old_llm_keys:
            cfg["api_key"] = old_llm_keys[name]
    for name, cfg in campus_config.get("embedding_configs", {}).items():
        if name in old_emb_keys:
            cfg["api_key"] = old_emb_keys[name]

    with open(config_campus, "w", encoding="utf-8") as f:
        json.dump(campus_config, f, ensure_ascii=False, indent=4)

    shutil.copy2(config_campus, config_default)
    print(f"  [OK] 已加载现实主义青春文学故事配置（API Key 已保留）")

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
    """创建默认的现实主义青春小说配置"""
    default_config = {
        "last_interface_format": "OpenAI",
        "last_embedding_interface_format": "阿里云百炼",
        "llm_configs": {
            "DeepSeek V4 Pro": {
                "api_key": "",
                "base_url": "https://api.deepseek.com/v1",
                "model_name": "deepseek-v4-pro",
                "temperature": 0.7,
                "max_tokens": 32768,
                "timeout": 600,
                "interface_format": "OpenAI",
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
            "Claude Sonnet 4.6": {
                "api_key": "",
                "base_url": "https://clawapi.fulitimes.com",
                "model_name": "claude-sonnet-4-6",
                "temperature": 0.7,
                "max_tokens": 8192,
                "timeout": 600,
                "interface_format": "Claude",
            },
        },
        "embedding_configs": {
            "阿里云百炼": {
                "api_key": "",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "model_name": "text-embedding-v2",
                "retrieval_k": 4,
                "interface_format": "阿里云百炼",
            },
        },
        "other_params": {
            "topic": "南方某大学物理学院，电子科学与技术专业，张杰（四川人，高考复读，小镇做题家）和苏月（辽宁大连人，祖籍南方，温婉知性，大部分时间安静有文艺气息，偶尔调皮耍嘴皮子）。大四考研教室自始至终只有三人——张杰、苏月、陈北（靠窗最里面那一排：陈北坐最前面、张杰坐中间、苏月坐后面几排，兔子笼子放在最后一排角落，晚上九点后关门放兔子出来跑）。考研期间的奶黄包、螺蛳粉、考研兔子（苏月养在教室里，后来被老师发现送人，张杰每天第一个到教室铲屎、抱怨'高考复习都没这么辛苦过'），备考期间张杰给苏月补习高数/微积分/线性代数（讲三遍也不烦），苏月帮张杰补英语和政治（笔记用红笔标重点），讨论问题时张杰闻到苏月身上的味道走神想入非非、猫屋咖啡（她叫'猫南北'，他叫'大汪'）。张杰考上成都读研，苏月落榜。第二年苏月二战，来成都找他，去了九寨沟、峨眉山许愿、西安、壶口瀑布、延安。苏月送给张杰一本日记。苏月考上哈尔滨读研，两人表白在一起。异地两年，吵架增多，冷战拉长，删微信→偷看QQ空间→删QQ→删手机号，默认分手。十五年后张杰成家立业，偶尔想起她，仍有遗憾。",
            "genre": "现实主义青春文学·爱情与成长·遗憾但释然",
            "num_chapters": 40,
            "word_number": 2600,
            "filepath": "",
            "chapter_num": "1",
            "user_guidance": "这是一部以村上春树《挪威的森林》为文字底色、路遥《平凡的世界》为质感肌理的长篇现实主义青春小说。采用分层融合风格体系：第一层（底色60%）村上春树——克制的深情、短句呼吸感、感官精确、意象系统、潜台词对话；第二层（质感25%）路遥——'不评价只呈现'的细节哲学、经济现实的重量、家庭的暗流、中国校园特有感官细节、细节铺垫的耐心，路遥在生活质感和叙事深度上与村上并重；第三层（刀锋5%）太宰治《人间失格》——仅在关键情感高潮处使用自我解剖和温柔绝望；第四层（年代标记5%）八月长安——用2011至2026年具体时代事件标记时间坐标（IG夺冠、新冠疫情、ChatGPT等），霍达的信物意象贯穿全书；保留5%自由发挥空间。叙事采用第一人称回顾视角（张杰），以十五年后的目光回望大学岁月和那段刻骨铭心的异地恋。故事分四部：第一部考研准备期（2014-2015），穿插大一到大三回忆，考研教室最后三个人、奶黄包、螺蛳粉、考研兔子、互帮互助（张杰补苏月高数/苏月补张杰英语政治）、猫屋咖啡'猫南北/大汪'、迎新晚会视频、苏月写的那封信；第二部成都·重逢与表白（2015-2016），张杰考上成都读研、苏月落榜独自复习一年、苏月来成都+九寨沟+峨眉山许愿+西安+壶口瀑布+延安、苏月送出日记本、表白；第三部哈尔滨·异地与消磨（2016-2018），异地两年、吵架频率增加冷战时间拉长、删微信→偷看QQ空间→删QQ→删手机号、默认分开；第四部余生·回望与释然（2018至今），码农当牛马、买房买车结婚生子、消费记录是唯一物证、日常闪回（奶黄包/螺蛳粉/迎新晚会视频/筷子停顿/搬家时翻出日记本）。核心情感：遗憾但释然。",
            "characters_involved": "张杰, 苏月, 陈北, 林文, 赵航",
            "key_items": "奶黄包, 螺蛳粉（从嗤之以鼻到自己网购）, 考研兔子, 白色信封（那封信）, 深蓝色笔记本（日记本）, 消费记录, 迎新晚会视频, 黄色风衣",
            "scene_location": "南方某大学物理学院考研教室（学院1楼角落的大教室，能坐八十人但自始至终只有三人，靠窗最里面那一排：陈北坐最前面、张杰坐中间、苏月坐后面几排，兔子笼子放在最后一排角落，晚上九点后关门放兔子出来跑）、学校后门小吃街（螺蛳粉的酸辣味）、猫屋咖啡（学校附近小巷子里）、食堂二楼、操场跑道（傍晚六点夕阳）、图书馆四楼自习室（窗外芒果树）",
            "time_constraint": "2011年至2020年代，从大四考研到步入社会成家立业。主要集中在2014-2015考研准备期（第一部）、2015-2016成都重逢与表白（第二部）、2016-2018异地与消磨（第三部）、2018至今步入社会（第四部），穿插大一到大三的回忆碎片",
        },
        "choose_configs": {
            "prompt_draft_llm": "DeepSeek V4 Pro",
            "chapter_outline_llm": "DeepSeek V4 Pro",
            "architecture_llm": "Claude Sonnet 4.6",
            "final_chapter_llm": "Claude Sonnet 4.6",
            "consistency_review_llm": "DeepSeek V4 Pro"
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
    """启动现实主义青春小说写作智能体"""
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
