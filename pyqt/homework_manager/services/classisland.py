"""
ClassIsland 对接服务

通过 URI 协议与 ClassIsland 通信
原 src/homeworkfunc.py 的 uri_classisland 函数迁移
"""

import subprocess
import sys

from homework_manager.config.constants import CLASSISLAND_URI_PREFIX


class ClassIsland:
    """ClassIsland URI 协议通信"""

    @staticmethod
    def is_available() -> bool:
        """检查 ClassIsland 是否可用（仅打包后启用）"""
        return getattr(sys, "frozen", False)

    @classmethod
    def send_action(cls, mode: str, uri: str = "") -> None:
        """
        发送 ClassIsland 自动化操作

        参数:
            mode: 操作模式 (如 "start", "stop", "upload")
            uri: 具体的 URI 参数
        """
        if not cls.is_available():
            return
        full_uri = f"{CLASSISLAND_URI_PREFIX}/{mode}/{uri}"
        try:
            subprocess.Popen(
                ["start", full_uri],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    @classmethod
    def notify_start(cls) -> None:
        """通知 ClassIsland：HM 已启动"""
        cls.send_action("start", "hm")

    @classmethod
    def notify_stop(cls) -> None:
        """通知 ClassIsland：HM 已关闭"""
        cls.send_action("stop", "hm")

    @classmethod
    def notify_upload(cls, data: str) -> None:
        """通知 ClassIsland：上传作业数据"""
        cls.send_action("upload", data)
