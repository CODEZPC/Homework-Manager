from typing import *
import json
import main

LANG: Literal["zh-CN","en-US"]= "zh-CN"

with open("setting.json", "r") as f:
    LANG = json.load(f)["Language"]

DATA = {
    "zh-CN":{
        "homework.add.cancel": "取消",
        "homework.add.context": "内容",
        "homework.add.emphasize": "优先级",
        "homework.add.endtime": "截止时间",
        "homework.add.endtime.aftertomorrow": "后天",
        "homework.add.endtime.daya": "-1天",
        "homework.add.endtime.dayb": "+1天",
        "homework.add.endtime.noneed": "不收",
        "homework.add.endtime.today": "今天",
        "homework.add.endtime.tomorrow": "明天",
        "homework.add.help": "使用手册",
        "homework.add.subject": "科目",
        "homework.add.submit": "提交",
        "homework.add.title": "作业管理器·新建作业",
        "homework.add.warning.outlimit": "作业管理器·超过上限",
        "homework.add.warning.outlimit.desc": "作业数量已达上限，是否强制添加？",
        "homework.clear.complete": "作业管理器·清理完成",
        "homework.clear.complete.desc": "已清理 %d 个作业。",
        "homework.clear.nothing": "没有需要清理的作业。",
        "homework.del.desc": "确定要删除吗？",
        "homework.del.title": "作业管理器·删除提示",
        "homework.error": "作业管理器·错误",
        "homework.loading": "正在加载……",
        "menu.exit": "退出菜单",
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
        "ui.top.menu": "菜单",
        "ui.top.refresh": "刷新",
    },
    "en-US":{
        "homework.add.cancel": "Cancel",
        "homework.add.context": "Content",
        "homework.add.emphasize": "Priority",
        "homework.add.endtime": "Deadline",
        "homework.add.endtime.aftertomorrow": "DAT",
        "homework.add.endtime.daya": "-1D",
        "homework.add.endtime.dayb": "+1D",
        "homework.add.endtime.noneed": "None",
        "homework.add.endtime.today": "Today",
        "homework.add.endtime.tomorrow": "TMR",
        "homework.add.help": "User Manual",
        "homework.add.subject": "Subject",
        "homework.add.submit": "SUBMIT",
        "homework.add.title": "Homework Manager - Add Homework",
        "homework.add.warning.outlimit": "Homework Manager - Out of Limit",
        "homework.add.warning.outlimit.desc": "The number of homeworks has reached the limit. Do you want to force add it?",
        "homework.clear.complete": "Homework Manager - Clear Complete",
        "homework.clear.complete.desc": "Cleared %d homework(s).",
        "homework.clear.nothing": "There's no homework to clean up.",
        "homework.del.desc": "Are you sure you want to delete it?",
        "homework.del.title": "Homework Manager - Delete Confirmation",
        "homework.error": "Homework Manager - ERROR",
        "homework.loading": "Loading...",
        "menu.exit": "Exit Menu",
        "status.homework": "Homework(s)",
        "status.load": "Load",
        "status.mouse": "Mouse",
        "status.update.connecting": "Trying to connect to the server...",
        "status.update.download": "Downloading Update",
        "status.update.find": "Update found:",
        "status.update.latest": "No need to update",
        "status.update.offline": "Offline or failed to connect to the server",
        "status.update.restart": "Restart to Update",
        "title": "Homework Manager",
        "ui.top.add": "Add",
        "ui.top.clear": "Clear",
        "ui.top.exit": "Exit",
        "ui.top.menu": "Menu",
        "ui.top.refresh": "Refresh",
    }
}

def text(key):
    try:
        return DATA[LANG][key]
    except KeyError:
        return DATA["zh-CN"][key]