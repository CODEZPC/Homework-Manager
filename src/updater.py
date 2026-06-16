from typing import *
import requests
import json
import main

STATUS: Literal["None", "Connecting", "Needed", "Failed"] = "None"
UPDATE_NUM = None
UPDATE_NAME = None
UPDATE_VER = None
UPDATE_TYPE = None


def check():
    global STATUS, UPDATE_NAME, UPDATE_NUM, UPDATE_TYPE, UPDATE_VER

    STATUS = "Connecting"

    site = f"https://codezpc.cn/CodeAPI/Homework-Manager/update.json"
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
