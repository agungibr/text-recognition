import io
import tempfile
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.file_utils import load_dicom_as_bgr
from ui.theme import COLORS
from ui.widgets import ImageViewer


class CenterPanel(QWidget):
    fileSelected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._files: list[dict] = []
        self._results: dict[str, dict] = {}
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(2)

        splitter.addWidget(self._build_queue_pane())
        splitter.addWidget(self._build_preview_pane())
        splitter.setSizes([180, 400])

        root.addWidget(splitter)

    def _build_queue_pane(self) -> QWidget:
        self._queue_pane = QWidget()
        lay = QVBoxLayout(self._queue_pane)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(6)

        hdr = QHBoxLayout()
        self._queue_lbl = QLabel("FILE QUEUE")
        hdr.addWidget(self._queue_lbl)
        hdr.addStretch()
        lay.addLayout(hdr)

        self.file_list = QListWidget()
        self.file_list.setIconSize(QSize(18, 18))
        self.file_list.currentItemChanged.connect(self._on_item_changed)
        lay.addWidget(self.file_list)

        self._apply_queue_style()
        return self._queue_pane

    def _build_preview_pane(self) -> QWidget:
        self._preview_pane = QWidget()
        lay = QVBoxLayout(self._preview_pane)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(6)

        hdr = QHBoxLayout()
        self._preview_lbl = QLabel("PREVIEW")
        self._img_name_lbl = QLabel()
        hdr.addWidget(self._preview_lbl)
        hdr.addStretch()
        hdr.addWidget(self._img_name_lbl)
        lay.addLayout(hdr)

        self.image_viewer = ImageViewer()
        self.image_viewer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        lay.addWidget(self.image_viewer)

        self._apply_preview_style()
        return self._preview_pane

    def _apply_queue_style(self) -> None:
        self._queue_pane.setStyleSheet(
            f"background:{COLORS['surface']};"
            f"border-bottom:1px solid {COLORS['border']};"
        )
        self._queue_lbl.setStyleSheet(
            f"color:{COLORS['text_muted']};"
            f"font-size:10px;font-weight:700;letter-spacing:2px;"
        )

    def _apply_preview_style(self) -> None:
        self._preview_pane.setStyleSheet(f"background:{COLORS['bg']};")
        self._preview_lbl.setStyleSheet(
            f"color:{COLORS['text_muted']};"
            f"font-size:10px;font-weight:700;letter-spacing:2px;"
        )
        self._img_name_lbl.setStyleSheet(
            f"color:{COLORS['text_secondary']};"
            f"font-size:11px;font-family:'Consolas',monospace;"
        )

    def setFiles(self, files: list[dict]) -> None:
        self._files = files
        self.file_list.clear()

        for f in files:
            item = QListWidgetItem(f["name"])
            item.setData(Qt.ItemDataRole.UserRole, f)
            if Path(f["name"]).suffix.lower() == ".dcm":
                item.setForeground(QColor(COLORS["warning"]))
            self.file_list.addItem(item)

    def markProcessed(self, filename: str, result: dict) -> None:
        self._results[filename] = result
        n = len(result.get("detections", []))

        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            fd = item.data(Qt.ItemDataRole.UserRole)
            if fd and fd.get("name") == filename:
                item.setText(f"{filename}  [{n}]")
                item.setForeground(QColor(COLORS["success"]))
                break

    def clearResults(self) -> None:
        self._results.clear()

    def refresh_theme(self) -> None:
        self._apply_queue_style()
        self._apply_preview_style()
        self.image_viewer.refresh_theme()

    def _on_item_changed(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            return

        file_dict = current.data(Qt.ItemDataRole.UserRole)
        if file_dict is None:
            return

        self._img_name_lbl.setText(file_dict["name"])
        self._load_preview(file_dict)
        self.fileSelected.emit(file_dict)

    def _load_preview(self, file_dict: dict) -> None:
        name = file_dict["name"]
        ext = Path(name).suffix.lower()

        if file_dict.get("type") == "path":
            path = file_dict.get("path", "")
            self._preview_from_path(path, ext)

        elif file_dict.get("type") == "bytes":
            self._preview_from_bytes(file_dict.get("data", b""), ext)

        else:
            self.image_viewer.setImage("")

    def _preview_from_path(self, path: str, ext: str) -> None:
        if not path:
            self.image_viewer.setImage("")
            return

        if ext == ".dcm":
            try:
                bgr = load_dicom_as_bgr(path)
                self.image_viewer.setImage(bgr)
            except Exception as exc:
                self.image_viewer.setText(f"Cannot render DICOM: {exc}")
        else:
            self.image_viewer.setImage(path)

    def _preview_from_bytes(self, data: bytes, ext: str) -> None:
        if not data:
            self.image_viewer.setText("Preview unavailable")
            return

        try:
            from PIL import Image

            pil = Image.open(io.BytesIO(data))
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            pil.save(tmp.name)
            tmp.close()
            self.image_viewer.setImage(tmp.name)
        except Exception:
            self.image_viewer.setText("Preview unavailable")
