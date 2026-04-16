"""
Left Panel Module - File Browser Only

Simple file browser for selecting and opening DICOM files.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QListWidget,
    QListWidgetItem,
)

from ui.theme import COLORS


class LeftPanel(QWidget):
    """Left panel - File browser only."""

    fileSelected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(220)
        self.setMaximumWidth(280)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Create file browser card
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

        # File Browser Section
        layout.addWidget(self._create_file_browser_section())
        layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)

    def _create_file_browser_section(self) -> QFrame:
        """Create file browser section matching wireframe."""
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

        title_label = QLabel("Files")
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
        content_layout.setSpacing(8)

        # File list
        self._file_list = QListWidget()
        self._file_list.setMinimumHeight(300)
        self._file_list.setStyleSheet(f"""
            QListWidget {{
                background: {COLORS['surface2']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                outline: none;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 3px;
                color: {COLORS['text_secondary']};
                border: none;
            }}
            QListWidget::item:selected {{
                background: {COLORS['accent_bg']};
                color: {COLORS['text_primary']};
                font-weight: 500;
            }}
            QListWidget::item:hover {{
                background: {COLORS['surface3']};
            }}
        """)
        self._file_list.itemSelectionChanged.connect(self._on_file_selected)
        content_layout.addWidget(self._file_list)

        layout.addWidget(content)
        return card

    def _on_file_selected(self) -> None:
        """Handle file selection."""
        selected_items = self._file_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path:
                self.fileSelected.emit(file_path)

    def add_file(self, file_path: str, display_name: str = None) -> None:
        """Add a file to the list."""
        if display_name is None:
            display_name = file_path.split("\\")[-1] if "\\" in file_path else file_path.split("/")[-1]

        item = QListWidgetItem(display_name)
        item.setData(Qt.ItemDataRole.UserRole, file_path)
        self._file_list.addItem(item)

    def clear_files(self) -> None:
        """Clear all files from the list."""
        self._file_list.clear()

    def set_files(self, files: list) -> None:
        """Set files list. files is a list of (path, display_name) tuples."""
        self.clear_files()
        for file_path, display_name in files:
            self.add_file(file_path, display_name)

    def get_selected_file(self) -> str:
        """Get the currently selected file path."""
        selected_items = self._file_list.selectedItems()
        if selected_items:
            return selected_items[0].data(Qt.ItemDataRole.UserRole)
        return None

    def clear_all(self) -> None:
        """Clear all files from the list (compatibility method)."""
        self.clear_files()

    def set_from_image_data(self, data: dict) -> None:
        """Set patient data from DICOM metadata (compatibility method)."""
        pass  # Left panel is now files-only, data displayed in right panel

    def set_matched_data(self, data, confidence: float = 0.0) -> None:
        """Set matched patient data (compatibility method)."""
        pass  # Not used in simplified left panel

    def set_dose_result(self, dose_msv: float, comparison_text: str = "") -> None:
        """Display dose result (compatibility method)."""
        pass  # Dose shown in right panel instead
