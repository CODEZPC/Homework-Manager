"""
作业管理器 - 重构版

班级大屏作业管理器，采用 MVC 分层架构：
- models/   : 数据存储层
- views/    : UI 视图层
- services/ : 业务逻辑层

入口: app.py → main()
"""

from app import main, Application

__version__ = "1.6.2.15"
__all__ = ["main", "Application"]
