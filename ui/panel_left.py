import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton,
    QSlider, QCheckBox, QComboBox, QFileDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.theme import COLORS
from ui.widgets import Badge, Divider


class LeftPanel(QWidget):
    loadModelClicked  = pyqtSignal()
    loadOCRClicked    = pyqtSignal()
    addFilesClicked   = pyqtSignal()
    addFolderClicked  = pyqtSignal()
    clearFilesClicked = pyqtSignal()
    runClicked        = pyqtSignal()
    exportClicked     = pyqtSignal()

    _LANG_MAP: dict[str, list[str]] = {
        "id + en":      ["id", "en"],
        "en only":      ["en"],
        "id only":      ["id"],
        "id + en + ms": ["id", "en", "ms"],
        "ja + en":      ["ja", "en"],
        "ko + en":      ["ko", "en"],
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 14, 12, 14)
        root.setSpacing(0)

        self._add_app_header(root)
        root.addSpacing(14)

        self._add_model_group(root)
        root.addSpacing(10)

        self._add_ocr_group(root)
        root.addSpacing(10)

        self._add_detection_group(root)
        root.addSpacing(10)

        self._add_input_group(root)

        root.addStretch()

        root.addWidget(Divider())
        root.addSpacing(10)

        self.btn_run = QPushButton("▶  Run Detection")
        self.btn_run.setObjectName("primary")
        self.btn_run.setFixedHeight(40)
        self.btn_run.setEnabled(False)
        root.addWidget(self.btn_run)
        root.addSpacing(6)

        self.btn_export = QPushButton("↓  Export Results (ZIP)")
        self.btn_export.setEnabled(False)
        root.addWidget(self.btn_export)

        self.btn_run.clicked.connect(self.runClicked)
        self.btn_export.clicked.connect(self.exportClicked)

    def _add_app_header(self, root: QVBoxLayout) -> None:
        hdr = QWidget()
        hdr.setStyleSheet(
            f"background:{COLORS['surface']};border-radius:6px;"
        )
        lay = QVBoxLayout(hdr)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(2)

        title = QLabel("YOLO · OCR")
        title.setStyleSheet(
            f"color:{COLORS['text_primary']};"
            f"font-size:16px;font-weight:700;"
            f"letter-spacing:1px;font-family:'Consolas',monospace;"
        )
        sub = QLabel("Detection Suite  v1.0")
        sub.setStyleSheet(
            f"color:{COLORS['text_muted']};font-size:11px;letter-spacing:0.5px;"
        )

        lay.addWidget(title)
        lay.addWidget(sub)
        root.addWidget(hdr)

    def _add_model_group(self, root: QVBoxLayout) -> None:
        grp = QGroupBox("Model")
        lay = QVBoxLayout(grp)
        lay.setSpacing(8)

        _default_model = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "models", "best.pt",
        )
        self.model_path_edit = QLineEdit()
        self.model_path_edit.setPlaceholderText("Path to best.pt …")
        if os.path.isfile(_default_model):
            self.model_path_edit.setText(_default_model)

        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(72)
        browse_btn.clicked.connect(self._browse_model)

        path_row = QHBoxLayout()
        path_row.addWidget(self.model_path_edit)
        path_row.addWidget(browse_btn)
        lay.addLayout(path_row)

        status_row = QHBoxLayout()
        self.model_badge = Badge("idle", "Not loaded")
        self.btn_load_model = QPushButton("Load Model")
        self.btn_load_model.setObjectName("primary")
        self.btn_load_model.clicked.connect(self.loadModelClicked)

        status_row.addWidget(self.model_badge)
        status_row.addStretch()
        status_row.addWidget(self.btn_load_model)
        lay.addLayout(status_row)

        root.addWidget(grp)

    def _add_ocr_group(self, root: QVBoxLayout) -> None:
        grp = QGroupBox("OCR Engine")
        lay = QVBoxLayout(grp)
        lay.setSpacing(8)

        lang_row = QHBoxLayout()
        lang_lbl = QLabel("Lang")
        lang_lbl.setStyleSheet(
            f"color:{COLORS['text_secondary']};font-size:12px;"
        )
        lang_lbl.setFixedWidth(34)

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(list(self._LANG_MAP.keys()))
        lang_row.addWidget(lang_lbl)
        lang_row.addWidget(self.lang_combo)
        lay.addLayout(lang_row)

        self.gpu_check = QCheckBox("Use GPU (if available)")
        self.gpu_check.setChecked(True)
        lay.addWidget(self.gpu_check)

        status_row = QHBoxLayout()
        self.ocr_badge = Badge("idle", "Not loaded")
        self.btn_load_ocr = QPushButton("Load OCR")
        self.btn_load_ocr.setObjectName("primary")
        self.btn_load_ocr.clicked.connect(self.loadOCRClicked)

        status_row.addWidget(self.ocr_badge)
        status_row.addStretch()
        status_row.addWidget(self.btn_load_ocr)
        lay.addLayout(status_row)

        root.addWidget(grp)

    def _add_detection_group(self, root: QVBoxLayout) -> None:
        grp = QGroupBox("Detection")
        lay = QVBoxLayout(grp)
        lay.setSpacing(10)

        conf_hdr = QHBoxLayout()
        conf_lbl = QLabel("Confidence")
        conf_lbl.setStyleSheet(
            f"color:{COLORS['text_secondary']};font-size:12px;"
        )
        self._conf_val_lbl = QLabel("0.25")
        self._conf_val_lbl.setStyleSheet(
            f"color:{COLORS['accent']};"
            f"font-size:12px;font-family:'Consolas',monospace;font-weight:600;"
        )
        self._conf_val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        conf_hdr.addWidget(conf_lbl)
        conf_hdr.addStretch()
        conf_hdr.addWidget(self._conf_val_lbl)
        lay.addLayout(conf_hdr)

        self.conf_slider = QSlider(Qt.Orientation.Horizontal)
        self.conf_slider.setRange(0, 100)
        self.conf_slider.setValue(25)
        self.conf_slider.valueChanged.connect(
            lambda v: self._conf_val_lbl.setText(f"{v / 100:.2f}")
        )
        lay.addWidget(self.conf_slider)

        self.save_crops_check = QCheckBox("Save cropped detections")
        self.save_crops_check.setChecked(True)
        lay.addWidget(self.save_crops_check)

        root.addWidget(grp)

    def _add_input_group(self, root: QVBoxLayout) -> None:
        grp = QGroupBox("Input Files")
        lay = QVBoxLayout(grp)
        lay.setSpacing(6)

        btn_row = QHBoxLayout()
        self.btn_add_files  = QPushButton("+ Files")
        self.btn_add_folder = QPushButton("+ Folder")
        self.btn_clear      = QPushButton("Clear")
        self.btn_clear.setObjectName("danger")

        btn_row.addWidget(self.btn_add_files)
        btn_row.addWidget(self.btn_add_folder)
        btn_row.addWidget(self.btn_clear)
        lay.addLayout(btn_row)

        self._file_count_lbl = QLabel("0 files queued")
        self._file_count_lbl.setStyleSheet(
            f"color:{COLORS['text_muted']};font-size:11px;"
        )
        lay.addWidget(self._file_count_lbl)

        self.btn_add_files.clicked.connect(self.addFilesClicked)
        self.btn_add_folder.clicked.connect(self.addFolderClicked)
        self.btn_clear.clicked.connect(self.clearFilesClicked)

        root.addWidget(grp)

    def _browse_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select YOLO model",
            "",
            "PyTorch Model (*.pt *.pth)",
        )
        if path:
            self.model_path_edit.setText(path)

    @property
    def model_path(self) -> str:
        return self.model_path_edit.text().strip()

    @property
    def conf(self) -> float:
        return self.conf_slider.value() / 100.0

    @property
    def save_crops(self) -> bool:
        return self.save_crops_check.isChecked()

    @property
    def use_gpu(self) -> bool:
        return self.gpu_check.isChecked()

    @property
    def languages(self) -> list[str]:
        return self._LANG_MAP.get(
            self.lang_combo.currentText(), ["id", "en"]
        )

    def setFileCount(self, n: int) -> None:
        word = "file" if n == 1 else "files"
        self._file_count_lbl.setText(f"{n} {word} queued")

    def setRunnable(self, enabled: bool) -> None:
        self.btn_run.setEnabled(enabled)

    def setExportable(self, enabled: bool) -> None:
        self.btn_export.setEnabled(enabled)
