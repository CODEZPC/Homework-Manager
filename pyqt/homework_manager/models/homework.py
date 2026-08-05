"""
作业数据模型

对应原 homework.json 中每个作业对象的字段
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Homework:
    """单个作业条目"""

    content: str = ""  # 作业内容文本
    timestamp: str = ""  # 截止时间字符串 "YYYY/MM/DD HH:MM"
    emphasize: str = "标准"  # 优先级: "自动" | "很低" | "低" | "标准" | "高"

    # 以下为兼容旧数据字段
    extra: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Homework":
        """从字典创建（兼容旧数据格式）"""
        return cls(
            content=data.get("content", data.get("text", "")),
            timestamp=data.get("timestamp", data.get("time", "")),
            emphasize=data.get("emphasize", "标准"),
            extra={
                k: v
                for k, v in data.items()
                if k not in ("content", "text", "timestamp", "time", "emphasize")
            },
        )

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "content": self.content,
            "timestamp": self.timestamp,
            "emphasize": self.emphasize,
        }

    @property
    def is_empty(self) -> bool:
        return not self.content.strip()

    def __str__(self) -> str:
        return f"{self.content} [{self.timestamp}] ({self.emphasize})"
