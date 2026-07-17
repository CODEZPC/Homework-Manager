"""
时间分析服务 - 解析作业截止时间并生成显示文本与优先级。
"""

import time
import re
from typing import Any, Dict, Tuple, Union

import config


def analyze_time(
    timestamp: Union[int, float, str], emphasize: str = "自动"
) -> Tuple[str, int]:
    """
    计算目标时间与当前时间的关系，返回 (显示文本, 优先级数值)。

    优先级数值含义：
        4  -> 现在收（超紧急）
        3  -> 现在收 / 高优先级
        1  -> 即将收 / 标准优先级 / 今天收
        0  -> 后天收 / 本周收 / 下周收 / 不收 / 自定义文本（低优先级）
        -1 -> 时间已过 / 很低优先级
    """

    def emphasize_prefix(level: str) -> int:
        mapping = {
            "自动": 1,
            "很低": -1,
            "低": 0,
            "标准": 1,
            "高": 3,
        }
        return mapping.get(level, 1)

    # 字符串类型的时间直接作为自定义信息显示
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
    t_str = time.strftime("%H:%M", time.localtime(timestamp))
    w_str = time.strftime("%w", time.localtime(timestamp))
    auto = emphasize == "自动"

    if timestamp == 0:
        return ("不收", 0 if auto else emphasize_prefix(emphasize))
    elif timestamp < time_now - config.TIME_OUT:
        return ("时间已过", -1)
    elif timestamp < time_now - 60:
        return ("现在收", 3)
    elif timestamp < time_now:
        return ("现在收", 4)
    elif timestamp < time_now + config.TIME_OUT:
        return ("即将收", 1 if auto else emphasize_prefix(emphasize))
    elif timestamp < time_day_start + 86400:
        return (f"{t_str}收", 1 if auto else emphasize_prefix(emphasize))
    elif timestamp < time_day_start + 86400 * 2:
        return (f"明天{t_str}收", 1 if auto else emphasize_prefix(emphasize))
    elif timestamp < time_day_start + 86400 * 3:
        return (f"后天{t_str}收", 0 if auto else emphasize_prefix(emphasize))
    elif timestamp < time_day_start + 86400 * (8 - int(week_now)):
        return (
            f"周{we[int(w_str)]}{t_str}收",
            0 if auto else emphasize_prefix(emphasize),
        )
    elif timestamp < time_day_start + 86400 * (15 - int(week_now)):
        return (
            f"下周{we[int(w_str)]}{t_str}收",
            0 if auto else emphasize_prefix(emphasize),
        )
    else:
        return (f"{time.strftime('%Y/%m/%d', time.localtime(timestamp))}收", 0)


def analyze_time_string(timestring: str) -> str:
    """
    标准化时间字符串，补充日期部分。
    例："22:10" -> "2026/07/17 22:10"
    """
    timestring = timestring.replace("：", ":")
    timestring = timestring.replace("-", "/")

    y = time.strftime("%Y", time.localtime())
    m = time.strftime("%m", time.localtime())
    d = time.strftime("%d", time.localtime())

    if re.match(r"\d{1,2}:\d\d", timestring):
        timestring = f"{y}/{m}/{d} {timestring}"

    return timestring


def parse_deadline(deadline_str: str) -> Any:
    """
    将截止时间字符串解析为时间戳（int）或自定义文本（str）。
    - "0" / "" / "不收" -> 0（不收）
    - 有效时间字符串 -> Unix 时间戳
    - 其他 -> 原字符串（自定义文本）
    """
    if deadline_str in ("0", "", "不收"):
        return 0
    try:
        parsed = analyze_time_string(deadline_str)
        return int(time.mktime(time.strptime(parsed, "%Y/%m/%d %H:%M")))
    except (ValueError, OverflowError):
        return deadline_str


def sort_key(item: Dict[str, Any]) -> Tuple[int, Union[int, float], str]:
    """
    作业排序键函数。
    返回 (负优先级, 时间戳, 显示文本) 元组用于稳定排序。
    优先级高的在前，同优先级按时间升序。
    """
    t = item.get("time", 0)
    e = item.get("emphasize", "自动")
    try:
        label, prio = analyze_time(t, e)
    except Exception:
        label, prio = (str(t), 0)

    if isinstance(t, (int, float)):
        return (-prio, t, label)
    return (-prio, float("inf"), str(label))
