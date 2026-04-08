"""
Right Panel - Activity Log Module
Clinical-style activity timeline with clear timestamps.
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
    """Activity log panel for operational feedback."""

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

        self._log_list = QListWidget()
        self._log_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._log_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._log_list.setAlternatingRowColors(False)
        root.addWidget(self._log_list, 1)

        self._apply_styles()

    def _build_header(self) -> QWidget:
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        title = QLabel("Activity Log")
        title.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 13px; font-weight: 600;"
        )
        layout.addWidget(title)

        layout.addStretch()

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setObjectName("secondary")
        self._clear_btn.setFixedHeight(24)
        self._clear_btn.clicked.connect(self.clear)
        layout.addWidget(self._clear_btn)

        header.setStyleSheet(
            f"background: {COLORS['surface']}; border-bottom: 1px solid {COLORS['border']};"
        )
        return header

    def _apply_styles(self) -> None:
        self.setStyleSheet(f"background: {COLORS['bg']};")
        self._log_list.setStyleSheet(
            f"""
            QListWidget {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 7px 8px;
                margin: 1px 0;
                border-radius: 4px;
                border: none;
            }}
            QListWidget::item:hover {{
                background: {COLORS['surface2']};
            }}
            QListWidget::item:selected {{
                background: transparent;
            }}
            """
        )

    def append(self, message: str, log_type: str = TYPE_INFO) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        base_text = f"[{timestamp}] {message}"

        icons = {
            self.TYPE_INFO: "•",
            self.TYPE_SUCCESS: "✓",
            self.TYPE_WARNING: "!",
            self.TYPE_ERROR: "✕",
        }
        colors = {
            self.TYPE_INFO: COLORS["text_secondary"],
            self.TYPE_SUCCESS: COLORS["success"],
            self.TYPE_WARNING: COLORS["warning"],
            self.TYPE_ERROR: COLORS["error"],
        }

        item = QListWidgetItem(f"{icons.get(log_type, '•')}  {base_text}")
        item.setData(Qt.ItemDataRole.UserRole, {"type": log_type, "message": message})
        item.setForeground(QColor(colors.get(log_type, COLORS["text_secondary"])))
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
