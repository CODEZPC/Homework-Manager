from typing import *
import requests
import json
import os
import subprocess
import tempfile
import threading
import time
import sys
import main

STATUS: Literal["None", "Connecting", "Needed", "Failed", "Downloading", "Completed", "Latest"] = "None"
UPDATE_NUM = None
UPDATE_NAME = None
UPDATE_VER = None
UPDATE_TYPE = None

DOWNLOAD_SPEED = None
DOWNLOAD_PROCESS = None
DOWNLOAD_SIZE = None


def _app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def check():
    global STATUS, UPDATE_NAME, UPDATE_NUM, UPDATE_TYPE, UPDATE_VER

    STATUS = "Connecting"

    site = f"https://codezpc.cn/Homework-Manager/update.json"
    try:
        # 发送HTTP GET请求
        response = requests.get(site)
        response.raise_for_status()  # 如果请求失败则抛出异常
    except requests.exceptions.RequestException as e:
        print(f"Error fetching file: {e}")
        STATUS = "Failed"
        return

    DATA = json.loads(response.text)
    UPDATE_NUM = DATA["VERSION_NUM"]
    UPDATE_NAME = DATA["NAME"]
    UPDATE_TYPE = DATA["TYPE"]
    UPDATE_VER = DATA["VERSION"]

    if UPDATE_NUM > main.VERSION_NUM or DATA["TYPE"] == "Force":
        STATUS = "Needed"
    else:
        STATUS = "Latest"

def response(event):
    global STATUS
    if STATUS == "Failed" or STATUS == "Latest":
        thread = threading.Thread(target=check)
        thread.daemon = True
        thread.start()
    if STATUS == "Needed":
        STATUS = "Connecting"
        thread = threading.Thread(target=download_update)
        thread.daemon = True
        thread.start()
    if STATUS == "Completed":
        restart()

def download_update():
    global DOWNLOAD_SPEED, DOWNLOAD_PROCESS, DOWNLOAD_SIZE, STATUS

    STATUS = "Downloading"

    url = "https://codezpc.cn/Homework-Manager/main.exe"
    save_dir = os.path.join(_app_dir(), "update")
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, "main.exe")

    # 重置状态
    DOWNLOAD_SPEED = 0.0
    DOWNLOAD_PROCESS = 0.0
    DOWNLOAD_SIZE = 0

    try:
        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            # 获取文件总大小
            content_length = response.headers.get("content-length")
            DOWNLOAD_SIZE = int(content_length) if content_length else 0

            downloaded = 0
            last_time = time.time()
            last_downloaded = 0

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # 计算下载速度（每秒更新一次，保证平滑）
                        now = time.time()
                        delta = now - last_time
                        if delta >= 1.0:
                            DOWNLOAD_SPEED = (downloaded - last_downloaded) / delta
                            last_time = now
                            last_downloaded = downloaded

                        # 计算下载进度
                        if DOWNLOAD_SIZE > 0:
                            DOWNLOAD_PROCESS = (downloaded / DOWNLOAD_SIZE) * 100
                        # 若无法获取大小，进度保持 0

        # 下载完成
        DOWNLOAD_PROCESS = 100.0
        DOWNLOAD_SPEED = 0.0
        STATUS = "Completed"

    except Exception:
        # 出错时可设置标记，例如进度设为 -1 供外部判断
        DOWNLOAD_PROCESS = -1.0
        DOWNLOAD_SPEED = 0.0
        STATUS = "Failed"
    
def restart():
    """
    终止主程序，将 ./update/main.exe 移动/覆盖到当前目录的 main.exe，
    删除 ./update 目录，然后启动新的 main.exe。
    调用后当前进程立即退出。
    """
    app_dir = _app_dir()
    update_dir = os.path.join(app_dir, "update")
    new_exe_path = os.path.join(update_dir, "main.exe")
    current_exe_path = os.path.join(app_dir, "main.exe")

    # 确保更新文件存在
    if not os.path.exists(new_exe_path):
        print("更新文件不存在，无法重启。")
        return
    
    bat_path = os.path.join(app_dir, "update.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(f"""@echo off
timeout /t 2 /nobreak >nul
move /Y "{new_exe_path}" "{current_exe_path}"
rd /s /q "{update_dir}"
set _MEIPASS2=
set PYINSTALLER_RESET_ENVIRONMENT=1
start "" /D "{app_dir}" "{current_exe_path}"
del /f /q "%~f0"
""")

    subprocess.Popen([bat_path], shell=True)
    sys.exit()

if __name__ == "__main__":
    pass