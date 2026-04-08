"""
Right Panel - Activity Log Module
Displays application activity log.
"""

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.theme import COLORS


class RightPanel(QWidget):
    """Activity Log Panel - displays application events."""

    logCleared = Signal()

    TYPE_INFO = "info"
    TYPE_SUCCESS = "success"
    TYPE_WARNING = "warning"
    TYPE_ERROR = "error"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = self._build_header()
        root.addWidget(header)

        container = self._build_log_area()
        root.addWidget(container)

        self._apply_styles()

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("activityHeader")
        lay = QHBoxLayout(header)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        title = QLabel("Activity")
        title.setObjectName("activityTitle")
        lay.addWidget(title)
        lay.addStretch()

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setObjectName("clearBtn")
        self._clear_btn.setFixedSize(50, 24)
        self._clear_btn.clicked.connect(self.clear)
        lay.addWidget(self._clear_btn)

        return header

    def _build_log_area(self) -> QWidget:
        container = QWidget()
        container.setObjectName("logContainer")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(12, 8, 12, 12)
        lay.setSpacing(6)

        self._log_list = QListWidget()
        self._log_list.setObjectName("logList")
        self._log_list.setAlternatingRowColors(False)
        self._log_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        lay.addWidget(self._log_list)

        return container

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            f"QWidget#activityHeader {{ background: {COLORS['surface2']}; "
            f"border-bottom: 1px solid {COLORS['border']}; }}"
            f"QLabel#activityTitle {{ color: {COLORS['text_primary']}; "
            f"font-size: 13px; font-weight: 600; }}"
            f"QPushButton#clearBtn {{ background: transparent; "
            f"color: {COLORS['text_muted']}; border: 1px solid {COLORS['border']}; "
            f"border-radius: 4px; font-size: 11px; }}"
            f"QPushButton#clearBtn:hover {{ background: {COLORS['surface3']}; "
            f"color: {COLORS['text_secondary']}; }}"
            f"QWidget#logContainer {{ background: {COLORS['bg']}; }}"
            f"QListWidget#logList {{ background: {COLORS['surface']}; "
            f"border: 1px solid {COLORS['border']}; border-radius: 6px; "
            f"outline: none; padding: 4px; }}"
            f"QListWidget::item {{ padding: 8px 10px; border-radius: 4px; "
            f"border: none; margin: 1px 0; }}"
            f"QListWidget::item:selected {{ background: transparent; }}"
        )

    def append(self, message: str, log_type: str = TYPE_INFO) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry_text = f"[{timestamp}] {message}"

        item = QListWidgetItem(entry_text)
        item.setData(Qt.ItemDataRole.UserRole, {"type": log_type, "message": message})

        colors_map = {
            self.TYPE_SUCCESS: COLORS["success"],
            self.TYPE_WARNING: COLORS["warning"],
            self.TYPE_ERROR: COLORS["error"],
            self.TYPE_INFO: COLORS["text_secondary"],
        }
        color = colors_map.get(log_type, COLORS["text_secondary"])
        item.setForeground(QColor(color))

        icons_map = {
            self.TYPE_SUCCESS: "\u2713",
            self.TYPE_WARNING: "\u26a0",
            self.TYPE_ERROR: "\u2717",
            self.TYPE_INFO: "\u25cf",
        }
        icon = icons_map.get(log_type, "\u25cf")
        item.setText(f"{icon}  {entry_text}")

        self._log_list.addItem(item)
        self._log_list.scrollToBottom()

    def info(self, message: str) -> None:
        self.append(message, self.TYPE_INFO)

    def success(self, message: str) -> None:
        self.append(message, self.TYPE_SUCCESS)

    def warning(self, message: str) -> None:
        self.append(message, self.TYPE_WARNING)

    def error(self, message: str) -> None:
        self.append(message, self.TYPE_ERROR)

    def clear(self) -> None:
        self._log_list.clear()
        self.logCleared.emit()

    def count(self) -> int:
        return self._log_list.count()

    def refresh_theme(self) -> None:
        self._apply_styles()
