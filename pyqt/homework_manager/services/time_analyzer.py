"""
时间解析服务

从原 src/homeworkfunc.py 的 analyze_time / analyze_time_string 迁移

核心功能：
- 解析时间字符串，计算与当前时间的差距
- 返回显示文本和优先级数值
"""

import re
import time
from datetime import datetime

from homework_manager.config.constants import (
    EMPHASIZE_LEVELS,
    TIME_OUT,
)


class TimeAnalyzer:
    """时间解析器"""

    # 优先级权重映射
    EMPHASIZE_WEIGHTS = {
        "自动": None,  # 自动计算
        "很低": 0,
        "低": 1,
        "标准": 2,
        "高": 3,
    }

    @staticmethod
    def parse_time_string(time_str: str) -> str:
        """
        预处理时间字符串
        将 "HH:MM" 补全为 "YYYY/MM/DD HH:MM"
        """
        time_str = time_str.strip()
        # 匹配单独的时间格式 "H:MM" 或 "HH:MM"
        if re.match(r"^\d{1,2}:\d{2}$", time_str):
            today = datetime.now()
            time_str = today.strftime(f"%Y/%m/%d {time_str}")
        return time_str

    @classmethod
    def analyze(cls, timestamp: str, emphasize: str = "自动") -> tuple[str, int]:
        """
        核心时间解析

        参数:
            timestamp: 时间字符串 "YYYY/MM/DD HH:MM"
            emphasize: 优先级 "自动"|"很低"|"低"|"标准"|"高"

        返回:
            (显示文本, 优先级数值)
        """
        now = time.time()
        try:
            dt = datetime.strptime(timestamp, "%Y/%m/%d %H:%M")
            target = dt.timestamp()
        except (ValueError, TypeError):
            return ("时间格式错误", -1)

        diff = target - now

        # 计算优先级权重
        weight = cls.EMPHASIZE_WEIGHTS.get(emphasize, 2)

        if diff < -TIME_OUT:
            # 已过期超过 TIME_OUT 秒
            return ("时间已过", weight if weight is not None else 0)
        elif diff < 0:
            # 刚过期不久
            return ("现在收", weight if weight is not None else 3)
        elif diff < 600:
            # 10分钟内
            return ("即将收", weight if weight is not None else 4)
        elif diff < 3600:
            # 1小时内，显示具体时间
            dt_target = datetime.fromtimestamp(target)
            return (
                f"{dt_target.hour:02d}:{dt_target.minute:02d}收",
                weight if weight is not None else 3,
            )
        elif diff < 86400:
            # 今天内
            dt_target = datetime.fromtimestamp(target)
            if dt_target.day == datetime.now().day:
                return (
                    f"{dt_target.hour:02d}:{dt_target.minute:02d}收",
                    weight if weight is not None else 2,
                )
            else:
                return (
                    f"明天 {dt_target.hour:02d}:{dt_target.minute:02d}收",
                    weight if weight is not None else 2,
                )
        else:
            # 超过一天
            return ("不收", weight if weight is not None else 1)

    @classmethod
    def get_priority_value(cls, emphasize: str) -> int:
        """获取优先级数值（用于排序）"""
        return cls.EMPHASIZE_WEIGHTS.get(emphasize, 2)
