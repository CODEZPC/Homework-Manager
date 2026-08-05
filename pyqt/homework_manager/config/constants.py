"""
全局常量定义

从原 src/main.py 和 src/homeworkfunc.py 迁移而来
"""

# ==================== 应用信息 ====================
APP_NAME = "Homework Manager"
VERSION = "2.0.0"
VERSION_NUM = 2000000000

# ==================== 调试 ====================
DEBUG_DEFAULT = False

# ==================== 颜色 ====================
COLOR_DEFAULT = "#767F89"  # 默认灰色文字
COLOR_HIGHLIGHT = "#FFFFFF"  # 高亮白色
COLOR_WARNING = "#FFB74D"  # 警告橙色
COLOR_EXPIRED = "#EF5350"  # 过期红色
COLOR_UPCOMING = "#66BB6A"  # 即将收绿色
COLOR_BACKGROUND = "#1E1E1E"  # 背景深色

# ==================== 文件路径（相对于 app_dir） ====================
DATA_FILE = "homework.json"
SETTING_FILE = "setting.json"
LOCK_FILE = "lock/homework.lock"
UPDATE_URL = "https://codezpc.cn/Homework-Manager/update.json"

# ==================== 科目默认值 ====================
DEFAULT_SUBJECT_CODES = [
    "C",
    "M",
    "E",
    "P1",
    "H1",
    "G1",
    "PH1",
    "PH2",
    "CH2",
    "B1",
    "CH1",
    "OTH",
]
DEFAULT_SUBJECT_NAMES = [
    "语文",
    "数学",
    "英语",
    "政治 D1",
    "历史 D1",
    "地理 D1",
    "物理 D1",
    "物理 D2",
    "化学 D2",
    "生物 D1",
    "化学 D1",
    "其他",
]

# ==================== 优先级 ====================
EMPHASIZE_LEVELS = ["自动", "很低", "低", "标准", "高"]

# ==================== 时间相关 ====================
TIME_OUT = 300  # 过期判定阈值（秒）
TICK_INTERVAL = 1000  # 主循环 tick 间隔（毫秒）
ROLL_INTERVAL = 33  # Canvas 滚动动画间隔（毫秒）

# ==================== ClassIsland ====================
CLASSISLAND_URI_PREFIX = "classisland://app/api/automation"
ENABLE_CLASSISLAND_DEFAULT = True
