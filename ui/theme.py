from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

DARK_COLORS = {
    "bg": "#1A1D23",
    "surface": "#22262E",
    "surface2": "#2A2F38",
    "surface3": "#333844",
    "border": "#3A404D",
    "border_active": "#4A5060",
    "accent": "#3498DB",
    "accent_dim": "#2980B9",
    "accent_glow": "#3498DB33",
    "accent_hover": "#5DADE2",
    "success": "#27AE60",
    "success_dim": "#1E8449",
    "warning": "#F39C12",
    "warning_dim": "#D68910",
    "error": "#E74C3C",
    "error_dim": "#C0392B",
    "text_primary": "#ECF0F1",
    "text_secondary": "#BDC3C7",
    "text_muted": "#7F8C8D",
    "highlight": "#3498DB20",
}

LIGHT_COLORS = {
    "bg": "#F5F7FA",
    "surface": "#FFFFFF",
    "surface2": "#ECF0F5",
    "surface3": "#E2E8F0",
    "border": "#CBD5E1",
    "border_active": "#94A3B8",
    "accent": "#2980B9",
    "accent_dim": "#2471A3",
    "accent_glow": "#2980B920",
    "accent_hover": "#3498DB",
    "success": "#1E8449",
    "success_dim": "#27AE60",
    "warning": "#D68910",
    "warning_dim": "#F39C12",
    "error": "#C0392B",
    "error_dim": "#E74C3C",
    "text_primary": "#1A202C",
    "text_secondary": "#4A5568",
    "text_muted": "#718096",
    "highlight": "#2980B915",
}

COLORS = dict(DARK_COLORS)


def build_stylesheet(c):
    return f"""
QMainWindow, QWidget {{
    background-color: {c["bg"]};
    color: {c["text_primary"]};
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 13px;
}}
QSplitter::handle {{
    background: {c["border"]};
}}
QPushButton {{
    background: {c["surface2"]};
    color: {c["text_primary"]};
    border: 1px solid {c["border"]};
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 12px;
    font-weight: 500;
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
}}
QPushButton#primary:hover {{
    background: {c["accent_hover"]};
}}
QPushButton#primary:disabled {{
    background: {c["surface3"]};
    color: {c["text_muted"]};
}}
QPushButton#danger {{
    background: transparent;
    color: {c["error"]};
    border: 1px solid {c["error"]}80;
}}
QPushButton#danger:hover {{
    background: {c["error"]}15;
    border-color: {c["error"]};
}}
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
QProgressBar {{
    background: {c["surface2"]};
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c["accent"]}, stop:1 {c["accent_hover"]});
    border-radius: 3px;
}}
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
QScrollBar:vertical {{ height: 0; }}
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
QScrollBar:horizontal {{ height: 0; }}
QStatusBar {{
    background: {c["surface"]};
    border-top: 1px solid {c["border"]};
    color: {c["text_muted"]};
    font-size: 11px;
    padding: 4px 12px;
}}
QScrollArea {{
    background: transparent;
    border: none;
}}
QLabel {{
    background: transparent;
    color: {c["text_primary"]};
}}
QTextEdit {{
    background: {c["surface2"]};
    color: {c["text_primary"]};
    border: 1px solid {c["border"]};
    border-radius: 5px;
    padding: 8px;
}}
QTextEdit:focus {{
    border-color: {c["accent"]};
}}
QGroupBox {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: 6px;
    margin-top: 16px;
    padding: 16px 12px 8px;
    font-size: 11px;
    font-weight: 600;
    color: {c["text_secondary"]};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 12px;
    background: {c["surface"]};
    color: {c["text_secondary"]};
}}
"""


def build_palette(c):
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(c["bg"]))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(c["text_primary"]))
    pal.setColor(QPalette.ColorRole.Base, QColor(c["surface"]))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(c["surface2"]))
    pal.setColor(QPalette.ColorRole.Text, QColor(c["text_primary"]))
    pal.setColor(QPalette.ColorRole.Button, QColor(c["surface2"]))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(c["text_primary"]))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(c["accent"]))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    return pal


class ThemeManager:
    def __init__(self):
        self._settings = QSettings("RadiologyReader", "App")
        saved = self._settings.value("theme/mode", "dark")
        self._is_dark = saved != "light"
        self._apply_current()

    def _apply_current(self):
        src = DARK_COLORS if self._is_dark else LIGHT_COLORS
        COLORS.clear()
        COLORS.update(src)

    @property
    def is_dark(self):
        return self._is_dark

    def toggle(self):
        self._is_dark = not self._is_dark
        self._apply_current()
        self._settings.setValue("theme/mode", "dark" if self._is_dark else "light")

    def apply(self, app):
        app.setStyleSheet(build_stylesheet(COLORS))
        app.setPalette(build_palette(COLORS))


STYLESHEET = build_stylesheet(COLORS)
