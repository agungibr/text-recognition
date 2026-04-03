"""
ui/widgets.py
─────────────
Reusable custom Qt widgets used across all panels.

Exports:
    Badge         – coloured status pill (idle / busy / ok / error)
    SectionLabel  – small all-caps section header label
    ValueLabel    – monospace value display label
    MetricCard    – bordered card showing a label + large value
    Divider       – 1-px horizontal rule QFrame
    ImageViewer   – aspect-ratio-preserving image display label
    SectionGroup  – QFrame-based section container (replaces QGroupBox)

WHY SectionGroup INSTEAD OF QGroupBox
──────────────────────────────────────
QGroupBox with Fusion style on Windows has two compounding problems:

1. The CSS `margin-top` / `subcontrol-origin` approach for the title
   interacts badly with the Fusion style engine, causing the content
   area to be calculated as zero-height on some DPI configurations.

2. Children of a styled QGroupBox inherit `background-color` from the
   global `QWidget { background-color: ... }` rule, making them render
   with the same colour as the main window background — effectively
   invisible against the group box surface colour.

SectionGroup fixes both by:
  • Using a plain QFrame with a border (no title subcontrol tricks)
  • Drawing the title as a normal QLabel child with an explicit parent
  • Storing *every* internal child widget/layout as a `self._xxx`
    attribute so Python never garbage-collects their wrappers while
    the C++ Qt objects are still in use
  • Passing an explicit `parent` argument to every internal widget
    constructor so Qt's C++ ownership chain is unambiguous from the
    moment of construction
"""

import cv2
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.theme import COLORS

# ─────────────────────────────────────────────
#  BADGE
# ─────────────────────────────────────────────


class Badge(QLabel):
    """Coloured pill widget that reflects a named state."""

    STYLES = {
        "ok": (COLORS["success"], COLORS["success_dim"], "●"),
        "idle": (COLORS["text_muted"], COLORS["surface3"], "○"),
        "busy": (COLORS["warning"], "#5A3D00", "◌"),
        "error": (COLORS["error"], "#4A1A1A", "✕"),
    }

    def __init__(self, state: str = "idle", text: str = "", parent=None):
        super().__init__(parent)
        self.setState(state, text)

    def setState(self, state: str, text: str = "") -> None:
        """Update badge appearance.

        Args:
            state: One of ``"ok"``, ``"idle"``, ``"busy"``, ``"error"``.
            text:  Optional label shown next to the icon.
        """
        fg, bg, icon = self.STYLES.get(state, self.STYLES["idle"])
        label = f"{icon}  {text}" if text else icon
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


# ─────────────────────────────────────────────
#  SECTION LABEL
# ─────────────────────────────────────────────


class SectionLabel(QLabel):
    """Small all-caps muted section header."""

    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        self.setStyleSheet(f"""
            color: {COLORS["text_muted"]};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 2px;
            padding: 8px 0 4px 0;
        """)


# ─────────────────────────────────────────────
#  VALUE LABEL
# ─────────────────────────────────────────────


class ValueLabel(QLabel):
    """Monospace primary-colour value display."""

    def __init__(self, text: str = "—", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            color: {COLORS["text_primary"]};
            font-size: 13px;
            font-family: "Consolas", monospace;
        """)


# ─────────────────────────────────────────────
#  METRIC CARD
# ─────────────────────────────────────────────


class MetricCard(QFrame):
    """Bordered card that shows a small label above a large numeric value."""

    def __init__(self, label: str, value: str = "—", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS["surface2"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
                padding: 2px;
            }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(2)

        lbl = QLabel(label.upper(), self)
        lbl.setStyleSheet(
            f"color:{COLORS['text_muted']};"
            f"font-size:10px;font-weight:700;letter-spacing:1.5px;"
            f"background:transparent;border:none;"
        )

        self._val = QLabel(value, self)
        self._val.setStyleSheet(
            f"color:{COLORS['text_primary']};"
            f"font-size:18px;font-weight:600;"
            f"font-family:'Consolas',monospace;"
            f"background:transparent;border:none;"
        )

        lay.addWidget(lbl)
        lay.addWidget(self._val)

    def setValue(self, v) -> None:
        """Set the displayed value (accepts any type, converts via str)."""
        self._val.setText(str(v))


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
            self.setStyleSheet(f"""
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
            """)
            self._refresh()

        except Exception as exc:
            self._pix = None
            self._show_placeholder(f"Error: {exc}")

    # ── private ──────────────────────────────

    def _show_placeholder(self, text: str = "No image selected") -> None:
        self._pix = None
        self.setPixmap(QPixmap())
        self.setText(text)
        self.setStyleSheet(f"""
            background: {COLORS["surface"]};
            border: 1px dashed {COLORS["border_active"]};
            border-radius: 6px;
            color: {COLORS["text_muted"]};
            font-size: 12px;
            letter-spacing: 1px;
        """)

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

    Renders as a bordered card with a shaded title bar on top and a
    transparent content area below.  Unlike QGroupBox, it does **not**
    rely on CSS ``margin-top`` / ``subcontrol-origin`` for title
    placement, which is the root cause of invisible-content bugs with
    Fusion style on Windows.

    All internal child widgets are:

    * Created with an **explicit parent** argument so Qt's C++ ownership
      chain is established at construction time (no deferred reparenting).
    * Stored as ``self._xxx`` attributes so the Python reference count
      never drops to zero while the widget is alive.

    Usage::

        box = SectionGroup("Model")
        box.inner_layout().addWidget(some_widget)
        parent_layout.addWidget(box)
    """

    def __init__(self, title: str, parent=None):
        super().__init__(parent)

        # ── outer frame ───────────────────────────────────────────────────
        self.setObjectName("sectionGroup")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(f"""
            QFrame#sectionGroup {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
            }}
        """)

        # ── outer layout (installs directly on self) ──────────────────────
        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(0, 0, 0, 0)
        self._outer_layout.setSpacing(0)

        # ── title bar — explicit parent=self ─────────────────────────────
        self._title_bar = QWidget(self)
        self._title_bar.setObjectName("sgTitleBar")
        self._title_bar.setStyleSheet(f"""
            QWidget#sgTitleBar {{
                background: {COLORS["surface2"]};
                border-radius: 5px 5px 0px 0px;
                border-bottom: 1px solid {COLORS["border"]};
            }}
        """)

        # layout on the title bar
        self._title_bar_layout = QHBoxLayout(self._title_bar)
        self._title_bar_layout.setContentsMargins(12, 7, 12, 7)
        self._title_bar_layout.setSpacing(0)

        # title label — explicit parent=self._title_bar
        self._title_label = QLabel(title.upper(), self._title_bar)
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
        self._title_bar_layout.addWidget(self._title_label)
        self._outer_layout.addWidget(self._title_bar)

        # ── content widget — explicit parent=self ─────────────────────────
        self._content_widget = QWidget(self)
        self._content_widget.setObjectName("sgContent")
        self._content_widget.setStyleSheet("""
            QWidget#sgContent {
                background: transparent;
                border: none;
            }
        """)

        # inner layout installed on the content widget
        self._inner_layout = QVBoxLayout(self._content_widget)
        self._inner_layout.setContentsMargins(10, 10, 10, 10)
        self._inner_layout.setSpacing(8)

        self._outer_layout.addWidget(self._content_widget)

    # ── public API ────────────────────────────────────────────────────────

    def inner_layout(self) -> QVBoxLayout:
        """Return the content ``QVBoxLayout`` for adding child widgets."""
        return self._inner_layout
