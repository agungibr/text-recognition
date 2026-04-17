"""
Right Panel - Tabbed Display Module
DICOM Tags, Scan Results, and Dose Calculation.
"""

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.theme import COLORS


class RightPanel(QWidget):
    """Right panel - Tabbed display for Tags, Scan Results, and Dose Calculation."""

    calculateDose = Signal(float)

    TYPE_INFO = "info"
    TYPE_SUCCESS = "success"
    TYPE_WARNING = "warning"
    TYPE_ERROR = "error"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(280)
        self.setMaximumWidth(380)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Create tab widget
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget {{
                background: {COLORS['bg']};
                border: none;
            }}
            QTabBar {{
                background: {COLORS['surface']};
                border-bottom: 1px solid {COLORS['border']};
            }}
            QTabBar::tab {{
                background: {COLORS['surface3']};
                color: {COLORS['text_secondary']};
                padding: 6px 16px;
                margin-right: 2px;
                border: none;
                font-size: 11px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background: {COLORS['surface']};
                color: {COLORS['text_primary']};
                border-bottom: 2px solid {COLORS['accent']};
                margin-bottom: -1px;
            }}
            QTabBar::tab:hover {{
                background: {COLORS['surface2']};
            }}
        """)

        # Tab 1: Scan Text
        self._tabs.addTab(self._create_scan_text_tab(), "Scan Text")

        # Tab 2: Tags
        self._tabs.addTab(self._create_tags_tab(), "Tags")

        # Tab 3: Scan & Calculate
        self._tabs.addTab(self._create_calculate_tab(), "Scan & Calculate")

        root.addWidget(self._tabs)
        self._apply_styles()

    def _create_scan_text_tab(self) -> QWidget:
        """Create Scan Text tab."""
        container = QWidget()
        container.setStyleSheet(f"background: {COLORS['bg']};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Scan Text Info
        info_card = QFrame()
        info_card.setStyleSheet(f"""
            QFrame {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
            }}
        """)
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_layout.setSpacing(10)

        # ID field
        id_row = QWidget()
        id_layout = QHBoxLayout(id_row)
        id_layout.setContentsMargins(0, 0, 0, 0)
        id_layout.setSpacing(8)
        id_lbl = QLabel("ID")
        id_lbl.setStyleSheet(f"color: {COLORS['text_label']}; font-size: 11px; font-weight: 600; min-width: 40px;")
        self._scan_id_value = QLabel("—")
        self._scan_id_value.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 11px; font-family: monospace;")
        id_layout.addWidget(id_lbl)
        id_layout.addWidget(self._scan_id_value, 1)
        info_layout.addWidget(id_row)

        # Gender field
        gender_row = QWidget()
        gender_layout = QHBoxLayout(gender_row)
        gender_layout.setContentsMargins(0, 0, 0, 0)
        gender_layout.setSpacing(8)
        gender_lbl = QLabel("Gender")
        gender_lbl.setStyleSheet(f"color: {COLORS['text_label']}; font-size: 11px; font-weight: 600; min-width: 40px;")
        self._scan_gender_value = QLabel("—")
        self._scan_gender_value.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 11px;")
        gender_layout.addWidget(gender_lbl)
        gender_layout.addWidget(self._scan_gender_value, 1)
        info_layout.addWidget(gender_row)

        # Age field
        age_row = QWidget()
        age_layout = QHBoxLayout(age_row)
        age_layout.setContentsMargins(0, 0, 0, 0)
        age_layout.setSpacing(8)
        age_lbl = QLabel("Age")
        age_lbl.setStyleSheet(f"color: {COLORS['text_label']}; font-size: 11px; font-weight: 600; min-width: 40px;")
        self._scan_age_value = QLabel("—")
        self._scan_age_value.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 11px;")
        age_layout.addWidget(age_lbl)
        age_layout.addWidget(self._scan_age_value, 1)
        info_layout.addWidget(age_row)

        # Buttons
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)

        self._save_btn = QPushButton("Save")
        self._save_btn.setObjectName("secondary")
        self._save_btn.setFixedHeight(28)
        button_layout.addWidget(self._save_btn)

        self._load_btn = QPushButton("Load")
        self._load_btn.setObjectName("secondary")
        self._load_btn.setFixedHeight(28)
        button_layout.addWidget(self._load_btn)

        info_layout.addWidget(button_container)
        layout.addWidget(info_card)
        layout.addStretch()

        return container

    def _create_tags_tab(self) -> QWidget:
        """Create DICOM Tags tab with table view."""
        container = QWidget()
        container.setStyleSheet(f"background: {COLORS['bg']};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create table widget
        self._tags_table = QTableWidget()
        self._tags_table.setColumnCount(2)
        self._tags_table.setHorizontalHeaderLabels([
            "TAG Description", "Value"
        ])
        self._tags_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tags_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tags_table.setAlternatingRowColors(True)
        self._tags_table.setStyleSheet(f"""
            QTableWidget {{
                background: {COLORS['surface']};
                alternate-background-color: {COLORS['surface2']};
                border: 1px solid {COLORS['border']};
                gridline-color: {COLORS['border']};
            }}
            QTableWidget::item {{
                padding: 4px;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QHeaderView::section {{
                background: {COLORS['surface2']};
                color: {COLORS['text_primary']};
                padding: 6px;
                border: none;
                border-bottom: 1px solid {COLORS['border']};
                font-weight: bold;
                font-size: 10px;
            }}
        """)
        
        # Set column widths
        self._tags_table.setColumnWidth(0, 200)  # Description
        self._tags_table.setColumnWidth(1, 350)  # Value

        layout.addWidget(self._tags_table)

        return container

    def _create_calculate_tab(self) -> QWidget:
        """Create Dose Calculation tab."""
        container = QWidget()
        container.setStyleSheet(f"background: {COLORS['bg']};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Measure Radiotherapy Doses section
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(10)

        # Title
        title = QLabel("Measure Radiotherapy Doses")
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 11px; font-weight: 600;")
        card_layout.addWidget(title)

        # Weight input
        weight_row = QWidget()
        weight_layout = QHBoxLayout(weight_row)
        weight_layout.setContentsMargins(0, 0, 0, 0)
        weight_layout.setSpacing(8)

        weight_label = QLabel("Weight")
        weight_label.setStyleSheet(f"color: {COLORS['text_label']}; font-size: 11px; font-weight: 600; min-width: 60px;")
        self._weight_input = QDoubleSpinBox()
        self._weight_input.setRange(1.0, 300.0)
        self._weight_input.setValue(70.0)
        self._weight_input.setDecimals(1)
        self._weight_input.setSuffix(" kg")
        self._weight_input.setStyleSheet(f"""
            QDoubleSpinBox {{
                background: {COLORS["surface2"]};
                color: {COLORS["text_primary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QDoubleSpinBox:focus {{
                border-color: {COLORS["accent"]};
            }}
        """)

        weight_layout.addWidget(weight_label)
        weight_layout.addWidget(self._weight_input)
        card_layout.addWidget(weight_row)

        # Calculate button
        self._calculate_btn = QPushButton("Calculate")
        self._calculate_btn.setObjectName("primary")
        self._calculate_btn.setFixedHeight(32)
        self._calculate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._calculate_btn.clicked.connect(self._on_calculate_clicked)
        card_layout.addWidget(self._calculate_btn)

        # Estimate Dose display
        estimate_label = QLabel("Estimate Dose")
        estimate_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; font-weight: 600; margin-top: 8px;")
        card_layout.addWidget(estimate_label)

        self._dose_value = QLabel("—")
        self._dose_value.setStyleSheet(f"""
            color: {COLORS["text_primary"]};
            font-size: 28px;
            font-weight: 600;
            font-family: "Consolas", monospace;
        """)
        card_layout.addWidget(self._dose_value)

        layout.addWidget(card)
        layout.addStretch()

        return container

    def _update_tags(self, tags_dict: dict, image_path: str = None) -> None:
        """Update DICOM tags table with TAG Description and Value only."""
        self._tags_table.setRowCount(0)
        
        if not image_path:
            return
        
        try:
            import pydicom
            # Load the DICOM file to get all tags with metadata
            ds = pydicom.dcmread(image_path, stop_before_pixels=False)
            
            # Collect all tags
            tags_list = []
            for elem in ds:
                name = elem.name if hasattr(elem, 'name') else "Unknown"
                
                # Get value representation
                value_str = str(elem.value)
                if len(value_str) > 300:
                    value_str = value_str[:297] + "..."
                
                tags_list.append({
                    'name': name,
                    'value': value_str
                })
            
            # Add rows to table
            for tag_info in tags_list:
                row_pos = self._tags_table.rowCount()
                self._tags_table.insertRow(row_pos)
                
                # Create items
                name_item = QTableWidgetItem(tag_info['name'])
                value_item = QTableWidgetItem(tag_info['value'])
                
                # Style items
                for item in [name_item, value_item]:
                    item.setFont(QFont("Courier", 9))
                    item.setForeground(QColor(COLORS['text_primary']))
                
                # Set items
                self._tags_table.setItem(row_pos, 0, name_item)
                self._tags_table.setItem(row_pos, 1, value_item)
            
        except Exception as e:
            row_pos = self._tags_table.rowCount()
            self._tags_table.insertRow(row_pos)
            error_item = QTableWidgetItem(f"Error loading tags: {str(e)}")
            self._tags_table.setItem(row_pos, 0, error_item)


    def _on_calculate_clicked(self) -> None:
        weight = self._weight_input.value()
        self.calculateDose.emit(weight)

    def set_dicom_tags(self, tags: dict, image_path: str = None) -> None:
        """Set and display DICOM tags from image path or dict."""
        self._update_tags(tags, image_path)
        # Update scan text tab
        self._scan_id_value.setText(tags.get("patient_id", "—"))
        self._scan_gender_value.setText(tags.get("gender", "—"))
        self._scan_age_value.setText(tags.get("age", "—"))

    def set_dose_result(self, dose_msv: float) -> None:
        """Display dose calculation result."""
        self._dose_value.setText(f"{dose_msv:.2f} mSv")

    def clear_all(self) -> None:
        """Clear all displayed data."""
        self._scan_id_value.setText("—")
        self._scan_gender_value.setText("—")
        self._scan_age_value.setText("—")
        self._update_tags({})
        self._dose_value.setText("—")

    def info(self, message: str) -> None:
        """Log info message (for compatibility)."""
        pass  # Messages are logged internally but not displayed in UI

    def success(self, message: str) -> None:
        """Log success message (for compatibility)."""
        pass  # Messages are logged internally but not displayed in UI

    def warning(self, message: str) -> None:
        """Log warning message (for compatibility)."""
        pass  # Messages are logged internally but not displayed in UI

    def error(self, message: str) -> None:
        """Log error message (for compatibility)."""
        pass  # Messages are logged internally but not displayed in UI

    def _apply_styles(self) -> None:
        self.setStyleSheet(f"background: {COLORS['bg']};")

    def refresh_theme(self) -> None:
        self._apply_styles()


