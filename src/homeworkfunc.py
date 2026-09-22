import sys
import time
import json
import re
import subprocess
import tkinter.font as tkfont

import paths

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


def load_subjects():
    """从 _internal/config/setting.json 动态加载科目配置，失败则回退到硬编码默认值。"""
    global SUBJECT_CODES, SUBJECT_DISPLAY_NAMES
    try:
        with open(paths.CONFIG_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
        subjects = settings.get("Subjects", None)
        if subjects and isinstance(subjects, dict) and len(subjects) > 0:
            SUBJECT_CODES = list(subjects.values())
            SUBJECT_DISPLAY_NAMES = list(subjects.keys())
    except Exception:
        pass  # 回退到上方硬编码默认值


# 模块导入时自动加载
load_subjects()

EMPHASIZE_LEVELS = ["自动", "很低", "低", "标准", "高"]

ENABLE_CLASSISLAND = False

# 如果通过 PyInstaller 等打包为 exe，则自动启用 ClassIsland 调用
if getattr(sys, "frozen", False):
    ENABLE_CLASSISLAND = True

TIME_OUT = 300

def analyze_time(timestamp, emphasize="自动", word="收"):
    """
    计算目标时间与当前时间的关系，返回 (显示文案, 优先级数值) 元组。

    word: 文案的动词后缀，默认为 "收"（开始收集）；计算截止时间时传入 "截止"。
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
        return (
            "不收" if word == "收" else "未设截止",
            0 if auto else emphasize_prefix(emphasize),
        )
    elif timestamp < time.time() - TIME_OUT:
        return (
            "时间已过" if word == "收" else "已截止",
            -1,
        )
    elif timestamp < time.time() - 60:
        return (f"现在{word}", 3)
    elif timestamp < time.time():
        return (f"现在{word}", 4)
    elif timestamp < time.time() + TIME_OUT:
        return (f"即将{word}", 1 if auto else emphasize_prefix(emphasize))
    elif timestamp < time_day_start + 86400:
        return (f"{t}{word}", 1 if auto else emphasize_prefix(emphasize))
    elif timestamp < time_day_start + 86400 * 2:
        return (f"明天{t}{word}", 1 if auto else emphasize_prefix(emphasize))
    elif timestamp < time_day_start + 86400 * 3:
        return (f"后天{t}{word}", 0 if auto else emphasize_prefix(emphasize))
    elif timestamp < time_day_start + 86400 * (8 - int(week_now)):
        return (f"周{we[int(w)]}{t}{word}", 0 if auto else emphasize_prefix(emphasize))
    elif timestamp < time_day_start + 86400 * (15 - int(week_now)):
        return (
            f"下周{we[int(w)]}{t}{word}",
            0 if auto else emphasize_prefix(emphasize),
        )
    else:
        return (
            f"{time.strftime('%Y/%m/%d', time.localtime(timestamp))}{word}",
            0,
        )

def analyze_time_string(timestring):
    timestring = timestring.replace("：", ":")
    timestring = timestring.replace("-", "/")

    y = time.strftime("%Y", time.localtime())
    m = time.strftime("%m", time.localtime())
    d = time.strftime("%d", time.localtime())

    if re.match(r"\d{1,2}:\d\d", timestring):
        timestring = f"{y}/{m}/{d} {timestring}"

    return timestring

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
        subprocess.Popen(
            f"start classisland://app/api/automation/{mode}/{uri}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    else:
        return False

def _is_numeric_time(value):
    """判断是否为数值时间（排除布尔值）。"""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def has_open_deadline(item, now=None):
    """是否启用了截止时间且截止时间尚未到达（仍处于开放状态）。"""
    if now is None:
        now = time.time()
    d = item.get("deadline", 0)
    return _is_numeric_time(d) and d > now


def collect_status(item, now=None):
    """
    返回作业条目的时间状态数值（语义与 analyze_time 返回的优先级一致，
    供列表排序 / 置灰 / 高亮着色使用）。

    区别：当启用了截止时间且截止未到、而“开始收集”时间已到或已过时，
    仍按“现在收”(3) 处理，不会被 5 分钟超时误判为“时间已过”(-1)。
    """
    if now is None:
        now = time.time()
    t = item.get("time", 0)
    em = item.get("emphasize", "自动")
    if (
        has_open_deadline(item, now)
        and _is_numeric_time(t)
        and t > 0
        and t <= now
    ):
        return 3
    return analyze_time(t, em)[1]


def _sort_key(item):
    """
    作业排序键（数值越小越靠前），用于每个科目内部的稳定排序。

    排序规则：
    1. 状态优先级降序（现在收 / 可提交 > 即将收 / 标准 > 低 > 时间已过）；
    2. 同一优先级内按“有无有效时间”分组：
       有开始收集时间 → 不收（time <= 0） → 自定义文本；
    3. 有时间者再按关键时间升序：
       - 尚未开始收集（time > now）→ 按开始收集时间升序；
       - 已开始收集（含超过 5 分钟）且截止未到 → 按截止时间升序（越近越靠前）；
       - 其余 → 按开始收集时间升序。
    """
    t = item.get("time", 0)
    e = item.get("emphasize", "自动")
    d = item.get("deadline", 0)

    # 使用 analyze_time 获取优先级（数字越大优先越高），随后按时间再按文字排序
    try:
        label, prio = analyze_time(t, e)
    except Exception:
        label, prio = (str(t), 0)

    # 截止时间未到且已开始收集的作业按“现在收”处理（不因超时被置底）
    try:
        prio = collect_status(item)
    except Exception:
        pass

    now = time.time()

    if _is_numeric_time(t) and t > 0:
        # kind 0：有有效的开始收集时间
        kind = 0
        if t > now:
            phase = 1  # 尚未开始收集 → 按开始收集时间升序
            ts = t
        else:
            phase = 0  # 已开始收集 / 已过
            if _is_numeric_time(d) and d > now:
                ts = d  # 可提交阶段 → 按截止时间升序（越近越靠前）
            else:
                ts = t
    elif _is_numeric_time(t):
        # kind 1：不收（time <= 0），排在有时间的作业之后
        kind, phase, ts = 1, 0, 0
    else:
        # kind 2：自定义文本，排在最后
        kind, phase, ts = 2, 0, 0

    return (-prio, kind, phase, ts, str(label))

def speed_test():
    a = 0
    t = time.time()
    for i in range(10000000):
        a += i
    t = time.time() - t
    return 10000000 / t

if __name__ == "__main__":
    print(speed_test())