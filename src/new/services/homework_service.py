"""
作业业务逻辑层 - 作业的增删改查与排序。
"""

import json
from typing import Any, Dict, List, Optional, Tuple

from models.data_store import DataStore
from services.time_analyzer import sort_key


class HomeworkService:
    """作业数据操作服务。"""

    def __init__(self, data_store: DataStore):
        self._store = data_store

    def load_and_sort(self, subject_codes: List[str]) -> Dict[str, Any]:
        """
        加载 homework.json，对每个科目的作业列表排序，
        若数据有变化则自动写回。返回完整 data 字典。
        """
        data = self._store.load_homework()
        if not data:
            return data

        changed = False
        for code in subject_codes:
            items = self._store.get_subject_items(data, code)
            sorted_items = sorted(items, key=sort_key)
            if sorted_items != items:
                data[code] = sorted_items
                changed = True

        if changed:
            self._store.save_homework(data)

        return data

    def add_homework(self, data: Dict[str, Any], subject_code: str,
                     content: str, deadline: Any, emphasize: str) -> bool:
        """添加一条新作业。"""
        items = self._store.get_subject_items(data, subject_code)
        items.append({
            "content": content,
            "time": deadline,
            "emphasize": emphasize,
        })
        return self._store.save_homework(data)

    def update_homework(self, data: Dict[str, Any],
                        old_subject: str, old_index: int,
                        new_subject: str, content: str,
                        deadline: Any, emphasize: str) -> bool:
        """
        更新（替换）一条已有作业。
        若科目发生变化，则从旧科目移除并添加到新科目。
        """
        new_item = {
            "content": content,
            "time": deadline,
            "emphasize": emphasize,
        }

        if old_subject == new_subject:
            try:
                items = self._store.get_subject_items(data, old_subject)
                items[old_index] = new_item
            except (IndexError, KeyError):
                items = self._store.get_subject_items(data, new_subject)
                items.append(new_item)
        else:
            # 从旧科目移除
            try:
                old_items = self._store.get_subject_items(data, old_subject)
                old_items.pop(old_index)
            except (IndexError, KeyError):
                pass
            # 添加到新科目
            new_items = self._store.get_subject_items(data, new_subject)
            new_items.append(new_item)

        return self._store.save_homework(data)

    def delete_homework(self, data: Dict[str, Any],
                        subject_codes: List[str],
                        global_index: int) -> Optional[bool]:
        """
        按全局索引删除一条作业。返回是否成功保存。
        """
        count = 0
        for code in subject_codes:
            items = self._store.get_subject_items(data, code)
            for item in items:
                if count == global_index:
                    items.remove(item)
                    return self._store.save_homework(data)
                count += 1
        return None  # 未找到

    def clear_expired(self, data: Dict[str, Any],
                      subject_codes: List[str]) -> int:
        """
        清理所有已过期作业。返回清理数量。
        """
        import time
        import config

        removed = 0
        for code in subject_codes:
            items = self._store.get_subject_items(data, code)
            new_items = []
            for item in items:
                t = item.get("time", 0)
                try:
                    t = int(t)
                except (TypeError, ValueError):
                    try:
                        t = float(t)
                    except (TypeError, ValueError):
                        t = 0

                if t != 0 and t < time.time() - config.TIME_OUT:
                    removed += 1
                else:
                    new_items.append(item)
            data[code] = new_items

        if removed > 0:
            self._store.save_homework(data)
        return removed

    def find_homework(self, data: Dict[str, Any],
                      subject_codes: List[str],
                      global_index: int) -> Optional[Tuple[str, int, Dict]]:
        """
        按全局索引查找作业，返回 (科目代码, 科目内索引, 作业字典)。
        """
        count = 0
        for code in subject_codes:
            items = self._store.get_subject_items(data, code)
            for idx, item in enumerate(items):
                if count == global_index:
                    return (code, idx, item)
                count += 1
        return None
