from typing import *
import main

LANG: Literal["zh-CN","en-US"]= "zh-CN"

DATA = {
    "zh-CN":{
        "homework.clear.complete": "作业管理器·清理完成",
        "homework.clear.complete.desc": "已清理 %d 个已过期作业。",
        "homework.clear.nothing": "没有需要清理的作业。",
        "homework.loading": "正在加载……",
        "status.homework": "作业数",
        "status.load": "负载",
        "status.mouse": "鼠标",
        "status.update.connecting": "尝试连接至服务器……",
        "status.update.download": "下载更新中……",
        "status.update.find": "发现更新：",
        "status.update.latest": "无需更新",
        "status.update.offline": "离线或未能连接到服务器",
        "status.update.restart": "重启以更新",
        "title": "作业管理器",
        "ui.top.add": "添加",
        "ui.top.clear": "清理",
        "ui.top.exit": "退出",
        "ui.top.refresh": "刷新",
    }
}

def text(key):
    return DATA[LANG][key]