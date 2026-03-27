from tkinter import *
from tkinter import messagebox
import mouse
import json
import sys
import time
import os
import msvcrt

COLOR = "#767F89"
DEBUG = False
VERSION = "1.3.4"


def analyze_time(timestamp):
    we = ["日", "一", "二", "三", "四", "五", "六"]
    time_day_start = time.mktime(
        time.strptime(
            time.strftime("%Y-%m-%d", time.localtime(time.time())) + " 00:00:00",
            "%Y-%m-%d %H:%M:%S",
        )
    )
    time_now = time.time()
    week_now = time.strftime("%w", time.localtime(time_now))
    t = time.strftime("%H:%M", time.localtime(timestamp))
    w = time.strftime("%w", time.localtime(timestamp))
    if timestamp == 0:
        return "暂时不收"
    elif timestamp < time.time() - 600:
        return "时间已过"
    elif timestamp < time.time():
        return "现在收"
    elif timestamp < time_day_start + 86400:
        return f"{t}收"
    elif timestamp < time_day_start + 86400 * 2:
        return f"明天{t}收"
    elif timestamp < time_day_start + 86400 * 3:
        return f"后天{t}收"
    elif timestamp < time_day_start + 86400 * (8 - int(week_now)):
        return f"周{we[int(w)]}{t}收"
    elif timestamp < time_day_start + 86400 * (15 - int(week_now)):
        return f"下周{we[int(w)]}{t}收"
    else:
        return f"{time.strftime('%Y/%m/%d', time.localtime(timestamp))}收"


def charater_count(string):
    count = 0
    start = 0
    page = []
    eng = "~!@#$%^&*()_+`1234567890-={}|[]\\:\"';<>?,./QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm "
    for i, j in enumerate(string):
        if j in eng:
            count += 1
        else:
            count += 1.666667
        if 70 <= count <= 71 and i <= len(string) - 1:
            if string[i + 1] not in eng:
                page.append(string[start : i + 1])
                start = i + 1
                count = 0
        elif 70 <= count <= 71 and i == len(string) - 1:
            page.append(string[start : i + 1])
            start = i + 1
            count = 0
        elif count >= 71:
            page.append(string[start : i + 1])
            start = i + 1
            count = 0
    page.append(string[start:])
    if page[-1] == "":
        page.pop()
    return page


def getwidth(object):
    tk.update_idletasks()
    return object.winfo_width()


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
        self.homework_page_list = []  # 作业内容存储
        self.subject_codes = [
            "C",
            "M",
            "E",
            "P1",
            "H1",
            "G1",
            "PH1",
            "PH2",
            "CH1",
            "CH2",
            "B1",
            "OTH",
        ]
        self.subject_display_names = [
            "语文 ",
            "数学 ",
            "英语 ",
            "政治 D1",
            "历史 D1",
            "地理 D1",
            "物理 D1",
            "物理 D2",
            "化学 D1",
            "化学 D2",
            "生物 D1",
            "其他",
        ]
        self.reminder_schedule = []  # 计划的tk.after
        self.draw_homework()
        tk.bind("<Motion>", self.mouse_move)
        self.tick = 0
        tk.after(1, self.on_tick)

    def on_tick(self):
        if self.tick > 2:
            try:
                self.ui_top_exit.place_forget()
                self.ui_top_add.place_forget()
                self.ui_top_refresh.place_forget()
            except:
                pass
        if self.tick > 300:
            mouse.move(400, 1200)
            mouse.click()
            self.tick = 3
        self.tick += 1
        tk.after(1000, self.on_tick)

    def draw_homework(self):
        """显示作业列表"""
        for i in self.reminder_schedule:
            tk.after_cancel(i)
        for i in self.homework_list:
            i.place_forget()
        with open("homework.json", "r", encoding="utf-8") as f:
            self.data = json.load(f)
        
        # 按时间戳对 homework.json 每一科进行排序并写回文件
        try:
            for key, lst in self.data.items():
                try:
                    lst.sort(key=lambda it: int(it.get("time", 0)))
                except Exception:
                    lst.sort(key=lambda it: it.get("time", 0))
            with open("homework.json", "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

        self.homework_list = []
        self.homework_page_list = []
        for i, j in enumerate(self.subject_codes):
            for k in self.data[j]:
                content = self.subject_display_names[i] + ":" + k["content"]
                content = charater_count(content)
                self.homework_page_list.append(content)
                self.homework_list.append(
                    Label(
                        tk,
                        text=content[0],
                    )
                )
                if analyze_time(k["time"]) == "时间已过":
                    self.homework_list[-1].config(fg=COLOR)
        inv = 35 if len(self.homework_list) < 10 else 30
        for idx, widget in enumerate(self.homework_list):
            widget.place(x=45, y=40 + idx * inv)

        self.upload_track()
        tk.after(1, self.roll_show)

    def upload_track(self, aid=-1):
        """每分钟更新一次时间"""
        if aid != -1:
            tk.after_cancel(aid)
            self.reminder_schedule.remove(aid)

        for i in self.time_list:
            i.place_forget()
        self.time_list = []
        for i, j in enumerate(self.subject_codes):
            for k in self.data[j]:
                self.time_list.append(
                    Label(
                        tk,
                        text=analyze_time(k["time"]),
                        width=13,
                        justify="right",
                        anchor="e",
                    )
                )
                time_text = self.time_list[-1].cget("text")
                if time_text == "现在收":
                    self.time_list[-1].config(fg="#23272E", bg="#C8C8C8")
                elif (
                    "后天" not in time_text
                    and "周" not in time_text
                    and "/" not in time_text
                    and "时间" not in time_text
                    and "不" not in time_text
                ):
                    self.time_list[-1].config(bg="#23272E", fg="#C8C8C8")
                else:
                    self.time_list[-1].config(bg="#23272E", fg=COLOR)
        inv = 35 if len(self.time_list) < 10 else 30
        for idx, widget in enumerate(self.time_list):
            widget.place(x=1075, y=40 + idx * inv)
        now = time.localtime()
        remaining_seconds = 60 - now.tm_sec
        aid = tk.after(remaining_seconds * 1000, lambda: self.upload_track(aid))
        self.reminder_schedule.append(aid)

    def roll_show(self):
        for i, j in enumerate(self.homework_list):
            j.config(text=self.homework_page_list[i][0])
            self.homework_page_list[i].append(self.homework_page_list[i].pop(0))
        tk.after(1, self.roll_title)

    def roll_title(self, arg=21, aid=-1):
        if aid != -1:
            tk.after_cancel(aid)
            self.reminder_schedule.remove(aid)

        if arg == -1:
            tk.after(1, self.roll_show)
            return
        self.ui_title.config(
            text=time.strftime(
                f"%H:%M:%S R{str(arg).zfill(2)} T{str(self.tick).zfill(3)}" if DEBUG else f"%H:%M:%S {VERSION}", time.localtime(time.time())
            )
        )
        aid = tk.after(200, self.roll_title, arg - 1, aid)
        self.reminder_schedule.append(aid)

    def load_ui(self):
        tk.title("作业管理器")
        tk.geometry("1280x720")
        tk.attributes("-fullscreen", True)  # ! Uncomment when release
        tk.config(bg="#23272E")
        tk.resizable(False, False)

        self.ui_title = Label(
            tk,
            fg=COLOR,
        )
        self.ui_title.place(x=10, y=5)
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
                    if t != 0 and t < time.time() - 600:
                        removed += 1
                    else:
                        new_list.append(item)
                self.data[key] = new_list
            if removed > 0:
                with open("homework.json", "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("清理完成", f"已清理 {removed} 个已过期作业。")
            else:
                messagebox.showinfo("清理完成", "没有需要清理的作业。")
            self.draw_homework()
        except Exception as e:
            messagebox.showerror("错误", f"清理作业时发生错误：{e}")

    def new_homework(
        self,
        subject_index=None,
        content_text=None,
        deadline_timestamp=None,
        replace_target=None,
    ):
        if len(self.homework_list) >= 22:
            messagebox.showerror("超过上限", "作业数量已达上限")
            return
        new_window = Toplevel(tk)
        new_window.title("新建作业")
        new_window.config(bg="#23272E")
        new_window.resizable(False, False)

        Label(new_window, text=" ").grid(row=0, column=0)
        Label(new_window, text=" ").grid(row=999, column=999)

        Label(new_window, text="科目", bg="#23272E").grid(row=1, column=1)
        subject_var = StringVar(new_window)
        if subject_index is not None and 0 <= subject_index < len(self.subject_display_names):
            subject_var.set(self.subject_display_names[subject_index])
        else:
            subject_var.set(self.subject_display_names[0])
        OptionMenu(new_window, subject_var, *self.subject_display_names).grid(row=1, column=2)

        Label(new_window, text="内容", bg="#23272E").grid(row=2, column=1)
        content_entry = Entry(new_window, width=60, relief=RIDGE)
        content_entry.grid(row=2, column=2)
        if content_text:
            content_entry.insert(0, content_text)

        Label(new_window, text="  截止时间  ", bg="#23272E").grid(row=3, column=1)
        if deadline_timestamp is not None:
            if deadline_timestamp == 0:
                time_value = "0"
            else:
                time_value = time.strftime(
                    "%Y/%m/%d %H:%M:%S", time.localtime(deadline_timestamp)
                )
        else:
            time_value = time.strftime("%Y/%m/%d 22:10:00", time.localtime(time.time()))

        time_entry = Entry(
            new_window,
            width=20,
            textvariable=StringVar(new_window, value=time_value),
            relief=FLAT,
            justify="center",
        )
        time_entry.grid(row=3, column=2)

        def submit():
            new_subject_index = self.subject_display_names.index(subject_var.get())
            new_subject_key = self.subject_codes[new_subject_index]
            content = content_entry.get()
            deadline_str = time_entry.get()
            try:
                if deadline_str == "0":
                    new_deadline_ts = 0
                else:
                    new_deadline_ts = int(
                        time.mktime(time.strptime(deadline_str, "%Y/%m/%d %H:%M:%S"))
                    )
                new_item = {"content": content, "time": new_deadline_ts}
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
                with open("homework.json", "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=4)
                self.draw_homework()
                new_window.destroy()
            except ValueError:
                Label(
                    new_window,
                    text="时间格式错误！请使用 YYYY/MM/DD HH:MM:SS",
                    fg="red",
                    bg="#23272E",
                ).place(x=10, y=130)

        Button(new_window, text="提交", command=submit, relief=FLAT).grid(
            row=4, column=2, sticky="e"
        )
        Button(new_window, text="取消", command=new_window.destroy, relief=FLAT).grid(
            row=4, column=2, sticky="w"
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
        if not messagebox.askyesno("提示", "确定要删除吗？"):
            return
        count = 0
        for i in self.subject_codes:
            for j in self.data[i]:
                if count == index:
                    self.data[i].remove(j)
                    with open("homework.json", "w", encoding="utf-8") as f:
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
                    orig_index = self.data[subject_key].index(j)
                    self.new_homework(
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

        inv = 35 if len(self.homework_list) < 10 else 30
        self.arg = int((y - 40) // inv)
        if self.arg >= len(self.homework_list):
            self.arg = -1
        # self.title.config(text=f"鼠标位置：({x}, {y}),{self.arg}")

        self.ui_top_exit.place(x=1225, y=0)
        self.ui_top_refresh.place(x=1169, y=0)
        self.ui_top_add.place(x=1113, y=0)
        self.ui_top_clear.place(x=1057, y=0)

        if self.arg <= -1:
            self.ui_side_edit.place_forget()
            self.ui_side_delete.place_forget()
            return
        
        self.ui_side_delete.place(x=5, y=45 + self.arg * inv)
        self.ui_side_edit.place(x=25, y=45 + self.arg * inv)
        self.ui_side_delete.config(command=lambda: self.delete_homework(self.arg))
        self.ui_side_edit.config(command=lambda: self.edit_homework(self.arg))
    
    def exit(self):
        sys.exit(0)


if __name__ == "__main__":
    # 进程检测：仅允许单个实例运行（使用文件锁）
    def _acquire_lock(lock_path="homework.lock"):
        try:
            lock_file = open(lock_path, "w")
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            return lock_file
        except OSError:
            return None

    _lock = _acquire_lock()
    if not _lock:
        tmp_root = Tk()
        tmp_root.withdraw()
        messagebox.showwarning("提示", "程序已在运行，无法启动多个实例。")
        tmp_root.destroy()
        sys.exit(0)

    tk = Tk()
    app = HomeworkTool()
    tk.mainloop()
