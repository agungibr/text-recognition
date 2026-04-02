COLORS = {
    "bg":             "#0F1117",
    "surface":        "#171B26",
    "surface2":       "#1E2333",
    "surface3":       "#252B3B",
    "border":         "#2A3045",
    "border_active":  "#3D4F7C",
    "accent":         "#4B8BF4",
    "accent_dim":     "#2D5599",
    "accent_glow":    "#4B8BF433",
    "success":        "#2ECC71",
    "success_dim":    "#1A7A44",
    "warning":        "#F39C12",
    "error":          "#E74C3C",
    "text_primary":   "#E8ECF4",
    "text_secondary": "#8892A4",
    "text_muted":     "#4A5568",
    "highlight":      "#4B8BF420",
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLORS["bg"]};
    color: {COLORS["text_primary"]};
    font-family: "Consolas", "Menlo", monospace;
    font-size: 13px;
}}

QSplitter::handle {{
    background: {COLORS["border"]};
}}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical   {{ height: 1px; }}

QGroupBox {{
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    margin-top: 20px;
    padding: 12px 10px 10px 10px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: {COLORS["text_secondary"]};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 12px;
    top: 6px;
    background: {COLORS["surface"]};
    color: {COLORS["text_secondary"]};
}}

QPushButton {{
    background: {COLORS["surface2"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 5px;
    padding: 8px 18px;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.3px;
}}
QPushButton:hover {{
    background: {COLORS["surface3"]};
    border-color: {COLORS["border_active"]};
}}
QPushButton:pressed {{
    background: {COLORS["accent_dim"]};
    border-color: {COLORS["accent"]};
}}
QPushButton:disabled {{
    color: {COLORS["text_muted"]};
    border-color: {COLORS["border"]};
    background: {COLORS["surface"]};
}}

QPushButton#primary {{
    background: {COLORS["accent"]};
    color: #fff;
    border: none;
    font-weight: 600;
    letter-spacing: 0.5px;
}}
QPushButton#primary:hover {{
    background: #5C9BFF;
}}
QPushButton#primary:pressed {{
    background: {COLORS["accent_dim"]};
}}
QPushButton#primary:disabled {{
    background: {COLORS["accent_dim"]};
    color: #ffffff60;
}}

QPushButton#danger {{
    background: transparent;
    color: {COLORS["error"]};
    border: 1px solid {COLORS["error"]}60;
}}
QPushButton#danger:hover {{
    background: {COLORS["error"]}15;
    border-color: {COLORS["error"]};
}}

QPushButton#success {{
    background: {COLORS["success_dim"]};
    color: {COLORS["success"]};
    border: 1px solid {COLORS["success"]}60;
    font-weight: 600;
}}

QLineEdit, QComboBox {{
    background: {COLORS["surface2"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 5px;
    padding: 7px 10px;
    selection-background-color: {COLORS["accent"]};
}}
QLineEdit:focus, QComboBox:focus {{
    border-color: {COLORS["accent"]};
    background: {COLORS["surface3"]};
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
    border-top: 5px solid {COLORS["text_secondary"]};
    margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    background: {COLORS["surface2"]};
    border: 1px solid {COLORS["border_active"]};
    selection-background-color: {COLORS["accent_dim"]};
    outline: none;
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {COLORS["surface3"]};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {COLORS["accent"]};
    border: 2px solid {COLORS["bg"]};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::sub-page:horizontal {{
    background: {COLORS["accent"]};
    border-radius: 2px;
}}

QCheckBox {{
    color: {COLORS["text_secondary"]};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid {COLORS["border_active"]};
    background: {COLORS["surface2"]};
}}
QCheckBox::indicator:checked {{
    background: {COLORS["accent"]};
    border-color: {COLORS["accent"]};
}}
QCheckBox:hover {{
    color: {COLORS["text_primary"]};
}}

QListWidget {{
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 5px;
    outline: none;
    padding: 2px;
}}
QListWidget::item {{
    padding: 7px 10px;
    border-radius: 3px;
    color: {COLORS["text_secondary"]};
    border-bottom: 1px solid {COLORS["border"]};
}}
QListWidget::item:selected {{
    background: {COLORS["highlight"]};
    color: {COLORS["text_primary"]};
    border-left: 2px solid {COLORS["accent"]};
}}
QListWidget::item:hover {{
    background: {COLORS["surface2"]};
    color: {COLORS["text_primary"]};
}}

QTableWidget {{
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 5px;
    gridline-color: {COLORS["border"]};
    outline: none;
    selection-background-color: {COLORS["highlight"]};
}}
QTableWidget::item {{
    padding: 6px 10px;
    color: {COLORS["text_primary"]};
    border: none;
}}
QTableWidget::item:selected {{
    background: {COLORS["highlight"]};
    color: {COLORS["accent"]};
}}
QHeaderView::section {{
    background: {COLORS["surface2"]};
    color: {COLORS["text_secondary"]};
    border: none;
    border-bottom: 1px solid {COLORS["border"]};
    border-right: 1px solid {COLORS["border"]};
    padding: 7px 10px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}}

QProgressBar {{
    background: {COLORS["surface2"]};
    border: none;
    border-radius: 3px;
    height: 4px;
    text-align: center;
    font-size: 0px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS["accent"]}, stop:1 #7AB8FF);
    border-radius: 3px;
}}

QScrollBar:vertical {{
    background: {COLORS["surface"]};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS["surface3"]};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS["border_active"]};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {COLORS["surface"]};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS["surface3"]};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {COLORS["border_active"]};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

QFrame#divider {{
    background: {COLORS["border"]};
    max-height: 1px;
    min-height: 1px;
}}

QStatusBar {{
    background: {COLORS["surface"]};
    border-top: 1px solid {COLORS["border"]};
    color: {COLORS["text_muted"]};
    font-size: 11px;
    padding: 0 12px;
}}

QScrollArea {{
    background: transparent;
    border: none;
}}
"""
