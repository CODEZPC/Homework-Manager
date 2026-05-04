from tkinter import *
from tkinter import messagebox

try:
    import mouse
except Exception:
    # 在无法导入或权限受限时降级为 None，避免程序崩溃
    mouse = None

import pygetwindow
import json
import keyboard
import os
import sys
import time
import msvcrt
import homeworkfunc as homeworkfunc

COLOR = "#767F89"
DEBUG = False
DATA = "homework.json"
VERSION = "1.4.1.2"


def acquire_lock(lock_path=".\\lock\\homework.lock"):
    """
    尝试获取一个简单的文件锁（Windows 下使用 msvcrt），
    成功返回打开的文件对象（必须保持引用以维持锁），失败返回 None。
    """
    try:
        lock_file = open(lock_path, "w")
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        return lock_file
    except FileNotFoundError:
        # 如果锁文件所在目录不存在，尝试创建目录后重试
        try:
            os.makedirs(os.path.dirname(lock_path), exist_ok=True)
            lock_file = open(lock_path, "w")
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            return lock_file
        except Exception:
            return None
    except PermissionError:
        return None


class HomeworkTool:
    def __init__(self):

        # 默认UI配置
        tk.option_add("*Background", "#23272E")
        tk.option_add("*Foreground", "#C8C8C8")
        tk.option_add("*Font", ("JetBrains Mono", 18))
        self.load_ui()

        # 列表初始化
        self.homework_list = []  # 作业UI
        self.time_list = []  # 时间UI
        self.homework_widths = []  # 作业UI宽度（用于滚动显示）
        self.need_roll = []  # 需要滚动显示的作业索引
        self.new_position = []
        self.subject_codes = homeworkfunc.SUBJECT_CODES
        self.subject_display_names = homeworkfunc.SUBJECT_DISPLAY_NAMES
        self.emphasize_levels = homeworkfunc.EMPHASIZE_LEVELS
        self.reminder_schedule = []  # 计划的tk.after
        for self.HOMEWORK_LIMIT in range(1000):
            if self.HOMEWORK_LIMIT * 30 + 40 >= tk.winfo_screenheight() - 40:
                break

        # 各类定时器的 id（用于取消），初始化为 None
        self._upload_aid = None

        self.mousex, self.mousey = 0, 0

        # 校验资源完整性
        homeworkfunc.resource_check(self.subject_codes)

        # 显示
        self.draw_homework()

        # 鼠标移动事件绑定（用于显示/隐藏按钮）
        tk.bind("<Motion>", self.mouse_move)

        # 自动隐藏按钮的计时器
        self.tick = 0
        tk.after(1, self.on_tick)
        self.info()
        self.ui_pack()

    def on_tick(self):
        """
        每秒调用一次，自动隐藏按钮并防止锁屏。
        """

        # 3秒
        if self.tick > 2:
            try:
                # 隐藏UI按钮
                self.ui_top_exit.place_forget()
                self.ui_top_add.place_forget()
                self.ui_top_refresh.place_forget()
                self.ui_top_clear.place_forget()
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
        object.config(
            state=DISABLED,
            text=f"{second / 10 if second <= 99 else second // 10}s",
            font=("JetBrains Mono", 14),
        )
        tk.after(100, lambda: self.cooldown(object, original, second - 1))

    def draw_homework(self):
        """显示作业列表"""

        self.ui_top_add.config(state=DISABLED)
        self.ui_top_refresh.config(state=DISABLED)
        self.ui_top_clear.config(state=DISABLED)

        # 取消之前计划的提醒（如果有）
        for i in self.reminder_schedule:
            tk.after_cancel(i)

        # 清理之前在 canvas 上的显示与时间显示
        try:
            self.list_canvas.delete("all")
        except Exception:
            # 若 canvas 尚未创建，忽略
            pass
        self.list_canvas.place_forget()  # 隐藏 canvas，后续重新 place
        for i in self.time_list:
            i.place_forget()
        a = Label(tk, text="正在加载...", fg=COLOR, font=("HYWenHei-85W", 24))
        a.place(x=45, y=40)
        tk.update()  # 强制更新界面，确保之前的内容被隐藏

        # 重新加载数据
        with open(DATA, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        # 按规则对每个科目的作业列表排序并在发生变更时写回文件。
        def _sort_key(item):
            t = item.get("time", 0)
            # 规范化字符串值
            if isinstance(t, str):
                return (2, 2)
            else:
                # 非字符串（通常为 int/float）
                try:
                    num = float(t)
                    if num == 0:
                        return (2, 1)
                    return (1, num)
                except Exception:
                    return (2, 2)

        # 对每个 subject 列表应用稳定排序，若发生变化则写回文件一次
        _changed = False
        for key in self.subject_codes:
            orig = self.data.get(key, [])
            # 使用稳定排序，保留相同键的原始相对顺序
            sorted_list = sorted(orig, key=_sort_key)
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

        # 使用 canvas 渲染文本项并缓存宽度与滚动标记
        self.homework_list = []  # 存放文本内容
        self.canvas_items = []
        self.canvas_widths = []
        self.need_roll = []

        # 先收集所有文本和状态
        all_items = []
        for i, subj in enumerate(self.subject_codes):
            a.config(text=f"正在加载 - {self.subject_display_names[i]}...")
            for k in self.data[subj]:
                content = self.subject_display_names[i] + ":" + k["content"]
                status = homeworkfunc.analyze_time(k["time"], k["emphasize"])[1]
                all_items.append((content, status))
            if keyboard.is_pressed("tab"):
                time.sleep(0.6)

        canvas_width = self.POSITION_TIME_DISPLAY_X - 50
        self.list_canvas.place(
            x=45, y=40, width=canvas_width, height=tk.winfo_screenheight() - 60
        )
        inv = 35 if len(all_items) < 10 else 30
        for idx, (text, status) in enumerate(all_items):
            # Canvas 的原点位于屏幕 x=45,y=40，因此在 canvas 内坐标使用相对偏移
            y = idx * inv
            fill = "#C8C8C8"
            if status == -1:
                fill = COLOR
            # 在 canvas 内使用 (0, y) 放置，anchor='nw' 以左上角对齐，保证与原来 place(x=45,y=40+...) 对齐
            item = self.list_canvas.create_text(
                0, y, text=text, anchor="nw", fill=fill, font=("JetBrains Mono", 18)
            )
            self.canvas_items.append(item)
            self.homework_list.append(text)
            bbox = self.list_canvas.bbox(item)
            width = (bbox[2] - bbox[0]) if bbox else 0
            self.canvas_widths.append(width)
            self.need_roll.append(width + 45 > self.POSITION_TIME_DISPLAY_X)

        self.ui_pack()

        a.place_forget()  # 隐藏加载提示
        del a  # 删除加载提示对象

        self.cooldown(self.ui_top_add, "添加")
        self.cooldown(self.ui_top_refresh, "刷新")
        self.cooldown(self.ui_top_clear, "清空")

        # 更新时间显示并计划下一次更新，启动 canvas 滚动
        self.upload_time_display()
        try:
            if getattr(self, "_page_aid", None) is not None:
                tk.after_cancel(self._page_aid)
        except Exception:
            pass
        self._page_interval = 33
        self._page_aid = tk.after(self._page_interval, self.canvas_roll)
        self.reminder_schedule.append(self._page_aid)

    def upload_time_display(self):
        """
        每分钟更新一次时间显示。
        使用实例属性 `_upload_aid` 跟踪上一次调度以便安全取消。
        """

        # 取消上一次的定时器（如果存在）
        if getattr(self, "_upload_aid", None) is not None:
            try:
                tk.after_cancel(self._upload_aid)
                self.reminder_schedule.remove(self._upload_aid)
            except Exception:
                pass

        # 隐藏之前的时间显示
        for i in self.time_list:
            i.place_forget()

        # 清空时间显示列表
        self.time_list = []

        # 重新生成时间显示
        idx = 0
        upload = 0
        for i, j in enumerate(self.subject_codes):
            for k in self.data[j]:
                time_status = homeworkfunc.analyze_time(k["time"], k["emphasize"])
                self.time_list.append(
                    Label(
                        tk,
                        text=time_status[0],
                        width=13,
                        justify="right",
                        anchor="e",
                    )
                )
                if time_status[1] >= 3:
                    self.time_list[-1].config(bg="#C8C8C8", fg="#23272E")
                    if time_status[1] == 4:
                        upload = 1
                elif time_status[1] == 2:
                    self.time_list[-1].config(bg="#666666", fg="#FFFFFF")
                elif time_status[1] == 1:
                    self.time_list[-1].config(bg="#23272E", fg="#C8C8C8")
                elif time_status[1] == 0:
                    self.time_list[-1].config(bg="#23272E", fg=COLOR)
                elif time_status[1] == -1:
                    self.time_list[-1].config(bg="#23272E", fg=COLOR)
                    try:
                        self.list_canvas.itemconfig(self.canvas_items[idx], fill=COLOR)
                    except Exception:
                        # 兼容旧数据结构，如果 canvas_items 不存在则忽略
                        try:
                            self.homework_list[idx] = self.homework_list[idx]
                        except Exception:
                            pass
                idx += 1
        inv = 35 if len(self.time_list) < 10 else 30
        for idx, widget in enumerate(self.time_list):
            widget.place(x=self.POSITION_TIME_DISPLAY_X, y=40 + idx * inv)

        if upload:
            homeworkfunc.uri_classisland("Homeworkmode-upload")

        now = time.localtime()
        remaining_seconds = 60 - now.tm_sec
        # 只传递方法引用，由方法内部追踪 aid
        self._upload_aid = tk.after(remaining_seconds * 1000, self.upload_time_display)
        self.reminder_schedule.append(self._upload_aid)

    def roll_show(self):
        # Deprecated wrapper: call new canvas_roll
        return self.canvas_roll()

    def canvas_roll(self):
        # 单帧移动幅度与间隔
        dx = 2
        interval = getattr(self, "_page_interval", 33)
        left_bound = 45

        # 对每个需要滚动的 canvas 项目移动（使用 canvas 内坐标）
        canvas_left = self.list_canvas.winfo_x()
        left_bound_canvas = left_bound - canvas_left
        target_right_canvas = self.POSITION_TIME_DISPLAY_X - canvas_left
        for idx, item in enumerate(getattr(self, "canvas_items", [])):
            if not self.need_roll[idx]:
                continue
            bbox = self.list_canvas.bbox(item)
            if not bbox:
                continue
            x1, y1, x2, y2 = bbox
            # 如果整条文本已经移出左侧（右边界 < left_bound_canvas），把它跳到右侧显示线处（canvas 内坐标）
            if x2 < left_bound_canvas:
                # 将文本的左边对齐到全局 POSITION_TIME_DISPLAY_X（转换为 canvas 内坐标）
                target_left_canvas = self.POSITION_TIME_DISPLAY_X - canvas_left
                shift = target_left_canvas - x1
                if shift != 0:
                    self.list_canvas.move(item, shift, 0)
            else:
                self.list_canvas.move(item, -dx, 0)

        # 计划下一帧
        try:
            if getattr(self, "_page_aid", None) is not None:
                # 移除旧的记录（下一行会覆盖）
                try:
                    self.reminder_schedule.remove(self._page_aid)
                except Exception:
                    pass
        except Exception:
            pass
        self._page_aid = tk.after(interval, self.canvas_roll)
        self.reminder_schedule.append(self._page_aid)

    def ui_pack(self):
        self.ui_title.place_forget()
        self.ui_info_basic.place_forget()
        self.ui_info_time.place_forget()
        self.ui_info_mouse.place_forget()
        self.ui_info_homework.place_forget()
        self.ui_info_tick.place_forget()
        self.mask_left.place_forget()
        self.mask_right.place_forget()

        self.mask_left.place(x=0, y=0, relheight=1)
        self.mask_right.place(x=tk.winfo_screenwidth() - 17, y=0, relheight=1)
        self.ui_info_basic.place(x=10, y=tk.winfo_screenheight() - 20)
        self.ui_info_mouse.place(
            x=homeworkfunc.getwidth(self.ui_info_basic, tk)
            + self.ui_info_basic.winfo_x()
            + 10,
            y=tk.winfo_screenheight() - 20,
        )
        self.ui_info_time.place(
            x=homeworkfunc.getwidth(self.ui_info_mouse, tk)
            + self.ui_info_mouse.winfo_x()
            + 10,
            y=tk.winfo_screenheight() - 20,
        )
        self.ui_info_homework.place(
            x=homeworkfunc.getwidth(self.ui_info_time, tk)
            + self.ui_info_time.winfo_x()
            + 10,
            y=tk.winfo_screenheight() - 20,
        )
        self.ui_info_tick.place(
            x=homeworkfunc.getwidth(self.ui_info_homework, tk)
            + self.ui_info_homework.winfo_x()
            + 10,
            y=tk.winfo_screenheight() - 20,
        )
        if not homeworkfunc.uri_classisland("homeworkmode-on"):
            self.ui_title.place(x=10, y=5)

    def load_ui(self):
        tk.title("作业管理器")
        tk.geometry("1280x720")
        tk.attributes("-fullscreen", True)  # ! Uncomment when release
        tk.config(bg="#23272E")
        tk.resizable(False, False)

        self.POSITION_TIME_DISPLAY_X = tk.winfo_screenwidth() - 205
        self.POSITION_TOP_EXIT_X = tk.winfo_screenwidth() - 55
        self.POSITION_TOP_REFRESH_X = tk.winfo_screenwidth() - 111
        self.POSITION_TOP_ADD_X = tk.winfo_screenwidth() - 167
        self.POSITION_TOP_CLEAR_X = tk.winfo_screenwidth() - 223

        # 左右遮罩（保留为实例变量，便于控制叠放顺序）
        self.mask_left = Frame(tk, width=45)
        self.mask_right = Frame(tk, width=17)

        self.ui_title = Label(
            tk,
            text=f"Homework Manager - Today [VER {VERSION}]",
            fg=COLOR,
        )
        self.ui_top_exit = Button(
            tk,
            text="退出",
            fg=COLOR,
            font=("汉仪文黑-85W", 14),
            relief=FLAT,
            command=self.exit,
        )
        self.ui_top_refresh = Button(
            tk,
            text="刷新",
            fg=COLOR,
            font=("汉仪文黑-85W", 14),
            relief=FLAT,
            command=self.draw_homework,
        )
        self.ui_top_add = Button(
            tk,
            text="新建",
            fg=COLOR,
            font=("汉仪文黑-85W", 14),
            relief=FLAT,
            command=self.new_homework,
        )
        self.ui_top_clear = Button(
            tk,
            text="清理",
            fg=COLOR,
            font=("汉仪文黑-85W", 14),
            relief=FLAT,
            command=self.clear_homework,
        )

        self.ui_side_delete = Button(
            tk, text="×", fg=COLOR, relief=FLAT, font=("JetBrains Mono", 8)
        )
        self.ui_side_edit = Button(
            tk, text="E", fg=COLOR, relief=FLAT, font=("JetBrains Mono", 8)
        )

        # 创建用于显示作业列表的 Canvas（替代多个 Label）
        self.list_canvas = Canvas(tk, bg="#23272E", highlightthickness=0)
        canvas_width = self.POSITION_TIME_DISPLAY_X - 50
        self.list_canvas.place(
            x=45, y=40, width=canvas_width, height=tk.winfo_screenheight() - 60
        )

        self.ui_info_basic = Label(
            tk, text="", font=("JetBrains Mono", 7), fg=COLOR
        )  # 用于显示基本信息
        self.ui_info_time = Label(
            tk, text="", font=("JetBrains Mono", 7), fg=COLOR
        )  # 用于显示时间状态
        self.ui_info_mouse = Label(
            tk, text="", font=("JetBrains Mono", 7), fg=COLOR
        )  # 用于显示鼠标位置
        self.ui_info_homework = Label(
            tk, text="", font=("JetBrains Mono", 7), fg=COLOR
        )  # 用于显示作业数量
        self.ui_info_tick = Label(
            tk, text="", font=("JetBrains Mono", 7), fg=COLOR
        )  # 用于显示 tick 计数

    def info(self, window_background=0, homework_exceed=0):
        def is_foreground():
            return pygetwindow.getActiveWindow() and pygetwindow.getActiveWindow().title == tk.title()

        flash_homework = 20
        flash_background = 100

        if not is_foreground():
            window_background += 1
            if window_background > flash_background * 2:
                window_background = 1
        else:
            window_background = 0

        homework = len(self.homework_list)
        if homework > self.HOMEWORK_LIMIT:
            homework_exceed += 1
            if homework_exceed > flash_homework * 2:
                homework_exceed = 1
        else:
            homework_exceed = 0

        self.ui_info_basic.config(
            text=(
                f"Homework Manager {VERSION}"
                if window_background <= flash_background
                else f"   Background    {VERSION}"
            ),
            bg=("#23272E" if window_background <= flash_background else "#0000FF"),
            fg=(COLOR if window_background <= flash_background else "#FFFFFF"),
        )

        self.ui_info_time.config(
            text=f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}"
        )

        if mouse:
            self.ui_info_mouse.config(
                text=f"Mouse: ({self.mousex:04d}, {self.mousey:04d})",
                fg=COLOR,
            )
        else:
            self.ui_info_mouse.config(text="Mouse: (====N/A====)", fg="#FFFF00")

        self.ui_info_homework.config(
            text=f"Homeworks: {f"{homework:02d}" if homework <= self.HOMEWORK_LIMIT + 5 else "-+"}/{self.HOMEWORK_LIMIT:02d}",
            fg=(
                COLOR
                if homework_exceed == 0
                else ("#FFFF00" if homework_exceed <= flash_homework else "#000000")
            ),
            bg=("#FFFF00" if homework_exceed > flash_homework else "#23272E"),
        )

        self.ui_info_tick.config(text=f"Tick: {self.tick:03d}")
        tk.after(33, lambda: self.info(window_background, homework_exceed))

    def clear_homework(self):
        # 清理所有“时间已过”的作业（时间戳非0且早于当前时间10分钟以前）
        removed = 0
        try:
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
                    # 时间为0表示不收，跳过；过期规则：比当前时间早超过10分钟视为已过
                    if t != 0 and t < time.time() - homeworkfunc.TIME_OUT:
                        removed += 1
                    else:
                        new_list.append(item)
                self.data[key] = new_list
            if removed > 0:
                with open(DATA, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=4)
                messagebox.showinfo(
                    "作业管理器·清理完成", f"已清理 {removed} 个已过期作业。"
                )
            else:
                messagebox.showinfo("作业管理器·清理完成", "没有需要清理的作业。")
                return
            self.draw_homework()
        except Exception as e:
            messagebox.showerror("作业管理器·错误", f"清理作业时发生错误：{e}")

    def new_homework(
        self,
        emphasize_index=None,
        subject_index=None,
        content_text=None,
        deadline_timestamp=None,
        replace_target=None,
    ):
        new_window = Toplevel(tk)
        new_window.title("作业管理器·新建作业")
        new_window.config(bg="#23272E")
        new_window.resizable(False, False)
        new_window.attributes("-topmost", True)

        Label(new_window, text=" ").grid(row=0, column=0)
        Label(new_window, text=" ").grid(row=999, column=999)

        Label(new_window, text="科目", bg="#23272E").grid(row=1, column=1)
        subject_var = StringVar(new_window)
        if subject_index is not None and 0 <= subject_index < len(
            self.subject_display_names
        ):
            subject_var.set(self.subject_display_names[subject_index])
        else:
            subject_var.set(self.subject_display_names[0])
        OptionMenu(new_window, subject_var, *self.subject_display_names).grid(
            row=1, column=2
        )

        Label(new_window, text="内容", bg="#23272E").grid(row=2, column=1)
        content_entry = Entry(new_window, width=60, relief=RIDGE)
        content_entry.grid(row=2, column=2)
        if content_text:
            content_entry.insert(0, content_text)

        Label(new_window, text="  截止时间  ", bg="#23272E").grid(row=3, column=1)

        # * 重要：时间解析位
        if deadline_timestamp is not None:
            try:
                if deadline_timestamp == 0:
                    raise TypeError

                time_value = time.strftime(
                    "%Y/%m/%d %H:%M", time.localtime(deadline_timestamp)
                )
            except TypeError:
                time_value = deadline_timestamp
        else:
            time_value = time.strftime("%Y/%m/%d 22:10", time.localtime(time.time()))

        time_entry = Entry(
            new_window,
            width=20,
            textvariable=StringVar(new_window, value=time_value),
            relief=FLAT,
            justify="center",
        )
        time_entry.grid(row=3, column=2)

        Label(new_window, text="优先级", bg="#23272E").grid(row=4, column=1)
        emphasize_var = StringVar(new_window)
        if emphasize_index is not None and 0 <= emphasize_index < len(
            self.emphasize_levels
        ):
            emphasize_var.set(self.emphasize_levels[emphasize_index])
        else:
            emphasize_var.set(self.emphasize_levels[0])
        OptionMenu(new_window, emphasize_var, *self.emphasize_levels).grid(
            row=4, column=2
        )

        def submit():
            if len(self.homework_list) >= self.HOMEWORK_LIMIT:
                new_window.attributes("-topmost", False)
                if not messagebox.askyesno(
                    "作业管理器·超过上限", "作业数量已达上限，是否强制添加？"
                ):
                    new_window.attributes("-topmost", True)
                    return
            new_subject_index = self.subject_display_names.index(subject_var.get())
            new_subject_key = self.subject_codes[new_subject_index]
            content = content_entry.get()
            deadline_str = time_entry.get()
            new_emphasize = emphasize_var.get()

            # * 重要：时间解析位
            try:
                if deadline_str == "0" or deadline_str == "":
                    new_deadline_ts = 0
                    raise KeyboardInterrupt

                new_deadline_ts = int(
                    time.mktime(time.strptime(deadline_str, "%Y/%m/%d %H:%M"))
                )
            except ValueError:
                new_deadline_ts = deadline_str
            except KeyboardInterrupt:
                pass

            new_item = {
                "content": content,
                "time": new_deadline_ts,
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
            new_window.destroy()

        def show_help():
            help_window = Toplevel(tk)
            help_window.title("作业管理器·帮助")
            help_window.config(bg="#23272E")
            help_window.resizable(False, False)
            help_window.attributes("-topmost", True)

            Label(
                help_window,
                text="""截止时间格式：YYYY/MM/DD HH:MM\n0或留空代表暂时不收\n或者输入任意字符以自定义信息\n\n通常地，在优先级为自动的情况下，\n2天内收的作业按“标准”显示，\n在2天以上按“低”显示，\n目前收取按“高”显示，\n时间已过按“很低”显示，\n自定义信息默认按“标准”显示\n\n也可以自定义优先级，\n在时间已过/现在收的显示不受影响""",
                font=("Jetbrains Mono", 14),
            ).grid(row=1, column=1, padx=20, pady=20)

        Button(new_window, text="提交", command=submit, relief=FLAT).grid(
            row=5, column=2, sticky="e"
        )
        Button(new_window, text="取消", command=new_window.destroy, relief=FLAT).grid(
            row=5, column=2, sticky="w"
        )
        Button(new_window, text="帮助", command=show_help, relief=FLAT).grid(
            row=5, column=2, sticky="s"
        )
        # 将窗口居中偏下显示（不改变窗口大小）
        new_window.update_idletasks()
        sw = new_window.winfo_screenwidth()
        sh = new_window.winfo_screenheight()
        ww = new_window.winfo_width()
        wh = new_window.winfo_height()
        x = (sw - ww) // 2
        y = int((sh - wh) * 0.8)  # 0.6 表示垂直方向偏下（0.5 为正中）
        new_window.geometry(f"+{x}+{y}")

    def delete_homework(self, index):
        if not messagebox.askyesno("作业管理器·提示", "确定要删除吗？"):
            return
        count = 0
        for i in self.subject_codes:
            for j in self.data[i]:
                if count == index:
                    self.data[i].remove(j)
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
                    deadline_ts = j.get("time", 0)
                    emphasize_index = self.emphasize_levels.index(j["emphasize"])
                    orig_index = self.data[subject_key].index(j)
                    self.new_homework(
                        emphasize_index=emphasize_index,
                        subject_index=subject_index,
                        content_text=content_text,
                        deadline_timestamp=deadline_ts,
                        replace_target=(subject_key, orig_index),
                    )
                    return
                count += 1

    def mouse_move(self, event):
        self.tick = 0
        x = event.x_root - tk.winfo_rootx()
        y = event.y_root - tk.winfo_rooty()
        self.mousex, self.mousey = x, y

        inv = 35 if len(self.homework_list) < 10 else 30
        self.arg = int((y - 40) // inv)
        if self.arg >= len(self.homework_list):
            self.arg = -1
        # self.title.config(text=f"鼠标位置：({x}, {y}),{self.arg}")

        self.ui_top_exit.place(x=self.POSITION_TOP_EXIT_X, y=0)
        self.ui_top_refresh.place(x=self.POSITION_TOP_REFRESH_X, y=0)
        self.ui_top_add.place(x=self.POSITION_TOP_ADD_X, y=0)
        self.ui_top_clear.place(x=self.POSITION_TOP_CLEAR_X, y=0)

        if self.arg <= -1:
            self.ui_side_edit.place_forget()
            self.ui_side_delete.place_forget()
            return

        self.ui_side_delete.place(x=5, y=42 + self.arg * inv)
        self.ui_side_edit.place(x=25, y=42 + self.arg * inv)
        self.ui_side_delete.config(command=lambda: self.delete_homework(self.arg))
        self.ui_side_edit.config(command=lambda: self.edit_homework(self.arg))

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
        messagebox.showwarning("作业管理器·提示", "程序已在运行，无法启动多个实例。")
        tmp_root.destroy()
        sys.exit(0)

    # 创建全局 tk（保持与原代码兼容）并启动应用
    global tk
    tk = Tk()
    app = HomeworkTool()
    tk.mainloop()


if __name__ == "__main__":
    main()
