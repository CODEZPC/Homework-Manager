import time
import json

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


def analyze_time(timestamp):
    """
    计算目标时间与当前时间的关系，返回一个字符串表示目标时间的状态。
    """
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


def charater_count(string, limit=70):
    """
    计算字符串在指定长度限制下的分页情况。
    """
    count = 0
    start = 0
    page = []
    eng = "~!@#$%^&*()_+`1234567890-={}|[]\\:\"';<>?,./QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm "
    for i, j in enumerate(string):
        if j in eng:
            count += 1
        else:
            count += 1.666667
        if limit <= count <= limit + 1 and i <= len(string) - 1:
            if string[i + 1] not in eng:
                page.append(string[start : i + 1])
                start = i + 1
                count = 0
        elif limit <= count <= limit + 1 and i == len(string) - 1:
            page.append(string[start : i + 1])
            start = i + 1
            count = 0
        elif count >= limit + 1:
            page.append(string[start : i + 1])
            start = i + 1
            count = 0
    page.append(string[start:])
    if page[-1] == "":
        page.pop()
    return page


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
