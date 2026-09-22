from tkinter import *
from tkinter import messagebox
import tkinter.font as tkfont

try:
    import mouse
except Exception:
    # 在无法导入或权限受限时降级为 None，避免程序崩溃
    mouse = None

import pygetwindow
import json
import keyboard
import os
import psutil
import subprocess
import sys
import threading
import time
import msvcrt

import default_json as default_json
import paths

default_json.check()

import help
import homeworkfunc
import dataupdate
import backup
import theme
import menu
import updater

COLOR = theme.MUTED
DEBUG = False
DATA = "homework.json"
PAGE_ROTATE_MS = 12000  # 翻页轮播默认间隔（毫秒）；可由 setting.json 的 Rotation.PageMs 覆盖
DEADLINE_ROTATE_MS = 5000  # 「收 / 截止」文案轮播默认间隔（毫秒）；对应 Rotation.DeadlineMs
VERSION = "1.8.0"
VERSION_NUM = 1008000000
tk = None


def get_rotation_ms(key, default):
    """
    读取 setting.json 中 "Rotation" 段的轮播时间参数（毫秒）。

    键：`DeadlineMs`（「收 / 截止」文案轮播）/ `PageMs`（多页翻页轮播）。
    缺失 / 非法时返回 default；最小 1000ms，避免间隔过小造成空转。
    每次调度定时器时读取一次，后续调节界面修改配置后无需重启即可生效。
    """
    try:
        with open(paths.CONFIG_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
        rotation = settings.get("Rotation", {})
        value = rotation.get(key, default) if isinstance(rotation, dict) else default
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return default
        return max(1000, int(value))
    except Exception:
        return default


def acquire_lock(lock_path=None):
    """
    尝试获取一个简单的文件锁（Windows 下使用 msvcrt），
    成功返回打开的文件对象（必须保持引用以维持锁），失败返回 None。

    锁文件默认位于 _internal/lock/homework.lock；若旧版本的 lock/homework.lock
    仍然存在（可能有旧实例在运行），会一并探测，保证同一时间只有一个实例。
    """
    if lock_path is None:
        lock_path = paths.LOCK_FILE

    def _try(path):
        try:
            lock_file = open(path, "w")
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            return lock_file
        except FileNotFoundError:
            # 如果锁文件所在目录不存在，尝试创建目录后重试
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                lock_file = open(path, "w")
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                return lock_file
            except Exception:
                return None
        except Exception:
            return None

    lock_file = _try(lock_path)
    if lock_file is None:
        return None

    # 兼容检查：旧版本锁文件残留时，探测是否被旧实例占用
    legacy = paths.LEGACY_LOCK_FILE
    if os.path.abspath(lock_path) != os.path.abspath(legacy) and os.path.exists(legacy):
        probe = _try(legacy)
        if probe is None:
            # 旧锁被占用 → 旧实例仍在运行，放弃启动
            try:
                lock_file.close()
            except Exception:
                pass
            return None
        # 未被占用 → 旧锁是残留文件，清理掉
        try:
            probe.close()
        except Exception:
            pass
        try:
            os.remove(legacy)
        except Exception:
            pass
        try:
            os.rmdir(os.path.dirname(legacy))
        except Exception:
            pass

    return lock_file

def _app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

def restart_service():
    app_dir = _app_dir()
    current_exe_path = os.path.join(app_dir, "main.exe")
    bat_path = os.path.join(app_dir, "update.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(f"""@echo off
timeout /t 1 /nobreak >nul
set _MEIPASS2=
set PYINSTALLER_RESET_ENVIRONMENT=1
start "" /D "{app_dir}" "{current_exe_path}"
del /f /q "%~f0"
""")

    subprocess.Popen([bat_path], shell=True)
    sys.exit()

class HomeworkTool:
    def __init__(self):

        # 默认UI配置
        tk.option_add("*Background", theme.BG)
        tk.option_add("*Foreground", theme.FG)
        tk.option_add("*Font", ("Jetbrains mono", 18))
        self.load_ui()

        # 列表初始化
        self.homework_list = []  # 全部作业文本（仅用于计数）
        self.time_list = []  # 当前页的时间 UI
        self.canvas_items = []
        self.canvas_widths = []
        self.subject_codes = homeworkfunc.SUBJECT_CODES
        self.subject_display_names = homeworkfunc.SUBJECT_DISPLAY_NAMES
        self.emphasize_levels = homeworkfunc.EMPHASIZE_LEVELS
        self.reminder_schedule = []  # 计划的tk.after

        # 列表排版参数：按屏幕高度计算每页可容纳的行数，超出一页则分页轮播
        self.LIST_FONT = tkfont.Font(root=tk, family="HYWenHei-85W", size=18)
        self.LINE_HEIGHT = self.LIST_FONT.metrics("linespace") + 8
        self.LIST_TOP = 40
        self.LIST_LEFT = 45
        self.LIST_HEIGHT = max(120, tk.winfo_screenheight() - self.LIST_TOP - 44)
        self.LINES_PER_PAGE = max(1, self.LIST_HEIGHT // self.LINE_HEIGHT)
        self.WRAP_WIDTH = max(80, (self.POSITION_TIME_DISPLAY_X - 50) - 12)
        self._entries = []
        self._page = 0
        self._page_count = 1
        self._page_entries = []
        self._page_entry_y = {}
        self._entry_canvas = {}
        self._entry_fill = {}
        self._page_rotate_aid = None
        self._page_fade_aid = None
        self._hover_idx = -1
        self.arg = -1

        # 各类定时器的 id（用于取消），初始化为 None
        self._upload_aid = None
        self._rot_aid = None  # 截止时间轮播定时器
        self._rot = 0  # 轮播相位（0=开始收集文案，1=截止时间文案）

        self.mousex, self.mousey = 0, 0
        self.load_amount = 0  # 负载量

        # 校验资源完整性
        homeworkfunc.resource_check(self.subject_codes)

        # 启动前自动备份核心数据（后续升级 / 修复可能改写 homework.json）
        backup.backup_file("homework.json", tag="homework")
        backup.backup_file(paths.CONFIG_FILE, tag="setting")

        # 自动升级旧版本 homework.json 数据（补齐 deadline 字段等）
        dataupdate.migrate()

        # 显示
        self.draw_homework()

        # 鼠标移动事件绑定（用于显示/隐藏按钮）
        tk.bind("<Motion>", self.mouse_move)

        # 自动隐藏按钮的计时器
        self.tick = 0
        tk.after(1, self.on_tick)
        self.info()
        tk.after(100, self.ui_pack)

    def on_tick(self):
        """
        每秒调用一次，自动隐藏按钮并防止锁屏。
        """

        # 3秒
        if self.tick > 2:
            try:
                # 隐藏UI按钮
                self.top_frame.place_forget()
                self.ui_side_delete.place_forget()
                self.ui_side_edit.place_forget()
            except:
                pass

        # 5分钟
        if self.tick > 300:
            # 自动防止锁屏/进入休眠的兼容性处理（在无法使用 mouse 时安全跳过）
            if mouse:
                try:
                    mouse.move(400, 1200)
                    mouse.click()
                except Exception:
                    # 鼠标库可能在某些环境中不可用或权限受限，忽略异常
                    pass
            self.tick = 3
        self.tick += 1

        # 继续调用自己
        tk.after(1000, self.on_tick)

    def cooldown(self, object, original, second=5):
        """
        对指定按钮进行短暂禁用，防止重复点击。

        second: 禁用持续时间（1/10 秒）
        """
        if second <= 0:
            object.config(state=NORMAL, text=original, font=("汉仪文黑-85W", 14))
            return
        object.config(state=DISABLED)
        tk.after(100, lambda: self.cooldown(object, original, second - 1))

    def draw_homework(self):
        """显示作业列表"""

        self.ui_top_add.config(state=DISABLED)
        self.ui_top_clear.config(state=DISABLED)

        # 取消之前计划的提醒（如果有）
        for i in self.reminder_schedule:
            tk.after_cancel(i)
        self.reminder_schedule = []

        # 取消定时器
        self._cancel_deadline_rotation()
        self._cancel_page_rotation()
        self._rot = 0

        # 清理之前在 canvas 上的显示与时间显示
        try:
            self.list_canvas.delete("all")
        except Exception:
            # 若 canvas 尚未创建，忽略
            pass
        self.list_canvas.place_forget()  # 隐藏 canvas，后续重新 place
        for i in self.time_list:
            i.place_forget()
        a = Label(
            self.main_frame, text="正在加载……", fg=COLOR, font=("HYWenHei-85W", 24)
        )
        a.place(x=45, y=40)
        tk.update()  # 强制更新界面，确保之前的内容被隐藏

        # 重新加载数据
        with open(DATA, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        # 验证并修复数据：处理多余的/缺失的科目键
        _data_fixed = False
        # 找出多余键（存在于 JSON 但不在 subject_codes 中，且值为列表）
        known_keys = set(self.subject_codes)
        extra_keys = [
            k for k in self.data
            if k not in known_keys and isinstance(self.data[k], list)
        ]
        if extra_keys:
            # 自动把 homework.json 中尚未配置的科目并入配置（而非删除），
            # 避免“setting 中无、homework 中有”的科目数据丢失
            self._import_extra_subjects(extra_keys)
        # 找出缺失键（存在于 subject_codes 但不在 JSON 中）
        missing_keys = [k for k in self.subject_codes if k not in self.data]
        if missing_keys:
            for k in missing_keys:
                self.data[k] = []
            _data_fixed = True
        if _data_fixed:
            try:
                with open(DATA, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=4)
            except Exception:
                pass

        # 对每个 subject 列表应用稳定排序，若发生变化则写回文件一次
        _changed = False
        for key in self.subject_codes:
            orig = self.data.get(key, [])
            # 使用稳定排序，保留相同键的原始相对顺序
            sorted_list = sorted(orig, key=homeworkfunc._sort_key)
            if sorted_list != orig:
                self.data[key] = sorted_list
                _changed = True
        if _changed:
            try:
                with open(DATA, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=4)
            except Exception:
                # 写入失败不应导致程序崩溃，继续显示已有内容
                pass

        # 构建条目：按像素宽度自动换行（不再横向滚动）
        self._entries = self._build_entries()
        self.homework_list = [e["text"] for e in self._entries]
        self._page = 0

        # 渲染当前页（内部同时计划下一次时间刷新）
        self.upload_time_display()

        self.ui_pack()

        a.place_forget()  # 隐藏加载提示
        del a  # 删除加载提示对象

        self.cooldown(self.ui_top_add, "添加")
        self.cooldown(self.ui_top_clear, "清理")

        # 超出一页时启动分页轮播
        self._start_page_rotation()

        # 启动“开始收集 / 截止”文案轮播（每 5 秒）
        self._start_deadline_rotation()

    def upload_time_display(self):
        """每分钟刷新一次显示（重新渲染当前页）。"""
        # 取消上一次的定时器（如果存在）
        if getattr(self, "_upload_aid", None) is not None:
            try:
                tk.after_cancel(self._upload_aid)
                self.reminder_schedule.remove(self._upload_aid)
            except Exception:
                pass

        upload = self._render_page()
        if upload:
            homeworkfunc.uri_classisland("Homeworkmode-upload")

        now = time.localtime()
        remaining_seconds = 60 - now.tm_sec
        # 只传递方法引用，由方法内部追踪 aid
        self._upload_aid = tk.after(remaining_seconds * 1000, self.upload_time_display)
        self.reminder_schedule.append(self._upload_aid)

    def _wrap_text(self, text):
        """
        按像素宽度把文本拆分为多行（自动换行，不再横向滚动）。
        以逐字符宽度累加估算，保证整行不超过 WRAP_WIDTH。
        """
        width = getattr(self, "WRAP_WIDTH", 0) or 600
        lines = []
        cur = ""
        cur_w = 0
        for ch in str(text):
            w = self.LIST_FONT.measure(ch)
            if cur and cur_w + w > width:
                lines.append(cur)
                cur, cur_w = ch, w
            else:
                cur += ch
                cur_w += w
        if cur or not lines:
            lines.append(cur)
        return lines

    def _build_entries(self):
        """按显示顺序构建条目（含自动换行结果），供分页渲染使用。"""
        entries = []
        flat = 0
        for i, subj in enumerate(self.subject_codes):
            for k in self.data.get(subj, []):
                if i < len(self.subject_display_names):
                    name = self.subject_display_names[i]
                else:
                    name = subj
                text = name + ":" + str(k.get("content", ""))
                lines = self._wrap_text(text)
                entries.append(
                    {
                        "index": flat,  # 全列表序号（删除 / 编辑用）
                        "subject": subj,
                        "item": k,
                        "text": text,
                        "lines": lines,
                        "height": max(1, len(lines)) * self.LINE_HEIGHT,
                    }
                )
                flat += 1
            if keyboard.is_pressed("tab"):
                time.sleep(0.6)
        return entries

    def _paginate(self, entries):
        """
        按每页可容纳的行数对条目分页。

        正常情况下条目不拆分；若单个条目超过一页行数，则拆分到多页，
        续页（first_segment=False）不再重复显示时间标签。
        """
        per_page = max(1, getattr(self, "LINES_PER_PAGE", 1))
        pages = []
        cur = []
        used = 0
        for e in entries:
            lines = e.get("lines") or [""]
            start = 0
            while start < len(lines):
                if used >= per_page:
                    pages.append(cur)
                    cur, used = [], 0
                take = min(per_page - used, len(lines) - start)
                seg = dict(e)
                seg["lines"] = lines[start : start + take]
                seg["height"] = take * self.LINE_HEIGHT
                seg["first_segment"] = start == 0
                cur.append(seg)
                used += take
                start += take
            if used >= per_page:
                pages.append(cur)
                cur, used = [], 0
        if cur:
            pages.append(cur)
        return pages or [[]]

    def _render_page(self):
        """
        渲染当前页：内容（自动换行）+ 右侧时间标签。
        返回是否需要触发 ClassIsland 的提交通知。
        """
        try:
            self.list_canvas.delete("all")
        except Exception:
            pass
        for widget in self.time_list:
            try:
                widget.destroy()
            except Exception:
                pass
        self.time_list = []
        self.canvas_items = []
        self.canvas_widths = []
        self._page_entries = []
        self._page_entry_y = {}
        self._entry_canvas = {}
        self._entry_fill = {}
        self._hover_idx = -1
        self.arg = -1

        entries = getattr(self, "_entries", [])
        pages = self._paginate(entries)
        self._page_count = max(1, len(pages))
        if self._page >= self._page_count or self._page < 0:
            self._page = 0
        page_entries = pages[self._page]

        canvas_width = self.POSITION_TIME_DISPLAY_X - 50
        self.list_canvas.place(
            x=self.LIST_LEFT,
            y=self.LIST_TOP,
            width=canvas_width,
            height=self.LIST_HEIGHT,
        )

        upload = 0
        y = 0
        for e in page_entries:
            k = e["item"]
            status = homeworkfunc.collect_status(k)
            fill = theme.DIM if status == -1 else theme.FG

            ids = []
            for li, line in enumerate(e["lines"]):
                item_id = self.list_canvas.create_text(
                    0,
                    y + li * self.LINE_HEIGHT,
                    text=line,
                    anchor="nw",
                    fill=fill,
                    font=self.LIST_FONT,
                )
                ids.append(item_id)
                self.canvas_items.append(item_id)
                try:
                    bbox = self.list_canvas.bbox(item_id)
                    if bbox:
                        self.canvas_widths.append(bbox[2] - bbox[0])
                except Exception:
                    pass

            e["canvas"] = ids
            e["fill"] = fill
            e["label"] = None
            e["top"] = y
            self._page_entries.append(e)
            self._entry_canvas.setdefault(e["index"], []).extend(ids)
            self._entry_fill[e["index"]] = fill
            if e["index"] not in self._page_entry_y:
                self._page_entry_y[e["index"]] = y

            # 时间标签仅在条目首段创建，并与首行对齐
            if e.get("first_segment", True):
                chip_bg, chip_fg = theme.time_chip_style(status)
                label = Label(
                    self.main_frame,
                    text=self._time_cell_text(k),
                    width=13,
                    justify="left",
                    anchor="e",
                    font=("HYWenHei-85W", 15),
                    padx=10,
                    bd=0,
                    highlightthickness=0,
                    bg=chip_bg,
                    fg=chip_fg,
                )
                label.place(x=self.POSITION_TIME_DISPLAY_X, y=self.LIST_TOP + y + 2)
                e["label"] = label
                e["label_fg"] = chip_fg
                self.time_list.append(label)
                if status == 4:
                    upload = 1

            y += e["height"]

        try:
            self.calculate_canvas_load()
        except Exception:
            pass
        return upload

    def _start_page_rotation(self):
        """页数超出一页时，按 Rotation.PageMs（默认 PAGE_ROTATE_MS）间隔轮播各页。"""
        self._cancel_page_rotation()
        if getattr(self, "_page_count", 1) > 1:
            self._page_rotate_aid = tk.after(
                get_rotation_ms("PageMs", PAGE_ROTATE_MS), self._page_rotate_tick
            )
            self.reminder_schedule.append(self._page_rotate_aid)

    def _cancel_page_rotation(self):
        """取消已排程的分页轮播定时器。"""
        aid = getattr(self, "_page_rotate_aid", None)
        if aid is not None:
            try:
                tk.after_cancel(aid)
            except Exception:
                pass
            try:
                self.reminder_schedule.remove(aid)
            except Exception:
                pass
            self._page_rotate_aid = None

    def _cancel_page_fade(self):
        """取消正在执行的分页淡入淡出动画。"""
        aid = getattr(self, "_page_fade_aid", None)
        if aid is not None:
            try:
                tk.after_cancel(aid)
            except Exception:
                pass
            self._page_fade_aid = None

    def _change_page(self, offset):
        """按偏移量手动切换页面，并重置自动轮播计时。"""
        page_count = max(1, getattr(self, "_page_count", 1))
        if page_count <= 1:
            return
        self._cancel_page_rotation()
        self._cancel_page_fade()
        self._page = (self._page + offset) % page_count
        self._crossfade_page()

    def _page_previous(self):
        """切换到上一页。"""
        self._change_page(-1)

    def _page_next(self):
        """切换到下一页。"""
        self._change_page(1)

    def _fade_page(self, fade_in=False, step=0, steps=8, interval=30, on_end=None):
        """让当前页的作业文本和时间标签淡入或淡出。"""
        background = theme.BG
        progress = step / (steps - 1) if steps > 1 else 1.0
        try:
            if fade_in:
                for entry in getattr(self, "_page_entries", []):
                    fill = entry.get("fill", theme.FG)
                    color = self._rgb_to_hex(
                        tuple(
                            self._hex_to_rgb(background)[i]
                            + (self._hex_to_rgb(fill)[i] - self._hex_to_rgb(background)[i])
                            * progress
                            for i in range(3)
                        )
                    )
                    for item_id in entry.get("canvas", []):
                        self.list_canvas.itemconfig(item_id, fill=color)
                    label = entry.get("label")
                    if label is not None:
                        if "fade_bg" not in entry or "fade_fg" not in entry:
                            # 首次触及时补拍起始颜色（含动画途中条目被重新渲染的情况），
                            # 保证渐变目标取自有色快照，而不是被逐帧改写的控件属性
                            entry["fade_bg"] = label.cget("bg")
                            entry["fade_fg"] = label.cget("fg")
                        label.config(
                            bg=self._rgb_to_hex(
                                tuple(
                                    self._hex_to_rgb(background)[i]
                                    + (self._hex_to_rgb(entry.get("fade_bg", background))[i] - self._hex_to_rgb(background)[i])
                                    * progress
                                    for i in range(3)
                                )
                            ),
                            fg=self._rgb_to_hex(
                                tuple(
                                    self._hex_to_rgb(background)[i]
                                    + (self._hex_to_rgb(entry.get("label_fg", background))[i] - self._hex_to_rgb(background)[i])
                                    * progress
                                    for i in range(3)
                                )
                            ),
                        )
            else:
                for entry in getattr(self, "_page_entries", []):
                    for item_id in entry.get("canvas", []):
                        self.list_canvas.itemconfig(
                            item_id,
                            fill=self._rgb_to_hex(
                                tuple(
                                    self._hex_to_rgb(entry.get("fill", theme.FG))[i]
                                    + (self._hex_to_rgb(background)[i] - self._hex_to_rgb(entry.get("fill", theme.FG))[i])
                                    * progress
                                    for i in range(3)
                                )
                            ),
                        )
                    label = entry.get("label")
                    if label is not None:
                        if "fade_bg" not in entry or "fade_fg" not in entry:
                            # 首次触及时补拍起始颜色（含动画途中条目被重新渲染的情况）
                            entry["fade_bg"] = label.cget("bg")
                            entry["fade_fg"] = label.cget("fg")
                        label.config(
                            bg=self._rgb_to_hex(
                                tuple(
                                    self._hex_to_rgb(entry.get("fade_bg", background))[i]
                                    + (self._hex_to_rgb(background)[i] - self._hex_to_rgb(entry.get("fade_bg", background))[i])
                                    * progress
                                    for i in range(3)
                                )
                            ),
                            fg=self._rgb_to_hex(
                                tuple(
                                    self._hex_to_rgb(entry.get("fade_fg", background))[i]
                                    + (self._hex_to_rgb(background)[i] - self._hex_to_rgb(entry.get("fade_fg", background))[i])
                                    * progress
                                    for i in range(3)
                                )
                            ),
                        )
        except Exception:
            if on_end:
                on_end()
            return

        if step < steps - 1:
            self._page_fade_aid = tk.after(
                interval,
                lambda: self._fade_page(fade_in, step + 1, steps, interval, on_end),
            )
        elif on_end:
            self._page_fade_aid = None
            on_end()

    def _crossfade_page(self):
        """将当前页淡出，渲染下一页后再淡入。"""
        def render_next_page():
            try:
                upload = self._render_page()
                if upload:
                    homeworkfunc.uri_classisland("Homeworkmode-upload")
                self._fade_page(fade_in=True, on_end=self._start_page_rotation)
            except Exception:
                self._start_page_rotation()

        if not getattr(self, "_page_entries", []):
            render_next_page()
            return
        self._fade_page(fade_in=False, on_end=render_next_page)

    def _page_rotate_tick(self):
        """淡出当前页，切换到下一页后淡入。"""
        self._page = (self._page + 1) % max(1, getattr(self, "_page_count", 1))
        self._crossfade_page()

    def _deadline_of(self, item):
        """读取作业项的截止时间戳；仅接受数值，返回 0 表示未启用截止时间。"""
        try:
            d = item.get("deadline", 0)
        except Exception:
            return 0
        if isinstance(d, bool):
            return 0
        if isinstance(d, (int, float)):
            return d
        try:
            return float(d)
        except (TypeError, ValueError):
            return 0

    def _time_cell_text(self, item):
        """
        计算右侧时间单元格应显示的文案（含“开始收集 / 截止”轮播）。

        - 未启用截止时间：沿用原有“开始收集”显示逻辑；
        - 启用了截止时间：
            · 尚未开始收集、距开始尚早 → “xx:xx起”与“xx:xx截止”轮播；
            · 距开始收集不足 5 分钟 → “即将允许提交”与“xx:xx截止”轮播；
            · 已开始收集（即使超过 5 分钟）但截止未到 → “可提交”与“xx:xx截止”轮播；
            · 未设开始收集（不收）→ 单独显示“xx:xx截止”；
            · 自定义文本 → 在自定义信息与“xx:xx截止”间轮播；
            · 截止已到 → 恢复原有“时间已过”等逻辑。
        """
        t = item.get("time", 0)
        d = self._deadline_of(item)
        em = item.get("emphasize", "自动")
        now = time.time()

        num_t = isinstance(t, (int, float)) and not isinstance(t, bool)
        num_d = isinstance(d, (int, float)) and not isinstance(d, bool)
        open_deadline = num_d and d > now

        # 已开始收集、截止未到 → 轮播 “现在收” / “xx:xx截止”
        if num_t and t > 0 and t <= now and open_deadline:
            if getattr(self, "_rot", 0) == 0:
                return "可提交"
            return homeworkfunc.analyze_time(d, em, word="截止")[0]

        # “不收”但启用了截止时间 → 单独显示截止文案
        if num_t and t <= 0 and num_d and d > 0:
            return homeworkfunc.analyze_time(d, em, word="截止")[0]

        # 尚未开始收集、距开始仍较久且启用了截止时间 → 轮播 起/截止
        if num_t and t > now + homeworkfunc.TIME_OUT and open_deadline:
            if getattr(self, "_rot", 0) == 0:
                return homeworkfunc.analyze_time(t, em)[0][:-1] + "起"
            return homeworkfunc.analyze_time(d, em, word="截止")[0]

        # 距开始收集不足 5 分钟且启用了截止时间 → 轮播 “即将允许提交” / “xx:xx截止”
        # （截止开放时该阶段不应显示“即将收”）
        if num_t and now < t <= now + homeworkfunc.TIME_OUT and open_deadline:
            if getattr(self, "_rot", 0) == 0:
                return "即将允许提交"
            return homeworkfunc.analyze_time(d, em, word="截止")[0]

        # 自定义文本（字符串时间）且截止未到 → 在自定义信息与截止时间间轮播
        if isinstance(t, str) and t.strip() != "" and open_deadline:
            if getattr(self, "_rot", 0) == 0:
                return t
            return homeworkfunc.analyze_time(d, em, word="截止")[0]

        # 其余情况：沿用原有文案（即将收 / 时间已过 / 自定义文本等）
        return homeworkfunc.analyze_time(t, em)[0]

    @staticmethod
    def _hex_to_rgb(color):
        """把 #RRGGBB 颜色转换为 (r, g, b)。"""
        color = str(color).lstrip("#")
        return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def _rgb_to_hex(rgb):
        """把 (r, g, b) 转换为 #RRGGBB。"""
        return "#%02X%02X%02X" % tuple(
            max(0, min(255, int(round(v)))) for v in rgb
        )

    @classmethod
    def _same_color(cls, a, b):
        """比较两个颜色是否等价（忽略大小写 / 格式差异）。"""
        try:
            return cls._hex_to_rgb(a) == cls._hex_to_rgb(b)
        except Exception:
            return str(a) == str(b)

    def _fade_widget(self, widget, start, end, steps=6, interval=30, on_end=None):
        """
        将控件前景色从 start 渐变到 end，用于轮播文案的淡入 / 淡出。
        控件销毁后自动停止；on_end 在渐变结束后调用。
        """
        try:
            r0, g0, b0 = self._hex_to_rgb(start)
            r1, g1, b1 = self._hex_to_rgb(end)
        except Exception:
            try:
                widget.config(fg=end)
            except Exception:
                pass
            if on_end:
                on_end()
            return

        def step(i):
            try:
                if not widget.winfo_exists():
                    return
                t = i / (steps - 1) if steps > 1 else 1.0
                widget.config(
                    fg=self._rgb_to_hex(
                        (r0 + (r1 - r0) * t, g0 + (g1 - g0) * t, b0 + (b1 - b0) * t)
                    )
                )
            except Exception:
                return
            if i < steps - 1:
                try:
                    widget.after(interval, lambda: step(i + 1))
                except Exception:
                    pass
            elif on_end:
                try:
                    on_end()
                except Exception:
                    pass

        step(0)

    def _crossfade_time_label(self, widget, text, bg, fg, steps=5, interval=28):
        """轮播切换时对时间标签做淡出 → 换字/换底色 → 淡入。"""
        try:
            cur_fg = widget.cget("fg")
            cur_bg = widget.cget("bg")
        except Exception:
            try:
                widget.config(text=text, bg=bg, fg=fg)
            except Exception:
                pass
            return

        def swap():
            try:
                if not widget.winfo_exists():
                    return
                widget.config(text=text, bg=bg, fg=bg)
            except Exception:
                return
            self._fade_widget(widget, bg, fg, steps, interval)

        self._fade_widget(widget, cur_fg, cur_bg, steps, interval, on_end=swap)

    def _start_deadline_rotation(self):
        """启动「开始收集 / 截止」文案轮播（间隔取 Rotation.DeadlineMs，默认 5 秒）。"""
        self._cancel_deadline_rotation()
        self._rot = 0
        self._rot_aid = tk.after(
            get_rotation_ms("DeadlineMs", DEADLINE_ROTATE_MS),
            self._deadline_rotation_tick,
        )
        self.reminder_schedule.append(self._rot_aid)

    def _cancel_deadline_rotation(self):
        """取消已排程的截止时间轮播定时器。"""
        aid = getattr(self, "_rot_aid", None)
        if aid is not None:
            try:
                tk.after_cancel(aid)
            except Exception:
                pass
            try:
                self.reminder_schedule.remove(aid)
            except Exception:
                pass
            self._rot_aid = None

    def _deadline_rotation_tick(self):
        """按 Rotation.DeadlineMs（默认 5 秒）轮播一次：就地刷新当前页各时间 Label 的文案，并同步样式。"""
        self._rot = 1 - getattr(self, "_rot", 0)
        for e in getattr(self, "_page_entries", []):
            widget = e.get("label")
            if widget is None:
                continue  # 超长条目的续页没有时间标签
            try:
                k = e["item"]
                status_int = homeworkfunc.collect_status(k)
                text = self._time_cell_text(k)
                bg, fg = theme.time_chip_style(status_int)
                text_changed = widget.cget("text") != text
                bg_changed = not self._same_color(widget.cget("bg"), bg)
                if text_changed:
                    # 文案变化（轮播切换）→ 淡出淡入
                    self._crossfade_time_label(widget, text, bg, fg)
                elif bg_changed:
                    # 底色变化 → 立即换底色后渐变文字色
                    try:
                        widget.config(bg=bg)
                    except Exception:
                        pass
                    self._fade_widget(widget, widget.cget("fg"), fg)
                elif not self._same_color(widget.cget("fg"), fg):
                    # 仅文字颜色变化 → 渐变过渡
                    self._fade_widget(widget, widget.cget("fg"), fg)
                if status_int == -1:
                    for item_id in e.get("canvas", []):
                        try:
                            self.list_canvas.itemconfig(item_id, fill=theme.DIM)
                        except Exception:
                            pass
            except Exception:
                pass
        old = getattr(self, "_rot_aid", None)
        self._rot_aid = tk.after(
            get_rotation_ms("DeadlineMs", DEADLINE_ROTATE_MS),
            self._deadline_rotation_tick,
        )
        if old is not None:
            try:
                self.reminder_schedule.remove(old)
            except Exception:
                pass
        self.reminder_schedule.append(self._rot_aid)

    def calculate_canvas_load(self):
        """
        估算渲染负载并更新 `self.load_amount`（显示于底部信息栏）。

        取消横向滚动后，负载主要由作业数量与文本像素宽度决定，
        并尽可能纳入进程的 CPU 与内存占用作为参考。
        """
        count_items = len(getattr(self, "homework_list", []) or [])
        total_text_pixels = sum(getattr(self, "canvas_widths", []) or [0])

        load = int(count_items * 2 + total_text_pixels / 2000.0)

        # 尝试加入 CPU / 内存指标
        try:
            p = psutil.Process(os.getpid())
            mem_mb = p.memory_info().rss / 1024.0 / 1024.0
            cpu = p.cpu_percent(interval=None)
            load += int(cpu / 2 + mem_mb / 10)
        except Exception:
            pass

        # 限制为非负整数
        self.load_amount = max(0, int(load))

    def ui_pack(self):
        self.info_frame.place_forget()
        self.mask_left.place_forget()
        self.mask_right.place_forget()
        self.info_line.place_forget()

        self.mask_left.place(x=0, y=0, relheight=1)
        self.mask_right.place(x=tk.winfo_screenwidth() - 17, y=0, relheight=1)
        self.info_line.place(x=0, y=tk.winfo_screenheight() - 27, relwidth=1)
        self.info_frame.place(x=10, y=tk.winfo_screenheight() - 23)

    def load_ui(self):
        tk.title("作业管理器")
        tk.geometry("1280x720")
        tk.attributes("-fullscreen", True)  # ! Uncomment when release
        tk.config(bg="#23272E")
        tk.resizable(False, False)

        try:
            tk.iconbitmap("HM.ico")
        except:
            pass

        self.main_frame = Frame(tk, relief=FLAT)
        self.main_frame.place(x=0, y=0, relheight=1, relwidth=1)

        self.POSITION_TIME_DISPLAY_X = tk.winfo_screenwidth() - 205

        # 左右遮罩（保留为实例变量，便于控制叠放顺序）
        self.mask_left = Frame(self.main_frame, width=45)
        self.mask_right = Frame(self.main_frame, width=17)

        self.top_frame = Frame(self.main_frame, relief=FLAT)
        self.ui_top_exit = Button(
            self.top_frame,
            text="退出",
            fg=COLOR,
            font=("汉仪文黑-85W", 14),
            relief=FLAT,
            command=self.exit,
            width=3,
        )
        self.ui_top_add = Button(
            self.top_frame,
            text="添加",
            fg=COLOR,
            font=("汉仪文黑-85W", 14),
            relief=FLAT,
            command=self.new_homework,
            width=3,
        )
        self.ui_top_clear = Button(
            self.top_frame,
            text="清理",
            fg=COLOR,
            font=("汉仪文黑-85W", 14),
            relief=FLAT,
            command=self.clear_homework,
            width=3,
        )
        self.ui_top_help = Button(
            self.top_frame,
            text="帮助",
            fg=COLOR,
            font=("汉仪文黑-85W", 14),
            relief=FLAT,
            command=lambda: help.open_help(tk.winfo_screenwidth(), tk.winfo_screenheight()),
            width=3,
        )
        self.ui_top_menu = Button(
            self.top_frame,
            text="菜单",
            fg=COLOR,
            font=("汉仪文黑-85W", 14),
            relief=FLAT,
            command=menu.open_menu,
            width=3,
        )
        

        # 顶栏按钮：保持原有排列顺序与占位大小，仅应用配色与悬停反馈
        self.ui_top_exit.pack(side="right")
        self.ui_top_add.pack(side="right")
        self.ui_top_clear.pack(side="right")
        self.ui_top_help.pack(side="right")
        self.ui_top_menu.pack(side="right")

        theme.style_button(
            self.ui_top_exit, "danger", keep_geometry=True, font=("汉仪文黑-85W", 14)
        )
        theme.style_button(
            self.ui_top_add, "accent", keep_geometry=True, font=("汉仪文黑-85W", 14)
        )
        theme.style_button(
            self.ui_top_clear, "normal", keep_geometry=True, font=("汉仪文黑-85W", 14)
        )
        theme.style_button(
            self.ui_top_help, "normal", keep_geometry=True, font=("汉仪文黑-85W", 14)
        )
        theme.style_button(
            self.ui_top_menu, "normal", keep_geometry=True, font=("汉仪文黑-85W", 14)
        )

        self.ui_side_delete = Button(
            self.main_frame, text="×", fg=COLOR, relief=FLAT, font=("JetBrains Mono", 8)
        )
        self.ui_side_edit = Button(
            self.main_frame, text="E", fg=COLOR, relief=FLAT, font=("JetBrains Mono", 8)
        )
        # 保持原有尺寸/占位与配色，仅增加悬停反馈
        theme.style_button(self.ui_side_delete, "danger", keep_geometry=True)
        theme.style_button(self.ui_side_edit, "normal", keep_geometry=True)

        # 创建用于显示作业列表的 Canvas（替代多个 Label）
        self.list_canvas = Canvas(self.main_frame, bg=theme.BG, highlightthickness=0)
        canvas_width = self.POSITION_TIME_DISPLAY_X - 50
        self.list_canvas.place(
            x=45, y=40, width=canvas_width, height=tk.winfo_screenheight() - 60
        )

        self.info_frame = Frame(self.main_frame, relief=FLAT)

        # 底部信息栏上方的细分隔线
        self.info_line = Frame(self.main_frame, height=1, bg=theme.LINE)

        self.ui_info_basic = Label(
            self.info_frame, text="", font=("JetBrains Mono", 9), fg=COLOR
        )  # 用于显示基本信息
        self.ui_info_time = Label(
            self.info_frame, text="", font=("JetBrains Mono", 9), fg=COLOR
        )  # 用于显示时间状态
        self.ui_info_homework = Label(
            self.info_frame, text="", font=("JetBrains Mono", 9), fg=COLOR
        )  # 用于显示作业数量
        self.ui_info_load = Label(
            self.info_frame, text="", font=("JetBrains Mono", 9), fg=COLOR
        )  # 用于显示负载
        self.ui_info_mouse = Label(
            self.info_frame, text="", font=("JetBrains Mono", 9), fg=COLOR
        )  # 用于显示鼠标位置
        self.ui_info_tick = Label(
            self.info_frame, text="", font=("JetBrains Mono", 9), fg=COLOR
        )  # 用于显示 tick 计数
        self.ui_info_message = Label(
            self.info_frame, text="", font=("JetBrains Mono", 9), fg=COLOR
        )  # 自动更新

        # 信息栏：项之间加细分隔符，弱化分隔、突出内容
        def _pack_info(widget, first=False):
            if not first:
                Label(
                    self.info_frame,
                    text="│",
                    font=("JetBrains Mono", 9),
                    fg=theme.LINE,
                ).pack(side="left", padx=2)
            widget.pack(side="left", padx=2)

        _pack_info(self.ui_info_basic, first=True)
        _pack_info(self.ui_info_time)
        _pack_info(self.ui_info_homework)
        _pack_info(self.ui_info_load)
        _pack_info(self.ui_info_mouse)
        _pack_info(self.ui_info_tick)
        self.ui_page_prev = Button(
            self.info_frame,
            text="↑",
            command=self._page_previous,
            font=("JetBrains Mono", 10),
            relief=FLAT,
            width=2,
        )
        self.ui_page_next = Button(
            self.info_frame,
            text="↓",
            command=self._page_next,
            font=("JetBrains Mono", 10),
            relief=FLAT,
            width=2,
        )
        theme.style_button(self.ui_page_prev, "normal", padx=2, pady=0, font=("JetBrains Mono", 10))
        theme.style_button(self.ui_page_next, "normal", padx=2, pady=0, font=("JetBrains Mono", 10))
        _pack_info(self.ui_page_prev)
        self.ui_page_next.pack(side="left", padx=2)
        _pack_info(self.ui_info_message)

        self.ui_info_message.bind("<Button-1>", updater.response)

        homeworkfunc.uri_classisland("homeworkmode-on")

    def info(self, flash_tick=0):

        # 预处理与计时
        def is_foreground():
            return (
                pygetwindow.getActiveWindow()
                and pygetwindow.getActiveWindow().title == tk.title()
            )

        flash_load = 20
        flash_background = 80

        flash_tick += 1
        if flash_tick > 20000:
            flash_tick = 0

        # 解析当前显示内容

        if not is_foreground() and flash_tick // flash_background % 2 != 0:
            text_basic = f"   Background    {VERSION}"
            color_fg_basic = "#FFFFFF"
            color_bg_basic = "#005EFF"
        else:
            # COMMON
            text_basic = f"Homework Manager {VERSION}"
            color_fg_basic = COLOR
            color_bg_basic = "#23272E"

        homework = len(self.homework_list)
        # 不再限制作业数量，仅显示作业数
        text_homework = f"作业数: {homework:02d}"
        color_fg_homework = COLOR
        color_bg_homework = "#23272E"

        text_load = f"负载: {self.load_amount}"
        if self.load_amount > 200:
            if flash_tick // flash_load % 2 != 0:
                color_fg_load = "#FFFFFF"
                color_bg_load = "#FF0000"
            else:
                color_fg_load = "#FF0000"
                color_bg_load = "#23272E"
        elif self.load_amount > 100:
            if flash_tick // flash_load % 2 != 0:
                color_fg_load = "#000000"
                color_bg_load = "#FFFF00"
            else:
                color_fg_load = "#FFFF00"
                color_bg_load = "#23272E"
        else:
            color_fg_load = COLOR
            color_bg_load = "#23272E"

        # 更新UI

        self.ui_info_basic.config(
            text=text_basic,
            bg=color_bg_basic,
            fg=color_fg_basic,
        )

        self.ui_info_time.config(
            text=f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}"
        )

        self.ui_info_homework.config(
            text=text_homework,
            bg=color_bg_homework,
            fg=color_fg_homework,
        )

        self.ui_info_load.config(
            text=text_load,
            bg=color_bg_load,
            fg=color_fg_load,
        )

        if mouse:
            self.ui_info_mouse.config(
                text=f"鼠标: ({self.mousex:04d}, {self.mousey:04d})",
                fg=COLOR,
            )
        else:
            self.ui_info_mouse.config(
                text=f"鼠标: (====N/A====)", fg="#FFFF00"
            )

        self.ui_info_tick.config(text=f"Tick: {self.tick:03d}")

        if updater.STATUS == "None":
            self.ui_info_message.configure(text="", fg=COLOR, bg="#23272E")
        elif updater.STATUS == "Connecting":
            self.ui_info_message.configure(
                text="尝试连接至服务器……", fg="#FFFFFF", bg="#23272E"
            )
        elif updater.STATUS == "Latest":
            self.ui_info_message.configure(
                text="无需更新", fg="#1AFF00", bg="#23272E"
            )
        elif updater.STATUS == "Needed":
            self.ui_info_message.configure(
                text=f"发现更新：{updater.UPDATE_NAME} ({updater.UPDATE_TYPE} | {updater.UPDATE_VER})",
                fg="#FFFFFF",
                bg="#005EFF",
            )
        elif updater.STATUS == "Downloading":
            self.ui_info_message.configure(
                text=f"下载更新中……({updater.DOWNLOAD_PROCESS:.2f}% {updater.DOWNLOAD_SPEED / 1048576 :.2f}MB/s | {updater.DOWNLOAD_SIZE / 1048576 :.1f}MB)",
                fg="#FFFFFF",
                bg="#005EFF",
            )
        elif updater.STATUS == "Completed":
            self.ui_info_message.configure(
                text="重启以更新",
                fg="#000000",
                bg="#00FF40",
            )
        elif updater.STATUS == "Failed":
            self.ui_info_message.configure(
                text="离线或未能连接到服务器", fg="#FF0000", bg="#23272E"
            )

        tk.after(33, lambda: self.info(flash_tick))

    def clear_homework(self):
        # 清理所有“时间已过”的作业（时间戳非0且早于当前时间一定时间以前）
        removed = 0
        for key in self.subject_codes:
            new_list = []
            for item in self.data.get(key, []):
                try:
                    t = int(item.get("time", 0))
                except Exception:
                    try:
                        t = float(item.get("time", 0))
                    except Exception:
                        t = 0
                # 时间为0表示不收，跳过；过期规则：比当前时间早超过一定时间视为已过。
                # 但若启用了截止时间且截止未到，即使开始收集已超时也不清理。
                expired = (
                    t != 0
                    and t < time.time() - homeworkfunc.TIME_OUT
                    and not homeworkfunc.has_open_deadline(item)
                )
                if expired:
                    removed += 1
                else:
                    new_list.append(item)
            self.data[key] = new_list
        if removed > 0:
            # 批量删除前备份，便于恢复
            backup.backup_file(DATA, tag="homework")
            with open(DATA, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo(
                "作业管理器·清理完成",
                "已清理 %d 个作业。" % (removed),
            )
        else:
            messagebox.showinfo(
                "作业管理器·清理完成", "没有需要清理的作业。"
            )
            return
        self.draw_homework()

    def new_homework(
        self,
        emphasize_index=None,
        subject_index=None,
        content_text=None,
        collection_timestamp=None,
        existing_deadline=None,
        replace_target=None,
    ):
        # ── 页面式 UI：与菜单页 / 帮助页一致，内置于主窗口（覆盖整个窗口）──
        page = Frame(tk, bg=theme.BG, relief=FLAT)
        page.place(x=0, y=0, relheight=1, relwidth=1)

        # 顶部栏：右侧取消按钮（与菜单页“退出菜单”的位置、样式一致）
        page_top = Frame(page, bg=theme.BG, relief=FLAT)
        page_top.place(x=0, y=0, relwidth=1)
        page_cancel = Button(
            page_top,
            text="取消",
            fg=theme.MUTED,
            font=("汉仪文黑-85W", 14),
            relief=FLAT,
            command=page.destroy,
        )
        theme.style_button(
            page_cancel, "normal", padx=14, pady=4, font=("汉仪文黑-85W", 14)
        )
        page_cancel.pack(side="right", padx=(2, 14), pady=6)

        # 标题：居左（与菜单页“科目管理”一致：左侧色条 + 标题）
        title_frame = Frame(page, relief=FLAT)
        title_frame.place(x=20, y=30)
        Frame(title_frame, width=3, height=18, bg=theme.ACCENT).pack(
            side="left", padx=(0, 8)
        )
        Label(
            title_frame,
            text="编辑作业" if replace_target else "新建作业",
            fg=theme.FG,
            font=("HYWenHei-85W", 16),
        ).pack(side="left")

        # 表单容器：整体靠左放置（与菜单页内容一样从 x=20 开始）；
        # 宽度随窗口（屏幕）变化，输入列（col2）占满标签列右侧的剩余区域。
        form = Frame(page, relief=FLAT)
        form.place(x=20, y=70, relwidth=1, width=-40)
        form.grid_columnconfigure(2, weight=1)

        Label(form, text="科目", bg="#23272E", font=("HYWenHei-85W", 16)).grid(
            row=1, column=1
        )

        if subject_index is not None and 0 <= subject_index < len(
            self.subject_display_names
        ):
            subject_var = self.subject_display_names[subject_index]
        else:
            subject_var = self.subject_display_names[0]
            subject_index = 0

        def subject_change(index, objects):
            nonlocal subject_var
            subject_var = self.subject_display_names[index]
            for btn in objects:
                btn.configure(fg=theme.MUTED)
            objects[index].configure(fg=theme.ACCENT)

        # TODO SUBJECT SELECT
        subject_select_frame = Frame(form, relief=FLAT)
        subject_select_frame.grid(row=1, column=2)

        num = len(self.subject_display_names)
        # 计算第一行放多少个（向上取整，保证第二行不会多于第一行）
        row1_count = (num + 1) // 2

        # 创建两个行容器
        row1 = Frame(subject_select_frame)
        row2 = Frame(subject_select_frame)
        row1.pack()
        row2.pack()

        subject_select = []
        for i in range(len(self.subject_display_names)):
            # 根据 i 选择放在哪一行
            parent = row1 if i < row1_count else row2
            btn = Button(
                parent,
                text=self.subject_display_names[i],
                command=lambda i=i, ss=subject_select: subject_change(i, ss),
                relief=FLAT,
                font=("HYWenHei-85W", 15),
                fg=theme.ACCENT if subject_index == i else theme.MUTED,
                bd=0,
                highlightthickness=0,
                cursor="hand2",
                padx=10,
                pady=2,
            )
            theme.hover_bg(btn, theme.BG, theme.PANEL_HI)
            btn.pack(side="left", expand=True, padx=2)
            subject_select.append(btn)

        Label(form, text="内容", bg="#23272E", font=("HYWenHei-85W", 16)).grid(
            row=2, column=1
        )
        content_entry = Entry(form, width=60, font=("HYWenHei-85W", 16))
        theme.style_entry(content_entry)
        content_entry.grid(row=2, column=2, padx=6, pady=4)
        if content_text:
            content_entry.insert(0, content_text)

        Label(
            form, text="开始收集", bg="#23272E", font=("HYWenHei-85W", 16)
        ).grid(row=3, column=1)

        # * 重要：时间解析位（开始收集时间）
        if collection_timestamp is not None:
            try:
                if collection_timestamp == 0:
                    raise TypeError

                time_value = time.strftime(
                    "%Y/%m/%d %H:%M", time.localtime(collection_timestamp)
                )
            except TypeError:
                time_value = collection_timestamp
        else:
            time_value = time.strftime("%Y/%m/%d 22:30", time.localtime(time.time()))

        time_entry = Entry(
            form,
            width=20,
            textvariable=StringVar(form, value=time_value),
            justify="center",
            font=("HYWenHei-85W", 16),
        )
        theme.style_entry(time_entry)
        time_entry.grid(row=3, column=2, pady=4)

        time_select_frame = Frame(form, relief=FLAT)
        time_select_frame.grid(row=4, column=2)

        time_select = []

        time_select.append(
            Button(
                time_select_frame,
                text="不收",
                command=lambda: time_entry.configure(
                    textvariable=StringVar(
                        time_select_frame,
                        value="0",
                    )
                ),
                relief=FLAT,
                font=("HYWenHei-85W", 16),
            )
        )
        time_select.append(
            Button(
                time_select_frame,
                text="-1天",
                command=lambda: time_entry.configure(
                    textvariable=StringVar(
                        time_select_frame,
                        value=time.strftime(
                            "%Y/%m/%d 22:30",
                            time.localtime(
                                time.mktime(
                                    time.strptime(time_entry.get(), "%Y/%m/%d %H:%M")
                                )
                                - 86400
                            ),
                        ),
                    )
                ),
                relief=FLAT,
                font=("HYWenHei-85W", 16),
            )
        )
        time_select.append(
            Button(
                time_select_frame,
                text="今天",
                command=lambda: time_entry.configure(
                    textvariable=StringVar(
                        time_select_frame,
                        value=time.strftime(
                            "%Y/%m/%d 22:30", time.localtime(time.time())
                        ),
                    )
                ),
                relief=FLAT,
                font=("HYWenHei-85W", 16),
            )
        )
        time_select.append(
            Button(
                time_select_frame,
                text="明天",
                command=lambda: time_entry.configure(
                    textvariable=StringVar(
                        time_select_frame,
                        value=time.strftime(
                            "%Y/%m/%d 22:30", time.localtime(time.time() + 86400)
                        ),
                    )
                ),
                relief=FLAT,
                font=("HYWenHei-85W", 16),
            )
        )
        time_select.append(
            Button(
                time_select_frame,
                text="后天",
                command=lambda: time_entry.configure(
                    textvariable=StringVar(
                        time_select_frame,
                        value=time.strftime(
                            "%Y/%m/%d 22:30", time.localtime(time.time() + 86400 * 2)
                        ),
                    )
                ),
                relief=FLAT,
                font=("HYWenHei-85W", 16),
            )
        )
        time_select.append(
            Button(
                time_select_frame,
                text="+1天",
                command=lambda: time_entry.configure(
                    textvariable=StringVar(
                        time_select_frame,
                        value=time.strftime(
                            "%Y/%m/%d 22:30",
                            time.localtime(
                                time.mktime(
                                    time.strptime(time_entry.get(), "%Y/%m/%d %H:%M")
                                )
                                + 86400
                            ),
                        ),
                    )
                ),
                relief=FLAT,
                font=("HYWenHei-85W", 16),
            )
        )

        for i in time_select:
            i.pack(side="left", expand=True, padx=2)
        for i in time_select:
            theme.style_button(i, "chip", padx=10, pady=2, font=("HYWenHei-85W", 14))

        # ──────────── 截止时间（可选，由开关启用，默认关闭）────────────
        Label(
            form, text="截止时间", bg="#23272E", font=("HYWenHei-85W", 16)
        ).grid(row=5, column=1)

        # 解析已有截止时间的初值
        _deadline_value = time.strftime(
            "%Y/%m/%d 22:30", time.localtime(time.time())
        )
        try:
            _deadline_existing = (
                existing_deadline is not None
                and not isinstance(existing_deadline, bool)
                and float(existing_deadline) > 0
            )
        except Exception:
            _deadline_existing = False
        if _deadline_existing:
            _deadline_value = time.strftime(
                "%Y/%m/%d %H:%M",
                time.localtime(float(existing_deadline)),
            )
        deadline_on = _deadline_existing

        # 截止时间输入区域（含快捷按钮）；开关关闭时隐藏
        deadline_area = Frame(form, relief=FLAT)
        # 不加 sticky，使截止输入与“开始收集”输入行对齐且水平居中
        deadline_area.grid(row=5, column=2)
        deadline_entry = Entry(
            deadline_area,
            width=20,
            textvariable=StringVar(deadline_area, value=_deadline_value),
            justify="center",
            font=("HYWenHei-85W", 16),
        )
        theme.style_entry(deadline_entry)
        deadline_entry.pack(side="top", anchor="center", pady=4)

        deadline_preset = Frame(deadline_area, relief=FLAT)
        deadline_preset.pack(side="top", anchor="center")

        def _deadline_apply(value):
            deadline_entry.configure(
                textvariable=StringVar(deadline_area, value=value)
            )

        def _deadline_offset(days):
            try:
                base = time.strptime(deadline_entry.get(), "%Y/%m/%d %H:%M")
            except Exception:
                base = time.localtime(time.time())
            _deadline_apply(
                time.strftime(
                    "%Y/%m/%d 22:30",
                    time.localtime(time.mktime(base) + days * 86400),
                )
            )

        for _label, _cmd in [
            ("-1天", lambda: _deadline_offset(-1)),
            (
                "今天",
                lambda: _deadline_apply(
                    time.strftime("%Y/%m/%d 22:30", time.localtime(time.time()))
                ),
            ),
            (
                "明天",
                lambda: _deadline_apply(
                    time.strftime(
                        "%Y/%m/%d 22:30", time.localtime(time.time() + 86400)
                    )
                ),
            ),
            (
                "后天",
                lambda: _deadline_apply(
                    time.strftime(
                        "%Y/%m/%d 22:30", time.localtime(time.time() + 86400 * 2)
                    )
                ),
            ),
            ("+1天", lambda: _deadline_offset(1)),
        ]:
            theme.style_button(
                Button(
                    deadline_preset,
                    text=_label,
                    command=_cmd,
                    font=("HYWenHei-85W", 16),
                ),
                "chip",
                padx=10,
                pady=2,
                font=("HYWenHei-85W", 14),
            ).pack(side="left", expand=True, padx=2)

        deadline_switch = Button(
            form,
            text="已启用" if deadline_on else "未启用",
            fg=theme.ACCENT if deadline_on else theme.MUTED,
            relief=FLAT,
            font=("HYWenHei-85W", 15),
            command=lambda: None,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            padx=12,
            pady=4,
        )
        theme.hover_bg(deadline_switch, theme.BG, theme.PANEL_HI)
        deadline_switch.grid(row=5, column=2, sticky="w", padx=6)

        def toggle_deadline():
            nonlocal deadline_on
            deadline_on = not deadline_on
            deadline_switch.config(
                text="已启用" if deadline_on else "未启用",
                fg=theme.ACCENT if deadline_on else theme.MUTED,
            )
            if deadline_on:
                deadline_area.grid()
            else:
                deadline_area.grid_remove()

        deadline_switch.config(command=toggle_deadline)

        if not deadline_on:
            deadline_area.grid_remove()

        Label(form, text="优先级", bg="#23272E", font=("HYWenHei-85W", 16)).grid(
            row=7, column=1
        )
        emphasize_var = StringVar(form)
        if emphasize_index is not None and 0 <= emphasize_index < len(
            self.emphasize_levels
        ):
            emphasize_var.set(self.emphasize_levels[emphasize_index])
        else:
            emphasize_var.set(self.emphasize_levels[0])
        emphasize_menu = OptionMenu(form, emphasize_var, *self.emphasize_levels)
        theme.style_option_menu(emphasize_menu, font=("HYWenHei-85W", 14))
        emphasize_menu.grid(row=7, column=2)

        def submit():
            new_subject_index = self.subject_display_names.index(subject_var)
            new_subject_key = self.subject_codes[new_subject_index]
            content = content_entry.get()
            collection_str = time_entry.get()
            new_emphasize = emphasize_var.get()

            # * 重要：时间解析位（开始收集时间）
            try:
                if (
                    collection_str == "0"
                    or collection_str == ""
                    or collection_str == "不收"
                ):
                    new_collection_ts = 0
                    raise KeyboardInterrupt

                new_collection_ts = int(
                    time.mktime(
                        time.strptime(
                            homeworkfunc.analyze_time_string(collection_str),
                            "%Y/%m/%d %H:%M",
                        )
                    )
                )
            except ValueError:
                new_collection_ts = collection_str
            except KeyboardInterrupt:
                pass

            # 截止时间：仅当开关开启时保存（无效输入按 0 = 未设置处理）
            new_deadline_ts = 0
            if deadline_on:
                _dstr = deadline_entry.get()
                if _dstr not in ("0", "", "不收"):
                    try:
                        new_deadline_ts = int(
                            time.mktime(
                                time.strptime(
                                    homeworkfunc.analyze_time_string(_dstr),
                                    "%Y/%m/%d %H:%M",
                                )
                            )
                        )
                    except (ValueError, TypeError):
                        new_deadline_ts = 0

            new_item = {
                "content": content,
                "time": new_collection_ts,
                "deadline": new_deadline_ts,
                "emphasize": new_emphasize,
            }
            if replace_target:
                orig_key, orig_index = replace_target
                if orig_key == new_subject_key:
                    try:
                        self.data[orig_key][orig_index] = new_item
                    except Exception:
                        self.data[new_subject_key].append(new_item)
                else:
                    try:
                        self.data[orig_key].pop(orig_index)
                    except Exception:
                        try:
                            for idx, it in enumerate(self.data[orig_key]):
                                if it.get("content") == content:
                                    self.data[orig_key].pop(idx)
                                    break
                        except Exception:
                            pass
                    self.data[new_subject_key].append(new_item)
            else:
                self.data[new_subject_key].append(new_item)
            with open(DATA, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            self.draw_homework()
            page.destroy()

        # 操作按钮：居左排布（内嵌页面后不再需要随开关重新定位窗口）
        button_row = Frame(form, relief=FLAT)
        button_row.grid(row=8, column=2, sticky="w", pady=(10, 4))
        theme.style_button(
            Button(button_row, text="提交", command=submit, font=("HYWenHei-85W", 16)),
            "accent",
            padx=20,
            pady=4,
            font=("HYWenHei-85W", 16),
        ).pack(side="left")
        theme.style_button(
            Button(
                button_row,
                text="取消",
                command=page.destroy,
                font=("HYWenHei-85W", 16),
            ),
            "normal",
            padx=20,
            pady=4,
            font=("HYWenHei-85W", 16),
        ).pack(side="left", padx=(10, 0))

    def _import_extra_subjects(self, extra_keys):
        """
        把 homework.json 中存在但尚未配置到 setting.json 的科目键自动并入，
        并刷新内存中的科目列表，使数据在本会话即可显示（而不是被丢弃）。
        """
        try:
            with open(paths.CONFIG_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception:
            settings = {}
        if not isinstance(settings, dict):
            settings = {}
        subjects = settings.get("Subjects")
        if not isinstance(subjects, dict):
            subjects = {}
        known_codes = set(subjects.values())
        changed = False
        for k in extra_keys:
            if k in ("VER",):
                continue
            if k not in known_codes and k not in subjects:
                subjects[k] = k
                changed = True
        if changed:
            settings["Subjects"] = subjects
            try:
                paths.ensure_dirs()
                with open(paths.CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(settings, f, ensure_ascii=False, indent=4)
            except Exception:
                pass
            # 刷新模块级科目表，让本会话立即生效
            homeworkfunc.load_subjects()
            self.subject_codes = list(homeworkfunc.SUBJECT_CODES)
            self.subject_display_names = list(homeworkfunc.SUBJECT_DISPLAY_NAMES)

    def delete_homework(self, index):
        if not messagebox.askyesno("作业管理器·删除提示", "确定要删除吗？"):
            return
        count = 0
        for i in self.subject_codes:
            for j in self.data[i]:
                if count == index:
                    self.data[i].remove(j)
                    # 删除前备份，便于恢复
                    backup.backup_file(DATA, tag="homework")
                    with open(DATA, "w", encoding="utf-8") as f:
                        json.dump(self.data, f, ensure_ascii=False, indent=4)
                    self.draw_homework()
                    return
                count += 1

    def edit_homework(self, index):
        count = 0
        for subject_key in self.subject_codes:
            for j in self.data[subject_key]:
                if count == index:
                    try:
                        subject_index = self.subject_codes.index(subject_key)
                    except ValueError:
                        subject_index = 0
                    content_text = j.get("content", "")
                    collection_ts = j.get("time", 0)
                    existing_deadline = j.get("deadline", 0)
                    emphasize_index = self.emphasize_levels.index(j["emphasize"])
                    orig_index = self.data[subject_key].index(j)
                    self.new_homework(
                        emphasize_index=emphasize_index,
                        subject_index=subject_index,
                        content_text=content_text,
                        collection_timestamp=collection_ts,
                        existing_deadline=existing_deadline,
                        replace_target=(subject_key, orig_index),
                    )
                    return
                count += 1

    def mouse_move(self, event):
        self.tick = 0
        x = event.x_root - tk.winfo_rootx()
        y = event.y_root - tk.winfo_rooty()
        self.mousex, self.mousey = x, y

        # 根据当前页各条目的纵向范围定位鼠标所在作业
        local_y = y - self.LIST_TOP
        self.arg = -1
        self._hover_seg_y = 0
        acc = 0
        for e in getattr(self, "_page_entries", []):
            if acc <= local_y < acc + e["height"]:
                self.arg = e["index"]
                self._hover_seg_y = acc
                break
            acc += e["height"]

        # 行悬停高亮
        self._update_row_hover()

        self.top_frame.place(x=0, y=0, relwidth=1)

        if self.arg <= -1:
            self.ui_side_edit.place_forget()
            self.ui_side_delete.place_forget()
            return

        entry_y = getattr(self, "_hover_seg_y", 0)
        self.ui_side_delete.place(x=5, y=self.LIST_TOP + entry_y + 2)
        self.ui_side_edit.place(x=25, y=self.LIST_TOP + entry_y + 2)
        self.ui_side_delete.config(command=lambda: self.delete_homework(self.arg))
        self.ui_side_edit.config(command=lambda: self.edit_homework(self.arg))

    def _update_row_hover(self):
        """行悬停时提亮该条目文字，离开时还原（配合左侧操作按钮）。"""
        idx = getattr(self, "arg", -1)
        prev = getattr(self, "_hover_idx", -1)
        if idx == prev:
            return
        canvas_map = getattr(self, "_entry_canvas", {})
        fills = getattr(self, "_entry_fill", {})
        for item_id in canvas_map.get(prev, []):
            try:
                self.list_canvas.itemconfig(
                    item_id, fill=fills.get(prev, theme.FG)
                )
            except Exception:
                pass
        for item_id in canvas_map.get(idx, []):
            try:
                self.list_canvas.itemconfig(item_id, fill=theme.FG_HOVER)
            except Exception:
                pass
        self._hover_idx = idx

    def exit(self):
        homeworkfunc.uri_classisland("homeworkmode-off")
        sys.exit(0)


def main():
    """
    程序入口：尝试获取进程锁，启动 GUI 主循环。
    """

    _lock = acquire_lock()
    if not _lock:
        # 无法获取锁，提示用户程序已在运行
        tmp_root = Tk()
        tmp_root.withdraw()
        messagebox.showwarning("错误", "程序已在运行，无法启动多个实例。")
        tmp_root.destroy()
        sys.exit(0)

    # 创建全局 tk（保持与原代码兼容）并启动应用
    global tk
    tk = Tk()
    app = HomeworkTool()

    thread = threading.Thread(target=updater.check)
    thread.daemon = True
    thread.start()

    tk.mainloop()


if __name__ == "__main__":
    main()
