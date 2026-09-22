from typing import *
import requests
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import zipfile
import main

STATUS: Literal["None", "Connecting", "Needed", "Failed", "Downloading", "Completed", "Latest"] = "None"
UPDATE_NUM = None
UPDATE_NAME = None
UPDATE_VER = None
UPDATE_TYPE = None
# 完整更新包名（update.json 的可选字段 PACKAGE，例如 "main.zip"）。
# 为 None 时回退旧逻辑：只下载单文件 main.exe（兼容旧版本客户端 / 单文件安装）。
UPDATE_PACKAGE = None

DOWNLOAD_SPEED = None
DOWNLOAD_PROCESS = None
DOWNLOAD_SIZE = None

BASE_URL = "https://codezpc.cn/Homework-Manager/"
PACKAGE_FILE = "main.zip"  # 完整包下载到 update/ 后的本地文件名（便于统一解压）
LEGACY_EXE = "main.exe"  # 旧版单文件更新载荷


def _app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def check():
    global STATUS, UPDATE_NAME, UPDATE_NUM, UPDATE_TYPE, UPDATE_VER, UPDATE_PACKAGE

    STATUS = "Connecting"

    site = BASE_URL + "update.json"
    try:
        # 发送HTTP GET请求
        response = requests.get(site)
        response.raise_for_status()  # 如果请求失败则抛出异常
    except requests.exceptions.RequestException as e:
        print(f"Error fetching file: {e}")
        STATUS = "Failed"
        return

    try:
        DATA = json.loads(response.text)
        UPDATE_NUM = DATA["VERSION_NUM"]
        UPDATE_NAME = DATA["NAME"]
        UPDATE_TYPE = DATA["TYPE"]
        UPDATE_VER = DATA["VERSION"]
        # 可选：-D 完整包（zip）。缺失时回退旧逻辑（仅下载 main.exe）。
        package = DATA.get("PACKAGE")
        UPDATE_PACKAGE = package.strip() if isinstance(package, str) and package.strip() else None
    except Exception as e:
        # 缺少必要字段 / 格式错误 → 视为检查失败，避免线程中断导致状态卡在 Connecting
        print(f"Error parsing update.json: {e}")
        STATUS = "Failed"
        return

    if UPDATE_NUM > main.VERSION_NUM or UPDATE_TYPE == "Force":
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

def _download_file(url, file_path):
    """流式下载单个文件，实时更新进度 / 速度；成功返回 True。"""
    global DOWNLOAD_SPEED, DOWNLOAD_PROCESS, DOWNLOAD_SIZE

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
        return True

    except Exception:
        # 出错时可设置标记，例如进度设为 -1 供外部判断
        DOWNLOAD_PROCESS = -1.0
        DOWNLOAD_SPEED = 0.0
        return False


def extract_package(zip_path, dest_dir):
    """
    解压完整更新包到 dest_dir（先清空旧内容）。

    包内应为程序目录结构（顶层包含 main.exe 与 _internal/ 等），
    解压后由 update.bat 复制回程序目录。
    """
    if os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir, ignore_errors=True)
    os.makedirs(dest_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        if not any(os.path.basename(n).lower() == LEGACY_EXE for n in names):
            raise ValueError("更新包中缺少 main.exe")
        zf.extractall(dest_dir)


def download_update():
    """
    下载更新。

    - `update.json` 提供 `PACKAGE`（-D 完整包）时：下载整包并解压到 `update/package`；
    - 否则回退旧逻辑：只下载单文件 `main.exe` 到 `update/main.exe`。
    """
    global STATUS

    STATUS = "Downloading"

    save_dir = os.path.join(_app_dir(), "update")
    os.makedirs(save_dir, exist_ok=True)

    # 清理上一次遗留的更新载荷，避免新旧混用
    for name in ("package", LEGACY_EXE, PACKAGE_FILE):
        stale = os.path.join(save_dir, name)
        if os.path.isdir(stale):
            shutil.rmtree(stale, ignore_errors=True)
        elif os.path.exists(stale):
            try:
                os.remove(stale)
            except Exception:
                pass

    if UPDATE_PACKAGE:
        url = BASE_URL + UPDATE_PACKAGE
        file_path = os.path.join(save_dir, PACKAGE_FILE)
    else:
        url = BASE_URL + LEGACY_EXE
        file_path = os.path.join(save_dir, LEGACY_EXE)

    if not _download_file(url, file_path):
        STATUS = "Failed"
        return

    if UPDATE_PACKAGE:
        # 批处理无法解压，这里先解压好，重启脚本只负责复制文件
        try:
            extract_package(file_path, os.path.join(save_dir, "package"))
        except Exception:
            STATUS = "Failed"
            return

    STATUS = "Completed"
    
def _update_batch_text(app_dir, update_dir):
    """
    生成更新用批处理内容；找不到可用的更新载荷时返回 None。

    - 完整包模式（`update/package` 存在）：清理 `_internal` 中除用户目录
      （config / backup / lock / log）以外的旧运行时文件后整目录复制
      （robocopy 覆盖 main.exe 与 _internal 等，不触碰用户数据文件）；
    - 单文件模式（`update/main.exe` 存在）：只覆盖 exe（旧逻辑，兼容仅提供 main.exe 的更新）。
    """
    package_dir = os.path.join(update_dir, "package")
    new_exe_path = os.path.join(update_dir, LEGACY_EXE)
    current_exe_path = os.path.join(app_dir, LEGACY_EXE)
    internal_dir = os.path.join(app_dir, "_internal")

    if os.path.isdir(package_dir):
        return f"""@echo off
timeout /t 2 /nobreak >nul
for /d %%D in ("{internal_dir}\\*") do if /i not "%%~nxD"=="config" if /i not "%%~nxD"=="backup" if /i not "%%~nxD"=="lock" if /i not "%%~nxD"=="log" rd /s /q "%%D"
del /f /q /a-d "{internal_dir}\\*" >nul 2>nul
robocopy "{package_dir}" "{app_dir}" /E /IS /IT /R:5 /W:1 >nul
rd /s /q "{update_dir}"
set _MEIPASS2=
set PYINSTALLER_RESET_ENVIRONMENT=1
start "" /D "{app_dir}" "{current_exe_path}"
del /f /q "%~f0"
"""

    if os.path.exists(new_exe_path):
        return f"""@echo off
timeout /t 2 /nobreak >nul
move /Y "{new_exe_path}" "{current_exe_path}"
rd /s /q "{update_dir}"
set _MEIPASS2=
set PYINSTALLER_RESET_ENVIRONMENT=1
start "" /D "{app_dir}" "{current_exe_path}"
del /f /q "%~f0"
"""

    return None


def restart():
    """
    生成更新脚本并退出当前进程：

    - 完整包模式：`update/package`（已解压）整体复制回程序目录（覆盖 exe 与 _internal 运行时文件，
      保留 config / backup / lock / log 等用户目录）；
    - 单文件模式：把 `update/main.exe` 覆盖到程序目录（旧逻辑）。

    调用后当前进程立即退出。
    """
    app_dir = _app_dir()
    update_dir = os.path.join(app_dir, "update")
    bat_text = _update_batch_text(app_dir, update_dir)
    if bat_text is None:
        print("更新文件不存在，无法重启。")
        return
    
    bat_path = os.path.join(app_dir, "update.bat")
    with open(bat_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(bat_text)

    subprocess.Popen([bat_path], shell=True)
    sys.exit()

if __name__ == "__main__":
    pass