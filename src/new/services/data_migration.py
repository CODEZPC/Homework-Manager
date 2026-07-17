"""
数据版本迁移 - 升级 homework.json 的数据格式。
"""

import json
from typing import Dict, Any

import config


def migrate(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    按需执行数据格式升级，从 VER 0 到当前最大版本。
    返回迁移后的 data。
    """
    current_ver = data.get("VER", 0)
    max_ver = config.DATA_VERSION_MAX

    if current_ver >= max_ver:
        return data

    # 版本 0 → 1：添加 emphasize 字段
    if current_ver < 1:
        data = _migrate_v0_to_v1(data)
        current_ver = 1

    # 版本 1 → 2：旧优先级名称转换
    if current_ver < 2:
        data = _migrate_v1_to_v2(data)
        current_ver = 2

    return data


def _migrate_v0_to_v1(data: Dict[str, Any]) -> Dict[str, Any]:
    """V0→V1：为所有作业添加 emphasize 字段，默认 "Standard"。"""
    data["VER"] = 1
    subject_codes = _get_subject_codes()
    for code in subject_codes:
        items = data.get(code, [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    item.setdefault("emphasize", "Standard")
    return data


def _migrate_v1_to_v2(data: Dict[str, Any]) -> Dict[str, Any]:
    """V1→V2：旧优先级名称转换为新名称。"""
    data["VER"] = 2
    old_levels = ["Ignored", "Unimportant", "Standard", "Urgent"]
    new_levels = ["很低", "低", "标准", "高"]
    mapping = dict(zip(old_levels, new_levels))

    subject_codes = _get_subject_codes()
    for code in subject_codes:
        items = data.get(code, [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    old = item.get("emphasize", "标准")
                    if old in mapping:
                        item["emphasize"] = mapping[old]
    return data


def _get_subject_codes() -> list:
    """尝试从 setting.json 获取科目代码列表。"""
    try:
        with open(config.SETTING_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
        subjects = settings.get("Subjects", {})
        if subjects:
            return list(subjects.values())
    except Exception:
        pass
    return config.DEFAULT_SUBJECT_CODES
