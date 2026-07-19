"""
ClassIsland 集成服务 - 通过 URI 协议与 ClassIsland 课表工具交互。
"""

import subprocess
import config
from models import Logger

_logger = Logger()
_loglayer = "Classisland"


def call_uri(uri: str, mode: str = "run") -> bool:
    """
    调用 ClassIsland 的 URI 解析接口。

    :param uri: 要解析的 URI 字符串
    :param mode: 解析模式，"run" 表示直接运行，"revert" 表示撤销
    :return: 是否成功发起调用
    """
    if not config.ENABLE_CLASSISLAND:
        return False
    try:
        subprocess.Popen(
            f"start classisland://app/api/automation/{mode}/{uri}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except Exception:
        return False


def homework_mode_on() -> bool:
    """通知 ClassIsland 作业模式已开启。"""
    _logger.log_output(_loglayer, "Info", "Classisland ON")
    return call_uri("homeworkmode-on")


def homework_mode_off() -> bool:
    """通知 ClassIsland 作业模式已关闭。"""
    _logger.log_output(_loglayer, "Info", "Classisland OFF")
    return call_uri("homeworkmode-off")


def homework_upload() -> bool:
    """通知 ClassIsland 有作业需要提交。"""
    _logger.log_output(_loglayer, "Info", "Classisland Homework Update")
    return call_uri("Homeworkmode-upload")
