"""
Custom Widgets Module

Provides reusable UI widgets for the Radiology Reader application.
Optimized for PySide6 compatibility.
"""

import cv2
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStyleOption,
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
#  BADGES & LABELS
# ═══════════════════════════════════════════════════════════════════════════


class Badge(QLabel):
    """Status badge with colored indicator."""

    def __init__(self, state: str = "idle", text: str = "", parent=None):
        super().__init__(parent)
        self._state = state
        self._text = text
        self._apply_style()

    @staticmethod
    def _style_for(state: str) -> tuple:
        styles = {
            "ok": (COLORS["success"], COLORS["success_dim"], "●"),
            "idle": (COLORS["text_muted"], COLORS["surface3"], "○"),
            "busy": (COLORS["warning"], COLORS["warning_dim"], "◌"),
            "error": (COLORS["error"], COLORS["error_dim"], "✕"),
        }
        return styles.get(state, styles["idle"])

    def _apply_style(self) -> None:
        fg, bg, icon = self._style_for(self._state)
        label = f"{icon}  {self._text}" if self._text else icon
        self.setText(label)
        self.setStyleSheet(f"""
            QLabel {{
                background: {bg};
                color: {fg};
                border: 1px solid {fg}40;
                border-radius: 10px;
                padding: 2px 10px 2px 8px;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }}
        """)

    def setState(self, state: str, text: str = "") -> None:
        """Update badge state and optional text."""
        self._state = state
        self._text = text
        self._apply_style()

    def refresh_theme(self) -> None:
        """Reapply theme styling."""
        self._apply_style()


class SectionLabel(QLabel):
    """Section header label with uppercase styling."""

    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            color: {COLORS["text_muted"]};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 2px;
            padding: 8px 0 4px 0;
        """)

    def refresh_theme(self) -> None:
        self._apply_style()


class ValueLabel(QLabel):
    """Value display label with monospace font."""

    def __init__(self, text: str = "—", parent=None):
        super().__init__(text, parent)
        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            color: {COLORS["text_primary"]};
            font-size: 13px;
            font-family: "Consolas", monospace;
        """)

    def refresh_theme(self) -> None:
        self._apply_style()


class MetricCard(QFrame):
    """Metric display card with label and large value."""

    def __init__(self, label: str, value: str = "—", parent=None):
        super().__init__(parent)
        self._label_text = label.upper()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(2)

        self._lbl = QLabel(self._label_text, self)
        self._val = QLabel(value, self)

        lay.addWidget(self._lbl)
        lay.addWidget(self._val)
        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS["surface2"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
                padding: 2px;
            }}
        """)
        self._lbl.setStyleSheet(
            f"color:{COLORS['text_muted']};"
            f"font-size:10px;font-weight:700;letter-spacing:1.5px;"
            f"background:transparent;border:none;"
        )
        self._val.setStyleSheet(
            f"color:{COLORS['text_primary']};"
            f"font-size:18px;font-weight:600;"
            f"font-family:'Consolas',monospace;"
            f"background:transparent;border:none;"
        )

    def setValue(self, v) -> None:
        """Update the displayed value."""
        self._val.setText(str(v))

    def refresh_theme(self) -> None:
        self._apply_style()


# ═══════════════════════════════════════════════════════════════════════════
#  LAYOUT HELPERS
# ═══════════════════════════════════════════════════════════════════════════


class Divider(QFrame):
    """Horizontal divider line."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("divider")
        self.setFrameShape(QFrame.Shape.HLine)


class SectionGroup(QFrame):
    """Collapsible section group with title bar."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title_text = title.upper()
        self.setObjectName("sectionGroup")
        self.setFrameShape(QFrame.Shape.NoFrame)

        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(0, 0, 0, 0)
        self._outer_layout.setSpacing(0)

        self._title_bar = QWidget(self)
        self._title_bar.setObjectName("sgTitleBar")

        self._title_bar_layout = QHBoxLayout(self._title_bar)
        self._title_bar_layout.setContentsMargins(12, 7, 12, 7)
        self._title_bar_layout.setSpacing(0)

        self._title_label = QLabel(self._title_text, self._title_bar)
        self._title_bar_layout.addWidget(self._title_label)
        self._outer_layout.addWidget(self._title_bar)

        self._content_widget = QWidget(self)
        self._content_widget.setObjectName("sgContent")

        self._inner_layout = QVBoxLayout(self._content_widget)
        self._inner_layout.setContentsMargins(10, 10, 10, 10)
        self._inner_layout.setSpacing(8)

        self._outer_layout.addWidget(self._content_widget)

        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            QFrame#sectionGroup {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
            }}
        """)
        self._title_bar.setStyleSheet(f"""
            QWidget#sgTitleBar {{
                background: {COLORS["surface2"]};
                border-radius: 5px 5px 0px 0px;
                border-bottom: 1px solid {COLORS["border"]};
            }}
        """)
        self._title_label.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                border: none;
                color: {COLORS["text_muted"]};
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1.5px;
            }}
        """)
        self._content_widget.setStyleSheet("""
            QWidget#sgContent {
                background: transparent;
                border: none;
            }
        """)

    def inner_layout(self) -> QVBoxLayout:
        """Return the content layout for adding child widgets."""
        return self._inner_layout

    def refresh_theme(self) -> None:
        self._apply_style()


# ═══════════════════════════════════════════════════════════════════════════
#  IMAGE VIEWER
# ═══════════════════════════════════════════════════════════════════════════


class ImageViewer(QLabel):
    """Image display widget with zoom and pan support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 240)
        self._pix = None
        self._zoom_level = 1.0
        self._show_placeholder()

    def setImage(self, path_or_array) -> None:
        """Set image from file path or numpy array."""
        try:
            if isinstance(path_or_array, str):
                if not path_or_array:
                    self._show_placeholder("No image")
                    return
                pix = QPixmap(path_or_array)
                if pix.isNull():
                    raise ValueError(f"Cannot load image: {path_or_array}")
            else:
                arr = path_or_array
                if len(arr.shape) == 2:
                    arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2RGB)
                elif arr.shape[2] == 4:
                    arr = cv2.cvtColor(arr, cv2.COLOR_BGRA2RGB)
                else:
                    arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)

                h, w, c = arr.shape
                qimg = QImage(arr.data, w, h, c * w, QImage.Format.Format_RGB888)
                pix = QPixmap.fromImage(qimg)

            self._pix = pix
            self._apply_image_style()
            self._refresh()

        except Exception as exc:
            self._pix = None
            self._show_placeholder(f"Error: {exc}")

    def clear(self) -> None:
        """Clear the displayed image."""
        self._pix = None
        self._show_placeholder()

    def setZoomLevel(self, zoom: float) -> None:
        """Set zoom level (1.0 = 100%)."""
        self._zoom_level = max(0.1, min(zoom, 5.0))
        self._refresh()

    def getZoomLevel(self) -> float:
        """Get current zoom level."""
        return self._zoom_level

    def refresh_theme(self) -> None:
        """Refresh theme styling."""
        if self._pix and not self._pix.isNull():
            self._apply_image_style()
        else:
            self._apply_placeholder_style()

    def _apply_image_style(self) -> None:
        self.setStyleSheet(f"""
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 6px;
        """)

    def _apply_placeholder_style(self) -> None:
        self.setStyleSheet(f"""
            background: {COLORS["surface"]};
            border: 2px dashed {COLORS["border_active"]};
            border-radius: 6px;
            color: {COLORS["text_muted"]};
            font-size: 12px;
            letter-spacing: 1px;
        """)

    def _show_placeholder(self, text: str = "No image selected") -> None:
        self._pix = None
        self.setPixmap(QPixmap())
        self.setText(text)
        self._apply_placeholder_style()

    def _refresh(self) -> None:
        if self._pix and not self._pix.isNull():
            scaled_size = self._pix.size() * self._zoom_level
            scaled = self._pix.scaled(
                scaled_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh()

    def wheelEvent(self, event) -> None:
        """Handle mouse wheel for zoom."""
        delta = event.angleDelta().y()
        if delta > 0:
            self.setZoomLevel(self._zoom_level * 1.1)
        else:
            self.setZoomLevel(self._zoom_level / 1.1)


# ═══════════════════════════════════════════════════════════════════════════
#  INFO DISPLAY WIDGETS
# ═══════════════════════════════════════════════════════════════════════════


class InfoRow(QWidget):
    """Label + value row for displaying information."""

    def __init__(self, label: str, value: str = "—", parent=None):
        super().__init__(parent)
        self._label_text = label

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(8)

        self._lbl = QLabel(label)
        self._val = QLabel(value)

        self._lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        lay.addWidget(self._lbl)
        lay.addStretch()
        lay.addWidget(self._val)

        self._apply_style()

    def _apply_style(self) -> None:
        self._lbl.setStyleSheet(f"""
            color: {COLORS["text_secondary"]};
            font-size: 12px;
        """)
        self._val.setStyleSheet(f"""
            color: {COLORS["text_primary"]};
            font-size: 12px;
            font-family: "Consolas", monospace;
        """)

    def setValue(self, value: str) -> None:
        """Update the value."""
        self._val.setText(value)

    def getValue(self) -> str:
        """Get current value."""
        return self._val.text()


class StatusIndicator(QLabel):
    """Status indicator with colored dot."""

    STATUS_COLORS = {
        "success": (COLORS["success"], "●"),
        "error": (COLORS["error"], "✕"),
        "warning": (COLORS["warning"], "⚠"),
        "info": (COLORS["accent"], "ℹ"),
        "idle": (COLORS["text_muted"], "○"),
    }

    def __init__(self, status: str = "idle", text: str = "", parent=None):
        super().__init__(parent)
        self._status = status
        self.setText(text)
        self._apply_style()

    def _apply_style(self) -> None:
        color, icon = self.STATUS_COLORS.get(self._status, self.STATUS_COLORS["idle"])
        self.setStyleSheet(f"""
            color: {color};
            font-size: 12px;
        """)

    def setStatus(self, status: str, text: str = "") -> None:
        """Update status and optional text."""
        self._status = status
        if text:
            self.setText(text)
        self._apply_style()

    def refresh_theme(self) -> None:
        self._apply_style()
