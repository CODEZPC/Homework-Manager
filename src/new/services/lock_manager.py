"""
进程锁服务 - 防止程序多实例运行。
"""

import os
import msvcrt
from typing import Optional
from io import TextIOWrapper

import config


def acquire_lock(lock_path: Optional[str] = None) -> Optional[TextIOWrapper]:
    """
    尝试获取文件锁（Windows 下使用 msvcrt）。

    成功返回打开的文件对象（必须保持引用以维持锁），失败返回 None。
    """
    if lock_path is None:
        lock_path = config.LOCK_PATH

    try:
        lock_file = open(lock_path, "w")
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        return lock_file
    except FileNotFoundError:
        try:
            os.makedirs(os.path.dirname(lock_path), exist_ok=True)
            lock_file = open(lock_path, "w")
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            return lock_file
        except Exception:
            return None
    except (PermissionError, OSError):
        return None
