"""
作业管理器 - 全局配置常量

所有可配置的颜色、尺寸、路径、版本信息等均集中于此。
"""

import os
import sys

# ──────────────── 版本信息 ────────────────
VERSION = "1.6.2.15"
VERSION_NUM = 1006002015

# ──────────────── 路径配置 ────────────────
def _app_dir() -> str:
    """获取应用程序所在目录（兼容 PyInstaller 打包）。
    对于开发模式，数据文件位于上级目录（src/）。
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    # 开发模式：当前文件在 src/new/ 下，数据文件在 src/ 下
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APP_DIR = _app_dir()
DATA_FILE = os.path.join(APP_DIR, "homework.json")
SETTING_FILE = os.path.join(APP_DIR, "setting.json")
LOCK_PATH = os.path.join(APP_DIR, "lock", "homework.lock")
UPDATE_DIR = os.path.join(APP_DIR, "update")
UPDATE_EXE_PATH = os.path.join(UPDATE_DIR, "main.exe")
CURRENT_EXE_PATH = os.path.join(APP_DIR, "main.exe")

# ──────────────── 颜色主题 ────────────────
COLOR_BG_MAIN = "#23272E"
COLOR_BG_DARK = "#1C1F25"
COLOR_BG_SELECT = "#2E333C"
COLOR_FG_PRIMARY = "#C8C8C8"
COLOR_FG_DIM = "#767F89"
COLOR_FG_ACCENT = "#005EFF"
COLOR_FG_WHITE = "#FFFFFF"
COLOR_FG_BLACK = "#000000"
COLOR_FG_GREEN = "#1AFF00"
COLOR_FG_RED = "#FF0000"
COLOR_FG_YELLOW = "#FFFF00"
COLOR_BG_WARN = "#FFFF00"
COLOR_BG_ERROR = "#FF0000"
COLOR_BG_INFO = "#005EFF"
COLOR_BG_SUCCESS = "#00FF40"
COLOR_BG_TIME_HIGH = "#C8C8C8"
COLOR_BG_TIME_MED = "#666666"

# 兼容旧代码别名
COLOR = COLOR_FG_DIM

# ──────────────── 默认科目配置 ────────────────
DEFAULT_SUBJECT_CODES = [
    "C", "M", "E", "P1", "H1", "G1",
    "PH1", "PH2", "CH1", "CH2", "B1", "OTH",
]

DEFAULT_SUBJECT_DISPLAY_NAMES = [
    "语文 ", "数学 ", "英语 ",
    "政治 D1", "历史 D1", "地理 D1",
    "物理 D1", "物理 D2", "化学 D1", "化学 D2",
    "生物 D1", "其他",
]

EMPHASIZE_LEVELS = ["自动", "很低", "低", "标准", "高"]

# ──────────────── 时间与超时 ────────────────
TIME_OUT = 300  # 超时时间（秒），过期作业判定阈值

# ──────────────── UI 布局常量 ────────────────
UI_SIDE_MARGIN_LEFT = 45
UI_SIDE_MARGIN_RIGHT = 17
UI_TIME_DISPLAY_WIDTH = 205
UI_CANVAS_TOP = 40
UI_CANVAS_BOTTOM_MARGIN = 60
UI_INFO_BAR_BOTTOM = 20
UI_INFO_BAR_LEFT = 10
UI_ITEM_SPACING_NORMAL = 35
UI_ITEM_SPACING_COMPACT = 30
UI_ITEM_SPACING_THRESHOLD = 10

# Canvas 滚动参数
CANVAS_SCROLL_DX = 2
CANVAS_SCROLL_INTERVAL = 33  # ms，约 30fps

# 按钮冷却时间（1/10 秒为单位）
BUTTON_COOLDOWN_TICKS = 5

# Tick 行为参数
TICK_HIDE_BUTTONS = 3       # 超过此 tick 隐藏按钮
TICK_ANTI_SLEEP = 300       # 超过此 tick 触发防屏保
TICK_ANTI_SLEEP_RESET = 3   # 防屏保后重置 tick

# 防屏保鼠标目标位置
ANTI_SLEEP_MOUSE_X = 400
ANTI_SLEEP_MOUSE_Y = 1200

# ──────────────── ClassIsland ────────────────
ENABLE_CLASSISLAND = getattr(sys, "frozen", False)

# ──────────────── 更新服务器 ────────────────
UPDATE_URL = "https://codezpc.cn/Homework-Manager/update.json"
DOWNLOAD_URL = "https://codezpc.cn/Homework-Manager/main.exe"

# ──────────────── 数据版本 ────────────────
DATA_VERSION_MAX = 2

# ──────────────── 字体 ────────────────
FONT_DEFAULT = ("JetBrains Mono", 18)
FONT_BUTTON = ("汉仪文黑-85W", 14)
FONT_TITLE = ("HYWenHei-85W", 24)
FONT_HOMEWORK = ("HYWenHei-85W", 18)
FONT_TIME = ("HYWenHei-85W", 16)
FONT_DIALOG = ("HYWenHei-85W", 16)
FONT_INFO = ("JetBrains Mono", 9)
FONT_LISTBOX = ("JetBrains Mono", 12)
FONT_HELP = ("HYWenHei-85W", 12)
FONT_SIDE_BUTTON = ("JetBrains Mono", 8)

# ──────────────── 调试 ────────────────
DEBUG = False
