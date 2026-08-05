"""
Homework Manager - PyQt 重构版
入口点：启动应用程序

用法：
    python main.py          # 正常启动
    python main.py --debug  # 调试模式
"""

import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from homework_manager.app import Application


def main():
    """应用程序主入口"""
    debug = "--debug" in sys.argv
    app = Application(debug=debug)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
