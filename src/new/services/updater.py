"""
自动更新服务 - 检查、下载、重启更新。

所有网络操作在后台线程执行，通过回调通知 UI 状态变化。
"""

import os
import sys
import json
import subprocess
import threading
import time
from typing import Callable, Optional

import requests

import config


# ──────────────── 状态常量 ────────────────
class UpdateStatus:
    NONE = "None"
    CONNECTING = "Connecting"
    NEEDED = "Needed"
    FAILED = "Failed"
    DOWNLOADING = "Downloading"
    COMPLETED = "Completed"
    LATEST = "Latest"


class Updater:
    """自动更新管理器。"""

    def __init__(self):
        self._loglayer = "Update"

        self.status: str = UpdateStatus.NONE
        self.update_num: Optional[int] = None
        self.update_name: Optional[str] = None
        self.update_ver: Optional[str] = None
        self.update_type: Optional[str] = None

        self.download_speed: float = 0.0
        self.download_process: float = 0.0
        self.download_size: int = 0

        self._on_status_change: Optional[Callable[[str], None]] = None

    def set_callback(self, callback: Callable[[str], None]) -> None:
        """设置状态变更回调（线程安全，回调在后台线程调用）。"""
        self._on_status_change = callback

    def _notify(self) -> None:
        """通知状态变更。"""
        if self._on_status_change:
            try:
                self._on_status_change(self.status)
            except Exception:
                pass

    def check(self) -> None:
        """在后台线程检查更新。"""
        self.status = UpdateStatus.CONNECTING
        self._notify()

        try:
            response = requests.get(config.UPDATE_URL, timeout=15)
            response.raise_for_status()
            data = json.loads(response.text)

            self.update_num = data["VERSION_NUM"]
            self.update_name = data["NAME"]
            self.update_type = data["TYPE"]
            self.update_ver = data["VERSION"]

            if self.update_num > config.VERSION_NUM or data["TYPE"] == "Force":
                self.status = UpdateStatus.NEEDED
            else:
                self.status = UpdateStatus.LATEST
        except requests.exceptions.RequestException as e:
            print(f"[Updater] 检查更新失败: {e}")
            self.status = UpdateStatus.FAILED

        self._notify()

    def start_check(self) -> None:
        """在后台线程中启动更新检查。"""
        thread = threading.Thread(target=self.check, daemon=True)
        thread.start()

    def handle_click(self) -> None:
        """
        处理用户点击更新消息区域的事件。
        根据当前状态执行相应操作（检查 / 下载 / 重启）。
        """
        if self.status in (UpdateStatus.FAILED, UpdateStatus.LATEST, UpdateStatus.NONE):
            self.start_check()
        elif self.status == UpdateStatus.NEEDED:
            self.status = UpdateStatus.CONNECTING
            self._notify()
            thread = threading.Thread(target=self._download, daemon=True)
            thread.start()
        elif self.status == UpdateStatus.COMPLETED:
            self._restart()

    def _download(self) -> None:
        """在后台线程下载更新。"""
        self.status = UpdateStatus.DOWNLOADING
        self.download_speed = 0.0
        self.download_process = 0.0
        self.download_size = 0
        self._notify()

        os.makedirs(config.UPDATE_DIR, exist_ok=True)

        try:
            with requests.get(config.DOWNLOAD_URL, stream=True, timeout=60) as response:
                response.raise_for_status()

                content_length = response.headers.get("content-length")
                self.download_size = int(content_length) if content_length else 0

                downloaded = 0
                last_time = time.time()
                last_downloaded = 0

                with open(config.UPDATE_EXE_PATH, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            now = time.time()
                            delta = now - last_time
                            if delta >= 1.0:
                                self.download_speed = (
                                    downloaded - last_downloaded
                                ) / delta
                                last_time = now
                                last_downloaded = downloaded

                            if self.download_size > 0:
                                self.download_process = (
                                    downloaded / self.download_size
                                ) * 100

            self.download_process = 100.0
            self.download_speed = 0.0
            self.status = UpdateStatus.COMPLETED

        except Exception as e:
            print(f"[Updater] 下载失败: {e}")
            self.download_process = -1.0
            self.download_speed = 0.0
            self.status = UpdateStatus.FAILED

        self._notify()

    def _restart(self) -> None:
        """
        终止主程序，用更新文件替换当前 exe 并重启。
        """
        if not os.path.exists(config.UPDATE_EXE_PATH):
            print("[Updater] 更新文件不存在，无法重启。")
            return

        bat_path = os.path.join(config.APP_DIR, "update.bat")
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(f"""@echo off
timeout /t 2 /nobreak >nul
move /Y "{config.UPDATE_EXE_PATH}" "{config.CURRENT_EXE_PATH}"
rd /s /q "{config.UPDATE_DIR}"
set _MEIPASS2=
set PYINSTALLER_RESET_ENVIRONMENT=1
start "" /D "{config.APP_DIR}" "{config.CURRENT_EXE_PATH}"
del /f /q "%~f0"
""")

        subprocess.Popen([bat_path], shell=True)
        sys.exit()


def restart_service() -> None:
    """
    立即重启当前 exe（非更新场景的重启）。
    """
    bat_path = os.path.join(config.APP_DIR, "update.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(f"""@echo off
timeout /t 1 /nobreak >nul
set _MEIPASS2=
set PYINSTALLER_RESET_ENVIRONMENT=1
start "" /D "{config.APP_DIR}" "{config.CURRENT_EXE_PATH}"
del /f /q "%~f0"
""")

    subprocess.Popen([bat_path], shell=True)
    sys.exit()
