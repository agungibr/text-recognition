"""
Custom Widgets Module - Clinical-Grade UI Components

Provides reusable UI widgets for the Radiology Reader application.
Designed for clarity, readability, and professional medical software appearance.
"""

import cv2
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ui.theme import COLORS


# ═══════════════════════════════════════════════════════════════════════════
#  SLIDERS
# ═══════════════════════════════════════════════════════════════════════════


class NoScrollSlider(QSlider):
    """Horizontal slider that ignores mouse wheel events."""

    def wheelEvent(self, event):
        event.ignore()


# ═══════════════════════════════════════════════════════════════════════════
#  STATUS INDICATORS
# ═══════════════════════════════════════════════════════════════════════════


class StatusBadge(QLabel):
    """Compact status badge for displaying state."""

    STATES = {
        "idle": {"color": COLORS["text_muted"], "bg": COLORS["surface2"], "icon": "○"},
        "active": {"color": COLORS["accent"], "bg": COLORS["accent_bg"], "icon": "●"},
        "success": {"color": COLORS["success"], "bg": COLORS["success_bg"], "icon": "✓"},
        "warning": {"color": COLORS["warning"], "bg": COLORS["warning_bg"], "icon": "!"},
        "error": {"color": COLORS["error"], "bg": COLORS["error_bg"], "icon": "✕"},
    }

    def __init__(self, state: str = "idle", text: str = "", parent=None):
        super().__init__(parent)
        self._state = state
        self._text = text
        self._apply_style()

    def _apply_style(self) -> None:
        cfg = self.STATES.get(self._state, self.STATES["idle"])
        display = f"{cfg['icon']}  {self._text}" if self._text else cfg["icon"]
        self.setText(display)
        self.setStyleSheet(f"""
            QLabel {{
                background: {cfg["bg"]};
                color: {cfg["color"]};
                border-radius: 10px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 500;
            }}
        """)

    def setState(self, state: str, text: str = "") -> None:
        self._state = state
        self._text = text
        self._apply_style()


# ═══════════════════════════════════════════════════════════════════════════
#  TYPOGRAPHY COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════


class SectionHeader(QLabel):
    """Section header with uppercase styling for panel titles."""

    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        self.setStyleSheet(f"""
            color: {COLORS["text_muted"]};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1px;
            padding: 4px 0;
        """)


class FieldLabel(QLabel):
    """Label for form fields - slightly muted."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            color: {COLORS["text_label"]};
            font-size: 12px;
            font-weight: 500;
        """)


class FieldValue(QLabel):
    """Value display with monospace font for data clarity."""

    def __init__(self, text: str = "—", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            color: {COLORS["text_primary"]};
            font-size: 13px;
            font-family: "Consolas", "SF Mono", monospace;
        """)


# ═══════════════════════════════════════════════════════════════════════════
#  CARD COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════


class Card(QFrame):
    """Clean card container with subtle border."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
            }}
        """)


class InfoCard(QFrame):
    """Card for displaying labeled information."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title = title

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        self._title_label = QLabel(title.upper())
        self._value_label = QLabel("—")

        layout.addWidget(self._title_label)
        layout.addWidget(self._value_label)

        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS["surface2"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
            }}
        """)
        self._title_label.setStyleSheet(f"""
            color: {COLORS["text_muted"]};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1px;
            background: transparent;
            border: none;
        """)
        self._value_label.setStyleSheet(f"""
            color: {COLORS["text_primary"]};
            font-size: 16px;
            font-weight: 600;
            font-family: "Consolas", monospace;
            background: transparent;
            border: none;
        """)

    def setValue(self, value) -> None:
        self._value_label.setText(str(value) if value else "—")


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION GROUP - Panel Section Container
# ═══════════════════════════════════════════════════════════════════════════


class SectionGroup(QFrame):
    """Clean section container with header bar."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title_text = title

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {COLORS["text_primary"]};
            font-size: 12px;
            font-weight: 600;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        header.setStyleSheet(f"""
            background: {COLORS["surface2"]};
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        """)
        outer.addWidget(header)

        # Content area
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(12, 10, 12, 10)
        self._content_layout.setSpacing(8)

        self._content.setStyleSheet("background: transparent;")
        outer.addWidget(self._content)

        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
            }}
        """)

    def inner_layout(self) -> QVBoxLayout:
        return self._content_layout


# ═══════════════════════════════════════════════════════════════════════════
#  IMAGE VIEWER
# ═══════════════════════════════════════════════════════════════════════════


class ImageViewer(QLabel):
    """Clean image display widget with zoom support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 240)
        self._pixmap = None
        self._zoom = 1.0
        self._show_placeholder()

    def setImage(self, source) -> None:
        """Set image from file path or numpy array."""
        try:
            if isinstance(source, str):
                if not source:
                    self._show_placeholder("No image")
                    return
                pix = QPixmap(source)
                if pix.isNull():
                    raise ValueError("Cannot load image")
            else:
                arr = source
                if len(arr.shape) == 2:
                    arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2RGB)
                elif arr.shape[2] == 4:
                    arr = cv2.cvtColor(arr, cv2.COLOR_BGRA2RGB)
                else:
                    arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)

                h, w, ch = arr.shape
                qimg = QImage(arr.data, w, h, ch * w, QImage.Format.Format_RGB888)
                pix = QPixmap.fromImage(qimg)

            self._pixmap = pix
            self._apply_image_style()
            self._refresh()

        except Exception as e:
            self._pixmap = None
            self._show_placeholder(f"Error: {e}")

    def clear(self) -> None:
        self._pixmap = None
        self._show_placeholder()

    def setZoomLevel(self, zoom: float) -> None:
        self._zoom = max(0.1, min(zoom, 5.0))
        self._refresh()

    def getZoomLevel(self) -> float:
        return self._zoom

    def _apply_image_style(self) -> None:
        self.setStyleSheet(f"""
            background: {COLORS["bg"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 4px;
        """)

    def _show_placeholder(self, text: str = "No image loaded") -> None:
        self._pixmap = None
        self.setPixmap(QPixmap())
        self.setText(text)
        self.setStyleSheet(f"""
            background: {COLORS["surface"]};
            border: 1px dashed {COLORS["border_light"]};
            border-radius: 6px;
            color: {COLORS["text_muted"]};
            font-size: 13px;
        """)

    def _refresh(self) -> None:
        if self._pixmap and not self._pixmap.isNull():
            scaled_size = self._pixmap.size() * self._zoom
            scaled = self._pixmap.scaled(
                scaled_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh()

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y()
        if delta > 0:
            self.setZoomLevel(self._zoom * 1.1)
        else:
            self.setZoomLevel(self._zoom / 1.1)


# ═══════════════════════════════════════════════════════════════════════════
#  INFO ROW - Label + Value Pair
# ═══════════════════════════════════════════════════════════════════════════


class InfoRow(QWidget):
    """Horizontal label + value row for clean data display."""

    def __init__(self, label: str, value: str = "—", parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        self._label = QLabel(label)
        self._label.setStyleSheet(f"""
            color: {COLORS["text_label"]};
            font-size: 12px;
        """)
        self._label.setMinimumWidth(80)

        self._value = QLabel(value)
        self._value.setStyleSheet(f"""
            color: {COLORS["text_primary"]};
            font-size: 12px;
            font-family: "Consolas", monospace;
        """)

        layout.addWidget(self._label)
        layout.addStretch()
        layout.addWidget(self._value)

    def setValue(self, value: str) -> None:
        self._value.setText(value if value else "—")

    def getValue(self) -> str:
        return self._value.text()


# ═══════════════════════════════════════════════════════════════════════════
#  DIVIDER
# ═══════════════════════════════════════════════════════════════════════════


class Divider(QFrame):
    """Subtle horizontal divider line."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {COLORS['border']};")
