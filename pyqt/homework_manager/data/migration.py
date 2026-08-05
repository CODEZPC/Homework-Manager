"""
数据版本迁移

从原 src/dataupdate.py 迁移
自动检测并升级 homework.json 的数据结构版本
"""

import json
import os

from homework_manager.config.constants import DATA_FILE
from homework_manager.utils.platform import get_app_dir


class DataMigration:
    """数据版本迁移器"""

    TARGET_VERSION = 2  # 目标数据版本号

    @classmethod
    def run(cls, filepath: str | None = None) -> bool:
        """
        执行数据迁移
        返回 True 表示有变更
        """
        path = filepath or os.path.join(get_app_dir(), DATA_FILE)
        if not os.path.exists(path):
            return False

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        current_ver = data.get("VER", 0)
        changed = False

        while current_ver < cls.TARGET_VERSION:
            data = cls._migrate_step(current_ver, data)
            current_ver += 1
            changed = True

        if changed:
            data["VER"] = current_ver
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

        return changed

    @classmethod
    def _migrate_step(cls, level: int, data: dict) -> dict:
        """单步迁移"""
        if level == 0:
            # 添加 emphasize 字段，默认 "Standard" → "标准"
            for key, items in data.items():
                if key == "VER" or not isinstance(items, list):
                    continue
                for item in items:
                    if "emphasize" not in item:
                        item["emphasize"] = "标准"

        elif level == 1:
            # 旧版英文优先级 → 中文
            mapping = {
                "Auto": "自动",
                "VeryLow": "很低",
                "Low": "低",
                "Standard": "标准",
                "High": "高",
            }
            for key, items in data.items():
                if key == "VER" or not isinstance(items, list):
                    continue
                for item in items:
                    old = item.get("emphasize", "标准")
                    item["emphasize"] = mapping.get(old, old)

        return data
