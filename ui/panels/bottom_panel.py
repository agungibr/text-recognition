"""
Bottom Panel Module
Clean display for extracted OCR and metadata information.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
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
    """Bottom information panel with structured extracted data."""

    save_clicked = Signal()
    clear_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel("Extracted Information")
        title.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 14px; font-weight: 600;"
        )
        header.addWidget(title)
        header.addStretch()

        self._status_label = QLabel("No Text Found")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setFixedHeight(24)
        self._status_label.setStyleSheet(
            f"""
            color: {COLORS['text_muted']};
            background: {COLORS['surface2']};
            border-radius: 12px;
            padding: 0 10px;
            font-size: 11px;
            """
        )
        header.addWidget(self._status_label)

        self._btn_save = QPushButton("Save Results")
        self._btn_save.setObjectName("primary")
        self._btn_save.setFixedHeight(28)
        self._btn_save.clicked.connect(self.save_clicked)
        header.addWidget(self._btn_save)

        self._btn_clear = QPushButton("Clear")
        self._btn_clear.setObjectName("secondary")
        self._btn_clear.setFixedHeight(28)
        self._btn_clear.clicked.connect(self.clear_clicked)
        header.addWidget(self._btn_clear)

        root.addLayout(header)

        card = QWidget()
        card.setStyleSheet(
            f"background: {COLORS['surface']}; border: 1px solid {COLORS['border']}; border-radius: 6px;"
        )
        form = QFormLayout(card)
        form.setContentsMargins(12, 12, 12, 12)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self._patient_name = QLineEdit()
        self._patient_name.setPlaceholderText("Patient name")
        form.addRow("Patient Name", self._patient_name)

        self._exam_type = QLineEdit()
        self._exam_type.setPlaceholderText("Examination type")
        form.addRow("Examination", self._exam_type)

        self._notes = QTextEdit()
        self._notes.setPlaceholderText("Embedded text extracted from image")
        self._notes.setMaximumHeight(92)
        form.addRow("Extracted Text", self._notes)

        root.addWidget(card)
        self._apply_styles()

    def _apply_styles(self) -> None:
        self.setStyleSheet(f"background: {COLORS['bg']};")
        edit_style = (
            f"background: {COLORS['surface2']}; color: {COLORS['text_primary']}; "
            f"border: 1px solid {COLORS['border']}; border-radius: 4px; padding: 6px 8px; font-size: 12px;"
        )
        self._patient_name.setStyleSheet(f"QLineEdit {{ {edit_style} }}")
        self._exam_type.setStyleSheet(f"QLineEdit {{ {edit_style} }}")
        self._notes.setStyleSheet(f"QTextEdit {{ {edit_style} padding: 8px; }}")

    def set_extracted_data(self, data: dict) -> None:
        if data.get("patient_name"):
            self._patient_name.setText(data["patient_name"])
        if data.get("exam_type"):
            self._exam_type.setText(data["exam_type"])
        if data.get("notes"):
            self._notes.setPlainText(data["notes"])
        elif data.get("full_text"):
            text = data["full_text"]
            self._notes.setPlainText(text[:500] + "..." if len(text) > 500 else text)

        self.set_text_found(bool(data.get("full_text") or data.get("patient_name")))

    def set_text_found(self, found: bool) -> None:
        if found:
            self._status_label.setText("Text Found")
            self._status_label.setStyleSheet(
                f"""
                color: {COLORS['success']};
                background: {COLORS['success_bg']};
                border-radius: 12px;
                padding: 0 10px;
                font-size: 11px;
                font-weight: 600;
                """
            )
        else:
            self._status_label.setText("No Text Found")
            self._status_label.setStyleSheet(
                f"""
                color: {COLORS['text_muted']};
                background: {COLORS['surface2']};
                border-radius: 12px;
                padding: 0 10px;
                font-size: 11px;
                """
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
