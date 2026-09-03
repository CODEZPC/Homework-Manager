import json

# ─────────────────────────────────────────────────────────────────────
# homework.json 数据版本说明
#   - 旧版（无 VER，或 VER 0~2）：每个作业仅有 content / time / emphasize；
#     time 被理解为“开始收集时间”。
#   - 当前版本 VER 3：为每个作业新增可选字段 deadline（截止时间），
#     0 或缺失表示未启用截止时间。
# ─────────────────────────────────────────────────────────────────────
DATA_VERSION = 3

# 旧英文优先级名 → 当前中文优先级名
_EMPHASIZE_LEGACY = {
    "Ignored": "很低",
    "Unimportant": "低",
    "Standard": "标准",
    "Urgent": "高",
}
_VALID_EMPHASIZE = {"自动", "很低", "低", "标准", "高"}


def _normalize_deadline(value):
    """将 deadline 规范化为数值时间戳；无法解析时返回 0。"""
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0


def _normalize_item(item):
    """
    将单个作业条目升级为当前格式：
    {content, time, deadline, emphasize}

    返回 (规范化后的条目, 是否有改动)。无法识别的条目返回 (None, False)。
    """
    # 极旧格式：条目本身就是纯字符串（仅内容）
    if isinstance(item, str):
        return (
            {
                "content": item,
                "time": 0,
                "deadline": 0,
                "emphasize": "自动",
            },
            True,
        )

    if not isinstance(item, dict):
        return None, False

    changed = False

    if not isinstance(item.get("content"), str):
        item["content"] = str(item.get("content", ""))
        changed = True

    if "time" not in item:
        item["time"] = 0
        changed = True

    if "deadline" not in item:
        # 旧版数据没有截止时间字段 → 补为 0（未启用）
        item["deadline"] = 0
        changed = True
    elif not (
        isinstance(item["deadline"], (int, float))
        and not isinstance(item["deadline"], bool)
    ):
        item["deadline"] = _normalize_deadline(item["deadline"])
        changed = True

    em = item.get("emphasize")
    if not isinstance(em, str) or em not in _VALID_EMPHASIZE:
        if isinstance(em, str) and em in _EMPHASIZE_LEGACY:
            item["emphasize"] = _EMPHASIZE_LEGACY[em]
        else:
            item["emphasize"] = "自动"
        changed = True

    return item, changed


def migrate(path="homework.json"):
    """
    程序启动时调用：将旧版本 homework.json 自动升级到 DATA_VERSION。

    - 为每个作业补齐 deadline（旧数据默认 0 = 未启用截止时间）；
    - 将旧英文优先级名映射为中文，缺失/非法优先级置为“自动”；
    - 补充 / 提升 VER 到当前版本。

    返回本次是否有任何改动。文件缺失或无法解析时返回 False。
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return False

    if not isinstance(data, dict):
        return False

    try:
        version = int(data.get("VER", 0))
    except (TypeError, ValueError):
        version = 0

    changed = False

    # 升级所有科目列表中的作业条目（任意值为 list 的键，不依赖科目配置）
    for key in list(data.keys()):
        if not isinstance(data[key], list):
            continue
        new_list = []
        for item in data[key]:
            norm, item_changed = _normalize_item(item)
            if norm is None:
                # 无法识别的条目：丢弃以免程序崩溃
                changed = True
                continue
            new_list.append(norm)
            changed = changed or item_changed
        data[key] = new_list

    if version < DATA_VERSION:
        data["VER"] = DATA_VERSION
        changed = True

    if changed:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            return False
    return changed


if __name__ == "__main__":
    if migrate():
        print("homework.json 已自动升级至版本 %d。" % DATA_VERSION)
    else:
        print("homework.json 无需处理。")