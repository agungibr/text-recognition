"""
Center Panel Module
Main image viewer panel for displaying radiology images with detection overlay.
"""

from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.theme import COLORS


class ImageDisplayLabel(QLabel):
    """Custom label for displaying images with placeholder support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._placeholder_text = "No image loaded"
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._apply_placeholder_style()

    def set_placeholder(self, text: str) -> None:
        self._placeholder_text = text
        self.clear()
        self.setText(text)
        self._apply_placeholder_style()

    def _apply_placeholder_style(self) -> None:
        self.setStyleSheet(
            f"QLabel {{ background: {COLORS['surface']}; "
            f"border: 2px dashed {COLORS['border_active']}; "
            f"border-radius: 8px; color: {COLORS['text_muted']}; "
            f"font-size: 14px; padding: 20px; }}"
        )

    def clear(self) -> None:
        super().clear()
        self.setText(self._placeholder_text)
        self._apply_placeholder_style()

    def has_image(self) -> bool:
        return self.pixmap() is not None and not self.pixmap().isNull()


class CenterPanel(QWidget):
    """Center panel containing the main image viewer."""

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

        toolbar = self._build_toolbar()
        root.addWidget(toolbar)

        viewer_container = self._build_viewer_area()
        root.addWidget(viewer_container, 1)

        footer = self._build_footer()
        root.addWidget(footer)

    def _build_toolbar(self) -> QWidget:
        toolbar = QWidget()
        toolbar.setFixedHeight(40)
        toolbar.setStyleSheet(
            f"QWidget {{ background: {COLORS['surface']}; "
            f"border-bottom: 1px solid {COLORS['border']}; }}"
        )

        lay = QHBoxLayout(toolbar)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(12)

        self._zoom_out_btn = QPushButton("-")
        self._zoom_out_btn.setFixedSize(28, 28)
        self._zoom_out_btn.setToolTip("Zoom out")
        self._zoom_out_btn.clicked.connect(self._zoom_out)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; "
            f"font-family: 'Consolas', monospace; min-width: 45px;"
        )

        self._zoom_in_btn = QPushButton("+")
        self._zoom_in_btn.setFixedSize(28, 28)
        self._zoom_in_btn.setToolTip("Zoom in")
        self._zoom_in_btn.clicked.connect(self._zoom_in)

        self._reset_zoom_btn = QPushButton("Reset")
        self._reset_zoom_btn.setFixedSize(55, 28)
        self._reset_zoom_btn.setToolTip("Reset zoom to 100%")
        self._reset_zoom_btn.clicked.connect(self._reset_zoom)

        lay.addWidget(self._zoom_out_btn)
        lay.addWidget(self._zoom_label)
        lay.addWidget(self._zoom_in_btn)
        lay.addWidget(self._reset_zoom_btn)
        lay.addSpacing(20)

        self._show_overlay_check = QCheckBox("Show Detections")
        self._show_overlay_check.setChecked(True)
        self._show_overlay_check.setStyleSheet(
            f"QCheckBox {{ color: {COLORS['text_secondary']}; }}"
        )
        self._show_overlay_check.toggled.connect(self._toggle_overlay)
        lay.addWidget(self._show_overlay_check)

        lay.addStretch()

        self._detection_count_lbl = QLabel("No detections")
        self._detection_count_lbl.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px;"
        )
        lay.addWidget(self._detection_count_lbl)

        return toolbar

    def _build_viewer_area(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet(f"background: {COLORS['bg']};")

        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)

        self._image_label = ImageDisplayLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumSize(400, 300)

        scroll = QScrollArea()
        scroll.setWidget(self._image_label)
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay.addWidget(scroll)

        return container

    def _build_footer(self) -> QWidget:
        footer = QWidget()
        footer.setFixedHeight(32)
        footer.setStyleSheet(
            f"QWidget {{ background: {COLORS['surface']}; "
            f"border-top: 1px solid {COLORS['border']}; }}"
        )

        lay = QHBoxLayout(footer)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(20)

        self._size_label = QLabel("Size: -")
        self._size_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px; "
            f"font-family: 'Consolas', monospace;"
        )

        self._footer_zoom_label = QLabel("Zoom: 100%")
        self._footer_zoom_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px; "
            f"font-family: 'Consolas', monospace;"
        )

        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px;"
        )

        lay.addWidget(self._size_label)
        lay.addWidget(self._footer_zoom_label)
        lay.addStretch()
        lay.addWidget(self._status_label)

        return footer

    def set_image(self, path: str) -> bool:
        """Load and display an image from path."""
        try:
            from core.dicom_handler import DicomHandler

            image = DicomHandler.load_image(path)

            if image is None:
                self._show_error(f"Cannot load: {path}")
                return False

            self._current_image = image
            self._detections = []

            self._update_display()

            h, w = image.shape[:2]
            self._size_label.setText(f"Size: {w} x {h}")
            self._status_label.setText("Image loaded")

            self.image_loaded.emit(path, w, h)

            return True

        except Exception as e:
            self._show_error(f"Error loading image: {str(e)}")
            return False

    def set_image_array(self, image: np.ndarray) -> None:
        """Set image from numpy array."""
        self._current_image = image.copy()
        self._detections = []

        self._update_display()

        h, w = image.shape[:2]
        self._size_label.setText(f"Size: {w} x {h}")
        self._status_label.setText("Image set")

        self.image_loaded.emit("", w, h)

    def set_detections(self, detections: list) -> None:
        """Set detection results to overlay on image."""
        self._detections = detections

        count = len(detections)
        if count == 0:
            self._detection_count_lbl.setText("No detections")
            self._status_label.setText("No text found")
        else:
            self._detection_count_lbl.setText(
                f"{count} detection{'s' if count != 1 else ''}"
            )
            self._status_label.setText("Text found")

        self._update_display()

    def _update_display(self) -> None:
        if self._current_image is None:
            self._image_label.set_placeholder("No image loaded")
            return

        display_img = self._current_image.copy()

        if self._show_overlay and self._detections:
            display_img = self._draw_detections(display_img)

        rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w

        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)

        if self._zoom_level != 1.0:
            scaled_size = pixmap.size() * self._zoom_level
            pixmap = pixmap.scaled(
                scaled_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        self._image_label.setPixmap(pixmap)

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

            color = (0, 255, 0)
            cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)

            conf = det.get("conf", 0)
            text = f"{conf:.2f}"

            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(result, (x1, y1 - th - 4), (x1 + tw + 4, y1), color, -1)

            cv2.putText(
                result,
                text,
                (x1 + 2, y1 - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1,
            )

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
        self._footer_zoom_label.setText(f"Zoom: {percent}%")

        self._update_display()

        self.zoom_changed.emit(self._zoom_level)

    def get_zoom_level(self) -> float:
        return self._zoom_level

    def clear(self) -> None:
        self._current_image = None
        self._detections = []
        self._image_label.set_placeholder("No image loaded")
        self._size_label.setText("Size: -")
        self._zoom_label.setText("100%")
        self._footer_zoom_label.setText("Zoom: 100%")
        self._detection_count_lbl.setText("No detections")
        self._status_label.setText("Ready")
        self._zoom_level = 1.0

    def _show_error(self, message: str) -> None:
        self._status_label.setText(message)
        self._image_label.set_placeholder(message)
