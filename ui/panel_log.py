from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
)
from PyQt6.QtGui import QColor

from ui.theme import COLORS


class LogPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(130)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(4)

        hdr = QHBoxLayout()

        lbl = QLabel("LOG")
        lbl.setStyleSheet(
            f"color:{COLORS['text_muted']};"
            f"font-size:10px;font-weight:700;letter-spacing:2px;"
        )

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedSize(50, 20)
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_muted']};
                border: none;
                font-size: 11px;
            }}
            QPushButton:hover {{
                color: {COLORS['text_secondary']};
            }}
        """)
        self._clear_btn.clicked.connect(self.clear)

        hdr.addWidget(lbl)
        hdr.addStretch()
        hdr.addWidget(self._clear_btn)
        root.addLayout(hdr)

        self._log_list = QListWidget()
        self._log_list.setStyleSheet(f"""
            QListWidget {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
                font-size: 11px;
                font-family: "Consolas", monospace;
            }}
            QListWidget::item {{
                padding: 2px 8px;
                border: none;
                color: {COLORS["text_secondary"]};
            }}
        """)
        root.addWidget(self._log_list)

    def append(self, msg: str) -> None:
        ts   = datetime.now().strftime("%H:%M:%S")
        item = QListWidgetItem(f"  {ts}  {msg}")

        if any(tok in msg for tok in ("✕", "Error", "error")):
            item.setForeground(QColor(COLORS["error"]))
        elif any(tok in msg for tok in ("✔", "Done")):
            item.setForeground(QColor(COLORS["success"]))
        elif any(tok in msg for tok in ("→", "Processing")):
            item.setForeground(QColor(COLORS["accent"]))

        self._log_list.addItem(item)
        self._log_list.scrollToBottom()

    def clear(self) -> None:
        self._log_list.clear()
