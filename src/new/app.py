"""
作业管理器 - 应用程序入口

整合 Model-View-Service 三层架构，管理全局状态与应用生命周期。
"""

import os
import sys

# 确保 new/ 目录在 sys.path 中，使直接运行 python app.py 也能正常工作
_pkg_dir = os.path.dirname(os.path.abspath(__file__))
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

import tkinter as tk
from tkinter import messagebox
import tkinter.font as tkfont
import json
import time
import threading
from typing import Optional

# ──────────────── 可选依赖 ────────────────
try:
    import mouse as mouse_lib
except Exception:
    mouse_lib = None

try:
    import pygetwindow
except Exception:
    pygetwindow = None

try:
    import keyboard as keyboard_lib
except Exception:
    keyboard_lib = None

import psutil

import config
from models import Logger
from models import DataStore
from services import (
    HomeworkService,
    Updater,
    restart_service,
    acquire_lock,
    analyze_time,
    analyze_time_string,
    parse_deadline,
    sort_key,
    homework_mode_on,
    homework_mode_off,
    homework_upload,
)
from services.data_migration import migrate
from views import (
    RootWindow,
    MainScreen,
    HomeworkDialog,
    MenuDialog,
    HelpDialog,
)


class Application:
    """应用程序主控制器，管理所有子系统和生命周期。"""

    def __init__(self):
        # ── 日志层 ──
        self._logger = Logger()
        self._logger.setup_logging()
        self._loglayer = "Main"

        # ── UI 层（需先创建以获取屏幕尺寸） ──
        self._root = RootWindow()
        self._tk = self._root.tk
        self._screen_w, self._screen_h = self._root.get_screen_size()
        self._logger.log_output(self._loglayer, "Info", "创建主窗口完成")

        # ── 数据层 ──
        self._store = DataStore()
        self._store.ensure_defaults()
        self._logger.log_output(self._loglayer, "Info", "数据校验完成")

        # ── 业务层 ──
        self._homework_svc = HomeworkService(self._store)
        self._updater = Updater()
        self._updater.set_callback(self._on_update_status_change)
        self._logger.log_output(self._loglayer, "Info", "自动更新启动完成")

        # ── 科目配置 ──
        self._subjects = self._store.get_subjects()
        self._subject_codes = list(self._subjects.values())
        self._subject_names = list(self._subjects.keys())
        self._logger.log_output(self._loglayer, "Info", "科目配置获取完成")

        # ── 作业数据 ──
        self._homework_data: dict = {}
        self._homework_count = 0
        self._logger.log_output(self._loglayer, "Info", "作业数据初始化完成")

        # ── Canvas 渲染状态 ──
        self._canvas_items: list = []
        self._canvas_widths: list = []
        self._need_roll: list = []
        self._last_frame_time: Optional[float] = None
        self._load_amount = 0
        self._logger.log_output(self._loglayer, "Info", "渲染器初始化完成")

        # ── 定时器 ID ──
        self._tick_aid: Optional[str] = None
        self._upload_aid: Optional[str] = None
        self._scroll_aid: Optional[str] = None
        self._info_aid: Optional[str] = None
        self._reminder_aids: list = []
        self._logger.log_output(self._loglayer, "Info", "定时器初始化完成")

        # ── 状态 ──
        self._tick = 0
        self._mouse_x = 0
        self._mouse_y = 0

        # ── 计算作业上限 ──
        self._homework_limit = self._calc_homework_limit()
        self._logger.log_output(self._loglayer, "Info", "状态常量初始化完成")

        # ── 主界面 ──
        self._screen = MainScreen(
            parent=self._tk,
            on_exit=self._on_exit,
            on_add=self._on_add,
            on_clear=self._on_clear,
            on_menu=self._on_menu,
            on_help=self._on_help,
            on_update_click=self._on_update_click,
            screen_width=self._screen_w,
            screen_height=self._screen_h,
        )
        self._logger.log_output(self._loglayer, "Info", "主界面启动完成")

        # ── 时间显示 Label 列表 ──
        self._time_labels: list = []

        # ── 数据迁移 ──
        self._migrate_data()
        self._logger.log_output(self._loglayer, "Info", "自动数据迁移检验完成")

        # ── 启动 ──
        homework_mode_on()
        self._draw_homework()
        self._start_timers()

    # ──────────────── 初始化辅助 ────────────────

    def _calc_homework_limit(self) -> int:
        """根据屏幕高度计算最大作业显示数量。"""
        for limit in range(1000):
            if (
                limit * config.UI_ITEM_SPACING_COMPACT + config.UI_CANVAS_TOP
                >= self._screen_h - config.UI_CANVAS_TOP
            ):
                return limit
        return 100

    def _migrate_data(self) -> None:
        """执行数据版本迁移。"""
        data = self._store.load_homework()
        migrated = migrate(data)
        if migrated.get("VER", 0) != data.get("VER", 0):
            self._store.save_homework(migrated)

    # ──────────────── 定时器 ────────────────

    def _start_timers(self) -> None:
        """启动所有周期性定时器。"""
        self._tick_aid = self._root.after(1000, self._on_tick)
        self._info_aid = self._root.after(33, self._info_loop, 0)

    def _cancel_all_reminders(self) -> None:
        """取消所有已计划的提醒。"""
        for aid in self._reminder_aids:
            try:
                self._root.after_cancel(aid)
            except Exception:
                pass
        self._reminder_aids.clear()

    def _schedule_reminder(self, aid: str) -> None:
        """记录一个提醒 ID 以便后续取消。"""
        self._reminder_aids.append(aid)

    # ──────────────── Tick 循环 ────────────────

    def _on_tick(self) -> None:
        """每秒 Tick 处理：自动隐藏按钮、防屏保。"""
        # 隐藏按钮（3 秒后）
        if self._tick > config.TICK_HIDE_BUTTONS:
            try:
                self._screen.hide_top_bar()
                self._screen.hide_side_buttons()
            except Exception:
                pass

        # 防屏保（5 分钟后）
        if self._tick > config.TICK_ANTI_SLEEP:
            if mouse_lib:
                try:
                    mouse_lib.move(config.ANTI_SLEEP_MOUSE_X, config.ANTI_SLEEP_MOUSE_Y)
                    mouse_lib.click()
                except Exception:
                    pass
            self._tick = config.TICK_ANTI_SLEEP_RESET

        self._tick += 1
        self._tick_aid = self._root.after(1000, self._on_tick)
        self._schedule_reminder(self._tick_aid)

    # ──────────────── 信息栏更新 ────────────────

    def _info_loop(self, flash_tick: int = 0) -> None:
        """约 30fps 更新底部信息栏。"""
        flash_tick += 1
        if flash_tick > 20000:
            flash_tick = 0

        # 前台检测
        is_fg = (
            pygetwindow
            and pygetwindow.getActiveWindow()
            and pygetwindow.getActiveWindow().title == self._tk.title()
        )

        # 基本信息
        if not is_fg and flash_tick // 80 % 2 != 0:
            self._screen.info_bar.update_basic(
                f"   Background    {config.VERSION}",
                fg=config.COLOR_FG_WHITE,
                bg=config.COLOR_BG_INFO,
            )
        else:
            self._screen.info_bar.update_basic(
                f"Homework Manager {config.VERSION} |",
            )

        # 时间
        self._screen.info_bar.update_time(
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}"
        )

        # 作业数
        hw = self._homework_count
        hw_text = f"作业数: {hw:02d}/{self._homework_limit:02d}"
        if hw > self._homework_limit + 5:
            if flash_tick // 20 % 2 != 0:
                self._screen.info_bar.update_homework_count(
                    hw_text, fg=config.COLOR_FG_WHITE, bg=config.COLOR_BG_ERROR
                )
            else:
                self._screen.info_bar.update_homework_count(
                    hw_text, fg=config.COLOR_FG_RED
                )
        elif hw > self._homework_limit:
            if flash_tick // 20 % 2 != 0:
                self._screen.info_bar.update_homework_count(
                    hw_text, fg=config.COLOR_FG_BLACK, bg=config.COLOR_BG_WARN
                )
            else:
                self._screen.info_bar.update_homework_count(
                    hw_text, fg=config.COLOR_FG_YELLOW
                )
        else:
            self._screen.info_bar.update_homework_count(hw_text)

        # 负载
        load_text = f"负载: {self._load_amount}"
        if self._load_amount > 200:
            if flash_tick // 20 % 2 != 0:
                self._screen.info_bar.update_load(
                    load_text, fg=config.COLOR_FG_WHITE, bg=config.COLOR_BG_ERROR
                )
            else:
                self._screen.info_bar.update_load(load_text, fg=config.COLOR_FG_RED)
        elif self._load_amount > 100:
            if flash_tick // 20 % 2 != 0:
                self._screen.info_bar.update_load(
                    load_text, fg=config.COLOR_FG_BLACK, bg=config.COLOR_BG_WARN
                )
            else:
                self._screen.info_bar.update_load(load_text, fg=config.COLOR_FG_YELLOW)
        else:
            self._screen.info_bar.update_load(load_text)

        # 鼠标
        if mouse_lib:
            self._screen.info_bar.update_mouse(
                f"鼠标: ({self._mouse_x:04d}, {self._mouse_y:04d})"
            )
        else:
            self._screen.info_bar.update_mouse(
                "鼠标: (====N/A====)", fg=config.COLOR_FG_YELLOW
            )

        # Tick
        self._screen.info_bar.update_tick(f"Tick: {self._tick:03d}")

        # 更新状态
        self._update_status_display()

        self._info_aid = self._root.after(33, self._info_loop, flash_tick)

    def _update_status_display(self) -> None:
        """根据 updater 状态更新信息栏消息区。"""
        s = self._updater.status
        if s == "None":
            self._screen.info_bar.update_message("")
        elif s == "Connecting":
            self._screen.info_bar.update_message(
                "尝试连接至服务器……", fg=config.COLOR_FG_WHITE
            )
        elif s == "Latest":
            self._screen.info_bar.update_message("无需更新", fg=config.COLOR_FG_GREEN)
        elif s == "Needed":
            self._screen.info_bar.update_message(
                f"发现更新：{self._updater.update_name} "
                f"({self._updater.update_type} | {self._updater.update_ver})",
                fg=config.COLOR_FG_WHITE,
                bg=config.COLOR_BG_INFO,
            )
        elif s == "Downloading":
            spd = (
                self._updater.download_speed / 1048576
                if self._updater.download_speed
                else 0
            )
            sz = (
                self._updater.download_size / 1048576
                if self._updater.download_size
                else 0
            )
            self._screen.info_bar.update_message(
                f"下载更新中……({self._updater.download_process:.2f}% "
                f"{spd:.2f}MB/s | {sz:.1f}MB)",
                fg=config.COLOR_FG_WHITE,
                bg=config.COLOR_BG_INFO,
            )
        elif s == "Completed":
            self._screen.info_bar.update_message(
                "重启以更新",
                fg=config.COLOR_FG_BLACK,
                bg=config.COLOR_BG_SUCCESS,
            )
        elif s == "Failed":
            self._screen.info_bar.update_message(
                "离线或未能连接到服务器",
                fg=config.COLOR_FG_RED,
            )

    def _on_update_status_change(self, status: str) -> None:
        """更新器状态变更回调（在后台线程调用，通过 after 回到主线程）。"""
        # after 确保在主线程中执行 UI 更新
        pass  # info_loop 已经每秒都在更新状态显示，无需额外操作

    # ──────────────── 作业列表绘制 ────────────────

    def _draw_homework(self) -> None:
        """加载数据并重新绘制作业列表。"""
        # 禁用按钮
        self._screen._btn_add.config(state=tk.DISABLED)
        self._screen._btn_clear.config(state=tk.DISABLED)

        # 取消之前的定时提醒
        self._cancel_all_reminders()

        # 清除 Canvas
        try:
            self._screen.canvas.delete("all")
        except Exception:
            pass

        # 清除时间标签
        for lbl in self._time_labels:
            try:
                lbl.place_forget()
            except Exception:
                pass
        self._time_labels.clear()

        # 显示加载提示
        loading_label = tk.Label(
            self._screen.main_frame,
            text="正在加载……",
            fg=config.COLOR_FG_DIM,
            font=config.FONT_TITLE,
        )
        loading_label.place(x=config.UI_SIDE_MARGIN_LEFT, y=config.UI_CANVAS_TOP)
        self._tk.update()

        # 加载并排序数据
        self._homework_data = self._homework_svc.load_and_sort(self._subject_codes)

        # 验证并修复键
        self._homework_data, extra_keys, missing_keys = (
            self._store.validate_and_fix_keys(self._homework_data, self._subject_codes)
        )

        if extra_keys:
            messagebox.showwarning(
                "作业管理器·数据警告",
                f"homework.json 中包含未配置的科目键：{', '.join(extra_keys)}，"
                f"已自动忽略。\n如需使用，请在设置中添加对应科目。",
            )

        if extra_keys or missing_keys:
            self._store.save_homework(self._homework_data)

        # 收集所有作业文本
        all_items = []
        for i, code in enumerate(self._subject_codes):
            for item in self._homework_data.get(code, []):
                content = f"{self._subject_names[i]}:{item['content']}"
                status = analyze_time(item["time"], item.get("emphasize", "自动"))[1]
                all_items.append((content, status))
            if keyboard_lib and keyboard_lib.is_pressed("tab"):
                time.sleep(0.6)

        self._homework_count = len(all_items)

        # 在 Canvas 中绘制
        canvas_width = self._screen.time_display_x - config.UI_SIDE_MARGIN_LEFT - 5
        self._screen.canvas.place(
            x=config.UI_SIDE_MARGIN_LEFT,
            y=config.UI_CANVAS_TOP,
            width=canvas_width,
            height=self._screen_h - config.UI_CANVAS_BOTTOM_MARGIN,
        )

        self._canvas_items = []
        self._canvas_widths = []
        self._need_roll = []

        spacing = (
            config.UI_ITEM_SPACING_COMPACT
            if len(all_items) >= config.UI_ITEM_SPACING_THRESHOLD
            else config.UI_ITEM_SPACING_NORMAL
        )

        for idx, (txt, status) in enumerate(all_items):
            y = idx * spacing
            fill = config.COLOR_FG_PRIMARY
            if status == -1:
                fill = config.COLOR_FG_DIM

            item = self._screen.canvas.create_text(
                0,
                y,
                text=txt,
                anchor="nw",
                fill=fill,
                font=config.FONT_HOMEWORK,
            )
            self._canvas_items.append(item)

            bbox = self._screen.canvas.bbox(item)
            width = (bbox[2] - bbox[0]) if bbox else 0
            self._canvas_widths.append(width)
            self._need_roll.append(
                width + config.UI_SIDE_MARGIN_LEFT > self._screen.time_display_x
            )

        # 移除加载提示
        loading_label.place_forget()
        del loading_label

        # 恢复按钮
        self._screen.cooldown_button(self._screen._btn_add, "添加")
        self._screen.cooldown_button(self._screen._btn_clear, "清理")

        # 更新时间显示
        self._upload_time_display()

        # 启动 Canvas 滚动
        if self._scroll_aid:
            self._root.after_cancel(self._scroll_aid)
        self._scroll_aid = self._root.after(
            config.CANVAS_SCROLL_INTERVAL, self._canvas_roll
        )
        self._schedule_reminder(self._scroll_aid)

    # ──────────────── 时间显示更新 ────────────────

    def _upload_time_display(self) -> None:
        """每分钟更新右侧时间显示列。"""
        if self._upload_aid:
            try:
                self._root.after_cancel(self._upload_aid)
            except Exception:
                pass

        # 清除旧标签
        for lbl in self._time_labels:
            try:
                lbl.place_forget()
            except Exception:
                pass
        self._time_labels.clear()

        idx = 0
        upload = 0
        spacing = (
            config.UI_ITEM_SPACING_COMPACT
            if self._homework_count >= config.UI_ITEM_SPACING_THRESHOLD
            else config.UI_ITEM_SPACING_NORMAL
        )

        for code in self._subject_codes:
            for item in self._homework_data.get(code, []):
                time_status = analyze_time(
                    item["time"],
                    item.get("emphasize", "自动"),
                )

                lbl = tk.Label(
                    self._screen.main_frame,
                    text=time_status[0],
                    width=13,
                    justify="left",
                    anchor="e",
                    font=config.FONT_TIME,
                )

                if time_status[1] >= 3:
                    lbl.config(bg=config.COLOR_BG_TIME_HIGH, fg=config.COLOR_BG_MAIN)
                    if time_status[1] == 4:
                        upload = 1
                elif time_status[1] == 2:
                    lbl.config(bg=config.COLOR_BG_TIME_MED, fg=config.COLOR_FG_WHITE)
                elif time_status[1] == 1:
                    lbl.config(bg=config.COLOR_BG_MAIN, fg=config.COLOR_FG_PRIMARY)
                elif time_status[1] == 0:
                    lbl.config(bg=config.COLOR_BG_MAIN, fg=config.COLOR_FG_DIM)
                elif time_status[1] == -1:
                    lbl.config(bg=config.COLOR_BG_MAIN, fg=config.COLOR_FG_DIM)
                    try:
                        self._screen.canvas.itemconfig(
                            self._canvas_items[idx], fill=config.COLOR_FG_DIM
                        )
                    except Exception:
                        pass

                lbl.place(
                    x=self._screen.time_display_x,
                    y=config.UI_CANVAS_TOP + idx * spacing,
                )
                self._time_labels.append(lbl)
                idx += 1

        if upload:
            homework_upload()

        now = time.localtime()
        remaining_seconds = 60 - now.tm_sec
        self._upload_aid = self._root.after(
            remaining_seconds * 1000, self._upload_time_display
        )
        self._schedule_reminder(self._upload_aid)

    # ──────────────── Canvas 滚动 ────────────────

    def _canvas_roll(self) -> None:
        """Canvas 文本滚动一帧。"""
        dx = config.CANVAS_SCROLL_DX
        interval = config.CANVAS_SCROLL_INTERVAL

        now = time.perf_counter()
        frame_dt = None
        if self._last_frame_time is not None:
            frame_dt = now - self._last_frame_time
        self._last_frame_time = now

        canvas_left = self._screen.canvas.winfo_x()
        target_right_canvas = self._screen.time_display_x - canvas_left

        for idx, item in enumerate(self._canvas_items):
            if not self._need_roll[idx]:
                continue
            bbox = self._screen.canvas.bbox(item)
            if not bbox:
                continue
            x1, y1, x2, y2 = bbox
            if x2 < config.UI_SIDE_MARGIN_LEFT - canvas_left:
                shift = target_right_canvas - x1
                if shift != 0:
                    self._screen.canvas.move(item, shift, 0)
            else:
                self._screen.canvas.move(item, -dx, 0)

        self._calc_load(frame_dt, dx)

        if self._scroll_aid:
            try:
                self._root.after_cancel(self._scroll_aid)
            except Exception:
                pass
        self._scroll_aid = self._root.after(interval, self._canvas_roll)
        self._schedule_reminder(self._scroll_aid)

    def _calc_load(self, frame_dt: Optional[float], dx: int) -> None:
        """计算渲染负载。"""
        count_items = len(self._canvas_items)
        rolling_count = sum(1 for n in self._need_roll if n)
        total_pixels = sum(self._canvas_widths)

        if frame_dt and frame_dt > 0:
            fps = 1.0 / frame_dt
        else:
            fps = 1000.0 / float(config.CANVAS_SCROLL_INTERVAL)

        pixels_per_second = dx * fps * max(1, rolling_count)

        load = int(
            count_items * 1
            + rolling_count * 6
            + pixels_per_second / 500.0
            + total_pixels / 2000.0
        )

        try:
            p = psutil.Process(os.getpid())
            mem_mb = p.memory_info().rss / 1024.0 / 1024.0
            cpu = p.cpu_percent(interval=None)
            load += int(cpu / 2 + mem_mb / 10)
        except Exception:
            pass

        self._load_amount = max(0, int(load))

    # ──────────────── 按钮事件处理 ────────────────

    def _on_exit(self) -> None:
        """退出程序。"""
        homework_mode_off()
        self._tk.destroy()
        sys.exit(0)

    def _on_add(self) -> None:
        """打开添加作业对话框。"""
        self._screen.cooldown_button(self._screen._btn_add, "添加")
        HomeworkDialog(
            parent=self._tk,
            subject_display_names=self._subject_names,
            subject_codes=self._subject_codes,
            emphasize_levels=config.EMPHASIZE_LEVELS,
            on_submit=self._on_homework_submit,
            homework_limit=self._homework_limit,
            current_count=self._homework_count,
        )

    def _on_clear(self) -> None:
        """批量清理已过期作业。"""
        self._screen.cooldown_button(self._screen._btn_clear, "清理")
        removed = self._homework_svc.clear_expired(
            self._homework_data, self._subject_codes
        )
        if removed > 0:
            messagebox.showinfo("作业管理器·清理完成", f"已清理 {removed} 个作业。")
            self._draw_homework()
        else:
            messagebox.showinfo("作业管理器·清理完成", "没有需要清理的作业。")

    def _on_menu(self) -> None:
        """打开科目管理菜单。"""
        MenuDialog(
            parent=self._tk,
            data_store=self._store,
            on_restart=restart_service,
        )

    def _on_help(self) -> None:
        """打开帮助手册。"""
        HelpDialog(
            parent=self._tk,
            version=config.VERSION,
            screen_width=self._screen_w,
            screen_height=self._screen_h,
        )

    def _on_update_click(self) -> None:
        """处理更新消息点击。"""
        self._updater.handle_click()

    def _on_homework_submit(
        self,
        subject_idx: int,
        subject_code: str,
        content: str,
        deadline,
        emphasize: str,
        replace_target=None,
    ) -> None:
        """处理作业提交（添加或编辑）。"""
        if replace_target:
            old_code, old_idx = replace_target
            self._homework_svc.update_homework(
                self._homework_data,
                old_subject=old_code,
                old_index=old_idx,
                new_subject=subject_code,
                content=content,
                deadline=deadline,
                emphasize=emphasize,
            )
        else:
            self._homework_svc.add_homework(
                self._homework_data,
                subject_code=subject_code,
                content=content,
                deadline=deadline,
                emphasize=emphasize,
            )
        self._draw_homework()

    # ──────────────── 鼠标事件 ────────────────

    def _on_mouse_move(self, event: tk.Event) -> None:
        """鼠标移动处理：重置 tick、显示/隐藏按钮。"""
        self._tick = 0
        self._mouse_x, self._mouse_y = self._screen.get_mouse_position(event)

        self._screen.show_top_bar()

        hovered = self._screen.get_hovered_index(self._mouse_y, self._homework_count)

        if hovered < 0:
            self._screen.hide_side_buttons()
            return

        self._screen.show_side_buttons(
            index=hovered,
            item_count=self._homework_count,
            on_delete=lambda: self._delete_homework(hovered),
            on_edit=lambda: self._edit_homework(hovered),
        )

    def _delete_homework(self, index: int) -> None:
        """删除指定索引的作业。"""
        if not messagebox.askyesno("作业管理器·删除提示", "确定要删除吗？"):
            return
        result = self._homework_svc.delete_homework(
            self._homework_data, self._subject_codes, index
        )
        if result:
            self._draw_homework()

    def _edit_homework(self, index: int) -> None:
        """编辑指定索引的作业。"""
        found = self._homework_svc.find_homework(
            self._homework_data, self._subject_codes, index
        )
        if not found:
            return

        subject_code, subj_idx, item = found

        try:
            subject_index = self._subject_codes.index(subject_code)
        except ValueError:
            subject_index = 0

        try:
            emphasize_index = config.EMPHASIZE_LEVELS.index(
                item.get("emphasize", "自动")
            )
        except ValueError:
            emphasize_index = 0

        HomeworkDialog(
            parent=self._tk,
            subject_display_names=self._subject_names,
            subject_codes=self._subject_codes,
            emphasize_levels=config.EMPHASIZE_LEVELS,
            on_submit=self._on_homework_submit,
            subject_index=subject_index,
            content_text=item.get("content", ""),
            deadline_value=item.get("time", 0),
            emphasize_index=emphasize_index,
            replace_target=(subject_code, subj_idx),
            homework_limit=self._homework_limit,
            current_count=self._homework_count,
        )

    # ──────────────── 运行 ────────────────

    def run(self) -> None:
        """启动应用主循环。"""
        # 重新绑定鼠标移动事件（覆盖 MainScreen 中的占位绑定）
        self._tk.unbind("<Motion>")
        self._tk.bind("<Motion>", self._on_mouse_move)

        # 启动更新检查
        thread = threading.Thread(target=self._updater.check, daemon=True)
        thread.start()

        self._root.mainloop()


def main() -> None:
    """程序入口：获取进程锁，启动 GUI。"""
    _lock = acquire_lock()
    if not _lock:
        tmp_root = tk.Tk()
        tmp_root.withdraw()
        messagebox.showwarning("错误", "程序已在运行，无法启动多个实例。")
        tmp_root.destroy()
        sys.exit(0)

    app = Application()
    app.run()


if __name__ == "__main__":
    main()
