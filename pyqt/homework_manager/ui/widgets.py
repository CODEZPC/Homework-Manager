"""
可复用 UI 组件

- CooldownButton: 带冷却的按钮（防止重复点击）
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QTimer

from homework_manager.config.constants import COLOR_DEFAULT, COLOR_BACKGROUND


class CooldownButton(QPushButton):
    """带冷却时间的按钮"""

    COOLDOWN_MS = 500  # 冷却时间（毫秒）

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._enabled = True
        self._cooldown_timer = QTimer(self)
        self._cooldown_timer.setSingleShot(True)
        self._cooldown_timer.timeout.connect(self._enable)

        self.setStyleSheet(f"""
            QPushButton {{
                color: {COLOR_DEFAULT};
                background: transparent;
                border: 1px solid {COLOR_DEFAULT};
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                color: white;
                border-color: white;
            }}
            QPushButton:disabled {{
                color: #555;
                border-color: #555;
            }}
        """)

    def mousePressEvent(self, event) -> None:
        if self._enabled:
            self._enabled = False
            self.setEnabled(False)
            self._cooldown_timer.start(self.COOLDOWN_MS)
            super().mousePressEvent(event)

    def _enable(self) -> None:
        self._enabled = True
        self.setEnabled(True)
