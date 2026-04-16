"""
Center Panel Module - DICOM Viewer

Professional-style viewer using QGraphicsView/QGraphicsScene with
pan, wheel zoom, and smooth image rendering.
"""

from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.theme import COLORS


class DicomGraphicsView(QGraphicsView):
    """High-quality interactive image view (pan + zoom) for DICOM images."""

    zoom_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._placeholder_item: Optional[QGraphicsSimpleTextItem] = None

        self._zoom_level = 1.0
        self._min_zoom = 0.15
        self._max_zoom = 8.0

        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setBackgroundBrush(Qt.GlobalColor.black)

        self._show_placeholder("No image loaded")

    def _show_placeholder(self, text: str) -> None:
        self._scene.clear()
        self._pixmap_item = None
        self._placeholder_item = self._scene.addSimpleText(text)
        self._placeholder_item.setBrush(Qt.GlobalColor.lightGray)
        self._scene.setSceneRect(-200, -40, 400, 80)
        self.centerOn(0, 0)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.resetTransform()
        self._zoom_level = 1.0
        self.zoom_changed.emit(self._zoom_level)

    def has_image(self) -> bool:
        return self._pixmap_item is not None

    def clear_image(self) -> None:
        self._show_placeholder("No image loaded")

    def set_image(self, bgr_image: np.ndarray, preserve_view: bool = False) -> None:
        if bgr_image is None or bgr_image.size == 0:
            self._show_placeholder("No image loaded")
            return

        rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
        pix = QPixmap.fromImage(qimg)

        if preserve_view and self._pixmap_item is not None:
            self._pixmap_item.setPixmap(pix)
            self._scene.setSceneRect(self._pixmap_item.boundingRect())
            return

        self._scene.clear()
        self._placeholder_item = None
        self._pixmap_item = self._scene.addPixmap(pix)
        self._scene.setSceneRect(self._pixmap_item.boundingRect())
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.resetTransform()
        self._zoom_level = 1.0
        self.zoom_changed.emit(self._zoom_level)
        self.fit_in_view()

    def fit_in_view(self) -> None:
        if not self.has_image():
            return
        self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom_level = float(self.transform().m11())
        self.zoom_changed.emit(self._zoom_level)

    def get_zoom_level(self) -> float:
        return self._zoom_level

    def set_zoom_level(self, new_zoom: float) -> None:
        if not self.has_image():
            return
        new_zoom = max(self._min_zoom, min(new_zoom, self._max_zoom))
        if abs(new_zoom - self._zoom_level) < 1e-8:
            return
        factor = new_zoom / self._zoom_level
        self.scale(factor, factor)
        self._zoom_level = new_zoom
        self.zoom_changed.emit(self._zoom_level)

    def wheelEvent(self, event) -> None:
        if not self.has_image():
            event.ignore()
            return

        zoom_factor = 1.15 if event.angleDelta().y() > 0 else (1.0 / 1.15)
        target_zoom = self._zoom_level * zoom_factor
        target_zoom = max(self._min_zoom, min(target_zoom, self._max_zoom))
        self.set_zoom_level(target_zoom)
        event.accept()


class CenterPanel(QWidget):
    """Center panel containing professional interactive image viewer."""

    zoom_changed = Signal(float)
    image_loaded = Signal(str, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_image: Optional[np.ndarray] = None
        self._detections: list = []
        self._show_overlay = True
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        toolbar = self._create_toolbar()
        root.addWidget(toolbar)

        viewer_container = self._create_viewer_area()
        root.addWidget(viewer_container, 1)

        footer = self._create_footer()
        root.addWidget(footer)

    def _create_toolbar(self) -> QWidget:
        toolbar = QWidget()
        toolbar.setFixedHeight(38)
        toolbar.setStyleSheet(
            f"""
            QWidget {{
                background: {COLORS['surface']};
                border-bottom: 1px solid {COLORS['border']};
            }}
            """
        )

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        # Zoom controls
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(zoom_label)

        self._zoom_out_btn = QPushButton("−")
        self._zoom_out_btn.setFixedSize(26, 26)
        self._zoom_out_btn.clicked.connect(self._zoom_out)
        layout.addWidget(self._zoom_out_btn)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setFixedWidth(50)
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zoom_label.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-family: Consolas, monospace; font-size: 11px;"
        )
        layout.addWidget(self._zoom_label)

        self._zoom_in_btn = QPushButton("+")
        self._zoom_in_btn.setFixedSize(26, 26)
        self._zoom_in_btn.clicked.connect(self._zoom_in)
        layout.addWidget(self._zoom_in_btn)

        self._fit_btn = QPushButton("Fit")
        self._fit_btn.setFixedHeight(26)
        self._fit_btn.clicked.connect(self._fit_view)
        layout.addWidget(self._fit_btn)

        self._reset_zoom_btn = QPushButton("Reset")
        self._reset_zoom_btn.setFixedHeight(26)
        self._reset_zoom_btn.clicked.connect(self._reset_zoom)
        layout.addWidget(self._reset_zoom_btn)

        layout.addStretch()

        self._detection_count_lbl = QLabel("No detections")
        self._detection_count_lbl.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px;"
        )
        layout.addWidget(self._detection_count_lbl)

        return toolbar

    def _create_viewer_area(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet(f"background: {COLORS['bg']};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)

        self._graphics_view = DicomGraphicsView()
        self._graphics_view.zoom_changed.connect(self._on_view_zoom_changed)
        self._graphics_view.setStyleSheet(
            f"""
            QGraphicsView {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
            """
        )
        layout.addWidget(self._graphics_view)
        return container

    def _create_footer(self) -> QWidget:
        footer = QWidget()
        footer.setFixedHeight(80)
        footer.setStyleSheet(
            f"""
            QWidget {{
                background: {COLORS['surface']};
                border-top: 1px solid {COLORS['border']};
            }}
            """
        )

        layout = QVBoxLayout(footer)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # First row: Image info
        info_row1 = QWidget()
        info_layout1 = QHBoxLayout(info_row1)
        info_layout1.setContentsMargins(0, 0, 0, 0)
        info_layout1.setSpacing(24)

        self._size_label = QLabel("Size: -")
        self._size_label.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 11px; font-family: Consolas, monospace; font-weight: 500;"
        )
        info_layout1.addWidget(self._size_label)

        self._footer_zoom_label = QLabel("Zoom: 100%")
        self._footer_zoom_label.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 11px; font-family: Consolas, monospace; font-weight: 500;"
        )
        info_layout1.addWidget(self._footer_zoom_label)

        info_layout1.addStretch()

        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px;"
        )
        info_layout1.addWidget(self._status_label)

        layout.addWidget(info_row1)

        # Second row: Pixel info (will be updated when mouse over image)
        info_row2 = QWidget()
        info_layout2 = QHBoxLayout(info_row2)
        info_layout2.setContentsMargins(0, 0, 0, 0)
        info_layout2.setSpacing(24)

        self._mouse_pos_label = QLabel("X: - Y: -")
        self._mouse_pos_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 10px; font-family: Consolas, monospace;"
        )
        info_layout2.addWidget(self._mouse_pos_label)

        self._pixel_value_label = QLabel("Value: -")
        self._pixel_value_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 10px; font-family: Consolas, monospace;"
        )
        info_layout2.addWidget(self._pixel_value_label)

        info_layout2.addStretch()

        layout.addWidget(info_row2)

        return footer

    def _on_view_zoom_changed(self, zoom: float) -> None:
        percent = max(1, int(round(zoom * 100)))
        self._zoom_label.setText(f"{percent}%")
        self._footer_zoom_label.setText(f"Zoom: {percent}%")
        self.zoom_changed.emit(zoom)

    def set_image(self, path: str) -> bool:
        """Load and display an image from path."""
        try:
            from core.dicom_handler import DicomHandler

            image = DicomHandler.load_image(path, include_overlay=True)
            if image is None:
                self._status_label.setText("Cannot load image")
                self._graphics_view.clear_image()
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
            self._status_label.setText(f"Error: {str(e)}")
            self._graphics_view.clear_image()
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
            self._graphics_view.clear_image()
            return

        display_img = self._current_image.copy()
        if self._show_overlay and self._detections:
            display_img = self._draw_detections(display_img)

        had_image = self._graphics_view.has_image()
        self._graphics_view.set_image(display_img, preserve_view=had_image)

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

            color = (80, 200, 120)
            cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)

            conf = det.get("conf", 0)
            text = f"{conf:.0%}"
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(result, (x1, y1 - th - 6), (x1 + tw + 6, y1), color, -1)
            cv2.putText(
                result,
                text,
                (x1 + 3, y1 - 3),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 0, 0),
                1,
            )
        return result

    def _toggle_overlay(self, checked: bool) -> None:
        self._show_overlay = checked
        self._update_display()

    def _zoom_in(self) -> None:
        self._graphics_view.set_zoom_level(self._graphics_view.get_zoom_level() * 1.15)

    def _zoom_out(self) -> None:
        self._graphics_view.set_zoom_level(self._graphics_view.get_zoom_level() / 1.15)

    def _reset_zoom(self) -> None:
        self._graphics_view.set_zoom_level(1.0)

    def _fit_view(self) -> None:
        self._graphics_view.fit_in_view()

    def get_zoom_level(self) -> float:
        return self._graphics_view.get_zoom_level()

    def clear(self) -> None:
        self._current_image = None
        self._detections = []
        self._graphics_view.clear_image()
        self._size_label.setText("Size: -")
        self._zoom_label.setText("100%")
        self._footer_zoom_label.setText("Zoom: 100%")
        self._mouse_pos_label.setText("X: - Y: -")
        self._pixel_value_label.setText("Value: -")
        self._detection_count_lbl.setText("No detections")
        self._status_label.setText("Ready")
