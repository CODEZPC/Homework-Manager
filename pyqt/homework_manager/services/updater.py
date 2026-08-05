"""
自动更新服务

从原 src/updater.py 迁移

状态机：
    None → Connecting → Needed/Failed/Latest
    Needed → Downloading → Completed
    Completed → 重启
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from enum import Enum, auto
from typing import Callable

import requests

from homework_manager.config.constants import VERSION_NUM, UPDATE_URL
from homework_manager.utils.platform import get_app_dir


class UpdateStatus(Enum):
    """更新状态"""

    NONE = auto()
    CONNECTING = auto()
    NEEDED = auto()  # 有新版本可用
    FAILED = auto()  # 检查失败
    DOWNLOADING = auto()  # 正在下载
    COMPLETED = auto()  # 下载完成
    LATEST = auto()  # 已是最新


class Updater:
    """自动更新管理器"""

    def __init__(self):
        self.status = UpdateStatus.NONE
        self.status_changed: Callable[[UpdateStatus], None] | None = None

        # 远程版本信息
        self.remote_version_num: int = 0
        self.remote_version_name: str = ""
        self.remote_version_type: str = ""

        # 下载进度
        self.download_progress: float = 0.0  # 0.0 ~ 1.0
        self.download_speed: float = 0.0  # KB/s
        self.download_size: int = 0  # 总大小 (bytes)

        self._thread: threading.Thread | None = None

    # ==================== 检查更新 ====================

    def check(self) -> None:
        """启动后台线程检查更新"""
        if self._thread and self._thread.is_alive():
            return
        self._set_status(UpdateStatus.CONNECTING)
        self._thread = threading.Thread(target=self._check_sync, daemon=True)
        self._thread.start()

    def _check_sync(self) -> None:
        """同步执行更新检查"""
        try:
            resp = requests.get(UPDATE_URL, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            self.remote_version_num = data.get("version_num", 0)
            self.remote_version_name = data.get("version_name", "")
            self.remote_version_type = data.get("type", "")

            if self.remote_version_num > VERSION_NUM:
                self._set_status(UpdateStatus.NEEDED)
            else:
                self._set_status(UpdateStatus.LATEST)
        except Exception:
            self._set_status(UpdateStatus.FAILED)

    # ==================== 下载更新 ====================

    def download(self) -> None:
        """启动后台线程下载更新"""
        if self.status != UpdateStatus.NEEDED:
            return
        self._set_status(UpdateStatus.DOWNLOADING)
        self._thread = threading.Thread(target=self._download_sync, daemon=True)
        self._thread.start()

    def _download_sync(self) -> None:
        """同步下载更新文件"""
        try:
            download_url = f"{UPDATE_URL.rsplit('/', 1)[0]}/main.exe"
            resp = requests.get(download_url, stream=True, timeout=60)
            resp.raise_for_status()

            self.download_size = int(resp.headers.get("content-length", 0))

            update_dir = os.path.join(get_app_dir(), "update")
            os.makedirs(update_dir, exist_ok=True)

            filepath = os.path.join(update_dir, "main.exe")
            downloaded = 0
            start_time = time.time()

            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        elapsed = time.time() - start_time
                        self.download_progress = (
                            downloaded / self.download_size
                            if self.download_size > 0
                            else 0
                        )
                        self.download_speed = (
                            (downloaded / 1024) / elapsed if elapsed > 0 else 0
                        )

            self._set_status(UpdateStatus.COMPLETED)
        except Exception:
            self._set_status(UpdateStatus.FAILED)

    # ==================== 重启安装 ====================

    @staticmethod
    def restart() -> None:
        """生成 update.bat 并重启程序"""
        app_dir = get_app_dir()
        bat_path = os.path.join(app_dir, "update.bat")
        exe_path = os.path.join(app_dir, "main.exe")
        new_exe_path = os.path.join(app_dir, "update", "main.exe")

        # 生成批处理：等待旧进程退出 → 替换 → 启动新版本 → 清理
        bat_content = f"""@echo off
timeout /t 2 /nobreak >nul
move /y "{new_exe_path}" "{exe_path}"
rmdir /s /q "{os.path.join(app_dir, 'update')}"
start "" "{exe_path}"
del "%~f0"
"""
        with open(bat_path, "w", encoding="gbk") as f:
            f.write(bat_content)

        subprocess.Popen(
            ["cmd", "/c", bat_path],
            creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.DETACHED_PROCESS,
        )
        sys.exit(0)

    # ==================== 内部方法 ====================

    def _set_status(self, status: UpdateStatus) -> None:
        self.status = status
        if self.status_changed:
            self.status_changed(status)
