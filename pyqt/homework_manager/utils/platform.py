"""
平台工具函数

从原 src/main.py 的 _app_dir / restart_service 迁移
"""

import os
import sys


def get_app_dir() -> str:
    """
    获取应用程序所在目录
    兼容 PyInstaller 打包和直接运行
    """
    if getattr(sys, "frozen", False):
        # PyInstaller 打包后
        return os.path.dirname(sys.executable)
    else:
        # 直接运行 Python 脚本
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def restart_service() -> None:
    """生成 update.bat 并重启程序（用于服务重启）"""
    app_dir = get_app_dir()
    bat_path = os.path.join(app_dir, "update.bat")
    exe_path = os.path.join(app_dir, "main.exe")

    bat_content = f"""@echo off
timeout /t 2 /nobreak >nul
start "" "{exe_path}"
del "%~f0"
"""
    import subprocess

    with open(bat_path, "w", encoding="gbk") as f:
        f.write(bat_content)

    subprocess.Popen(
        ["cmd", "/c", bat_path],
        creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.DETACHED_PROCESS,
    )
    sys.exit(0)
