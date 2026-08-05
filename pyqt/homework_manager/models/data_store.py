"""
作业数据持久化

封装 homework.json 的读写操作
"""

import json
import os
from typing import Any

from homework_manager.config.constants import DATA_FILE
from homework_manager.utils.platform import get_app_dir


class DataStore:
    """作业数据存储管理"""

    def __init__(self, filepath: str | None = None):
        self.app_dir = get_app_dir()
        self.filepath = filepath or os.path.join(self.app_dir, DATA_FILE)
        self._data: dict[str, list[dict]] = {}

    # ==================== 读写 ====================

    def load(self) -> dict[str, list[dict]]:
        """从 JSON 文件加载作业数据"""
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = {}
        return self._data

    def save(self) -> None:
        """保存作业数据到 JSON 文件"""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=4)

    # ==================== 科目操作 ====================

    def get_subject_homeworks(self, subject_code: str) -> list[dict]:
        """获取指定科目的作业列表"""
        return self._data.get(subject_code, [])

    def add_homework(self, subject_code: str, homework: dict) -> None:
        """添加作业到指定科目"""
        self._data.setdefault(subject_code, [])
        self._data[subject_code].append(homework)
        self.save()

    def edit_homework(self, subject_code: str, index: int, homework: dict) -> None:
        """编辑指定位置的作业"""
        if subject_code in self._data and 0 <= index < len(self._data[subject_code]):
            self._data[subject_code][index] = homework
            self.save()

    def delete_homework(self, subject_code: str, index: int) -> None:
        """删除指定位置的作业"""
        if subject_code in self._data and 0 <= index < len(self._data[subject_code]):
            del self._data[subject_code][index]
            self.save()

    def clear_expired(self, subject_code: str, indices: list[int]) -> None:
        """批量删除指定科目中已过期的作业（indices 需降序排列）"""
        if subject_code not in self._data:
            return
        for i in sorted(indices, reverse=True):
            if 0 <= i < len(self._data[subject_code]):
                del self._data[subject_code][i]
        self.save()

    # ==================== 科目结构操作 ====================

    def add_subject_key(self, subject_code: str) -> None:
        """为 homework.json 添加新科目键（初始化为空列表）"""
        if subject_code not in self._data:
            self._data[subject_code] = []
            self.save()

    def remove_subject_key(self, subject_code: str) -> None:
        """从 homework.json 删除科目键"""
        if subject_code in self._data:
            del self._data[subject_code]
            self.save()

    # ==================== 版本 ====================

    @property
    def version(self) -> int:
        """获取数据版本号"""
        return self._data.get("VER", 0)

    @version.setter
    def version(self, ver: int) -> None:
        self._data["VER"] = ver

    # ==================== 工具 ====================

    @property
    def all_subject_codes(self) -> list[str]:
        """获取所有科目代码（排除 VER 等元字段）"""
        return [k for k in self._data if k != "VER"]

    def get_total_count(self) -> int:
        """获取作业总数"""
        return sum(len(v) for k, v in self._data.items() if k != "VER")

    def get_flat_list(self, subject_codes: list[str]) -> list[tuple[str, int, dict]]:
        """
        获取扁平化的作业列表
        返回 [(科目代码, 索引, 作业字典), ...]
        """
        result = []
        for code in subject_codes:
            if code in self._data:
                for i, item in enumerate(self._data[code]):
                    result.append((code, i, item))
        return result
