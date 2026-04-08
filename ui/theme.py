"""
Theme Module - Clinical-Grade Medical Software Appearance

Provides a professional, clinical-grade dark theme designed for
hospital environments. Prioritizes readability, clarity, and
reduced eye strain during extended use.
"""

from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

# Clinical-grade dark theme - muted, professional colors
DARK_COLORS = {
    # Base backgrounds - neutral charcoal tones
    "bg": "#1C1E21",
    "surface": "#242629",
    "surface2": "#2C2F33",
    "surface3": "#35383D",
    "panel": "#272A2E",
    
    # Borders - subtle separation
    "border": "#3A3D42",
    "border_light": "#44484E",
    "border_active": "#505560",
    
    # Primary accent - muted medical blue
    "accent": "#4A90B8",
    "accent_dim": "#3D7A9E",
    "accent_hover": "#5BA3CC",
    "accent_bg": "#4A90B815",
    
    # Status colors - muted for clinical use
    "success": "#5B9A6F",
    "success_bg": "#5B9A6F15",
    "warning": "#C4944D",
    "warning_bg": "#C4944D15",
    "error": "#C25D5D",
    "error_bg": "#C25D5D15",
    
    # Text hierarchy - high contrast for readability
    "text_primary": "#E8EAED",
    "text_secondary": "#B4B8BD",
    "text_muted": "#7D8590",
    "text_label": "#9BA1A8",
    
    # Highlights
    "highlight": "#4A90B820",
    "selection": "#4A90B830",
}

# Light theme variant (for accessibility)
LIGHT_COLORS = {
    "bg": "#F5F6F8",
    "surface": "#FFFFFF",
    "surface2": "#F0F1F3",
    "surface3": "#E8E9EB",
    "panel": "#FAFBFC",
    
    "border": "#D1D5DB",
    "border_light": "#E5E7EB",
    "border_active": "#9CA3AF",
    
    "accent": "#3B7BA8",
    "accent_dim": "#2D6690",
    "accent_hover": "#4889B8",
    "accent_bg": "#3B7BA810",
    
    "success": "#4A8A5C",
    "success_bg": "#4A8A5C10",
    "warning": "#A67B3D",
    "warning_bg": "#A67B3D10",
    "error": "#A84D4D",
    "error_bg": "#A84D4D10",
    
    "text_primary": "#1F2937",
    "text_secondary": "#4B5563",
    "text_muted": "#9CA3AF",
    "text_label": "#6B7280",
    
    "highlight": "#3B7BA815",
    "selection": "#3B7BA820",
}

COLORS = dict(DARK_COLORS)


def build_stylesheet(c):
    """Generate clinical-grade stylesheet with consistent spacing and typography."""
    return f"""
/* ============================================
   BASE STYLES - Clinical Grade Medical UI
   ============================================ */

QMainWindow, QWidget {{
    background-color: {c["bg"]};
    color: {c["text_primary"]};
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
    font-size: 13px;
}}

/* Panel containers */
QFrame[frameShape="0"], QWidget#panel {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: 6px;
}}

/* ============================================
   TYPOGRAPHY
   ============================================ */

QLabel {{
    background: transparent;
    color: {c["text_primary"]};
    border: none;
}}

QLabel[class="title"] {{
    font-size: 15px;
    font-weight: 600;
    color: {c["text_primary"]};
}}

QLabel[class="section"] {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    color: {c["text_muted"]};
    text-transform: uppercase;
}}

QLabel[class="label"] {{
    font-size: 12px;
    color: {c["text_label"]};
}}

QLabel[class="value"] {{
    font-size: 13px;
    font-family: "Consolas", "SF Mono", monospace;
    color: {c["text_primary"]};
}}

/* ============================================
   BUTTONS - Clear, Functional Design
   ============================================ */

QPushButton {{
    background: {c["surface2"]};
    color: {c["text_primary"]};
    border: 1px solid {c["border"]};
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
    min-height: 18px;
}}

QPushButton:hover {{
    background: {c["surface3"]};
    border-color: {c["border_light"]};
}}

QPushButton:pressed {{
    background: {c["accent_dim"]};
}}

QPushButton:disabled {{
    color: {c["text_muted"]};
    background: {c["surface"]};
    border-color: {c["border"]};
}}

QPushButton#primary {{
    background: {c["accent"]};
    color: #FFFFFF;
    border: none;
    font-weight: 600;
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

QPushButton#secondary {{
    background: transparent;
    border: 1px solid {c["border"]};
    color: {c["text_secondary"]};
}}

QPushButton#secondary:hover {{
    background: {c["surface2"]};
    color: {c["text_primary"]};
}}

QPushButton#danger {{
    background: transparent;
    color: {c["error"]};
    border: 1px solid {c["error"]}60;
}}

QPushButton#danger:hover {{
    background: {c["error_bg"]};
}}

/* ============================================
   INPUT FIELDS
   ============================================ */

QLineEdit, QTextEdit {{
    background: {c["surface2"]};
    color: {c["text_primary"]};
    border: 1px solid {c["border"]};
    border-radius: 4px;
    padding: 6px 10px;
    selection-background-color: {c["selection"]};
}}

QLineEdit:focus, QTextEdit:focus {{
    border-color: {c["accent"]};
    background: {c["surface"]};
}}

QLineEdit:disabled, QTextEdit:disabled {{
    background: {c["surface"]};
    color: {c["text_muted"]};
}}

QComboBox {{
    background: {c["surface2"]};
    color: {c["text_primary"]};
    border: 1px solid {c["border"]};
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 18px;
}}

QComboBox:hover {{
    border-color: {c["border_light"]};
}}

QComboBox:focus {{
    border-color: {c["accent"]};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QSpinBox, QDoubleSpinBox {{
    background: {c["surface2"]};
    color: {c["text_primary"]};
    border: 1px solid {c["border"]};
    border-radius: 4px;
    padding: 4px 8px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {c["accent"]};
}}

/* ============================================
   SLIDERS & CHECKBOXES
   ============================================ */

QSlider::groove:horizontal {{
    height: 4px;
    background: {c["surface3"]};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {c["accent"]};
    border: 2px solid {c["bg"]};
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
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

QCheckBox::indicator:hover {{
    border-color: {c["accent"]};
}}

/* ============================================
   LISTS & TABLES
   ============================================ */

QListWidget {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: 4px;
    outline: none;
    padding: 4px;
}}

QListWidget::item {{
    padding: 8px 10px;
    border-radius: 3px;
    color: {c["text_secondary"]};
    border: none;
}}

QListWidget::item:selected {{
    background: {c["highlight"]};
    color: {c["text_primary"]};
}}

QListWidget::item:hover {{
    background: {c["surface2"]};
}}

/* ============================================
   SCROLL BARS - Minimal Design
   ============================================ */

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {c["surface3"]};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {c["border_active"]};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    height: 0;
    background: transparent;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {c["surface3"]};
    border-radius: 4px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {c["border_active"]};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    width: 0;
    background: transparent;
}}

/* ============================================
   PROGRESS BAR
   ============================================ */

QProgressBar {{
    background: {c["surface2"]};
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
}}

QProgressBar::chunk {{
    background: {c["accent"]};
    border-radius: 3px;
}}

/* ============================================
   GROUP BOX - Card Style
   ============================================ */

QGroupBox {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: 6px;
    margin-top: 14px;
    padding: 14px 12px 10px;
    font-size: 11px;
    font-weight: 600;
    color: {c["text_muted"]};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 10px;
    background: {c["surface"]};
    color: {c["text_label"]};
}}

/* ============================================
   SPLITTER
   ============================================ */

QSplitter::handle {{
    background: {c["border"]};
}}

QSplitter::handle:horizontal {{
    width: 1px;
}}

QSplitter::handle:vertical {{
    height: 1px;
}}

/* ============================================
   STATUS BAR & TOOLBAR
   ============================================ */

QStatusBar {{
    background: {c["surface"]};
    border-top: 1px solid {c["border"]};
    color: {c["text_muted"]};
    font-size: 11px;
    padding: 2px 12px;
}}

QToolBar {{
    background: {c["surface"]};
    border-bottom: 1px solid {c["border"]};
    padding: 4px 8px;
    spacing: 4px;
}}

QToolBar::separator {{
    width: 1px;
    background: {c["border"]};
    margin: 4px 8px;
}}

/* ============================================
   SCROLL AREA
   ============================================ */

QScrollArea {{
    background: transparent;
    border: none;
}}

QScrollArea > QWidget > QWidget {{
    background: transparent;
}}

/* ============================================
   MENU
   ============================================ */

QMenu {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: 4px;
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 3px;
}}

QMenu::item:selected {{
    background: {c["highlight"]};
}}

/* ============================================
   TOOLTIP
   ============================================ */

QToolTip {{
    background: {c["surface2"]};
    color: {c["text_primary"]};
    border: 1px solid {c["border"]};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}
"""


def build_palette(c):
    """Build QPalette for system-level color consistency."""
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
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(c["surface2"]))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor(c["text_primary"]))
    return pal


class ThemeManager:
    """Manages application theme (dark/light) with persistence."""

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

    def apply(self, app: QApplication):
        """Apply theme to the application."""
        app.setStyleSheet(build_stylesheet(COLORS))
        app.setPalette(build_palette(COLORS))
        
        # Set default font
        font = QFont("Segoe UI", 10)
        font.setStyleHint(QFont.StyleHint.SansSerif)
        app.setFont(font)


STYLESHEET = build_stylesheet(COLORS)
