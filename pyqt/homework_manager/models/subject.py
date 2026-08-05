"""
科目数据模型
"""

from dataclasses import dataclass


@dataclass
class Subject:
    """科目定义"""

    name: str  # 显示名称，如 "语文"
    code: str  # 科目代码，如 "C"

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.code)
