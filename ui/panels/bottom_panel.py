"""
Bottom Panel Module
Displays extracted information from OCR processing.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.theme import COLORS


class BottomPanel(QWidget):
    """Bottom panel showing extracted text information."""

    save_clicked = Signal()
    clear_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(8)

        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)

        self._title = QLabel("Extracted Information")
        self._title.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 14px; font-weight: 600;"
        )
        title_layout.addWidget(self._title)
        title_layout.addStretch()

        self._status_label = QLabel("No Text Found")
        self._status_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 12px; padding: 4px 12px; background: {COLORS['surface2']}; border-radius: 12px;"
        )
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self._status_label)

        self._btn_clear = QPushButton("Clear")
        self._btn_clear.setFixedSize(70, 28)
        self._btn_clear.setObjectName("danger")
        self._btn_clear.clicked.connect(self.clear_clicked)
        title_layout.addWidget(self._btn_clear)

        main_layout.addLayout(title_layout)

        info_group = QGroupBox()
        info_layout = QFormLayout(info_group)
        info_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        info_layout.setFormAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        info_layout.setSpacing(12)
        info_layout.setContentsMargins(16, 24, 16, 12)

        self._patient_name = QLineEdit()
        self._patient_name.setPlaceholderText("Patient name from OCR...")
        info_layout.addRow("Patient Name:", self._patient_name)

        self._exam_type = QLineEdit()
        self._exam_type.setPlaceholderText("e.g., CT Head, Chest X-ray...")
        info_layout.addRow("Examination Type:", self._exam_type)

        notes_layout = QVBoxLayout()
        self._notes = QTextEdit()
        self._notes.setPlaceholderText("Additional notes from OCR extraction...")
        self._notes.setMaximumHeight(80)
        notes_layout.addWidget(self._notes)
        info_layout.addRow("Notes:", notes_layout)

        main_layout.addWidget(info_group)
        self._apply_styles()

    def _apply_styles(self) -> None:
        self.setStyleSheet(f"background: {COLORS['bg']};")
        for child in self.findChildren(QLineEdit):
            child.setStyleSheet(
                f"QLineEdit {{ background: {COLORS['surface2']}; color: {COLORS['text_primary']}; border: 1px solid {COLORS['border']}; border-radius: 4px; padding: 6px 10px; font-size: 12px; }}"
            )
        self._notes.setStyleSheet(
            f"QTextEdit {{ background: {COLORS['surface2']}; color: {COLORS['text_primary']}; border: 1px solid {COLORS['border']}; border-radius: 4px; padding: 8px; font-size: 12px; }}"
        )

    def set_extracted_data(self, data: dict) -> None:
        if "patient_name" in data and data["patient_name"]:
            self._patient_name.setText(data["patient_name"])
        if "exam_type" in data and data["exam_type"]:
            self._exam_type.setText(data["exam_type"])
        if "notes" in data and data["notes"]:
            self._notes.setText(data["notes"])
        elif "full_text" in data and data["full_text"]:
            text = data["full_text"]
            if len(text) > 500:
                text = text[:500] + "..."
            self._notes.setText(text)
        has_text = bool(data.get("full_text") or data.get("patient_name"))
        self.set_text_found(has_text)

    def set_text_found(self, found: bool) -> None:
        if found:
            self._status_label.setText("Text Found")
            self._status_label.setStyleSheet(
                f"color: {COLORS['success']}; font-size: 12px; font-weight: 600; padding: 4px 12px; background: {COLORS['success']}20; border-radius: 12px;"
            )
        else:
            self._status_label.setText("No Text Found")
            self._status_label.setStyleSheet(
                f"color: {COLORS['text_muted']}; font-size: 12px; padding: 4px 12px; background: {COLORS['surface2']}; border-radius: 12px;"
            )

    def get_extracted_data(self) -> dict:
        return {
            "patient_name": self._patient_name.text().strip(),
            "exam_type": self._exam_type.text().strip(),
            "notes": self._notes.toPlainText().strip(),
        }

    def clear(self) -> None:
        self._patient_name.clear()
        self._exam_type.clear()
        self._notes.clear()
        self.set_text_found(False)

    def get_patient_name(self) -> str:
        return self._patient_name.text()

    def get_exam_type(self) -> str:
        return self._exam_type.text()

    def get_notes(self) -> str:
        return self._notes.toPlainText()
