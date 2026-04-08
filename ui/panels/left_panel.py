"""
Left Panel Module - Patient Information Display

Clinical-grade patient information panel displaying DICOM metadata
and matched database records. Designed for clarity and readability.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.theme import COLORS


class LeftPanel(QWidget):
    """Left panel - Patient information and dose estimation."""

    calculateDose = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(260)
        self.setMaximumWidth(320)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet(f"background: {COLORS['bg']};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # DICOM Metadata Section
        layout.addWidget(self._create_dicom_section())

        # Matched Data Section
        layout.addWidget(self._create_matched_section())

        # Dose Estimation Section
        layout.addWidget(self._create_dose_section())

        layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    def _create_section_card(self, title: str) -> tuple:
        """Create a clean card container with header."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet(f"""
            background: {COLORS["surface2"]};
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {COLORS["text_primary"]};
            font-size: 12px;
            font-weight: 600;
            background: transparent;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addWidget(header)

        # Content area
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 10, 12, 12)
        content_layout.setSpacing(6)
        layout.addWidget(content)

        return card, content_layout

    def _create_info_row(self, label: str) -> tuple:
        """Create a label-value row and return the value label."""
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"""
            color: {COLORS["text_label"]};
            font-size: 12px;
            background: transparent;
        """)
        lbl.setMinimumWidth(70)

        val = QLabel("—")
        val.setStyleSheet(f"""
            color: {COLORS["text_primary"]};
            font-size: 12px;
            font-family: "Consolas", "SF Mono", monospace;
            background: transparent;
        """)
        val.setWordWrap(True)

        layout.addWidget(lbl)
        layout.addWidget(val, 1)

        return row, val

    def _create_dicom_section(self) -> QFrame:
        """Create DICOM metadata section."""
        card, layout = self._create_section_card("DICOM Metadata")

        row, self._patient_id_label = self._create_info_row("Patient ID")
        layout.addWidget(row)

        row, self._name_label = self._create_info_row("Name")
        layout.addWidget(row)

        row, self._age_label = self._create_info_row("Age")
        layout.addWidget(row)

        row, self._gender_label = self._create_info_row("Gender")
        layout.addWidget(row)

        row, self._exam_date_label = self._create_info_row("Exam Date")
        layout.addWidget(row)

        return card

    def _create_matched_section(self) -> QFrame:
        """Create matched patient data section."""
        card, layout = self._create_section_card("Database Match")

        # Status row
        status_widget = QWidget()
        status_widget.setStyleSheet("background: transparent;")
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 4)
        status_layout.setSpacing(8)

        self._status_indicator = QLabel("○")
        self._status_indicator.setFixedWidth(16)
        self._status_indicator.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px; background: transparent;")

        self._status_text = QLabel("No match found")
        self._status_text.setStyleSheet(f"""
            color: {COLORS["text_muted"]};
            font-size: 12px;
            font-weight: 500;
            background: transparent;
        """)

        status_layout.addWidget(self._status_indicator)
        status_layout.addWidget(self._status_text)
        status_layout.addStretch()
        layout.addWidget(status_widget)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background: {COLORS['border']}; border: none;")
        layout.addWidget(divider)

        row, self._matched_patient_id = self._create_info_row("Patient ID")
        layout.addWidget(row)

        row, self._matched_age = self._create_info_row("Age")
        layout.addWidget(row)

        row, self._matched_gender = self._create_info_row("Gender")
        layout.addWidget(row)

        return card

    def _create_dose_section(self) -> QFrame:
        """Create dose estimation section."""
        card, layout = self._create_section_card("Dose Estimation")

        # Weight input row
        weight_widget = QWidget()
        weight_widget.setStyleSheet("background: transparent;")
        weight_layout = QHBoxLayout(weight_widget)
        weight_layout.setContentsMargins(0, 0, 0, 0)
        weight_layout.setSpacing(8)

        weight_label = QLabel("Weight")
        weight_label.setStyleSheet(f"color: {COLORS['text_label']}; font-size: 12px; background: transparent;")
        weight_label.setMinimumWidth(70)

        self._weight_input = QDoubleSpinBox()
        self._weight_input.setRange(1.0, 300.0)
        self._weight_input.setValue(70.0)
        self._weight_input.setDecimals(1)
        self._weight_input.setSuffix(" kg")
        self._weight_input.setFixedWidth(100)
        self._weight_input.setStyleSheet(f"""
            QDoubleSpinBox {{
                background: {COLORS["surface2"]};
                color: {COLORS["text_primary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QDoubleSpinBox:focus {{
                border-color: {COLORS["accent"]};
            }}
        """)

        weight_layout.addWidget(weight_label)
        weight_layout.addWidget(self._weight_input)
        weight_layout.addStretch()
        layout.addWidget(weight_widget)

        # Calculate button
        self._calculate_btn = QPushButton("Calculate Dose")
        self._calculate_btn.setObjectName("primary")
        self._calculate_btn.setFixedHeight(32)
        self._calculate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._calculate_btn.clicked.connect(self._on_calculate_clicked)
        layout.addWidget(self._calculate_btn)

        # Result display
        result_frame = QFrame()
        result_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS["surface2"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
            }}
        """)
        result_layout = QVBoxLayout(result_frame)
        result_layout.setContentsMargins(10, 8, 10, 8)
        result_layout.setSpacing(2)

        result_label = QLabel("Estimated Dose")
        result_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; font-weight: 600; letter-spacing: 0.5px; background: transparent;")
        result_layout.addWidget(result_label)

        self._dose_value_label = QLabel("— mSv")
        self._dose_value_label.setStyleSheet(f"""
            color: {COLORS["text_primary"]};
            font-size: 20px;
            font-weight: 600;
            font-family: "Consolas", monospace;
            background: transparent;
        """)
        result_layout.addWidget(self._dose_value_label)

        self._dose_info_label = QLabel("")
        self._dose_info_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
        result_layout.addWidget(self._dose_info_label)

        layout.addWidget(result_frame)

        return card

    def _on_calculate_clicked(self) -> None:
        weight = self._weight_input.value()
        self.calculateDose.emit(weight)

    def set_from_image_data(self, data: dict) -> None:
        """Set patient data from DICOM metadata."""
        self._patient_id_label.setText(data.get("patient_id") or "—")
        self._name_label.setText(data.get("name") or "—")
        
        age = data.get("age")
        self._age_label.setText(f"{age} years" if age else "—")
        
        gender = data.get("gender") or "—"
        self._gender_label.setText(gender)
        
        self._exam_date_label.setText(data.get("exam_date") or "—")

    def set_matched_data(self, data, confidence: float = 0.0) -> None:
        """Set matched patient data from database."""
        if data:
            self._status_indicator.setText("●")
            self._status_indicator.setStyleSheet(f"color: {COLORS['success']}; font-size: 14px; background: transparent;")
            self._status_text.setText("Match found")
            self._status_text.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px; font-weight: 500; background: transparent;")
            self._matched_patient_id.setText(data.get("patient_id") or "—")
            self._matched_age.setText(data.get("age") or "—")
            self._matched_gender.setText(data.get("gender") or "—")
        else:
            self._status_indicator.setText("○")
            self._status_indicator.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px; background: transparent;")
            self._status_text.setText("No match found")
            self._status_text.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; font-weight: 500; background: transparent;")
            self._matched_patient_id.setText("—")
            self._matched_age.setText("—")
            self._matched_gender.setText("—")

    def set_dose_result(self, dose_msv: float, comparison_text: str = "") -> None:
        """Display dose calculation result."""
        self._dose_value_label.setText(f"{dose_msv:.2f} mSv")
        self._dose_info_label.setText(comparison_text)

    def clear_all(self) -> None:
        """Clear all displayed data."""
        self._patient_id_label.setText("—")
        self._name_label.setText("—")
        self._age_label.setText("—")
        self._gender_label.setText("—")
        self._exam_date_label.setText("—")
        self.set_matched_data(None)
        self._dose_value_label.setText("— mSv")
        self._dose_info_label.setText("")

    def set_interactable(self, enabled: bool) -> None:
        """Enable/disable interactive elements."""
        self._calculate_btn.setEnabled(enabled)
        self._weight_input.setEnabled(enabled)
