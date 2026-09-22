import json
import os

import paths

KEYS = ["Subjects"]
VALUES = [{"Default": "Default"}]

# 配置文件位置：_internal/config/setting.json（旧版根目录 setting.json 会自动迁移）
SETTING_FILE = paths.CONFIG_FILE
HOMEWORK_FILE = "homework.json"

# 轮播时间参数默认值（毫秒）：截止时间文案轮播 / 分页轮播。
# 写入 setting.json 的 "Rotation" 段；后续的调节界面会修改这些键。
ROTATION_DEFAULTS = {"DeadlineMs": 5000, "PageMs": 12000}

# homework.json 中的元数据键，不参与科目恢复 / 同步
RESERVED_META = {"VER"}


def _load_json(path):
    """读取 JSON；文件缺失或解析失败返回 (None, False)。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), True
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return None, False


def _homework_subject_keys(hw):
    """
    提取 homework.json 中可视为“科目”的键：
    值为 list 且非保留元数据键（避免把 VER 等误当科目）。
    """
    if not isinstance(hw, dict):
        return []
    return [
        k for k, v in hw.items()
        if k not in RESERVED_META and isinstance(v, list)
    ]


def _normalize_subjects(subjects):
    """确保 subjects 为 dict 且非空；否则返回 None。"""
    if isinstance(subjects, dict) and len(subjects) > 0:
        return subjects
    return None


def check():
    """
    配置自检 / 修复（程序启动时自动调用）：

    0. 把旧版本位于程序根目录的 setting.json / backup / lock 自动迁移到 _internal 下；
    1. 确保 setting.json 存在且可解析；
    2. 若缺少科目配置（Subjects），从 homework.json 的科目列表键恢复
       （跳过 VER 等元数据键）；homework 也缺失时回退默认科目；
    3. 若 Subjects 已存在，把 homework.json 中存在但尚未配置的科目键
       并入配置（防止该键数据丢失）；
    4. 确保 "Rotation" 段存在（轮播时间参数，见 ROTATION_DEFAULTS）；
    5. 仅在确有变化 / 文件缺失时才写回 setting.json。
    """
    # 旧版本文件位置自动迁移（setting.json / backup / lock → _internal 下）
    paths.migrate_legacy()

    data, setting_ok = _load_json(SETTING_FILE)
    if not isinstance(data, dict):
        data = {}
    changed = not setting_ok

    # 读取 homework.json（可能不存在）
    hw, _ = _load_json(HOMEWORK_FILE)
    if not isinstance(hw, dict):
        hw = {}

    # 兼容旧版小写 "subjects"，统一归一到 "Subjects"
    subjects = data.get("Subjects")
    if subjects is None:
        subjects = data.get("subjects")
        if isinstance(subjects, dict):
            changed = True  # 需要迁移到 "Subjects"
        else:
            subjects = None
    subjects = _normalize_subjects(subjects)

    if subjects is None:
        # 缺少科目配置：优先从 homework.json 恢复（仅 list 键，不含 VER）
        subjects = {k: k for k in _homework_subject_keys(hw)}
        if not subjects:
            # 回退为默认科目
            subjects = dict(VALUES[0])
        changed = True
    else:
        # 已存在配置：把 homework 中未配置的科目键并入，避免数据丢失
        known_codes = set(subjects.values())
        for k in _homework_subject_keys(hw):
            if k not in known_codes and k not in subjects:
                subjects[k] = k
                changed = True

    # 统一写回 "Subjects"
    data["Subjects"] = subjects
    if "subjects" in data:
        del data["subjects"]

    # 轮播时间参数：确保 "Rotation" 段与各项存在且为数值（供后续调节界面修改）
    rotation = data.get("Rotation")
    if not isinstance(rotation, dict):
        rotation = {}
        changed = True
    for key, default in ROTATION_DEFAULTS.items():
        value = rotation.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            rotation[key] = default
            changed = True
    data["Rotation"] = rotation

    if changed or not os.path.exists(SETTING_FILE):
        try:
            paths.ensure_dirs()
            with open(SETTING_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass


if __name__ == "__main__":
    check()
