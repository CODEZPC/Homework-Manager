"""
数据存储层 - 统一管理 homework.json 和 setting.json 的读写。

所有 JSON 文件 I/O 集中于此，提供带错误处理的数据访问接口。
"""

import json
import os
import threading
from typing import Any, Dict, List, Optional, Tuple

import config


class DataStore:
    """JSON 数据文件的统一读写管理器，线程安全。"""

    def __init__(self):
        self._lock = threading.Lock()
        self._loglayer = "Data"

    # ──────────────── homework.json ────────────────

    def load_homework(self) -> Dict[str, Any]:
        """加载 homework.json，失败返回空字典。"""
        with self._lock:
            try:
                with open(config.DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError, PermissionError):
                return {}

    def save_homework(self, data: Dict[str, Any]) -> bool:
        """保存 homework.json，返回是否成功。"""
        with self._lock:
            try:
                with open(config.DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                return True
            except (PermissionError, OSError) as e:
                print(f"[DataStore] 保存 homework.json 失败: {e}")
                return False

    def get_subject_items(self, data: Dict[str, Any], subject_code: str) -> List[Dict]:
        """获取某科目的作业列表（安全访问）。"""
        items = data.get(subject_code, [])
        if isinstance(items, list):
            return items
        return []

    def set_subject_items(
        self, data: Dict[str, Any], subject_code: str, items: List[Dict]
    ) -> None:
        """设置某科目的作业列表。"""
        data[subject_code] = items

    def validate_and_fix_keys(
        self, data: Dict[str, Any], valid_codes: List[str]
    ) -> Tuple[Dict, List[str], List[str]]:
        """
        验证并修复 data 中的科目键：
        - 移除不在 valid_codes 中的多余键（仅当值为列表时）
        - 添加 valid_codes 中存在但 data 中缺失的键（初始化为 []）

        返回: (修复后的 data, 多余键列表, 缺失键列表)
        """
        extra_keys = [
            k for k in data if k not in valid_codes and isinstance(data.get(k), list)
        ]
        for k in extra_keys:
            del data[k]

        missing_keys = [k for k in valid_codes if k not in data]
        for k in missing_keys:
            data[k] = []

        return data, extra_keys, missing_keys

    # ──────────────── setting.json ────────────────

    def load_settings(self) -> Dict[str, Any]:
        """加载 setting.json，失败返回空字典。"""
        with self._lock:
            try:
                with open(config.SETTING_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError, PermissionError):
                return {}

    def save_settings(self, data: Dict[str, Any]) -> bool:
        """保存 setting.json，返回是否成功。"""
        with self._lock:
            try:
                with open(config.SETTING_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                return True
            except (PermissionError, OSError) as e:
                print(f"[DataStore] 保存 setting.json 失败: {e}")
                return False

    def get_subjects(self) -> Dict[str, str]:
        """
        从 setting.json 获取科目映射表。
        返回 {显示名称: 科目代码} 字典；失败返回默认值。
        """
        settings = self.load_settings()
        subjects = settings.get("Subjects", None)
        if subjects and isinstance(subjects, dict) and len(subjects) > 0:
            return subjects
        # 回退到硬编码默认值
        return dict(
            zip(config.DEFAULT_SUBJECT_DISPLAY_NAMES, config.DEFAULT_SUBJECT_CODES)
        )

    def save_subjects(self, subjects: Dict[str, str]) -> bool:
        """将科目映射表写入 setting.json。"""
        settings = self.load_settings()
        settings["Subjects"] = subjects
        return self.save_settings(settings)

    # ──────────────── 初始化与校验 ────────────────

    def ensure_defaults(self) -> None:
        """
        确保 setting.json 和 homework.json 存在且有效。
        若不存在则创建默认文件。
        """
        # 检查 setting.json
        settings = self.load_settings()
        if "Subjects" not in settings:
            # 尝试从 homework.json 恢复
            hw = self.load_homework()
            if hw and isinstance(hw, dict):
                subjects_map = {k: k for k in hw.keys() if k != "VER"}
                if subjects_map:
                    settings["Subjects"] = subjects_map
                else:
                    settings["Subjects"] = {"Default": "Default"}
            else:
                settings["Subjects"] = {"Default": "Default"}
            self.save_settings(settings)

        # 检查 homework.json
        try:
            with open(config.DATA_FILE, "r", encoding="utf-8") as f:
                pass
        except FileNotFoundError:
            subjects = self.get_subjects()
            data = {}
            for code in subjects.values():
                data[code] = []
            self.save_homework(data)
