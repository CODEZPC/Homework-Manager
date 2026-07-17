"""
作业添加/编辑对话框 - 弹出式窗口用于创建或修改作业。
"""

import tkinter as tk
from tkinter import Toplevel, Label, Entry, Button, Frame, OptionMenu, StringVar
from typing import Any, Callable, List, Optional, Tuple

import config
from services.time_analyzer import analyze_time_string, parse_deadline


class HomeworkDialog:
    """作业添加/编辑对话框。"""

    def __init__(
        self,
        parent: tk.Tk,
        subject_display_names: List[str],
        subject_codes: List[str],
        emphasize_levels: List[str],
        on_submit: Callable,
        # 编辑模式参数（可选）
        subject_index: int = 0,
        content_text: str = "",
        deadline_value: Any = None,
        emphasize_index: int = 0,
        replace_target: Optional[Tuple[str, int]] = None,
        homework_limit: int = 100,
        current_count: int = 0,
    ):
        """
        创建添加/编辑对话框。

        :param on_submit: 提交回调，接收 (subject_index, subject_code, content, deadline, emphasize, replace_target)
        """
        self._tk = parent
        self._subject_names = subject_display_names
        self._subject_codes = subject_codes
        self._emphasize_levels = emphasize_levels
        self._on_submit = on_submit
        self._replace_target = replace_target
        self._homework_limit = homework_limit
        self._current_count = current_count

        self._window = Toplevel(parent)
        self._window.title(
            "作业管理器·新建作业" if not replace_target else "作业管理器·编辑作业"
        )
        self._window.config(bg=config.COLOR_BG_MAIN)
        self._window.resizable(False, False)
        self._window.attributes("-topmost", True)

        self._subject_var = subject_display_names[subject_index]
        self._emphasize_var = StringVar(self._window)
        self._emphasize_var.set(emphasize_levels[emphasize_index])

        self._build_ui(subject_index, content_text, deadline_value)

    def _build_ui(
        self, subject_index: int, content_text: str, deadline_value: Any
    ) -> None:
        """构建对话框界面。"""
        w = self._window

        # 占位行
        Label(w, text=" ").grid(row=0, column=0)
        Label(w, text=" ").grid(row=999, column=999)

        # ── 科目选择 ──
        Label(w, text="科目", bg=config.COLOR_BG_MAIN, font=config.FONT_DIALOG).grid(
            row=1, column=1
        )

        subject_frame = Frame(w, relief=tk.FLAT)
        subject_frame.grid(row=1, column=2)

        num = len(self._subject_names)
        row1_count = (num + 1) // 2
        row1 = Frame(subject_frame)
        row2 = Frame(subject_frame)
        row1.pack()
        row2.pack()

        self._subject_btns: List[Button] = []

        def on_subject_change(idx: int):
            self._subject_var = self._subject_names[idx]
            for i, btn in enumerate(self._subject_btns):
                btn.configure(
                    fg=config.COLOR_FG_ACCENT if i == idx else config.COLOR_FG_PRIMARY
                )

        for i, name in enumerate(self._subject_names):
            parent_frame = row1 if i < row1_count else row2
            btn = Button(
                parent_frame,
                text=name,
                command=lambda i=i: on_subject_change(i),
                relief=tk.FLAT,
                font=config.FONT_DIALOG,
                fg=(
                    config.COLOR_FG_ACCENT
                    if subject_index == i
                    else config.COLOR_FG_PRIMARY
                ),
            )
            btn.pack(side="left", expand=True)
            self._subject_btns.append(btn)

        # ── 内容输入 ──
        Label(w, text="内容", bg=config.COLOR_BG_MAIN, font=config.FONT_DIALOG).grid(
            row=2, column=1
        )

        self._content_entry = Entry(
            w,
            width=60,
            relief=tk.RIDGE,
            font=config.FONT_DIALOG,
        )
        self._content_entry.grid(row=2, column=2)
        if content_text:
            self._content_entry.insert(0, content_text)

        # ── 截止时间 ──
        Label(
            w, text="截止时间", bg=config.COLOR_BG_MAIN, font=config.FONT_DIALOG
        ).grid(row=3, column=1, rowspan=2)

        import time

        if deadline_value is not None:
            try:
                if deadline_value == 0 or isinstance(deadline_value, str):
                    raise TypeError
                time_str = time.strftime(
                    "%Y/%m/%d %H:%M", time.localtime(int(deadline_value))
                )
            except (TypeError, ValueError, OverflowError):
                time_str = str(deadline_value) if deadline_value else "0"
        else:
            time_str = time.strftime("%Y/%m/%d 22:10", time.localtime(time.time()))

        self._time_var = StringVar(w, value=time_str)
        self._time_entry = Entry(
            w,
            width=20,
            textvariable=self._time_var,
            relief=tk.FLAT,
            justify="center",
            font=config.FONT_DIALOG,
        )
        self._time_entry.grid(row=3, column=2)

        # 时间快捷按钮
        time_btn_frame = Frame(w, relief=tk.FLAT)
        time_btn_frame.grid(row=4, column=2)

        time_presets = [
            ("不收", lambda: self._time_var.set("0")),
            ("-1天", lambda: self._adjust_time(-86400)),
            (
                "今天",
                lambda: self._time_var.set(
                    time.strftime("%Y/%m/%d 22:10", time.localtime(time.time()))
                ),
            ),
            (
                "明天",
                lambda: self._time_var.set(
                    time.strftime("%Y/%m/%d 22:10", time.localtime(time.time() + 86400))
                ),
            ),
            (
                "后天",
                lambda: self._time_var.set(
                    time.strftime(
                        "%Y/%m/%d 22:10", time.localtime(time.time() + 86400 * 2)
                    )
                ),
            ),
            ("+1天", lambda: self._adjust_time(86400)),
        ]

        for text, cmd in time_presets:
            btn = Button(
                time_btn_frame,
                text=text,
                command=cmd,
                relief=tk.FLAT,
                font=config.FONT_DIALOG,
            )
            btn.pack(side="left", expand=True)

        # ── 优先级 ──
        Label(w, text="优先级", bg=config.COLOR_BG_MAIN, font=config.FONT_DIALOG).grid(
            row=5, column=1
        )

        OptionMenu(w, self._emphasize_var, *self._emphasize_levels).grid(
            row=5, column=2
        )

        # ── 提交/取消 ──
        Button(
            w,
            text="提交",
            command=self._submit,
            relief=tk.FLAT,
            font=config.FONT_DIALOG,
        ).grid(row=6, column=2, sticky="e")

        Button(
            w,
            text="取消",
            command=w.destroy,
            relief=tk.FLAT,
            font=config.FONT_DIALOG,
        ).grid(row=6, column=2, sticky="w")

        # 居中偏下显示
        w.update_idletasks()
        sw = w.winfo_screenwidth()
        sh = w.winfo_screenheight()
        ww = w.winfo_width()
        wh = w.winfo_height()
        x = (sw - ww) // 2
        y = int((sh - wh) * 0.8)
        w.geometry(f"+{x}+{y}")

    def _adjust_time(self, delta: int) -> None:
        """调整当前时间输入值 ±delta 秒。"""
        import time

        current = self._time_var.get()
        try:
            ts = time.mktime(
                time.strptime(analyze_time_string(current), "%Y/%m/%d %H:%M")
            )
            new_ts = ts + delta
            self._time_var.set(time.strftime("%Y/%m/%d %H:%M", time.localtime(new_ts)))
        except (ValueError, OverflowError):
            pass

    def _submit(self) -> None:
        """提交作业数据。"""
        import tkinter.messagebox as messagebox

        # 检查上限
        if self._current_count >= self._homework_limit and not self._replace_target:
            self._window.attributes("-topmost", False)
            if not messagebox.askyesno(
                "作业管理器·超过上限", "作业数量已达上限，是否强制添加？"
            ):
                self._window.attributes("-topmost", True)
                return
            self._window.attributes("-topmost", True)

        subject_name = self._subject_var
        try:
            subject_idx = self._subject_names.index(subject_name)
        except ValueError:
            subject_idx = 0
        subject_code = self._subject_codes[subject_idx]

        content = self._content_entry.get()
        deadline = parse_deadline(self._time_var.get())
        emphasize = self._emphasize_var.get()

        self._on_submit(
            subject_idx=subject_idx,
            subject_code=subject_code,
            content=content,
            deadline=deadline,
            emphasize=emphasize,
            replace_target=self._replace_target,
        )
        self._window.destroy()
