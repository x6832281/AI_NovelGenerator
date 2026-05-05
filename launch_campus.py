# launch_campus.py
# -*- coding: utf-8 -*-
"""
校园青春回忆·爱情与遗憾 —— AI小说写作智能体 一键启动脚本

融合写作风格：村上春树《挪威的森林》× 太宰治《人间失格》× 八月长安《最好的我们》× 路遥《平凡的世界》
参考书目（按优先级）：
  ★★★ 主要参考：挪威的森林 / 人间失格 / 最好的我们
  ★  辅助参考：平凡的世界 / 匆匆那年 / 那时年少 / 穆斯林的葬礼

用法：
    python launch_campus.py

首次运行会自动：
  1. 将校园青春风格提示词注入提示词模块
  2. 加载 config_campus.json 配置（如不存在则自动创建）
  3. 启动 GUI 工作台
"""

import os
import sys
import json
import shutil
import importlib


def setup_campus_environment():
    """
    设置校园青春创作环境：
    1. 注入校园提示词到 prompt_definitions 模块
    2. 确保使用 config_campus.json 配置
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # ── 步骤1: 注入校园风格提示词 ──
    print("=" * 60)
    print("  🎓 校园青春回忆 · AI 小说写作智能体")
    print("  风格：村上春树《挪威的森林》× 太宰治《人间失格》× 八月长安《最好的我们》")
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

        print(f"  ✅ 已注入 {injected_count} 个校园青春风格提示词")
        print(f"  📚 核心参考：《挪威的森林》《人间失格》《最好的我们》")
        print(f"  📚 辅助参考：《平凡的世界》《匆匆那年》《那时年少》《穆斯林的葬礼》")
    except Exception as e:
        print(f"  ⚠️ 提示词注入警告: {e}")
        print("  将使用默认提示词继续运行...")

    # ── 步骤2: 检查知识库文件 ──
    knowledge_dir = os.path.join(base_dir, "knowledge")
    if os.path.exists(knowledge_dir):
        knowledge_files = os.listdir(knowledge_dir)
        print(f"\n  📖 写作风格知识库 ({len(knowledge_files)} 个文件):")
        for f in knowledge_files:
            print(f"     ▸ {f}")

    # ── 步骤3: 配置文件处理 ──
    config_campus = os.path.join(base_dir, "config_campus.json")
    config_default = os.path.join(base_dir, "config.json")

    if not os.path.exists(config_campus):
        print(f"\n  ⚠️ 未找到 config_campus.json，正在自动创建...")
        create_default_campus_config(config_campus)

    # 备份原有 config.json（如果存在且与校园配置不同）
    if os.path.exists(config_default):
        with open(config_default, "r", encoding="utf-8") as f:
            old_config = json.load(f)
        old_topic = old_config.get("other_params", {}).get("topic", "")
        if "校园" not in old_topic and "春上" not in old_topic:
            backup_path = config_default + ".bak"
            shutil.copy2(config_default, backup_path)
            print(f"\n  💾 已备份原配置到: {backup_path}")

    # 用校园配置覆盖当前配置
    shutil.copy2(config_campus, config_default)
    print(f"  ✅ 已加载校园青春故事配置")

    print("\n" + "=" * 60)
    print("  🚀 启动 GUI 工作台...")
    print("  💡 提示: 启动后请先配置 API Key, 再开始创作!")
    print("  💡 可导入 knowledge/ 目录下的文件作为写作风格知识库")
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
            "topic": "2008年秋天，一个来自北方小城的男生考入南方某大学，在图书馆邂逅了改变他整个大学时光的女孩。四年时光，从相遇到错过——不是谁的错，只是青春本身就充满了来不及和留不住",
            "genre": "校园青春文学·爱情与遗憾",
            "num_chapters": 36,
            "word_number": 3000,
            "filepath": "",
            "chapter_num": "1",
            "user_guidance": "这是一部融合多部经典作品风格的长篇校园青春小说。核心参考：村上春树《挪威的森林》式的克制深情与感官精确、太宰治《人间失格》式的自我解剖与温柔绝望、八月长安《最好的我们》式的'小事大写'与口语化幽默。辅助参考：路遥《平凡的世界》式的质朴社会观察、九夜茴《匆匆那年》式的年代记忆、一草《那时年少》式的校园成长、霍达《穆斯林的葬礼》式的悲美意象。采用第一人称回顾视角。语言：克制的深情——用平静的语调写汹涌情感，用朴素句子承载沉重命运。注重日常细节，用环境折射内心，用行动表达感情。融入：阶级差异、音乐、书信、季节更替作为情感计时器。整体不追求强情节，追求情感的累积与释放——像真正的青春一样，缓慢而不可逆转。",
            "characters_involved": "林晚, 苏雨, 陈北, 沈若溪",
            "key_items": "旧书店买的《挪威的森林》, 银色老式手表, 吉他社宣传单, 图书馆四楼靠窗第四排座位",
            "scene_location": "南方某大学校园: 图书馆、操场、梧桐大道、老教学楼天台、学校后门小吃街、男生宿舍420室",
            "time_constraint": "2008年-2012年，从大一入学到大四毕业",
        },
        "choose_configs": {
            "prompt_draft_llm": "DeepSeek V3",
            "chapter_outline_llm": "DeepSeek V3",
            "architecture_llm": "Gemini 2.5 Flash",
            "final_chapter_llm": "GPT 5",
            "consistency_review_llm": "DeepSeek V3",
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
