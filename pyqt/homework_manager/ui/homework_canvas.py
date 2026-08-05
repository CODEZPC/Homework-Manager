"""
作业 Canvas 渲染组件

从原 src/main.py 的 draw_homework / canvas_roll / upload_time_display 迁移
使用 QGraphicsView 实现作业列表渲染和横向滚动动画
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsTextItem
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QBrush, QPen

from homework_manager.config.constants import (
    COLOR_DEFAULT,
    COLOR_HIGHLIGHT,
    COLOR_WARNING,
    COLOR_EXPIRED,
    COLOR_UPCOMING,
    COLOR_BACKGROUND,
    EMPHASIZE_LEVELS,
)
from homework_manager.config.settings import Settings
from homework_manager.models.data_store import DataStore
from homework_manager.services.time_analyzer import TimeAnalyzer


class HomeworkCanvas(QGraphicsView):
    """作业画布组件"""

    def __init__(self, data_store: DataStore, settings: Settings, parent=None):
        super().__init__(parent)
        self.data_store = data_store
        self.settings = settings
        self.time_analyzer = TimeAnalyzer()

        # 场景
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # 外观
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND}; border: none;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setRenderHints(self.renderHints())

        # 滚动动画
        self._scroll_offset = 0
        self._scroll_items: list[tuple[QGraphicsTextItem, float]] = []

        # 选中状态
        self._selected: tuple[str, int, dict] | None = None

        # 字体
        self._font_main = QFont("Microsoft YaHei", 14)
        self._font_time = QFont("Microsoft YaHei", 11)

    # ==================== 数据刷新 ====================

    def refresh(self) -> None:
        """完全重建渲染"""
        self._scene.clear()
        self._scroll_items.clear()

        subjects = self.settings.subjects
        flat_list = self.data_store.get_flat_list(list(subjects.values()))

        if not flat_list:
            self._draw_empty_text()
            return

        y = 20
        line_height = 48

        for code, idx, item in flat_list:
            content = item.get("content", "")
            timestamp = item.get("timestamp", "")
            emphasize = item.get("emphasize", "标准")

            # 解析时间状态
            display_text, priority = self.time_analyzer.analyze(timestamp, emphasize)

            # 设置颜色
            color = self._get_color_for_priority(priority)

            # 左侧：作业内容
            subject_name = self._find_subject_name(code)
            full_text = f"[{subject_name}] {content}"
            text_item = QGraphicsTextItem(full_text)
            text_item.setFont(self._font_main)
            text_item.setDefaultTextColor(QColor(color))
            text_item.setPos(20, y)

            # 检查是否需要滚动
            text_width = text_item.boundingRect().width()
            view_width = self.viewport().width() - 180  # 留出右侧时间列空间
            if text_width > view_width:
                self._scroll_items.append((text_item, text_width))

            self._scene.addItem(text_item)

            # 右侧：时间状态
            time_item = QGraphicsTextItem(display_text)
            time_item.setFont(self._font_time)
            time_item.setDefaultTextColor(QColor(color))
            time_item.setPos(view_width + 20, y + 4)
            self._scene.addItem(time_item)

            # 存储数据（用于选中）
            text_item.setData(0, (code, idx, item))

            y += line_height

        self._scene.setSceneRect(0, 0, self.viewport().width(), y + 40)

    def refresh_time_display(self) -> None:
        """仅刷新时间显示列（每分钟调用）"""
        self.refresh()  # 简化实现：完全重建

    # ==================== 滚动动画 ====================

    def tick_roll(self) -> None:
        """每帧滚动动画"""
        self._scroll_offset += 2
        scroll_speed = 2

        for item, total_width in self._scroll_items:
            item_width = item.boundingRect().width()
            if item_width <= self.viewport().width() - 180:
                continue

            current_x = item.pos().x()
            new_x = current_x - scroll_speed

            # 循环滚动
            if new_x < -(total_width + 40):
                new_x = self.viewport().width() - 180

            item.setPos(new_x, item.pos().y())

    # ==================== 过期清理 ====================

    def clear_expired(self) -> None:
        """标记并返回过期作业"""
        from homework_manager.config.constants import TIME_OUT
        import time
        from datetime import datetime

        expired: list[tuple[str, int]] = []
        for code in self.data_store.all_subject_codes:
            items = self.data_store.get_subject_homeworks(code)
            for i, item in enumerate(items):
                ts = item.get("timestamp", "")
                try:
                    dt = datetime.strptime(ts, "%Y/%m/%d %H:%M")
                    if time.time() - dt.timestamp() > TIME_OUT:
                        expired.append((code, i))
                except ValueError:
                    pass

        for code, idx in sorted(expired, key=lambda x: -x[1]):
            self.data_store.delete_homework(code, idx)

    # ==================== 选中 ====================

    def get_selected(self) -> tuple[str, int, dict] | None:
        """获取当前选中项"""
        return self._selected

    # ==================== 内部方法 ====================

    def _draw_empty_text(self) -> None:
        """绘制空状态提示"""
        text = QGraphicsTextItem("暂无作业")
        text.setFont(self._font_main)
        text.setDefaultTextColor(QColor(COLOR_DEFAULT))
        w = self.viewport().width()
        h = self.viewport().height()
        tw = text.boundingRect().width()
        th = text.boundingRect().height()
        text.setPos((w - tw) / 2, (h - th) / 2)
        self._scene.addItem(text)

    def _get_color_for_priority(self, priority: int) -> str:
        """根据优先级返回颜色"""
        if priority <= 0:
            return COLOR_EXPIRED
        elif priority <= 1:
            return COLOR_DEFAULT
        elif priority <= 2:
            return COLOR_HIGHLIGHT
        elif priority <= 3:
            return COLOR_WARNING
        else:
            return COLOR_UPCOMING

    def _find_subject_name(self, code: str) -> str:
        """根据代码反查科目名称"""
        for name, c in self.settings.subjects.items():
            if c == code:
                return name
        return code
