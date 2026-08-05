"""
新建/编辑作业对话框

从原 src/main.py 的 new_homework / edit_homework 迁移
使用 QDialog 实现
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QDateTimeEdit,
    QPushButton,
    QDialogButtonBox,
    QLabel,
)
from PyQt6.QtCore import Qt, QDateTime

from homework_manager.config.constants import EMPHASIZE_LEVELS
from homework_manager.config.settings import Settings


class HomeworkDialog(QDialog):
    """作业编辑对话框"""

    def __init__(
        self,
        settings: Settings,
        parent=None,
        edit_data: tuple[str, int, dict] | None = None,
    ):
        super().__init__(parent)
        self.settings = settings
        self.edit_data = edit_data
        self.is_edit = edit_data is not None

        self._result_data: dict | None = None

        self._init_ui()
        if self.is_edit:
            self._load_edit_data()

    def _init_ui(self) -> None:
        """构建对话框 UI"""
        title = "编辑作业" if self.is_edit else "新建作业"
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 表单
        form = QFormLayout()

        # 科目选择
        self._subject_combo = QComboBox()
        for name in self.settings.get_subject_names():
            self._subject_combo.addItem(name)
        form.addRow("科目:", self._subject_combo)

        # 作业内容
        self._content_edit = QLineEdit()
        self._content_edit.setPlaceholderText("输入作业内容...")
        form.addRow("内容:", self._content_edit)

        # 截止时间
        self._time_edit = QDateTimeEdit()
        self._time_edit.setDisplayFormat("yyyy/MM/dd HH:mm")
        self._time_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self._time_edit.setCalendarPopup(True)
        form.addRow("截止时间:", self._time_edit)

        # 优先级
        self._emphasize_combo = QComboBox()
        for level in EMPHASIZE_LEVELS:
            self._emphasize_combo.addItem(level)
        self._emphasize_combo.setCurrentText("标准")
        form.addRow("优先级:", self._emphasize_combo)

        layout.addLayout(form)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_edit_data(self) -> None:
        """加载编辑数据到表单"""
        if self.edit_data is None:
            return
        code, idx, item = self.edit_data

        # 科目
        for name, c in self.settings.subjects.items():
            if c == code:
                self._subject_combo.setCurrentText(name)
                break

        # 内容
        self._content_edit.setText(item.get("content", ""))

        # 时间
        from PyQt6.QtCore import QDateTime

        ts = item.get("timestamp", "")
        try:
            dt = QDateTime.fromString(ts, "yyyy/MM/dd HH:mm")
            if dt.isValid():
                self._time_edit.setDateTime(dt)
        except Exception:
            pass

        # 优先级
        emphasize = item.get("emphasize", "标准")
        self._emphasize_combo.setCurrentText(emphasize)

    def _on_accept(self) -> None:
        """确认提交"""
        content = self._content_edit.text().strip()
        if not content:
            return  # 不允许空内容

        subject_name = self._subject_combo.currentText()
        subject_code = self.settings.subjects.get(subject_name, "OTH")

        self._result_data = {
            "subject_code": subject_code,
            "homework": {
                "content": content,
                "timestamp": self._time_edit.dateTime().toString("yyyy/MM/dd HH:mm"),
                "emphasize": self._emphasize_combo.currentText(),
            },
        }
        self.accept()

    def get_homework_data(self) -> dict | None:
        """获取提交的作业数据"""
        return self._result_data
