"""
ui/widgets.py
─────────────
Reusable custom Qt widgets used across all panels.

Exports:
    NoScrollSlider – QSlider subclass that ignores wheel events
    Badge          – coloured status pill (idle / busy / ok / error)
    SectionLabel   – small all-caps section header label
    ValueLabel     – monospace value display label
    MetricCard     – bordered card showing a label + large value
    Divider        – 1-px horizontal rule QFrame
    ImageViewer    – aspect-ratio-preserving image display label
    SectionGroup   – QFrame-based section container (replaces QGroupBox)

Every widget that uses inline, theme-dependent styles provides a public
``refresh_theme()`` method.  Call it after ``ThemeManager.toggle()`` to
re-apply colours without rebuilding the widget tree.
"""

import cv2
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ui.theme import COLORS


# ─────────────────────────────────────────────
#  NO-SCROLL SLIDER
# ─────────────────────────────────────────────


class NoScrollSlider(QSlider):
    """QSlider that ignores mouse-wheel events.

    Prevents accidental value changes when the user scrolls a parent
    QScrollArea.  The slider can still be changed by click or drag.
    """

    def wheelEvent(self, event: QEvent) -> None:      # type: ignore[override]
        event.ignore()


# ─────────────────────────────────────────────
#  BADGE
# ─────────────────────────────────────────────


class Badge(QLabel):
    """Coloured pill widget that reflects a named state."""

    def __init__(self, state: str = "idle", text: str = "", parent=None):
        super().__init__(parent)
        self._state = state
        self._text = text
        self._apply_style()

    @staticmethod
    def _style_for(state: str) -> tuple[str, str, str]:
        """Return (fg, bg, icon) for the given *state*."""
        styles = {
            "ok":    (COLORS["success"],    COLORS["success_dim"], "●"),
            "idle":  (COLORS["text_muted"], COLORS["surface3"],    "○"),
            "busy":  (COLORS["warning"],    COLORS["warning_dim"], "◌"),
            "error": (COLORS["error"],      COLORS["error_dim"],   "✕"),
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
        self._state = state
        self._text = text
        self._apply_style()

    def refresh_theme(self) -> None:
        self._apply_style()


# ─────────────────────────────────────────────
#  SECTION LABEL
# ─────────────────────────────────────────────


class SectionLabel(QLabel):
    """Small all-caps muted section header."""

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


# ─────────────────────────────────────────────
#  VALUE LABEL
# ─────────────────────────────────────────────


class ValueLabel(QLabel):
    """Monospace primary-colour value display."""

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


# ─────────────────────────────────────────────
#  METRIC CARD
# ─────────────────────────────────────────────


class MetricCard(QFrame):
    """Bordered card that shows a small label above a large numeric value."""

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
        self._val.setText(str(v))

    def refresh_theme(self) -> None:
        self._apply_style()


# ─────────────────────────────────────────────
#  DIVIDER
# ─────────────────────────────────────────────


class Divider(QFrame):
    """1-px horizontal rule that picks up the #divider stylesheet rule."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("divider")
        self.setFrameShape(QFrame.Shape.HLine)


# ─────────────────────────────────────────────
#  IMAGE VIEWER
# ─────────────────────────────────────────────


class ImageViewer(QLabel):
    """
    Aspect-ratio-preserving image display widget.

    Accepts either a file-path string or a NumPy BGR/BGRA/grayscale array
    via :meth:`setImage`.  Automatically rescales on resize.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 240)
        self._pix = None
        self._show_placeholder()

    # ── public ───────────────────────────────

    def setImage(self, path_or_array) -> None:
        """Load an image from *path_or_array* (str path or NumPy ndarray)."""
        try:
            if isinstance(path_or_array, str):
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

    def refresh_theme(self) -> None:
        if self._pix and not self._pix.isNull():
            self._apply_image_style()
        else:
            self._apply_placeholder_style()

    # ── private ──────────────────────────────

    def _apply_image_style(self) -> None:
        self.setStyleSheet(f"""
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 6px;
        """)

    def _apply_placeholder_style(self) -> None:
        self.setStyleSheet(f"""
            background: {COLORS["surface"]};
            border: 1px dashed {COLORS["border_active"]};
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
            scaled = self._pix.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh()


# ─────────────────────────────────────────────
#  SECTION GROUP  (QGroupBox replacement)
# ─────────────────────────────────────────────


class SectionGroup(QFrame):
    """
    Reliable QGroupBox replacement for Fusion-styled dark-theme apps.

    All internal child widgets are created with an explicit ``parent``
    argument and stored as ``self._xxx`` attributes for GC safety.
    """

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title_text = title.upper()

        # ── outer frame ───────────────────────────────────────────────
        self.setObjectName("sectionGroup")
        self.setFrameShape(QFrame.Shape.NoFrame)

        # ── outer layout ─────────────────────────────────────────────
        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(0, 0, 0, 0)
        self._outer_layout.setSpacing(0)

        # ── title bar ────────────────────────────────────────────────
        self._title_bar = QWidget(self)
        self._title_bar.setObjectName("sgTitleBar")

        self._title_bar_layout = QHBoxLayout(self._title_bar)
        self._title_bar_layout.setContentsMargins(12, 7, 12, 7)
        self._title_bar_layout.setSpacing(0)

        self._title_label = QLabel(self._title_text, self._title_bar)
        self._title_bar_layout.addWidget(self._title_label)
        self._outer_layout.addWidget(self._title_bar)

        # ── content widget ───────────────────────────────────────────
        self._content_widget = QWidget(self)
        self._content_widget.setObjectName("sgContent")

        self._inner_layout = QVBoxLayout(self._content_widget)
        self._inner_layout.setContentsMargins(10, 10, 10, 10)
        self._inner_layout.setSpacing(8)

        self._outer_layout.addWidget(self._content_widget)

        # Apply theme styles
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

    # ── public API ───────────────────────────────────────────────────

    def inner_layout(self) -> QVBoxLayout:
        """Return the content ``QVBoxLayout`` for adding child widgets."""
        return self._inner_layout

    def refresh_theme(self) -> None:
        self._apply_style()
