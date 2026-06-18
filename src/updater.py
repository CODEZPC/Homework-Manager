from typing import *
import requests
import json
import os
import threading
import time
import main

STATUS: Literal["None", "Connecting", "Needed", "Failed", "Downloading"] = "None"
UPDATE_NUM = None
UPDATE_NAME = None
UPDATE_VER = None
UPDATE_TYPE = None

DOWNLOAD_SPEED = None
DOWNLOAD_PROCESS = None
DOWNLOAD_SIZE = None


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
        STATUS = "None"

def response(event):
    global STATUS
    if STATUS == "Needed":
        STATUS = "Connecting"
        threading.Thread(target=download_update).start()

def download_update():
    global DOWNLOAD_SPEED, DOWNLOAD_PROCESS, DOWNLOAD_SIZE, STATUS

    STATUS = "Downloading"

    url = "https://codezpc.cn/Homework-Manager/main.exe"
    save_dir = "./update"
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

    except Exception:
        # 出错时可设置标记，例如进度设为 -1 供外部判断
        DOWNLOAD_PROCESS = -1.0
        DOWNLOAD_SPEED = 0.0
        raise

if __name__ == "__main__":
    pass