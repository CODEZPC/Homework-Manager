"""
主窗口 - 全屏无边框作业管理界面

从原 src/main.py 的 HomeworkTool 类迁移，改为 PyQt6 实现

核心功能：
- 全屏无边框窗口
- 顶部按钮栏（新建、编辑、删除、清理、科目、帮助、退出）
- Canvas 作业列表渲染（带横向滚动动画）
- 右侧时间状态列
- 底部信息栏（版本、时间、作业数、负载、更新状态）
- 鼠标移动显示/隐藏工具栏
- 自动防锁屏
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QGraphicsView,
    QGraphicsScene,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QFont

from homework_manager.config.constants import (
    APP_NAME,
    VERSION,
    COLOR_BACKGROUND,
    COLOR_DEFAULT,
    TICK_INTERVAL,
    ROLL_INTERVAL,
)
from homework_manager.config.settings import Settings
from homework_manager.models.data_store import DataStore
from homework_manager.services.time_analyzer import TimeAnalyzer
from homework_manager.services.classisland import ClassIsland
from homework_manager.services.updater import Updater, UpdateStatus
from homework_manager.ui.homework_canvas import HomeworkCanvas
from homework_manager.ui.homework_dialog import HomeworkDialog
from homework_manager.ui.subject_menu import SubjectMenu
from homework_manager.ui.help_panel import HelpPanel
from homework_manager.ui.widgets import CooldownButton
from homework_manager.utils.performance import PerformanceMonitor


class MainWindow(QMainWindow):
    """主窗口"""

    # 信号
    data_changed = pyqtSignal()

    def __init__(self, settings: Settings, debug: bool = False):
        super().__init__()
        self.settings = settings
        self.debug = debug

        # 核心服务
        self.data_store = DataStore()
        self.time_analyzer = TimeAnalyzer()
        self.classisland = ClassIsland()
        self.updater = Updater()
        self.perf_monitor = PerformanceMonitor()

        # 状态
        self._tick_count = 0
        self._mouse_idle_seconds = 0
        self._buttons_visible = True

        # 初始化
        self._init_ui()
        self._init_timers()
        self._load_data()
        self._start_update_check()

        # ClassIsland 通知
        self.classisland.notify_start()

    # ==================== UI 初始化 ====================

    def _init_ui(self) -> None:
        """构建界面"""
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.showFullScreen()
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        # 中央组件
        central = QWidget()
        self.setCentralWidget(central)
        self._main_layout = QVBoxLayout(central)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # 顶部按钮栏
        self._create_top_bar()
        # 作业画布区域
        self._create_canvas_area()
        # 底部信息栏
        self._create_bottom_bar()

    def _create_top_bar(self) -> None:
        """创建顶部工具栏"""
        self._top_bar = QFrame()
        self._top_bar.setFixedHeight(48)
        self._top_bar.setStyleSheet("background-color: rgba(30,30,30,0.9);")
        self._top_bar.setMouseTracking(True)

        layout = QHBoxLayout(self._top_bar)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(8)

        # 左侧按钮组
        buttons = [
            ("新建作业", self._on_new_homework),
            ("编辑作业", self._on_edit_homework),
            ("删除作业", self._on_delete_homework),
            ("清理过期", self._on_clear_expired),
        ]
        for text, slot in buttons:
            btn = CooldownButton(text)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        layout.addStretch()

        # 右侧按钮组
        buttons_right = [
            ("科目管理", self._on_subject_menu),
            ("帮助", self._on_help),
            ("退出", self._on_exit),
        ]
        for text, slot in buttons_right:
            btn = CooldownButton(text)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        self._main_layout.addWidget(self._top_bar)

    def _create_canvas_area(self) -> None:
        """创建作业渲染区域"""
        self.canvas = HomeworkCanvas(self.data_store, self.settings)
        self._main_layout.addWidget(self.canvas, stretch=1)

    def _create_bottom_bar(self) -> None:
        """创建底部信息栏"""
        self._bottom_bar = QLabel()
        self._bottom_bar.setFixedHeight(24)
        self._bottom_bar.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._bottom_bar.setStyleSheet(
            f"color: {COLOR_DEFAULT}; padding: 0 12px; font-size: 11px;"
        )
        self._bottom_bar.setMouseTracking(True)
        self._bottom_bar.mousePressEvent = self._on_bottom_click
        self._main_layout.addWidget(self._bottom_bar)

    # ==================== 定时器 ====================

    def _init_timers(self) -> None:
        """初始化定时器"""
        # 主 tick 定时器
        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._on_tick)
        self._tick_timer.start(TICK_INTERVAL)

        # 滚动动画定时器
        self._roll_timer = QTimer(self)
        self._roll_timer.timeout.connect(self._on_roll)
        self._roll_timer.start(ROLL_INTERVAL)

        # 信息刷新定时器
        self._info_timer = QTimer(self)
        self._info_timer.timeout.connect(self._refresh_info)
        self._info_timer.start(ROLL_INTERVAL)

    # ==================== 数据加载 ====================

    def _load_data(self) -> None:
        """加载作业数据并渲染"""
        self.data_store.load()
        self.canvas.refresh()

    # ==================== 更新检查 ====================

    def _start_update_check(self) -> None:
        """启动后台更新检查"""
        self.updater.status_changed = self._on_update_status_changed
        self.updater.check()

    def _on_update_status_changed(self, status: UpdateStatus) -> None:
        """更新状态变化回调"""
        self._refresh_info()

    # ==================== 定时回调 ====================

    def _on_tick(self) -> None:
        """每秒 tick"""
        self._tick_count += 1
        self._mouse_idle_seconds += 1

        # 3秒后隐藏按钮
        if self._mouse_idle_seconds >= 3 and self._buttons_visible:
            self._top_bar.hide()
            self._buttons_visible = False

        # 每分钟刷新时间显示
        if self._tick_count % 60 == 0:
            self.canvas.refresh_time_display()

        # 5分钟防锁屏
        if self._tick_count % 300 == 0:
            self.perf_monitor.simulate_activity()

    def _on_roll(self) -> None:
        """Canvas 横向滚动动画"""
        self.canvas.tick_roll()

    def _refresh_info(self) -> None:
        """刷新底部信息栏"""
        total = self.data_store.get_total_count()
        load = self.perf_monitor.calculate_load(self.data_store)
        update_str = self._get_update_status_text()

        info = (
            f"HM v{VERSION}  |  "
            f"作业: {total}  |  "
            f"负载: {load:.1f}  |  "
            f"Tick: {self._tick_count}"
        )
        if update_str:
            info += f"  |  {update_str}"
        self._bottom_bar.setText(info)

    def _get_update_status_text(self) -> str:
        """获取更新状态文本"""
        status_map = {
            UpdateStatus.CONNECTING: "检查更新中...",
            UpdateStatus.NEEDED: f"有新版本: {self.updater.remote_version_name} (点击下载)",
            UpdateStatus.FAILED: "更新检查失败 (点击重试)",
            UpdateStatus.DOWNLOADING: f"下载中... {self.updater.download_progress:.0%}",
            UpdateStatus.COMPLETED: "下载完成 (点击重启)",
            UpdateStatus.LATEST: "已是最新",
        }
        return status_map.get(self.updater.status, "")

    # ==================== 鼠标事件 ====================

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """鼠标移动：重置空闲计时、显示工具栏"""
        self._mouse_idle_seconds = 0
        if not self._buttons_visible:
            self._top_bar.show()
            self._buttons_visible = True

    # ==================== 按钮事件 ====================

    def _on_new_homework(self) -> None:
        """新建作业"""
        dialog = HomeworkDialog(self.settings, parent=self)
        if dialog.exec():
            data = dialog.get_homework_data()
            self.data_store.add_homework(data["subject_code"], data["homework"])
            self.canvas.refresh()

    def _on_edit_homework(self) -> None:
        """编辑作业（需要先选中）"""
        selected = self.canvas.get_selected()
        if selected is None:
            return
        code, idx, item = selected
        dialog = HomeworkDialog(self.settings, parent=self, edit_data=(code, idx, item))
        if dialog.exec():
            data = dialog.get_homework_data()
            self.data_store.edit_homework(data["subject_code"], idx, data["homework"])
            self.canvas.refresh()

    def _on_delete_homework(self) -> None:
        """删除作业"""
        selected = self.canvas.get_selected()
        if selected is None:
            return
        code, idx, _ = selected
        self.data_store.delete_homework(code, idx)
        self.canvas.refresh()

    def _on_clear_expired(self) -> None:
        """清理所有过期作业"""
        self.canvas.clear_expired()
        self.canvas.refresh()

    def _on_subject_menu(self) -> None:
        """打开科目管理"""
        menu = SubjectMenu(self.settings, self.data_store, parent=self)
        if menu.exec():
            self.canvas.refresh()

    def _on_help(self) -> None:
        """打开帮助面板"""
        panel = HelpPanel(self.width(), self.height(), parent=self)
        panel.exec()

    def _on_exit(self) -> None:
        """退出应用"""
        self.classisland.notify_stop()
        self.updater.status_changed = None
        self.close()

    def _on_bottom_click(self, event) -> None:
        """底部信息栏点击：触发更新操作"""
        status = self.updater.status
        if status == UpdateStatus.FAILED or status == UpdateStatus.NONE:
            self.updater.check()
        elif status == UpdateStatus.NEEDED:
            self.updater.download()
        elif status == UpdateStatus.COMPLETED:
            self.updater.restart()

    # ==================== 生命周期 ====================

    def closeEvent(self, event) -> None:
        """窗口关闭事件"""
        self.classisland.notify_stop()
        super().closeEvent(event)
