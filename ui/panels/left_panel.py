"""
Left Panel Module - Patient Information
Displays patient information extracted from images and matched data.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.theme import COLORS


class LeftPanel(QWidget):
    """Left panel containing patient information and dose estimation."""

    calculateDose = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(260)
        self.setMaximumWidth(340)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        inner_layout = QVBoxLayout(scroll_widget)
        inner_layout.setContentsMargins(12, 12, 12, 12)
        inner_layout.setSpacing(12)

        self._build_from_image_section(inner_layout)
        self._build_patient_found_section(inner_layout)
        self._build_dose_estimation_section(inner_layout)

        inner_layout.addStretch()

        scroll.setWidget(scroll_widget)
        root.addWidget(scroll)

    def _build_from_image_section(self, parent_layout) -> None:
        group = QGroupBox("From Image")
        layout = QFormLayout(group)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setSpacing(8)

        self._patient_id_label = QLabel("—")
        layout.addRow("Patient ID:", self._patient_id_label)

        self._name_label = QLabel("—")
        layout.addRow("Name:", self._name_label)

        self._age_label = QLabel("—")
        layout.addRow("Age:", self._age_label)

        self._gender_label = QLabel("—")
        layout.addRow("Gender:", self._gender_label)

        self._exam_date_label = QLabel("—")
        layout.addRow("Exam Date:", self._exam_date_label)

        parent_layout.addWidget(group)

    def _build_patient_found_section(self, parent_layout) -> None:
        group = QGroupBox("Patient Data Found")
        layout = QFormLayout(group)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setSpacing(8)

        status_row = QHBoxLayout()
        self._status_indicator = QLabel("○")
        self._status_text = QLabel("No Matching Data")
        self._status_indicator.setFixedWidth(20)
        status_row.addWidget(self._status_indicator)
        status_row.addWidget(self._status_text)
        status_row.addStretch()
        layout.addRow("Status:", status_row)

        self._matched_patient_id = QLabel("—")
        layout.addRow("Patient ID:", self._matched_patient_id)

        self._matched_age = QLabel("—")
        layout.addRow("Age:", self._matched_age)

        self._matched_gender = QLabel("—")
        layout.addRow("Gender:", self._matched_gender)

        parent_layout.addWidget(group)

    def _build_dose_estimation_section(self, parent_layout) -> None:
        group = QGroupBox("Dose Estimation")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        weight_row = QHBoxLayout()
        weight_row.addWidget(QLabel("Weight (kg):"))

        self._weight_input = QDoubleSpinBox()
        self._weight_input.setRange(1.0, 300.0)
        self._weight_input.setValue(70.0)
        self._weight_input.setDecimals(1)
        self._weight_input.setSuffix(" kg")
        self._weight_input.setMinimumWidth(100)
        weight_row.addWidget(self._weight_input)
        weight_row.addStretch()

        layout.addLayout(weight_row)

        self._calculate_btn = QPushButton("Calculate")
        self._calculate_btn.setObjectName("primary")
        self._calculate_btn.setFixedHeight(36)
        self._calculate_btn.clicked.connect(self._on_calculate_clicked)
        layout.addWidget(self._calculate_btn)

        result_frame = QFrame()
        result_frame.setFrameShape(QFrame.Shape.StyledPanel)
        result_layout = QVBoxLayout(result_frame)
        result_layout.setContentsMargins(8, 8, 8, 8)
        result_layout.setSpacing(4)

        self._dose_result_label = QLabel("Estimated Dose:")
        self._dose_result_label.setStyleSheet("font-weight: bold; color: #3498DB;")
        result_layout.addWidget(self._dose_result_label)

        self._dose_value_label = QLabel("— mSv")
        self._dose_value_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #ECF0F1;"
        )
        result_layout.addWidget(self._dose_value_label)

        self._dose_info_label = QLabel("")
        self._dose_info_label.setStyleSheet("font-size: 10px; color: #7F8C8D;")
        result_layout.addWidget(self._dose_info_label)

        layout.addWidget(result_frame)
        parent_layout.addWidget(group)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QGroupBox {
                background: """
            + COLORS["surface"]
            + """;
                border: 1px solid """
            + COLORS["border"]
            + """;
                border-radius: 8px;
                margin-top: 12px;
                padding: 16px 12px 12px;
                font-size: 11px;
                font-weight: 600;
                color: """
            + COLORS["text_secondary"]
            + """;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                left: 8px;
                background: """
            + COLORS["surface"]
            + """;
                color: """
            + COLORS["text_muted"]
            + """;
            }
            QFormLayout {
                spacing: 8px;
            }
            QFormLayout label {
                color: """
            + COLORS["text_secondary"]
            + """;
                font-size: 12px;
            }
            QLabel {
                background: transparent;
                color: """
            + COLORS["text_primary"]
            + """;
                font-size: 12px;
            }
            QFrame[frameShape="4"] {
                background: """
            + COLORS["surface2"]
            + """;
                border: 1px solid """
            + COLORS["border"]
            + """;
                border-radius: 6px;
            }
        """
        )

    def _on_calculate_clicked(self) -> None:
        weight = self._weight_input.value()
        self.calculateDose.emit(weight)

    def set_from_image_data(self, data: dict) -> None:
        self._patient_id_label.setText(data.get("patient_id", "—") or "—")
        self._name_label.setText(data.get("name", "—") or "—")
        self._age_label.setText(data.get("age", "—") or "—")
        gender = data.get("gender", "—") or "—"
        if gender and gender not in ("—", "O"):
            gender_map = {"M": "Male", "F": "Female"}
            gender = gender_map.get(gender.upper(), gender)
        self._gender_label.setText(gender)
        self._exam_date_label.setText(data.get("exam_date", "—") or "—")

    def set_matched_data(self, data, confidence: float = 0.0) -> None:
        if data:
            self._status_indicator.setText("●")
            self._status_indicator.setStyleSheet("color: " + COLORS["success"] + ";")
            self._status_text.setText("Data Found")
            self._status_text.setStyleSheet("color: " + COLORS["success"] + ";")
            self._matched_patient_id.setText(data.get("patient_id", "—") or "—")
            self._matched_age.setText(data.get("age", "—") or "—")
            self._matched_gender.setText(data.get("gender", "—") or "—")
        else:
            self._status_indicator.setText("○")
            self._status_indicator.setStyleSheet("color: " + COLORS["text_muted"] + ";")
            self._status_text.setText("No Matching Data")
            self._status_text.setStyleSheet("color: " + COLORS["text_muted"] + ";")
            self._matched_patient_id.setText("—")
            self._matched_age.setText("—")
            self._matched_gender.setText("—")

    def set_dose_result(self, dose_msv: float, comparison_text: str = "") -> None:
        self._dose_value_label.setText(f"{dose_msv:.2f} mSv")
        if comparison_text:
            self._dose_info_label.setText(comparison_text)

    def clear_all(self) -> None:
        self._patient_id_label.setText("—")
        self._name_label.setText("—")
        self._age_label.setText("—")
        self._gender_label.setText("—")
        self._exam_date_label.setText("—")
        self.set_matched_data(None)
        self._dose_value_label.setText("— mSv")
        self._dose_info_label.setText("")

    def set_interactable(self, enabled: bool) -> None:
        self._calculate_btn.setEnabled(enabled)
        self._weight_input.setEnabled(enabled)
