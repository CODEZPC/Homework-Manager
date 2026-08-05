"""
配置管理模块

管理 setting.json 的读写，包含：
- 科目定义 (Subjects)
- 应用配置参数
"""

import json
import os
from typing import Any

from homework_manager.config.constants import (
    SETTING_FILE,
    DEFAULT_SUBJECT_CODES,
    DEFAULT_SUBJECT_NAMES,
)
from homework_manager.utils.platform import get_app_dir


class Settings:
    """应用配置管理"""

    def __init__(self, filepath: str | None = None):
        self.app_dir = get_app_dir()
        self.filepath = filepath or os.path.join(self.app_dir, SETTING_FILE)
        self._data: dict[str, Any] = {}

    # ==================== 加载 / 保存 ====================

    def load(self) -> dict[str, Any]:
        """从文件加载配置"""
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = {}
        return self._data

    def save(self) -> None:
        """保存配置到文件"""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=4)

    # ==================== 默认值初始化 ====================

    def ensure_defaults(self) -> None:
        """确保配置文件存在且包含必要字段，缺失则写入默认值"""
        self.load()
        if "Subjects" not in self._data:
            self._data["Subjects"] = dict(
                zip(DEFAULT_SUBJECT_NAMES, DEFAULT_SUBJECT_CODES)
            )
            self.save()

    # ==================== 科目操作 ====================

    @property
    def subjects(self) -> dict[str, str]:
        """获取科目映射 {显示名称: 代码}"""
        return self._data.get("Subjects", {})

    def get_subject_codes(self) -> list[str]:
        """获取所有科目代码列表"""
        return list(self.subjects.values())

    def get_subject_names(self) -> list[str]:
        """获取所有科目显示名称列表"""
        return list(self.subjects.keys())

    def add_subject(self, name: str, code: str) -> None:
        """添加新科目"""
        self._data.setdefault("Subjects", {})[name] = code
        self.save()

    def remove_subject(self, name: str) -> None:
        """删除科目"""
        if name in self._data.get("Subjects", {}):
            del self._data["Subjects"][name]
            self.save()

    def rename_subject(
        self, old_name: str, new_name: str, new_code: str | None = None
    ) -> None:
        """重命名科目（可同时修改代码）"""
        subjects = self._data.get("Subjects", {})
        if old_name in subjects:
            code = new_code if new_code is not None else subjects[old_name]
            del subjects[old_name]
            subjects[new_name] = code
            self.save()

    def reorder_subjects(self, names: list[str]) -> None:
        """按新顺序重排科目"""
        old = self.subjects
        self._data["Subjects"] = {name: old[name] for name in names if name in old}
        self.save()

    # ==================== 通用读写 ====================

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()
