"""
根窗口管理 - 负责 Tk 根窗口的创建与全屏配置。
"""

import tkinter as tk
from typing import Tuple

import config


class RootWindow:
    """管理 Tkinter 根窗口。"""

    def __init__(self):
        self._tk = tk.Tk()
        self._setup_window()

    @property
    def tk(self) -> tk.Tk:
        return self._tk

    def _setup_window(self) -> None:
        """配置根窗口属性。"""
        self._tk.title("作业管理器")
        self._tk.geometry("1280x720")
        self._tk.attributes("-fullscreen", True)
        self._tk.config(bg=config.COLOR_BG_MAIN)
        self._tk.resizable(False, False)

        # 全局默认样式
        self._tk.option_add("*Background", config.COLOR_BG_MAIN)
        self._tk.option_add("*Foreground", config.COLOR_FG_PRIMARY)
        self._tk.option_add("*Font", config.FONT_DEFAULT)

    def get_screen_size(self) -> Tuple[int, int]:
        """返回屏幕宽高。"""
        return (self._tk.winfo_screenwidth(), self._tk.winfo_screenheight())

    def mainloop(self) -> None:
        """进入主事件循环。"""
        self._tk.mainloop()

    def update(self) -> None:
        """强制更新界面。"""
        self._tk.update()

    def after(self, ms: int, callback, *args) -> str:
        """安排延迟调用（返回 after id）。"""
        return self._tk.after(ms, callback, *args)

    def after_cancel(self, aid: str) -> None:
        """取消延迟调用。"""
        try:
            self._tk.after_cancel(aid)
        except Exception:
            pass
