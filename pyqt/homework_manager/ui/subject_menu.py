"""
科目管理窗口

从原 src/menu.py 迁移
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QInputDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from homework_manager.config.settings import Settings
from homework_manager.models.data_store import DataStore


class SubjectMenu(QDialog):
    """科目管理对话框"""

    def __init__(self, settings: Settings, data_store: DataStore, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.data_store = data_store
        self._modified = False

        self._init_ui()
        self._refresh_list()

    def _init_ui(self) -> None:
        """构建 UI"""
        self.setWindowTitle("科目管理")
        self.setMinimumSize(360, 480)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 科目列表
        self._list_widget = QListWidget()
        layout.addWidget(self._list_widget)

        # 按钮行 1：增删改
        btn_layout_1 = QHBoxLayout()
        buttons_1 = [
            ("添加", self._add_subject),
            ("重命名", self._rename_subject),
            ("删除", self._delete_subject),
        ]
        for text, slot in buttons_1:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            btn_layout_1.addWidget(btn)
        layout.addLayout(btn_layout_1)

        # 按钮行 2：排序
        btn_layout_2 = QHBoxLayout()
        buttons_2 = [
            ("上移", self._move_up),
            ("下移", self._move_down),
        ]
        for text, slot in buttons_2:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            btn_layout_2.addWidget(btn)
        btn_layout_2.addStretch()
        layout.addLayout(btn_layout_2)

        # 确定按钮
        self._ok_btn = QPushButton("确定")
        self._ok_btn.clicked.connect(self.accept)
        layout.addWidget(self._ok_btn)

    # ==================== 列表刷新 ====================

    def _refresh_list(self) -> None:
        """刷新科目列表"""
        self._list_widget.clear()
        for name in self.settings.get_subject_names():
            self._list_widget.addItem(name)

    # ==================== 操作 ====================

    def _add_subject(self) -> None:
        """添加科目"""
        name, ok = QInputDialog.getText(self, "添加科目", "科目名称:")
        if not ok or not name.strip():
            return
        code, ok2 = QInputDialog.getText(self, "科目代码", "科目代码 (如 C, M, E):")
        if not ok2 or not code.strip():
            return

        self.settings.add_subject(name.strip(), code.strip())
        self.data_store.add_subject_key(code.strip())
        self._modified = True
        self._refresh_list()

    def _rename_subject(self) -> None:
        """重命名科目"""
        current = self._list_widget.currentItem()
        if current is None:
            return
        old_name = current.text()
        old_code = self.settings.subjects.get(old_name, "")

        new_name, ok = QInputDialog.getText(
            self, "重命名科目", "新名称:", text=old_name
        )
        if not ok or not new_name.strip():
            return
        new_code, ok2 = QInputDialog.getText(
            self, "科目代码", "新代码 (留空保持不变):", text=old_code
        )
        if not ok2:
            return

        code = new_code.strip() if new_code.strip() else None
        self.settings.rename_subject(old_name, new_name.strip(), code)
        self._modified = True
        self._refresh_list()

    def _delete_subject(self) -> None:
        """删除科目"""
        if self._list_widget.count() <= 1:
            QMessageBox.warning(self, "无法删除", "至少保留一个科目")
            return

        current = self._list_widget.currentItem()
        if current is None:
            return
        name = current.text()
        code = self.settings.subjects.get(name, "")

        count = len(self.data_store.get_subject_homeworks(code))
        msg = f"确定删除科目「{name}」吗？\n该科目下有 {count} 条作业将被一同删除。"
        reply = QMessageBox.question(
            self,
            "确认删除",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.settings.remove_subject(name)
        self.data_store.remove_subject_key(code)
        self._modified = True
        self._refresh_list()

    def _move_up(self) -> None:
        """上移科目"""
        row = self._list_widget.currentRow()
        if row <= 0:
            return
        names = self.settings.get_subject_names()
        names[row], names[row - 1] = names[row - 1], names[row]
        self.settings.reorder_subjects(names)
        self._modified = True
        self._refresh_list()
        self._list_widget.setCurrentRow(row - 1)

    def _move_down(self) -> None:
        """下移科目"""
        row = self._list_widget.currentRow()
        if row >= self._list_widget.count() - 1:
            return
        names = self.settings.get_subject_names()
        names[row], names[row + 1] = names[row + 1], names[row]
        self.settings.reorder_subjects(names)
        self._modified = True
        self._refresh_list()
        self._list_widget.setCurrentRow(row + 1)
