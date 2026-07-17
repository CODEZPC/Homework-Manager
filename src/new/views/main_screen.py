"""
主屏幕视图 - 整合顶部按钮栏、作业 Canvas、侧边按钮、底部信息栏。
"""

import tkinter as tk
from tkinter import Frame, Button, Canvas, Label
from typing import Callable, List, Optional, Tuple

import config


class MainScreen:
    """主全屏界面，包含所有 UI 子组件。"""

    def __init__(
        self,
        parent: tk.Tk,
        on_exit: Callable[[], None],
        on_add: Callable[[], None],
        on_clear: Callable[[], None],
        on_menu: Callable[[], None],
        on_help: Callable[[], None],
        on_update_click: Callable[[], None],
        screen_width: int,
        screen_height: int,
    ):
        self._tk = parent
        self._screen_w = screen_width
        self._screen_h = screen_height
        self._on_exit = on_exit
        self._on_add = on_add
        self._on_clear = on_clear
        self._on_menu = on_menu
        self._on_help = on_help

        # 计算时间显示区域的 X 坐标
        self.time_display_x = screen_width - config.UI_TIME_DISPLAY_WIDTH

        # ── 主容器 ──
        self.main_frame = Frame(parent, relief=tk.FLAT)
        self.main_frame.place(x=0, y=0, relheight=1, relwidth=1)

        # ── 遮罩层（左右边距） ──
        self._mask_left = Frame(self.main_frame, width=config.UI_SIDE_MARGIN_LEFT)
        self._mask_right = Frame(self.main_frame, width=config.UI_SIDE_MARGIN_RIGHT)

        # ── 顶部按钮栏 ──
        self._top_frame = Frame(self.main_frame, relief=tk.FLAT)
        self._create_top_buttons()

        # ── 作业 Canvas ──
        canvas_width = self.time_display_x - config.UI_SIDE_MARGIN_LEFT - 5
        self.canvas = Canvas(
            self.main_frame,
            bg=config.COLOR_BG_MAIN,
            highlightthickness=0,
        )
        self.canvas.place(
            x=config.UI_SIDE_MARGIN_LEFT,
            y=config.UI_CANVAS_TOP,
            width=canvas_width,
            height=screen_height - config.UI_CANVAS_BOTTOM_MARGIN,
        )

        # ── 侧边操作按钮 ──
        self._side_delete = Button(
            self.main_frame,
            text="×",
            fg=config.COLOR_FG_DIM,
            relief=tk.FLAT,
            font=config.FONT_SIDE_BUTTON,
        )
        self._side_edit = Button(
            self.main_frame,
            text="E",
            fg=config.COLOR_FG_DIM,
            relief=tk.FLAT,
            font=config.FONT_SIDE_BUTTON,
        )

        # ── 底部信息栏 ──
        self.info_bar = InfoBar(
            self.main_frame,
            on_update_click=on_update_click,
        )

        # ── 遮罩放置 ──
        self._mask_left.place(x=0, y=0, relheight=1)
        self._mask_right.place(
            x=screen_width - config.UI_SIDE_MARGIN_RIGHT, y=0, relheight=1
        )
        self.info_bar.place(screen_height)

    # ──────────────── 顶部按钮 ────────────────

    def _create_top_buttons(self) -> None:
        """创建顶部按钮栏的所有按钮。"""
        btn_config = {
            "fg": config.COLOR_FG_DIM,
            "font": config.FONT_BUTTON,
            "relief": tk.FLAT,
            "width": 3,
        }

        buttons = [
            ("退出", self._on_exit),
            ("添加", self._on_add),
            ("清理", self._on_clear),
            ("帮助", self._on_help),
            ("菜单", self._on_menu),
        ]

        self._top_buttons: List[Button] = []
        for text, cmd in reversed(buttons):
            btn = Button(self._top_frame, text=text, command=cmd, **btn_config)
            btn.pack(side="right")
            self._top_buttons.append(btn)

        # 为 添加 和 清理 按钮保存引用以便冷却
        self._btn_exit = self._top_buttons[-1]
        self._btn_add = self._top_buttons[-2]
        self._btn_clear = self._top_buttons[-3]
        self._btn_help = self._top_buttons[-4]
        self._btn_menu = self._top_buttons[-5]

    # ──────────────── 顶部栏显示/隐藏 ────────────────

    def show_top_bar(self) -> None:
        """显示顶部按钮栏。"""
        self._top_frame.place(x=0, y=0, relwidth=1)

    def hide_top_bar(self) -> None:
        """隐藏顶部按钮栏。"""
        self._top_frame.place_forget()

    # ──────────────── 侧边按钮 ────────────────

    def show_side_buttons(
        self,
        index: int,
        item_count: int,
        on_delete: Callable[[], None],
        on_edit: Callable[[], None],
    ) -> None:
        """在指定行显示侧边编辑/删除按钮。"""
        spacing = (
            config.UI_ITEM_SPACING_COMPACT
            if item_count >= config.UI_ITEM_SPACING_THRESHOLD
            else config.UI_ITEM_SPACING_NORMAL
        )
        y = config.UI_CANVAS_TOP + 2 + index * spacing

        self._side_delete.place(x=5, y=y)
        self._side_edit.place(x=25, y=y)
        self._side_delete.config(command=on_delete)
        self._side_edit.config(command=on_edit)

    def hide_side_buttons(self) -> None:
        """隐藏侧边按钮。"""
        self._side_delete.place_forget()
        self._side_edit.place_forget()

    # ──────────────── 按钮冷却 ────────────────

    def cooldown_button(
        self,
        button: Button,
        original_text: str,
        remaining: int = config.BUTTON_COOLDOWN_TICKS,
    ) -> None:
        """
        按钮冷却：短暂禁用防止重复点击。
        remaining 以 1/10 秒为单位。
        """
        if remaining <= 0:
            button.config(state=tk.NORMAL, text=original_text, font=config.FONT_BUTTON)
            return
        button.config(state=tk.DISABLED)
        self._tk.after(
            100, lambda: self.cooldown_button(button, original_text, remaining - 1)
        )

    # ──────────────── 鼠标位置计算 ────────────────

    def get_mouse_position(self, event: tk.Event) -> Tuple[int, int]:
        """获取鼠标在窗口内的坐标。"""
        x = event.x_root - self._tk.winfo_rootx()
        y = event.y_root - self._tk.winfo_rooty()
        return (x, y)

    def get_hovered_index(self, y: int, item_count: int) -> int:
        """根据鼠标 Y 坐标计算悬停的作业行索引。"""
        spacing = (
            config.UI_ITEM_SPACING_COMPACT
            if item_count >= config.UI_ITEM_SPACING_THRESHOLD
            else config.UI_ITEM_SPACING_NORMAL
        )
        idx = int((y - config.UI_CANVAS_TOP) // spacing)
        if idx >= item_count:
            return -1
        return idx


class InfoBar:
    """底部信息栏，显示版本、时间、作业数、负载、鼠标、Tick、更新状态。"""

    def __init__(self, parent: Frame, on_update_click: Callable[[], None]):
        self._frame = Frame(parent, relief=tk.FLAT)

        self.labels: List[Label] = []
        field_names = ["basic", "time", "homework", "load", "mouse", "tick", "message"]

        for name in field_names:
            lbl = Label(
                self._frame,
                text="",
                font=config.FONT_INFO,
                fg=config.COLOR_FG_DIM,
            )
            lbl.pack(side="left")
            setattr(self, f"lbl_{name}", lbl)
            self.labels.append(lbl)

        # 更新消息区域可点击
        self.lbl_message.bind("<Button-1>", lambda e: on_update_click())

    def place(self, screen_height: int) -> None:
        """放置信息栏。"""
        self._frame.place(
            x=config.UI_INFO_BAR_LEFT, y=screen_height - config.UI_INFO_BAR_BOTTOM
        )

    def update_basic(
        self, text: str, fg: str = config.COLOR_FG_DIM, bg: str = config.COLOR_BG_MAIN
    ) -> None:
        self.lbl_basic.config(text=text, fg=fg, bg=bg)

    def update_time(self, text: str) -> None:
        self.lbl_time.config(text=text)

    def update_homework_count(
        self, text: str, fg: str = config.COLOR_FG_DIM, bg: str = config.COLOR_BG_MAIN
    ) -> None:
        self.lbl_homework.config(text=text, fg=fg, bg=bg)

    def update_load(
        self, text: str, fg: str = config.COLOR_FG_DIM, bg: str = config.COLOR_BG_MAIN
    ) -> None:
        self.lbl_load.config(text=text, fg=fg, bg=bg)

    def update_mouse(self, text: str, fg: str = config.COLOR_FG_DIM) -> None:
        self.lbl_mouse.config(text=text, fg=fg)

    def update_tick(self, text: str) -> None:
        self.lbl_tick.config(text=text)

    def update_message(
        self, text: str, fg: str = config.COLOR_FG_DIM, bg: str = config.COLOR_BG_MAIN
    ) -> None:
        self.lbl_message.config(text=text, fg=fg, bg=bg)
