"""
性能监控工具

从原 src/main.py 的 calculate_canvas_load 和 homeworkfunc.py 的 speed_test 迁移
"""

import os
import time
from typing import Any

import psutil


class PerformanceMonitor:
    """性能监控器"""

    @staticmethod
    def calculate_load(data_store: Any) -> float:
        """
        估算当前渲染负载

        返回负载指数（0~100）
        """
        total = data_store.get_total_count()
        # 简单线性模型：每条作业约贡献 5 点负载
        load = min(total * 5, 100)
        return load

    @staticmethod
    def get_cpu_usage() -> float:
        """获取当前 CPU 使用率 (%)"""
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception:
            return 0.0

    @staticmethod
    def get_memory_usage() -> float:
        """获取当前进程内存使用 (MB)"""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0

    @staticmethod
    def simulate_activity() -> None:
        """
        模拟用户活动以防止锁屏
        原实现使用 mouse / pygetwindow
        此处使用轻量级方案
        """
        try:
            import ctypes

            # 发送轻微鼠标移动事件防止锁屏
            ctypes.windll.user32.mouse_event(0x0001, 0, 0, 0, 0)
        except Exception:
            pass

    @staticmethod
    def speed_test() -> float:
        """
        性能测试：测量单次渲染循环耗时

        返回毫秒数
        """
        start = time.perf_counter()
        # 模拟一次排序 + 解析
        test_data = [
            ("2026/07/29 12:00", "标准"),
            ("2026/07/29 08:00", "高"),
        ]
        for ts, emp in test_data:
            from homework_manager.services.time_analyzer import TimeAnalyzer

            TimeAnalyzer.analyze(ts, emp)
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed
