from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

# ═════════════════════════════════════════════════════════════════════════════
#  COLOUR PALETTES
# ═════════════════════════════════════════════════════════════════════════════

DARK_COLORS: dict[str, str] = {
    "bg": "#0F1117",
    "surface": "#171B26",
    "surface2": "#1E2333",
    "surface3": "#252B3B",
    "border": "#2A3045",
    "border_active": "#3D4F7C",
    "accent": "#4B8BF4",
    "accent_dim": "#2D5599",
    "accent_glow": "#4B8BF433",
    "accent_hover": "#5C9BFF",
    "success": "#2ECC71",
    "success_dim": "#1A7A44",
    "warning": "#F39C12",
    "warning_dim": "#5A3D00",
    "error": "#E74C3C",
    "error_dim": "#4A1A1A",
    "text_primary": "#E8ECF4",
    "text_secondary": "#8892A4",
    "text_muted": "#4A5568",
    "highlight": "#4B8BF420",
}

LIGHT_COLORS: dict[str, str] = {
    "bg": "#F5F7FA",
    "surface": "#FFFFFF",
    "surface2": "#EDF0F5",
    "surface3": "#E2E6ED",
    "border": "#D1D9E6",
    "border_active": "#A0B0C8",
    "accent": "#3B7CF5",
    "accent_dim": "#2565C7",
    "accent_glow": "#3B7CF520",
    "accent_hover": "#5090FF",
    "success": "#1B9E4B",
    "success_dim": "#D4EDDA",
    "warning": "#D48806",
    "warning_dim": "#FFF3D6",
    "error": "#D93025",
    "error_dim": "#FDE8E8",
    "text_primary": "#1A1D26",
    "text_secondary": "#5A6577",
    "text_muted": "#8892A4",
    "highlight": "#3B7CF515",
}

COLORS: dict[str, str] = dict(DARK_COLORS)


def build_stylesheet(c: dict[str, str]) -> str:
    return f"""
/* ── base ──────────────────────────────────────────────── */
QMainWindow, QWidget {{
    background-color: {c["bg"]};
    color: {c["text_primary"]};
    font-family: "Consolas", "Menlo", monospace;
    font-size: 13px;
}}

/* ── splitter ──────────────────────────────────────────── */
QSplitter::handle {{
    background: {c["border"]};
}}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical   {{ height: 1px; }}

/* ── group box (kept for compatibility) ────────────────── */
QGroupBox {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: 6px;
    margin-top: 20px;
    padding: 12px 10px 10px 10px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    color: {c["text_secondary"]};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 12px;
    top: 6px;
    background: {c["surface"]};
    color: {c["text_secondary"]};
}}

/* ── buttons ───────────────────────────────────────────── */
QPushButton {{
    background: {c["surface2"]};
    color: {c["text_primary"]};
    border: 1px solid {c["border"]};
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.3px;
}}
QPushButton:hover {{
    background: {c["surface3"]};
    border-color: {c["border_active"]};
}}
QPushButton:pressed {{
    background: {c["accent_dim"]};
    border-color: {c["accent"]};
}}
QPushButton:disabled {{
    color: {c["text_muted"]};
    border-color: {c["border"]};
    background: {c["surface"]};
}}

QPushButton#primary {{
    background: {c["accent"]};
    color: #ffffff;
    border: none;
    font-weight: 600;
    letter-spacing: 0.5px;
}}
QPushButton#primary:hover {{
    background: {c["accent_hover"]};
}}
QPushButton#primary:pressed {{
    background: {c["accent_dim"]};
}}
QPushButton#primary:disabled {{
    background: {c["surface3"]};
    color: {c["text_muted"]};
}}

QPushButton#danger {{
    background: transparent;
    color: {c["error"]};
    border: 1px solid {c["error"]}60;
}}
QPushButton#danger:hover {{
    background: {c["error"]}15;
    border-color: {c["error"]};
}}
QPushButton#danger:pressed {{
    background: {c["error"]}30;
}}

QPushButton#success {{
    background: {c["success_dim"]};
    color: {c["success"]};
    border: 1px solid {c["success"]}60;
    font-weight: 600;
}}
QPushButton#success:hover {{
    border-color: {c["success"]};
}}
QPushButton#success:pressed {{
    background: {c["success"]}30;
}}

QPushButton#themeToggle {{
    background: {c["surface2"]};
    border: 1px solid {c["border"]};
    border-radius: 14px;
    padding: 4px 10px;
    font-size: 14px;
    min-width: 28px;
    min-height: 28px;
}}
QPushButton#themeToggle:hover {{
    background: {c["surface3"]};
    border-color: {c["border_active"]};
}}

/* ── inputs ────────────────────────────────────────────── */
QLineEdit, QComboBox {{
    background: {c["surface2"]};
    color: {c["text_primary"]};
    border: 1px solid {c["border"]};
    border-radius: 5px;
    padding: 7px 10px;
    selection-background-color: {c["accent"]};
}}
QLineEdit:focus, QComboBox:focus {{
    border-color: {c["accent"]};
    background: {c["surface3"]};
}}
QComboBox::drop-down {{
    border: none;
    width: 28px;
}}
QComboBox::down-arrow {{
    width: 12px;
    height: 12px;
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {c["text_secondary"]};
    margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    background: {c["surface2"]};
    border: 1px solid {c["border_active"]};
    selection-background-color: {c["accent_dim"]};
    outline: none;
}}

/* ── slider ────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    height: 4px;
    background: {c["surface3"]};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {c["accent"]};
    border: 2px solid {c["bg"]};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::sub-page:horizontal {{
    background: {c["accent"]};
    border-radius: 2px;
}}

/* ── checkbox ──────────────────────────────────────────── */
QCheckBox {{
    color: {c["text_secondary"]};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid {c["border_active"]};
    background: {c["surface2"]};
}}
QCheckBox::indicator:checked {{
    background: {c["accent"]};
    border-color: {c["accent"]};
}}
QCheckBox:hover {{
    color: {c["text_primary"]};
}}

/* ── list widget ───────────────────────────────────────── */
QListWidget {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: 5px;
    outline: none;
    padding: 2px;
}}
QListWidget::item {{
    padding: 7px 10px;
    border-radius: 3px;
    color: {c["text_secondary"]};
    border-bottom: 1px solid {c["border"]};
}}
QListWidget::item:selected {{
    background: {c["highlight"]};
    color: {c["text_primary"]};
    border-left: 2px solid {c["accent"]};
}}
QListWidget::item:hover {{
    background: {c["surface2"]};
    color: {c["text_primary"]};
}}

/* ── table widget ──────────────────────────────────────── */
QTableWidget {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: 5px;
    gridline-color: {c["border"]};
    outline: none;
    selection-background-color: {c["highlight"]};
}}
QTableWidget::item {{
    padding: 6px 10px;
    color: {c["text_primary"]};
    border: none;
}}
QTableWidget::item:selected {{
    background: {c["highlight"]};
    color: {c["accent"]};
}}
QHeaderView::section {{
    background: {c["surface2"]};
    color: {c["text_secondary"]};
    border: none;
    border-bottom: 1px solid {c["border"]};
    border-right: 1px solid {c["border"]};
    padding: 7px 10px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.8px;
}}

/* ── progress bar ──────────────────────────────────────── */
QProgressBar {{
    background: {c["surface2"]};
    border: none;
    border-radius: 3px;
    height: 4px;
    text-align: center;
    font-size: 0px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {c["accent"]}, stop:1 {c["accent_hover"]});
    border-radius: 3px;
}}

/* ── scrollbars ────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {c["surface"]};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {c["surface3"]};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c["border_active"]};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {c["surface"]};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {c["surface3"]};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {c["border_active"]};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ── misc ──────────────────────────────────────────────── */
QFrame#divider {{
    background: {c["border"]};
    max-height: 1px;
    min-height: 1px;
}}

QStatusBar {{
    background: {c["surface"]};
    border-top: 1px solid {c["border"]};
    color: {c["text_muted"]};
    font-size: 11px;
    padding: 0 12px;
}}

QScrollArea {{
    background: transparent;
    border: none;
}}
"""


def build_palette(c: dict[str, str]) -> QPalette:
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(c["bg"]))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(c["text_primary"]))
    pal.setColor(QPalette.ColorRole.Base, QColor(c["surface"]))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(c["surface2"]))
    pal.setColor(QPalette.ColorRole.Text, QColor(c["text_primary"]))
    pal.setColor(QPalette.ColorRole.Button, QColor(c["surface2"]))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(c["text_primary"]))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(c["accent"]))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(c["surface2"]))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor(c["text_primary"]))
    return pal


class ThemeManager:
    def __init__(self) -> None:
        self._settings = QSettings("YOLOxOCR", "DetectionSuite")
        saved = self._settings.value("theme/mode", "dark")
        self._is_dark: bool = saved != "light"
        src = DARK_COLORS if self._is_dark else LIGHT_COLORS
        COLORS.clear()
        COLORS.update(src)

    @property
    def is_dark(self) -> bool:
        return self._is_dark

    def toggle(self) -> None:
        self._is_dark = not self._is_dark
        src = DARK_COLORS if self._is_dark else LIGHT_COLORS
        COLORS.clear()
        COLORS.update(src)
        self._settings.setValue("theme/mode", "dark" if self._is_dark else "light")

    def apply(self, app: QApplication) -> None:
        app.setStyleSheet(build_stylesheet(COLORS))
        app.setPalette(build_palette(COLORS))


STYLESHEET = build_stylesheet(COLORS)
