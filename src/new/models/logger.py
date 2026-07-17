"""
日志输出层 - 统一管理 manager.log 的读写。
"""

import logging
import os
import sys
import threading
from typing import Literal


class Logger:
    """日志统一写入管理器"""

    def __init__(self):
        self._lock = threading.Lock()
        self._loglayer = "Logger"

    # ──────────────── 日志初始化 ────────────────

    def setup_logging(self, log_file: str = ".\\_internal\\log\\manager.log") -> None:
        """初始化日志系统，可在入口调用。"""

        if not os.path.exists(".\\_internal"):
            os.mkdir("_internal")
        if not os.path.exists(".\\_internal\\log"):
            os.mkdir("_internal\\log")

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
        self.log_output(
            self._loglayer, "Info", f"──────────────── 作业管理器启动 ────────────────"
        )
        self.log_output(
            self._loglayer, "Info", f"日志系统已初始化，日志文件: {log_file}"
        )

    # ──────────────── 日志输出 ────────────────

    def log_output(
        self,
        layer: str,
        level: Literal["Debug", "Info", "Warning", "Error", "Critical"],
        message: str,
    ) -> None:
        if level == "Debug":
            logging.debug(f"[{layer}] - {message}")
        elif level == "Info":
            logging.info(f"[{layer}] - {message}")
        elif level == "Warning":
            logging.warning(f"[{layer}] - {message}")
        elif level == "Error":
            logging.error(f"[{layer}] - {message}")
        elif level == "Critical":
            logging.critical(f"[{layer}] - {message}")
        else:
            raise ValueError("Unknown Logging Level")
