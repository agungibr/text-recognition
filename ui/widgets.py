import cv2
from PyQt6.QtWidgets import QLabel, QFrame, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage

from ui.theme import COLORS

class Badge(QLabel):
    STYLES = {
        "ok":    (COLORS["success"],      COLORS["success_dim"], "●"),
        "idle":  (COLORS["text_muted"],   COLORS["surface3"],    "○"),
        "busy":  (COLORS["warning"],      "#5A3D00",             "◌"),
        "error": (COLORS["error"],        "#4A1A1A",             "✕"),
    }

    def __init__(self, state: str = "idle", text: str = "", parent=None):
        super().__init__(parent)
        self.setState(state, text)

    def setState(self, state: str, text: str = "") -> None:
        """
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

class SectionLabel(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        self.setStyleSheet(f"""
            color: {COLORS["text_muted"]};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 2px;
            padding: 8px 0 4px 0;
        """)

class ValueLabel(QLabel):
    def __init__(self, text: str = "—", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            color: {COLORS["text_primary"]};
            font-size: 13px;
            font-family: "Consolas", monospace;
        """)

class MetricCard(QFrame):
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

        lbl = QLabel(label.upper())
        lbl.setStyleSheet(
            f"color:{COLORS['text_muted']};"
            f"font-size:10px;font-weight:700;letter-spacing:1.5px;"
        )

        self._val = QLabel(value)
        self._val.setStyleSheet(
            f"color:{COLORS['text_primary']};"
            f"font-size:18px;font-weight:600;"
            f"font-family:'Consolas',monospace;"
        )

        lay.addWidget(lbl)
        lay.addWidget(self._val)

    def setValue(self, v) -> None:
        self._val.setText(str(v))

class Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("divider")
        self.setFrameShape(QFrame.Shape.HLine)

class ImageViewer(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 240)
        self._pix = None
        self._show_placeholder()

    def setImage(self, path_or_array) -> None:
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
