import time
import json
import subprocess
import warnings
import os
import sys
import shutil
from tkinter import *
import tkinter.font as tkfont

SUBJECT_CODES = [
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

SUBJECT_DISPLAY_NAMES = [
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

EMPHASIZE_LEVELS = ["自动", "很低", "低", "标准", "高"]

ENABLE_CLASSISLAND = False

# 如果通过 PyInstaller 等打包为 exe，则自动启用 ClassIsland 调用
if getattr(sys, "frozen", False):
    ENABLE_CLASSISLAND = True

TIME_OUT = 300


def analyze_time(timestamp, emphasize="自动"):
    """
    计算目标时间与当前时间的关系，返回一个字符串表示目标时间的状态。
    """
    def emphasize_prefix(level):
        if level == "自动":
            return 1
        elif level == "很低":
            return -1
        elif level == "低":
            return 0
        elif level == "标准":
            return 1
        elif level == "高":
            return 3

    if isinstance(timestamp, str):
        return (timestamp, emphasize_prefix(emphasize))
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
    auto = emphasize == "自动"
    if timestamp == 0:
        return ("暂时不收", 0 if auto else emphasize_prefix(emphasize))
    elif timestamp < time.time() - TIME_OUT:
        return ("时间已过", -1)
    elif timestamp < time.time() - 60:
        return ("现在收", 3)
    elif timestamp < time.time():
        return ("现在收", 4)
    elif timestamp < time.time() + TIME_OUT:
        return ("即将收", 1 if auto else emphasize_prefix(emphasize))
    elif timestamp < time_day_start + 86400:
        return (f"{t}收", 1 if auto else emphasize_prefix(emphasize))
    elif timestamp < time_day_start + 86400 * 2:
        return (f"明天{t}收", 1 if auto else emphasize_prefix(emphasize))
    elif timestamp < time_day_start + 86400 * 3:
        return (f"后天{t}收", 0 if auto else emphasize_prefix(emphasize))
    elif timestamp < time_day_start + 86400 * (8 - int(week_now)):
        return (f"周{we[int(w)]}{t}收", 0 if auto else emphasize_prefix(emphasize))
    elif timestamp < time_day_start + 86400 * (15 - int(week_now)):
        return (f"下周{we[int(w)]}{t}收", 0 if auto else emphasize_prefix(emphasize))
    else:
        return (f"{time.strftime('%Y/%m/%d', time.localtime(timestamp))}收", 0)


def getwidth(object, tki):
    """
    返回给定控件文本的像素宽度（调用前请确保已有 `tki` 根）。
    优先通过控件的 `text` 与 `font` 来计算像素宽度，保证返回的是像素值而不是字符数。
    如果控件不包含文本（或无法读取），则回退到 `winfo_width()`。
    """
    tki.update_idletasks()
    try:
        text = object.cget("text")
    except Exception:
        return object.winfo_width()
    try:
        font_name = object.cget("font")
        font = tkfont.Font(root=tki, font=font_name)
    except Exception:
        font = tkfont.Font(root=tki)
    return font.measure(text)


def resource_check(subject_codes):
    """
    检查资源是否存在，如不存在则修复
    """
    try:
        with open("homework.json", "r", encoding="utf-8") as f:
            pass
    except FileNotFoundError:
        with open("homework.json", "w", encoding="utf-8") as f:
            data = {}
            for code in subject_codes:
                data[code] = []
            json.dump(data, f, ensure_ascii=False, indent=4)


def uri_classisland(uri, mode="run"):
    """
    调用 ClassIsland 的 URI 解析接口

    :param uri: 要解析的 URI 字符串
    :param mode: 解析模式，默认为 "run"，表示直接运行解析结果 -> ["run", "revert"]
    """
    if ENABLE_CLASSISLAND:
        subprocess.Popen(f"start classisland://app/api/automation/{mode}/{uri}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    else:
        return False


if __name__ == "__main__":
    uri_classisland("test")