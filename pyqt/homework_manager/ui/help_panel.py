"""
帮助面板

从原 src/help.py 迁移
使用 QTreeWidget 实现树形目录
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QTextEdit,
    QPushButton,
)
from PyQt6.QtCore import Qt


class HelpPanel(QDialog):
    """帮助信息面板"""

    # 帮助内容结构（与原 HELP 数据对应）
    HELP_DATA = {
        "概述": {
            "desc": "Homework Manager 是一款全屏作业管理工具，支持科目分组、时间追踪、优先级管理。",
            "children": {},
        },
        "添加与修改": {
            "desc": "点击顶部「新建作业」按钮，选择科目、输入内容、设定截止时间和优先级。\n选中作业后可点击「编辑」修改。",
            "children": {},
        },
        "删除与清理": {
            "desc": "选中作业后点击「删除」移除单条。\n点击「清理过期」批量移除已过期作业。",
            "children": {},
        },
        "科目管理": {
            "desc": "点击「科目管理」可添加、重命名、删除、排序科目。\n科目代码用于数据存储标识。",
            "children": {},
        },
        "界面布局": {
            "desc": "顶部：操作按钮栏\n中部：作业列表（Canvas 渲染）\n底部：状态信息栏",
            "children": {},
        },
        "存储与数据": {
            "desc": "作业数据存储在 homework.json 中，以科目代码为键分组。\n配置文件 setting.json 存储科目定义。",
            "children": {},
        },
        "优先级": {
            "desc": "优先级：「自动」根据时间自动计算，「很低」「低」「标准」「高」手动指定。",
            "children": {},
        },
        "ClassIsland 对接": {
            "desc": "打包版本可自动与 ClassIsland 通信，同步作业状态。",
            "children": {},
        },
        "自动更新": {
            "desc": "程序启动时自动检查更新。底部状态栏显示更新进度，点击可触发下载和安装。",
            "children": {},
        },
        "快捷键与操作": {
            "desc": "鼠标移到顶部显示工具栏，3秒无操作自动隐藏。\n全屏无边框窗口，Alt+F4 或点击退出。",
            "children": {},
        },
    }

    def __init__(self, window_width: int, window_height: int, parent=None):
        super().__init__(parent)
        self._window_width = window_width
        self._window_height = window_height

        self._init_ui()
        self._build_tree()

    def _init_ui(self) -> None:
        """构建 UI"""
        self.setWindowTitle("帮助")
        self.resize(int(self._window_width * 0.7), int(self._window_height * 0.7))
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 内容区
        content_layout = QHBoxLayout()

        # 左侧目录树
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setMaximumWidth(200)
        self._tree.currentItemChanged.connect(self._on_item_selected)
        content_layout.addWidget(self._tree)

        # 右侧详情
        self._detail = QTextEdit()
        self._detail.setReadOnly(True)
        content_layout.addWidget(self._detail, stretch=1)

        layout.addLayout(content_layout)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _build_tree(self) -> None:
        """构建帮助目录树"""
        for section, data in self.HELP_DATA.items():
            item = QTreeWidgetItem([section])
            item.setData(0, Qt.ItemDataRole.UserRole, data["desc"])
            self._tree.addTopLevelItem(item)

    def _on_item_selected(self, current: QTreeWidgetItem, _previous) -> None:
        """选中目录项时显示详情"""
        if current is None:
            return
        desc = current.data(0, Qt.ItemDataRole.UserRole)
        if desc:
            self._detail.setPlainText(desc)
