"""
进程锁管理

通过 Windows msvcrt 文件锁防止多实例运行
从原 src/main.py 的 acquire_lock 迁移
"""

import os
import sys

from homework_manager.config.constants import LOCK_FILE
from homework_manager.utils.platform import get_app_dir


class LockManager:
    """进程锁管理器"""

    def __init__(self, lock_path: str | None = None):
        self.app_dir = get_app_dir()
        self.lock_path = lock_path or os.path.join(self.app_dir, LOCK_FILE)
        self._fd = None

    def acquire(self) -> bool:
        """
        尝试获取进程锁
        返回 True 表示获取成功，False 表示已有实例在运行
        """
        try:
            # 确保 lock 目录存在
            os.makedirs(os.path.dirname(self.lock_path), exist_ok=True)

            self._fd = os.open(self.lock_path, os.O_CREAT | os.O_RDWR)

            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(self._fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

            return True
        except (IOError, OSError):
            if self._fd is not None:
                os.close(self._fd)
                self._fd = None
            return False

    def release(self) -> None:
        """释放进程锁"""
        if self._fd is not None:
            try:
                if sys.platform == "win32":
                    import msvcrt

                    msvcrt.locking(self._fd, msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(self._fd, fcntl.LOCK_UN)
            except Exception:
                pass
            finally:
                os.close(self._fd)
                self._fd = None
