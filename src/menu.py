from tkinter import *
from tkinter import messagebox, simpledialog
from tkinter import ttk
import json
import os

import main
import backup
import paths
import theme


class Menu:
    def __init__(self, parent_tk=None):
        self._subjects = {}
        self._subject_var = StringVar()
        self.load_menu()

    # ──────────────── 科目数据读写 ────────────────

    def _load_subjects_from_settings(self):
        """从 _internal/config/setting.json 读取 Subjects 字典。"""
        try:
            with open(paths.CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._subjects = data.get("Subjects", {})
        except Exception:
            self._subjects = {}

    def _save_subjects_to_settings(self):
        """将 Subjects 写回 _internal/config/setting.json。"""
        try:
            with open(paths.CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        data["Subjects"] = self._subjects
        try:
            paths.ensure_dirs()
            with open(paths.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def _sync_homework_json(self):
        """确保 homework.json 中包含所有已配置科目键（缺失则初始化为 []）。

        注意：不做任何删除——homework.json 中可能存在未被配置的旧科目数据，
        删除会丢失数据，故统一交由启动时的配置修复自动并入。
        """
        try:
            with open("homework.json", "r", encoding="utf-8") as f:
                hw_data = json.load(f)
            if not isinstance(hw_data, dict):
                return
        except Exception:
            return  # 文件缺失或损坏时不覆盖

        changed = False
        for code in self._subjects.values():
            if code not in hw_data:
                hw_data[code] = []
                changed = True
        if changed:
            with open("homework.json", "w", encoding="utf-8") as f:
                json.dump(hw_data, f, ensure_ascii=False, indent=4)

    def _remove_homework_key(self, code):
        """仅从 homework.json 中移除指定科目的键（用于科目删除）。

        只删除 list 类型的科目键；VER 等元数据键不会被误删。
        """
        try:
            with open("homework.json", "r", encoding="utf-8") as f:
                hw_data = json.load(f)
            if not isinstance(hw_data, dict) or code not in hw_data:
                return
            if not isinstance(hw_data[code], list):
                return
            del hw_data[code]
            with open("homework.json", "w", encoding="utf-8") as f:
                json.dump(hw_data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def _refresh_listbox(self):
        """刷新科目列表显示。"""
        self._subject_listbox.delete(0, END)
        for name, code in self._subjects.items():
            self._subject_listbox.insert(END, f"{name}  →  {code}")

    # ──────────────── 科目 CRUD 操作 ────────────────

    def _add_subject(self):
        name = simpledialog.askstring(
            "添加科目",
            "请输入科目显示名称：",
            parent=self.menu_frame,
        )
        if not name or not name.strip():
            return
        name = name.strip()

        if name in self._subjects:
            messagebox.showwarning(
                "作业管理器·错误",
                "科目名称已存在。",
                parent=self.menu_frame,
            )
            return

        code = simpledialog.askstring(
            "添加科目",
            f"请输入科目键名（英文标识）：",
            parent=self.menu_frame,
        )
        if not code or not code.strip():
            return
        code = code.strip().upper()

        if code == "VER":
            messagebox.showwarning(
                "作业管理器·错误",
                "VER 为系统保留键名，不能用作科目键。",
                parent=self.menu_frame,
            )
            return

        if code in self._subjects.values():
            messagebox.showwarning(
                "作业管理器·错误",
                "科目键名已存在。",
                parent=self.menu_frame,
            )
            return

        self._subjects[name] = code
        self._save_subjects_to_settings()
        self._sync_homework_json()
        self._refresh_listbox()
        self._needs_restart = True

    def _rename_subject(self):
        selection = self._subject_listbox.curselection()
        if not selection:
            messagebox.showinfo(
                "作业管理器·错误",
                "请先选择要重命名的科目。",
                parent=self.menu_frame,
            )
            return

        idx = selection[0]
        old_name = list(self._subjects.keys())[idx]
        old_code = self._subjects[old_name]

        new_name = simpledialog.askstring(
            "重命名科目",
            f"当前名称：{old_name}\n新显示名称：",
            parent=self.menu_frame,
            initialvalue=old_name,
        )
        if not new_name or not new_name.strip():
            return
        new_name = new_name.strip()

        if new_name != old_name and new_name in self._subjects:
            messagebox.showwarning(
                "作业管理器·错误",
                "科目名称已存在。",
                parent=self.menu_frame,
            )
            return

        new_code = simpledialog.askstring(
            "重命名科目",
            f"当前键名：{old_code}\n新键名（留空保持不变）：",
            parent=self.menu_frame,
            initialvalue=old_code,
        )
        if new_code is not None:
            new_code = new_code.strip().upper()
            if not new_code:
                new_code = old_code

        if new_code == "VER" and new_code != old_code:
            messagebox.showwarning(
                "作业管理器·错误",
                "VER 为系统保留键名，不能用作科目键。",
                parent=self.menu_frame,
            )
            return

        if new_code != old_code and new_code in self._subjects.values():
            messagebox.showwarning(
                "作业管理器·错误",
                "科目键名已存在。",
                parent=self.menu_frame,
            )
            return

        # 删除旧条目，添加新条目
        del self._subjects[old_name]
        self._subjects[new_name] = new_code

        # 如果键名变了，也要更新 homework.json
        if old_code != new_code:
            try:
                with open("homework.json", "r", encoding="utf-8") as f:
                    hw_data = json.load(f)
                if old_code in hw_data:
                    hw_data[new_code] = hw_data.pop(old_code)
                with open("homework.json", "w", encoding="utf-8") as f:
                    json.dump(hw_data, f, ensure_ascii=False, indent=4)
            except Exception:
                pass

        self._save_subjects_to_settings()
        self._refresh_listbox()
        self._needs_restart = True

    def _delete_subject(self):
        selection = self._subject_listbox.curselection()
        if not selection:
            messagebox.showinfo(
                "作业管理器·错误",
                "请先选择要删除的科目。",
                parent=self.menu_frame,
            )
            return

        idx = selection[0]
        name = list(self._subjects.keys())[idx]
        code = self._subjects[name]

        if len(self._subjects) <= 1:
            messagebox.showwarning(
                "作业管理器·错误",
                "至少需要保留一个科目。",
                parent=self.menu_frame,
            )
            return

        # 检查该科目是否有作业
        try:
            with open("homework.json", "r", encoding="utf-8") as f:
                hw_data = json.load(f)
            count = len(hw_data.get(code, []))
        except Exception:
            count = 0

        msg = f"确定要删除科目「{name}」吗？"
        if count > 0:
            msg += f"\n该科目下有 {count} 个作业将被同时删除。"
        msg += f"\n\nDelete subject \"{name}\"?"
        if count > 0:
            msg += f"\n{count} homework(s) under this subject will also be deleted."

        if not messagebox.askyesno(
            "删除科目 | Delete Subject", msg, parent=self.menu_frame
        ):
            return

        # 删除前备份该科目数据，便于恢复
        backup.backup_file("homework.json", tag="homework")

        del self._subjects[name]
        self._save_subjects_to_settings()
        self._remove_homework_key(code)
        self._refresh_listbox()
        self._needs_restart = True

    def _move_subject_up(self):
        """将选中的科目上移一位。"""
        selection = self._subject_listbox.curselection()
        if not selection or selection[0] == 0:
            return
        idx = selection[0]
        items = list(self._subjects.items())
        items[idx], items[idx - 1] = items[idx - 1], items[idx]
        self._subjects = dict(items)
        self._save_subjects_to_settings()
        self._refresh_listbox()
        self._subject_listbox.selection_set(idx - 1)
        self._needs_restart = True

    def _move_subject_down(self):
        """将选中的科目下移一位。"""
        selection = self._subject_listbox.curselection()
        if not selection or selection[0] >= len(self._subjects) - 1:
            return
        idx = selection[0]
        items = list(self._subjects.items())
        items[idx], items[idx + 1] = items[idx + 1], items[idx]
        self._subjects = dict(items)
        self._save_subjects_to_settings()
        self._refresh_listbox()
        self._subject_listbox.selection_set(idx + 1)
        self._needs_restart = True

    def load_menu(self):
        self._needs_restart = False
        self._load_subjects_from_settings()

        self.menu_frame = Frame(tk, relief=FLAT)
        self.menu_frame.place(x=0, y=0, relheight=1, relwidth=1)

        # ── 顶部关闭栏 ──
        self.menu_top_frame = Frame(self.menu_frame, relief=FLAT)
        self.menu_top_frame.place(x=0, y=0, relwidth=1)

        self.close_menu = Button(
            self.menu_top_frame,
            text="退出菜单",
            fg=theme.MUTED,
            font=("汉仪文黑-85W", 14),
            relief=FLAT,
            command=self.exit,
        )
        theme.style_button(
            self.close_menu, "normal", padx=14, pady=4, font=("汉仪文黑-85W", 14)
        )
        self.close_menu.pack(side="right", padx=(2, 14), pady=6)

        # ── 科目管理标题 ──
        subject_title_frame = Frame(self.menu_frame, relief=FLAT)
        subject_title_frame.place(x=20, y=30)

        Frame(subject_title_frame, width=3, height=18, bg=theme.ACCENT).pack(
            side="left", padx=(0, 8)
        )
        Label(
            subject_title_frame,
            text="科目管理",
            fg=theme.FG,
            font=("汉仪文黑-85W", 16),
        ).pack(side="left")

        # ── 科目列表 ──
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Custom.Vertical.TScrollbar",
            background="#39414D",          # 滑块背景
            troughcolor="#1B1F26",         # 槽背景
            arrowcolor=theme.MUTED,        # 箭头颜色
            bordercolor="#1B1F26",
            lightcolor="#454E5C",
            darkcolor="#1B1F26",
            relief="flat",
        )

        # 2. 配置滑块（thumb）——精确控制滚动条滑块
        style.configure(
            "Custom.Vertical.TScrollbar.thumb",
            background="#39414D",
            bordercolor="#1B1F26",
            relief="flat",
        )

        # 3. 状态映射：根据状态改变颜色（避免白色）
        style.map(
            "Custom.Vertical.TScrollbar",
            background=[
                ("active", "#454E5C"),      # 鼠标悬停时滑块变亮
                ("pressed", "#2E353F"),     # 按下时更深
                ("disabled", "#39414D")     # 禁用时也保持深色
            ],
            troughcolor=[
                ("disabled", "#1B1F26")     # 禁用时槽颜色不变
            ],
            arrowcolor=[
                ("disabled", theme.DIM)     # 禁用时箭头变暗，但仍可见
            ]
        )
        list_frame = Frame(self.menu_frame, relief=FLAT)
        list_frame.place(x=20, y=70, width=380, height=300)

        scrollbar = ttk.Scrollbar(list_frame, style="Custom.Vertical.TScrollbar")
        scrollbar.pack(side=RIGHT, fill=Y)

        self._subject_listbox = Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            bg="#1B1F26",
            fg=theme.FG,
            selectbackground=theme.PANEL_HI,
            selectforeground=theme.ACCENT,
            font=("JetBrains Mono", 12),
            highlightthickness=0,
            borderwidth=0,
            relief=FLAT,
            activestyle="none",
        )
        self._subject_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=self._subject_listbox.yview)

        self._refresh_listbox()

        # ── 操作按钮（5键一行，宽度与列表对齐） ──
        action_frame = Frame(self.menu_frame, relief=FLAT, width=380, height=40)
        action_frame.place(x=20, y=380)
        action_frame.pack_propagate(False)

        def _menu_btn(text, command, kind="normal"):
            btn = Button(
                action_frame,
                text=text,
                command=command,
                fg=theme.MUTED,
                font=("汉仪文黑-85W", 14),
                relief=FLAT,
            )
            theme.style_button(btn, kind, padx=0, pady=4, font=("汉仪文黑-85W", 14))
            btn.pack(side="left", fill=X, expand=True)
            return btn

        _menu_btn("添加", self._add_subject, "accent")
        _menu_btn("重命名", self._rename_subject)
        _menu_btn("删除", self._delete_subject, "danger")
        _menu_btn("上移", self._move_subject_up)
        _menu_btn("下移", self._move_subject_down)

    def change(self, key, value, restart=False):
        with open(paths.CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data[key] = value
        with open(paths.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if restart:
            messagebox.showinfo(
                "重启 | RESTART",
                "重启以应用更改\nRestart to Apply",
            )
            main.restart_service()

    def exit(self):
        if self._needs_restart:
            if messagebox.askyesno(
                "重启 | RESTART",
                "科目已修改，需要重启以应用更改。\n是否立即重启？\n\n"
                "Subjects have been modified. Restart to apply changes.\nRestart now?",
            ):
                main.restart_service()
        self.menu_frame.place_forget()


def open_menu():
    global tk, COLOR
    tk = main.tk
    COLOR = main.COLOR
    menu = Menu(parent_tk=tk)


if __name__ == "__main__":
    pass
