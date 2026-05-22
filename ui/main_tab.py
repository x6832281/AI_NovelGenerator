# ui/main_tab.py
# -*- coding: utf-8 -*-
import customtkinter as ctk
from tkinter import messagebox
from ui.context_menu import TextWidgetContextMenu

def build_main_tab(self):
    """
    主Tab包含左侧的"本章内容"编辑框和输出日志，以及右侧的主要操作和参数设置区
    """
    self.main_tab = self.tabview.add("Main Functions")
    self.main_tab.rowconfigure(0, weight=1)
    self.main_tab.columnconfigure(0, weight=1)
    self.main_tab.columnconfigure(1, weight=0)

    self.left_frame = ctk.CTkFrame(self.main_tab)
    self.left_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

    self.right_frame = ctk.CTkFrame(self.main_tab)
    self.right_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)

    build_left_layout(self)
    build_right_layout(self)

from utils import get_word_count

def build_left_layout(self):
    """
    左侧区域：本章内容(可编辑) + Step流程按钮 + 输出日志(只读)
    """
    self.left_frame.grid_rowconfigure(0, weight=0)
    self.left_frame.grid_rowconfigure(1, weight=2)
    self.left_frame.grid_rowconfigure(2, weight=0)
    self.left_frame.grid_rowconfigure(3, weight=1)
    self.left_frame.columnconfigure(0, weight=1)

    self.chapter_label = ctk.CTkLabel(self.left_frame, text="本章内容（可编辑）  字数：0", font=("Microsoft YaHei", 12))
    self.chapter_label.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="w")

    # 章节文本编辑框
    self.chapter_result = ctk.CTkTextbox(self.left_frame, wrap="word", font=("Microsoft YaHei", 14))
    TextWidgetContextMenu(self.chapter_result)
    self.chapter_result.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))



    def update_word_count(event=None):
        text = self.chapter_result.get("0.0", "end-1c")
        count = get_word_count(text)
        self.chapter_label.configure(text=f"本章内容（可编辑）  字数：{count}")

    self.chapter_result.bind("<KeyRelease>", update_word_count)
    self.chapter_result.bind("<ButtonRelease>", update_word_count)

    # Step 按钮区域
    self.step_buttons_frame = ctk.CTkFrame(self.left_frame)
    self.step_buttons_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
    self.step_buttons_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)


    self.btn_generate_architecture = ctk.CTkButton(
        self.step_buttons_frame,
        text="Step1. 生成架构",
        command=self.generate_novel_architecture_ui,
        font=("Microsoft YaHei", 12)
    )
    self.btn_generate_architecture.grid(row=0, column=0, padx=5, pady=2, sticky="ew")

    self.btn_generate_directory = ctk.CTkButton(
        self.step_buttons_frame,
        text="Step2. 生成目录",
        command=self.generate_chapter_blueprint_ui,
        font=("Microsoft YaHei", 12)
    )
    self.btn_generate_directory.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

    self.btn_generate_chapter = ctk.CTkButton(
        self.step_buttons_frame,
        text="Step3. 生成草稿",
        command=self.generate_chapter_draft_ui,
        font=("Microsoft YaHei", 12)
    )
    self.btn_generate_chapter.grid(row=0, column=2, padx=5, pady=2, sticky="ew")

    self.btn_finalize_chapter = ctk.CTkButton(
        self.step_buttons_frame,
        text="Step4. 定稿章节",
        command=self.finalize_chapter_ui,
        font=("Microsoft YaHei", 12)
    )
    self.btn_finalize_chapter.grid(row=0, column=3, padx=5, pady=2, sticky="ew")

    self.btn_batch_generate = ctk.CTkButton(
        self.step_buttons_frame,
        text="批量生成",
        command=self.generate_batch_ui,
        font=("Microsoft YaHei", 12)
    )
    self.btn_batch_generate.grid(row=0, column=4, padx=5, pady=2, sticky="ew")


    # 底部区域：日志 + AI检查 标签页
    self.bottom_tabview = ctk.CTkTabview(self.left_frame)
    self.bottom_tabview.grid(row=3, column=0, sticky="nsew", padx=5, pady=(0, 5))

    # 输出日志标签页
    self.log_tab = self.bottom_tabview.add("输出日志")
    self.log_tab.rowconfigure(0, weight=1)
    self.log_tab.columnconfigure(0, weight=1)

    self.log_text = ctk.CTkTextbox(self.log_tab, wrap="word", font=("Microsoft YaHei", 12))
    TextWidgetContextMenu(self.log_text)
    self.log_text.grid(row=0, column=0, sticky="nsew")
    self.log_text.configure(state="disabled")

    # AI检查标签页
    self.ai_check_tab = self.bottom_tabview.add("AI检查")
    self.ai_check_tab.rowconfigure(1, weight=1)
    self.ai_check_tab.columnconfigure(0, weight=1)

    ai_btn_frame = ctk.CTkFrame(self.ai_check_tab)
    ai_btn_frame.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
    ai_btn_frame.columnconfigure(0, weight=1)

    self.btn_ai_check = ctk.CTkButton(
        ai_btn_frame, text="开始AI检查(需LLM)",
        command=self.do_ai_check,
        font=("Microsoft YaHei", 12), width=140
    )
    self.btn_ai_check.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    self.btn_segmented_ai_check = ctk.CTkButton(
        ai_btn_frame, text="分段AI检测(无需LLM)",
        command=self.do_segmented_ai_check,
        font=("Microsoft YaHei", 12), width=170
    )
    self.btn_segmented_ai_check.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    self.ai_result_text = ctk.CTkTextbox(self.ai_check_tab, wrap="word", font=("Microsoft YaHei", 12))
    TextWidgetContextMenu(self.ai_result_text)
    self.ai_result_text.grid(row=1, column=0, sticky="nsew", padx=2, pady=(0, 2))
    self.ai_result_text.configure(state="disabled")

    # 基本检查标签页
    self.basic_check_tab = self.bottom_tabview.add("基本检查")
    self.basic_check_tab.rowconfigure(1, weight=1)
    self.basic_check_tab.columnconfigure(0, weight=1)

    basic_btn_frame = ctk.CTkFrame(self.basic_check_tab)
    basic_btn_frame.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
    basic_btn_frame.columnconfigure(0, weight=1)

    self.btn_basic_check = ctk.CTkButton(
        basic_btn_frame, text="开始基本检查",
        command=self.do_basic_check,
        font=("Microsoft YaHei", 12), width=120
    )
    self.btn_basic_check.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    self.basic_result_text = ctk.CTkTextbox(self.basic_check_tab, wrap="word", font=("Microsoft YaHei", 12))
    TextWidgetContextMenu(self.basic_result_text)
    self.basic_result_text.grid(row=1, column=0, sticky="nsew", padx=2, pady=(0, 2))
    self.basic_result_text.configure(state="disabled")

def build_right_layout(self):
    """
    右侧区域：配置区(tabview) + 小说主参数 + 可选功能按钮
    """
    self.right_frame.grid_rowconfigure(0, weight=0)
    self.right_frame.grid_rowconfigure(1, weight=1)
    self.right_frame.grid_rowconfigure(2, weight=0)
    self.right_frame.columnconfigure(0, weight=1)

    # 配置区（AI/Embedding）
    self.config_frame = ctk.CTkFrame(self.right_frame, corner_radius=10, border_width=2, border_color="gray")
    self.config_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    self.config_frame.columnconfigure(0, weight=1)
    # 其余部分将在 config_tab.py 与 novel_params_tab.py 中构建
