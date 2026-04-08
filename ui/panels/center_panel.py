"""
Center Panel Module - Image Viewer

Clinical-grade image viewer for radiology images with detection overlay.
Designed for clarity and minimal visual noise.
"""

from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.theme import COLORS


class CenterPanel(QWidget):
    """Center panel - Main image viewer with detection overlay."""

    zoom_changed = Signal(float)
    image_loaded = Signal(str, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_image: Optional[np.ndarray] = None
        self._detections: list = []
        self._show_overlay = True
        self._zoom_level = 1.0
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar
        toolbar = self._create_toolbar()
        root.addWidget(toolbar)

        # Image viewer area
        viewer = self._create_viewer()
        root.addWidget(viewer, 1)

        # Footer
        footer = self._create_footer()
        root.addWidget(footer)

    def _create_toolbar(self) -> QWidget:
        """Create minimal toolbar with zoom controls."""
        toolbar = QWidget()
        toolbar.setFixedHeight(38)
        toolbar.setStyleSheet(f"""
            QWidget {{
                background: {COLORS["surface"]};
                border-bottom: 1px solid {COLORS["border"]};
            }}
        """)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        # Zoom controls
        zoom_label = QLabel("Zoom")
        zoom_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(zoom_label)

        self._zoom_out_btn = QPushButton("−")
        self._zoom_out_btn.setFixedSize(26, 26)
        self._zoom_out_btn.setToolTip("Zoom out")
        self._zoom_out_btn.clicked.connect(self._zoom_out)
        self._zoom_out_btn.setStyleSheet(self._get_zoom_btn_style())
        layout.addWidget(self._zoom_out_btn)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setFixedWidth(45)
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zoom_label.setStyleSheet(f"""
            color: {COLORS["text_primary"]};
            font-family: "Consolas", monospace;
            font-size: 11px;
        """)
        layout.addWidget(self._zoom_label)

        self._zoom_in_btn = QPushButton("+")
        self._zoom_in_btn.setFixedSize(26, 26)
        self._zoom_in_btn.setToolTip("Zoom in")
        self._zoom_in_btn.clicked.connect(self._zoom_in)
        self._zoom_in_btn.setStyleSheet(self._get_zoom_btn_style())
        layout.addWidget(self._zoom_in_btn)

        self._reset_btn = QPushButton("Reset")
        self._reset_btn.setFixedHeight(26)
        self._reset_btn.setToolTip("Reset zoom to 100%")
        self._reset_btn.clicked.connect(self._reset_zoom)
        self._reset_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS["text_secondary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
                padding: 0 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {COLORS["surface2"]};
                color: {COLORS["text_primary"]};
            }}
        """)
        layout.addWidget(self._reset_btn)

        layout.addSpacing(16)

        # Detection toggle
        self._show_overlay_check = QCheckBox("Show Detections")
        self._show_overlay_check.setChecked(True)
        self._show_overlay_check.toggled.connect(self._toggle_overlay)
        self._show_overlay_check.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS["text_secondary"]};
                font-size: 12px;
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border-radius: 3px;
                border: 1px solid {COLORS["border_light"]};
                background: {COLORS["surface2"]};
            }}
            QCheckBox::indicator:checked {{
                background: {COLORS["accent"]};
                border-color: {COLORS["accent"]};
            }}
        """)
        layout.addWidget(self._show_overlay_check)

        layout.addStretch()

        # Detection count
        self._detection_label = QLabel("No detections")
        self._detection_label.setStyleSheet(f"""
            color: {COLORS["text_muted"]};
            font-size: 11px;
            padding: 3px 8px;
            background: {COLORS["surface2"]};
            border-radius: 3px;
        """)
        layout.addWidget(self._detection_label)

        return toolbar

    def _get_zoom_btn_style(self) -> str:
        return f"""
            QPushButton {{
                background: {COLORS["surface2"]};
                color: {COLORS["text_primary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {COLORS["surface3"]};
            }}
            QPushButton:pressed {{
                background: {COLORS["accent_dim"]};
            }}
        """

    def _create_viewer(self) -> QWidget:
        """Create image display area."""
        container = QWidget()
        container.setStyleSheet(f"background: {COLORS['bg']};")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)

        # Image label inside scroll area
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumSize(400, 300)
        self._image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._show_placeholder()

        scroll = QScrollArea()
        scroll.setWidget(self._image_label)
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
            }}
        """)

        layout.addWidget(scroll)
        return container

    def _create_footer(self) -> QWidget:
        """Create footer with image info."""
        footer = QWidget()
        footer.setFixedHeight(28)
        footer.setStyleSheet(f"""
            QWidget {{
                background: {COLORS["surface"]};
                border-top: 1px solid {COLORS["border"]};
            }}
        """)

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(16)

        self._size_label = QLabel("Size: —")
        self._size_label.setStyleSheet(f"""
            color: {COLORS["text_muted"]};
            font-size: 11px;
            font-family: "Consolas", monospace;
        """)
        layout.addWidget(self._size_label)

        self._zoom_footer_label = QLabel("Zoom: 100%")
        self._zoom_footer_label.setStyleSheet(f"""
            color: {COLORS["text_muted"]};
            font-size: 11px;
            font-family: "Consolas", monospace;
        """)
        layout.addWidget(self._zoom_footer_label)

        layout.addStretch()

        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet(f"""
            color: {COLORS["text_secondary"]};
            font-size: 11px;
        """)
        layout.addWidget(self._status_label)

        return footer

    def _show_placeholder(self, text: str = "No image loaded") -> None:
        """Show placeholder text when no image."""
        self._image_label.clear()
        self._image_label.setText(text)
        self._image_label.setStyleSheet(f"""
            QLabel {{
                background: {COLORS["surface"]};
                border: 1px dashed {COLORS["border_light"]};
                border-radius: 6px;
                color: {COLORS["text_muted"]};
                font-size: 13px;
            }}
        """)

    def set_image(self, path: str) -> bool:
        """Load and display image from path."""
        try:
            from core.dicom_handler import DicomHandler

            image = DicomHandler.load_image(path)
            if image is None:
                self._show_placeholder(f"Cannot load: {path}")
                return False

            self._current_image = image
            self._detections = []
            self._update_display()

            h, w = image.shape[:2]
            self._size_label.setText(f"Size: {w} × {h}")
            self._status_label.setText("Image loaded")

            self.image_loaded.emit(path, w, h)
            return True

        except Exception as e:
            self._show_placeholder(f"Error: {e}")
            return False

    def set_image_array(self, image: np.ndarray) -> None:
        """Set image from numpy array."""
        self._current_image = image.copy()
        self._detections = []
        self._update_display()

        h, w = image.shape[:2]
        self._size_label.setText(f"Size: {w} × {h}")
        self._status_label.setText("Image set")

        self.image_loaded.emit("", w, h)

    def set_detections(self, detections: list) -> None:
        """Set detection results for overlay."""
        self._detections = detections
        count = len(detections)

        if count == 0:
            self._detection_label.setText("No detections")
            self._status_label.setText("No text found")
        else:
            self._detection_label.setText(f"{count} detection{'s' if count != 1 else ''}")
            self._status_label.setText("Text detected")

        self._update_display()

    def _update_display(self) -> None:
        """Update the displayed image with optional overlay."""
        if self._current_image is None:
            self._show_placeholder()
            return

        display_img = self._current_image.copy()

        if self._show_overlay and self._detections:
            display_img = self._draw_detections(display_img)

        # Convert to QPixmap
        rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)

        # Apply zoom
        if self._zoom_level != 1.0:
            scaled_size = pixmap.size() * self._zoom_level
            pixmap = pixmap.scaled(
                scaled_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        self._image_label.setPixmap(pixmap)
        self._image_label.setStyleSheet(f"background: {COLORS['bg']};")

    def _draw_detections(self, image: np.ndarray) -> np.ndarray:
        """Draw detection boxes on image."""
        result = image.copy()
        h, w = result.shape[:2]

        for det in self._detections:
            xyxy = det.get("xyxy", [])
            if len(xyxy) != 4:
                continue

            x1, y1, x2, y2 = xyxy
            x1 = max(0, min(x1, w - 1))
            y1 = max(0, min(y1, h - 1))
            x2 = max(x1 + 1, min(x2, w))
            y2 = max(y1 + 1, min(y2, h))

            # Clinical green for detections
            color = (80, 200, 120)
            cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)

            # Confidence label
            conf = det.get("conf", 0)
            label = f"{conf:.0%}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(result, (x1, y1 - th - 6), (x1 + tw + 6, y1), color, -1)
            cv2.putText(result, label, (x1 + 3, y1 - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)

        return result

    def _toggle_overlay(self, checked: bool) -> None:
        self._show_overlay = checked
        self._update_display()

    def _zoom_in(self) -> None:
        self._set_zoom(self._zoom_level * 1.25)

    def _zoom_out(self) -> None:
        self._set_zoom(self._zoom_level / 1.25)

    def _reset_zoom(self) -> None:
        self._set_zoom(1.0)

    def _set_zoom(self, level: float) -> None:
        self._zoom_level = max(0.1, min(level, 5.0))
        percent = int(self._zoom_level * 100)
        self._zoom_label.setText(f"{percent}%")
        self._zoom_footer_label.setText(f"Zoom: {percent}%")
        self._update_display()
        self.zoom_changed.emit(self._zoom_level)

    def get_zoom_level(self) -> float:
        return self._zoom_level

    def clear(self) -> None:
        """Clear the displayed image."""
        self._current_image = None
        self._detections = []
        self._show_placeholder()
        self._size_label.setText("Size: —")
        self._zoom_label.setText("100%")
        self._zoom_footer_label.setText("Zoom: 100%")
        self._detection_label.setText("No detections")
        self._status_label.setText("Ready")
        self._zoom_level = 1.0
