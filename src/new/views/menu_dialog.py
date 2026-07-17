"""
科目管理菜单 - 科目的增删改查与排序。
"""

import tkinter as tk
from tkinter import (Frame, Label, Button, Listbox, Toplevel,
                     messagebox, simpledialog, ttk)
from tkinter import StringVar
import json
from typing import Callable, Dict, Optional

import config
from models.data_store import DataStore


class MenuDialog:
    """科目管理面板。"""

    def __init__(self, parent: tk.Tk,
                 data_store: DataStore,
                 on_restart: Callable[[], None]):
        self._tk = parent
        self._store = data_store
        self._on_restart = on_restart
        self._subjects: Dict[str, str] = {}
        self._needs_restart = False

        self._load_subjects()

        # ── 创建嵌入主窗口的覆盖面板 ──
        self._frame = Frame(parent, relief=tk.FLAT)
        self._frame.place(x=0, y=0, relheight=1, relwidth=1)

        self._build_ui()

    def _load_subjects(self) -> None:
        """从 setting.json 加载科目配置。"""
        self._subjects = self._store.get_subjects()

    def _save_subjects(self) -> None:
        """保存科目配置到 setting.json。"""
        self._store.save_subjects(self._subjects)

    def _sync_homework_json(self) -> None:
        """同步 homework.json 的键与 Subjects 保持一致。"""
        hw_data = self._store.load_homework()
        valid_codes = set(self._subjects.values())
        existing_codes = set(hw_data.keys())

        for code in valid_codes - existing_codes:
            hw_data[code] = []
        for code in existing_codes - valid_codes:
            del hw_data[code]

        self._store.save_homework(hw_data)

    def _refresh_listbox(self) -> None:
        """刷新科目列表显示。"""
        self._listbox.delete(0, tk.END)
        for name, code in self._subjects.items():
            self._listbox.insert(tk.END, f"{name}  →  {code}")

    # ──────────────── UI 构建 ────────────────

    def _build_ui(self) -> None:
        # 顶部关闭栏
        top_bar = Frame(self._frame, relief=tk.FLAT)
        top_bar.place(x=0, y=0, relwidth=1)

        Button(
            top_bar,
            text="退出菜单",
            fg=config.COLOR_FG_DIM,
            font=config.FONT_BUTTON,
            relief=tk.FLAT,
            command=self.exit,
        ).pack(side="right")

        # 科目管理标题
        Label(
            self._frame,
            text="科目管理",
            fg=config.COLOR_FG_PRIMARY,
            font=("汉仪文黑-85W", 16),
        ).place(x=20, y=30)

        # 科目列表
        self._build_subject_list()

        # 操作按钮
        self._build_action_buttons()

        self._refresh_listbox()

    def _build_subject_list(self) -> None:
        """构建带滚动条的科目列表。"""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Custom.Vertical.TScrollbar",
            background="#2E333C",
            troughcolor=config.COLOR_BG_DARK,
            arrowcolor=config.COLOR_FG_PRIMARY,
            bordercolor=config.COLOR_BG_DARK,
            lightcolor="#3A404C",
            darkcolor=config.COLOR_BG_DARK,
            relief="flat",
        )
        style.configure(
            "Custom.Vertical.TScrollbar.thumb",
            background="#2E333C",
            bordercolor=config.COLOR_BG_DARK,
            relief="flat",
        )
        style.map(
            "Custom.Vertical.TScrollbar",
            background=[
                ("active", "#3A404C"),
                ("pressed", config.COLOR_BG_DARK),
                ("disabled", "#3A404C"),
            ],
            troughcolor=[("disabled", config.COLOR_BG_DARK)],
            arrowcolor=[("disabled", "#5A5F6A")],
        )

        list_frame = Frame(self._frame, relief=tk.FLAT)
        list_frame.place(x=20, y=70, width=380, height=300)

        scrollbar = ttk.Scrollbar(list_frame, style="Custom.Vertical.TScrollbar")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._listbox = Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            bg=config.COLOR_BG_DARK,
            fg=config.COLOR_FG_PRIMARY,
            selectbackground=config.COLOR_BG_SELECT,
            selectforeground=config.COLOR_FG_WHITE,
            font=config.FONT_LISTBOX,
            highlightthickness=0,
            borderwidth=0,
        )
        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._listbox.yview)

    def _build_action_buttons(self) -> None:
        """构建操作按钮行。"""
        action_frame = Frame(self._frame, relief=tk.FLAT, width=380, height=40)
        action_frame.place(x=20, y=380)
        action_frame.pack_propagate(False)

        btn_style = {
            "fg": config.COLOR_FG_DIM,
            "font": config.FONT_BUTTON,
            "relief": tk.FLAT,
        }

        Button(action_frame, text="添加", command=self._add_subject,
               **btn_style).pack(side="left", fill=tk.X, expand=True)
        Button(action_frame, text="重命名", command=self._rename_subject,
               **btn_style).pack(side="left", fill=tk.X, expand=True)
        Button(action_frame, text="删除", command=self._delete_subject,
               **btn_style).pack(side="left", fill=tk.X, expand=True)
        Button(action_frame, text="上移", command=self._move_up,
               **btn_style).pack(side="left", fill=tk.X, expand=True)
        Button(action_frame, text="下移", command=self._move_down,
               **btn_style).pack(side="left", fill=tk.X, expand=True)

    # ──────────────── CRUD 操作 ────────────────

    def _add_subject(self) -> None:
        name = simpledialog.askstring(
            "添加科目", "请输入科目显示名称：", parent=self._frame)
        if not name or not name.strip():
            return
        name = name.strip()
        if name in self._subjects:
            messagebox.showwarning("作业管理器·错误", "科目名称已存在。",
                                   parent=self._frame)
            return

        code = simpledialog.askstring(
            "添加科目", f"请输入科目键名（英文标识）：", parent=self._frame)
        if not code or not code.strip():
            return
        code = code.strip().upper()
        if code in self._subjects.values():
            messagebox.showwarning("作业管理器·错误", "科目键名已存在。",
                                   parent=self._frame)
            return

        self._subjects[name] = code
        self._save_subjects()
        self._sync_homework_json()
        self._refresh_listbox()
        self._needs_restart = True

    def _rename_subject(self) -> None:
        selection = self._listbox.curselection()
        if not selection:
            messagebox.showinfo("作业管理器·错误", "请先选择要重命名的科目。",
                                parent=self._frame)
            return

        idx = selection[0]
        old_name = list(self._subjects.keys())[idx]
        old_code = self._subjects[old_name]

        new_name = simpledialog.askstring(
            "重命名科目", f"当前名称：{old_name}\n新显示名称：",
            parent=self._frame, initialvalue=old_name)
        if not new_name or not new_name.strip():
            return
        new_name = new_name.strip()
        if new_name != old_name and new_name in self._subjects:
            messagebox.showwarning("作业管理器·错误", "科目名称已存在。",
                                   parent=self._frame)
            return

        new_code = simpledialog.askstring(
            "重命名科目", f"当前键名：{old_code}\n新键名（留空保持不变）：",
            parent=self._frame, initialvalue=old_code)
        if new_code is not None:
            new_code = new_code.strip().upper()
            if not new_code:
                new_code = old_code

        if new_code != old_code and new_code in self._subjects.values():
            messagebox.showwarning("作业管理器·错误", "科目键名已存在。",
                                   parent=self._frame)
            return

        del self._subjects[old_name]
        self._subjects[new_name] = new_code

        if old_code != new_code:
            hw_data = self._store.load_homework()
            if old_code in hw_data:
                hw_data[new_code] = hw_data.pop(old_code)
                self._store.save_homework(hw_data)

        self._save_subjects()
        self._refresh_listbox()
        self._needs_restart = True

    def _delete_subject(self) -> None:
        selection = self._listbox.curselection()
        if not selection:
            messagebox.showinfo("作业管理器·错误", "请先选择要删除的科目。",
                                parent=self._frame)
            return

        idx = selection[0]
        name = list(self._subjects.keys())[idx]
        code = self._subjects[name]

        if len(self._subjects) <= 1:
            messagebox.showwarning("作业管理器·错误", "至少需要保留一个科目。",
                                   parent=self._frame)
            return

        hw_data = self._store.load_homework()
        count = len(hw_data.get(code, []))

        msg = f"确定要删除科目「{name}」吗？"
        if count > 0:
            msg += f"\n该科目下有 {count} 个作业将被同时删除。"
        msg += f"\n\nDelete subject \"{name}\"?"
        if count > 0:
            msg += f"\n{count} homework(s) under this subject will also be deleted."

        if not messagebox.askyesno("删除科目 | Delete Subject", msg,
                                   parent=self._frame):
            return

        del self._subjects[name]
        self._save_subjects()
        self._sync_homework_json()
        self._refresh_listbox()
        self._needs_restart = True

    def _move_up(self) -> None:
        selection = self._listbox.curselection()
        if not selection or selection[0] == 0:
            return
        idx = selection[0]
        items = list(self._subjects.items())
        items[idx], items[idx - 1] = items[idx - 1], items[idx]
        self._subjects = dict(items)
        self._save_subjects()
        self._refresh_listbox()
        self._listbox.selection_set(idx - 1)
        self._needs_restart = True

    def _move_down(self) -> None:
        selection = self._listbox.curselection()
        if not selection or selection[0] >= len(self._subjects) - 1:
            return
        idx = selection[0]
        items = list(self._subjects.items())
        items[idx], items[idx + 1] = items[idx + 1], items[idx]
        self._subjects = dict(items)
        self._save_subjects()
        self._refresh_listbox()
        self._listbox.selection_set(idx + 1)
        self._needs_restart = True

    # ──────────────── 退出 ────────────────

    def exit(self) -> None:
        """关闭菜单，若科目有变更则提示重启。"""
        if self._needs_restart:
            if messagebox.askyesno(
                "重启 | RESTART",
                "科目已修改，需要重启以应用更改。\n是否立即重启？\n\n"
                "Subjects have been modified. Restart to apply changes.\n"
                "Restart now?",
            ):
                self._on_restart()
        self._frame.place_forget()
