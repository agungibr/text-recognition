"""
Right Panel - Tabbed Display Module
DICOM Tags, Scan Results, and Dose Calculation.
"""

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
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
        """Create DICOM Tags tab."""
        container = QWidget()
        container.setStyleSheet(f"background: {COLORS['bg']};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create scrollable area for tags
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet(f"background: {COLORS['bg']};")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(12, 12, 12, 12)
        scroll_layout.setSpacing(8)

        # DICOM Tags Card
        self._tags_container = QWidget()
        self._tags_container.setStyleSheet("background: transparent;")
        self._tags_layout = QVBoxLayout(self._tags_container)
        self._tags_layout.setContentsMargins(0, 0, 0, 0)
        self._tags_layout.setSpacing(6)
        self._update_tags({})
        scroll_layout.addWidget(self._tags_container)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

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

    def _update_tags(self, tags_dict: dict) -> None:
        """Update DICOM tags display with ALL metadata."""
        # Clear existing layout
        while self._tags_layout.count():
            child = self._tags_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not tags_dict:
            empty_label = QLabel("No DICOM data loaded")
            empty_label.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
            self._tags_layout.addWidget(empty_label)
            return

        # Display ALL metadata from the dictionary
        # Priority order for common fields
        priority_fields = [
            "patient_id", "name", "birth_date", "gender", "age", "weight",
            "study_date", "study_time", "study_uid", "study_id", "study_description", "modality",
            "series_date", "series_time", "series_uid", "series_number", "series_description",
        ]

        # Display priority fields first
        displayed_keys = set()
        for key in priority_fields:
            if key in tags_dict:
                # Convert underscore to space and capitalize
                display_name = key.replace("_", " ").title()
                value = tags_dict[key]
                self._add_tag_row(display_name, str(value) if value else "—")
                displayed_keys.add(key)

        # Then display remaining fields alphabetically
        remaining_keys = sorted([k for k in tags_dict.keys() if k not in displayed_keys])
        for key in remaining_keys:
            # Skip internal/system keys
            if not key.startswith("_"):
                display_name = key.replace("_", " ").title()
                value = tags_dict[key]
                self._add_tag_row(display_name, str(value) if value else "—")

    def _add_tag_row(self, label: str, value: str) -> None:
        """Add a tag label-value row with proper spacing."""
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"""
            color: {COLORS["text_label"]};
            font-size: 11px;
            font-weight: 500;
            background: transparent;
        """)
        lbl.setMinimumWidth(80)
        lbl.setMaximumWidth(80)

        val = QLabel(value)
        val.setStyleSheet(f"""
            color: {COLORS["text_primary"]};
            font-size: 11px;
            font-family: "Consolas", "SF Mono", monospace;
            background: transparent;
        """)
        val.setWordWrap(True)

        layout.addWidget(lbl)
        layout.addWidget(val, 1)

        self._tags_layout.addWidget(row)

    def _on_calculate_clicked(self) -> None:
        weight = self._weight_input.value()
        self.calculateDose.emit(weight)

    def set_dicom_tags(self, tags: dict) -> None:
        """Set and display DICOM tags."""
        self._update_tags(tags)
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


