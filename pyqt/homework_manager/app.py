"""
Application 启动/引导类

负责：
- 进程锁检查
- 配置初始化
- 数据迁移
- 创建主窗口并启动事件循环
"""

import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from homework_manager.config.constants import (
    APP_NAME,
    VERSION,
    VERSION_NUM,
    DEBUG_DEFAULT,
    DATA_FILE,
    SETTING_FILE,
    LOCK_FILE,
)
from homework_manager.config.settings import Settings
from homework_manager.services.lock_manager import LockManager
from homework_manager.data.migration import DataMigration
from homework_manager.ui.main_window import MainWindow
from homework_manager.utils.platform import get_app_dir


class Application:
    """应用程序主类"""

    def __init__(self, debug: bool = DEBUG_DEFAULT):
        self.debug = debug
        self.app_dir = get_app_dir()
        self.qt_app: QApplication | None = None
        self.main_window: MainWindow | None = None
        self.settings: Settings | None = None
        self.lock_manager = LockManager()

    def run(self) -> int:
        """启动应用程序，返回退出码"""
        # 1. 获取进程锁（防止多开）
        if not self.lock_manager.acquire():
            print("程序已在运行中", file=sys.stderr)
            return 1

        # 2. 初始化配置
        self.settings = Settings()
        self.settings.ensure_defaults()

        # 3. 数据版本迁移
        migration = DataMigration()
        migration.run()

        # 4. 创建 QApplication
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName(APP_NAME)
        self.qt_app.setApplicationVersion(VERSION)

        # 设置图标
        icon_path = os.path.join(self.app_dir, "resources", "HM.ico")
        if os.path.exists(icon_path):
            self.qt_app.setWindowIcon(QIcon(icon_path))

        # 5. 创建并显示主窗口
        self.main_window = MainWindow(settings=self.settings, debug=self.debug)
        self.main_window.show()

        # 6. 进入事件循环
        exit_code = self.qt_app.exec()

        # 7. 清理
        self.lock_manager.release()

        return exit_code
