"""
ui/panel_left.py
────────────────
Left configuration panel — 280 px fixed-width sidebar.

Layout
──────
┌─────────────────────────────────────────┐
│  QScrollArea  (flexible, scrollable)    │
│  ┌───────────────────────────────────┐  │
│  │  MODEL          SectionGroup      │  │
│  │  OCR ENGINE     SectionGroup      │  │
│  │  DETECTION      SectionGroup      │  │
│  │  INPUT FILES    SectionGroup      │  │
│  └───────────────────────────────────┘  │
├─────────────────────────────────────────┤
│  [hint label — what's still needed]     │  ← always visible
│  ──────────────────────────────────     │
│  [▶  Run Detection]                     │
│  [↓  Export Results (ZIP)]              │
└─────────────────────────────────────────┘

The "YOLO · OCR / Detection Suite" header has been removed — it duplicates
the topbar title and wasted ~80 px of vertical space, causing the section
groups to be cramped / overflow on smaller windows.

The config area is wrapped in a QScrollArea so the panel never clips content
regardless of window height.  Run / Export live outside the scroll area so
they are always reachable without scrolling.

GC / ownership notes
────────────────────
Every widget that would otherwise be a local-variable stack casualty is
either:
  • stored as  self._xxx  (keeps the Python wrapper alive), OR
  • constructed with an explicit  parent=  argument (transfers C++ ownership
    to Qt immediately at construction time, before any stack frame can exit).

SectionGroup (ui/widgets.py) already stores its own internal children on
self, so all four section boxes are safe the moment they appear in self._xxx.
"""

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ui.theme import COLORS
from ui.widgets import Badge, Divider, SectionGroup


class LeftPanel(QWidget):
    """
    Configuration sidebar (fixed width 280 px).

    Signals
    -------
    loadModelClicked   – user pressed "Load Model"
    loadOCRClicked     – user pressed "Load OCR"
    addFilesClicked    – user pressed "+ Files"
    addFolderClicked   – user pressed "+ Folder"
    clearFilesClicked  – user pressed "Clear"
    runClicked         – user pressed "▶ Run Detection"
    exportClicked      – user pressed "↓ Export Results"
    """

    loadModelClicked = pyqtSignal()
    loadOCRClicked = pyqtSignal()
    addFilesClicked = pyqtSignal()
    addFolderClicked = pyqtSignal()
    clearFilesClicked = pyqtSignal()
    runClicked = pyqtSignal()
    exportClicked = pyqtSignal()

    # ── language-combo text → EasyOCR language codes ──────────────────────────
    _LANG_MAP: dict[str, list[str]] = {
        "id + en": ["id", "en"],
        "en only": ["en"],
        "id only": ["id"],
        "id + en + ms": ["id", "en", "ms"],
        "ja + en": ["ja", "en"],
        "ko + en": ["ko", "en"],
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280)
        self._build()

    # =========================================================================
    #  BUILD
    # =========================================================================

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── scrollable config area ─────────────────────────────────────────
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background: {COLORS['bg']}; border: none; }}"
        )

        self._scroll_widget = QWidget(self._scroll)
        self._scroll_widget.setStyleSheet(f"background: {COLORS['bg']};")
        self._scroll.setWidget(self._scroll_widget)

        self._inner_layout = QVBoxLayout(self._scroll_widget)
        self._inner_layout.setContentsMargins(10, 12, 10, 12)
        self._inner_layout.setSpacing(10)

        # build the four section groups into the scrollable area
        self._build_model_section()
        self._build_ocr_section()
        self._build_detection_section()
        self._build_input_section()
        self._inner_layout.addStretch()

        root.addWidget(self._scroll, 1)  # stretch = 1 → takes all spare height

        # ── fixed bottom strip (always visible, outside scroll) ────────────
        self._build_bottom(root)

    # ── section builders ──────────────────────────────────────────────────────

    def _build_model_section(self) -> None:
        self._box_model = SectionGroup("Model", self._scroll_widget)
        lay = self._box_model.inner_layout()

        # auto-fill model path if models/best.pt exists
        _default = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "models",
            "best.pt",
        )
        self.model_path_edit = QLineEdit(self._box_model)
        self.model_path_edit.setPlaceholderText("Path to best.pt …")
        if os.path.isfile(_default):
            self.model_path_edit.setText(_default)

        self._browse_btn = QPushButton("Browse", self._box_model)
        self._browse_btn.setFixedWidth(68)
        self._browse_btn.clicked.connect(self._browse_model)

        self._model_path_row = QHBoxLayout()
        self._model_path_row.setSpacing(6)
        self._model_path_row.addWidget(self.model_path_edit)
        self._model_path_row.addWidget(self._browse_btn)
        lay.addLayout(self._model_path_row)

        self.model_badge = Badge("idle", "Not loaded", self._box_model)
        self.btn_load_model = QPushButton("Load Model", self._box_model)
        self.btn_load_model.setObjectName("primary")
        self.btn_load_model.clicked.connect(self.loadModelClicked)

        self._model_status_row = QHBoxLayout()
        self._model_status_row.addWidget(self.model_badge)
        self._model_status_row.addStretch()
        self._model_status_row.addWidget(self.btn_load_model)
        lay.addLayout(self._model_status_row)

        self._inner_layout.addWidget(self._box_model)

    def _build_ocr_section(self) -> None:
        self._box_ocr = SectionGroup("OCR Engine", self._scroll_widget)
        lay = self._box_ocr.inner_layout()

        self._lang_lbl = QLabel("Lang", self._box_ocr)
        self._lang_lbl.setStyleSheet(
            f"color:{COLORS['text_secondary']};font-size:12px;"
            f"background:transparent;border:none;"
        )
        self._lang_lbl.setFixedWidth(34)

        self.lang_combo = QComboBox(self._box_ocr)
        self.lang_combo.addItems(list(self._LANG_MAP.keys()))

        self._lang_row = QHBoxLayout()
        self._lang_row.addWidget(self._lang_lbl)
        self._lang_row.addWidget(self.lang_combo)
        lay.addLayout(self._lang_row)

        self.gpu_check = QCheckBox("Use GPU (if available)", self._box_ocr)
        self.gpu_check.setChecked(True)
        lay.addWidget(self.gpu_check)

        self.ocr_badge = Badge("idle", "Not loaded", self._box_ocr)
        self.btn_load_ocr = QPushButton("Load OCR", self._box_ocr)
        self.btn_load_ocr.setObjectName("primary")
        self.btn_load_ocr.clicked.connect(self.loadOCRClicked)

        self._ocr_status_row = QHBoxLayout()
        self._ocr_status_row.addWidget(self.ocr_badge)
        self._ocr_status_row.addStretch()
        self._ocr_status_row.addWidget(self.btn_load_ocr)
        lay.addLayout(self._ocr_status_row)

        self._inner_layout.addWidget(self._box_ocr)

    def _build_detection_section(self) -> None:
        self._box_det = SectionGroup("Detection", self._scroll_widget)
        lay = self._box_det.inner_layout()

        self._conf_lbl = QLabel("Confidence", self._box_det)
        self._conf_lbl.setStyleSheet(
            f"color:{COLORS['text_secondary']};font-size:12px;"
            f"background:transparent;border:none;"
        )
        self._conf_val_lbl = QLabel("0.25", self._box_det)
        self._conf_val_lbl.setStyleSheet(
            f"color:{COLORS['accent']};font-size:12px;"
            f"font-family:'Consolas',monospace;font-weight:600;"
            f"background:transparent;border:none;"
        )
        self._conf_val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

        self._conf_hdr_row = QHBoxLayout()
        self._conf_hdr_row.addWidget(self._conf_lbl)
        self._conf_hdr_row.addStretch()
        self._conf_hdr_row.addWidget(self._conf_val_lbl)
        lay.addLayout(self._conf_hdr_row)

        self.conf_slider = QSlider(Qt.Orientation.Horizontal, self._box_det)
        self.conf_slider.setRange(0, 100)
        self.conf_slider.setValue(25)
        self.conf_slider.valueChanged.connect(
            lambda v: self._conf_val_lbl.setText(f"{v / 100:.2f}")
        )
        lay.addWidget(self.conf_slider)

        self.save_crops_check = QCheckBox("Save cropped detections", self._box_det)
        self.save_crops_check.setChecked(True)
        lay.addWidget(self.save_crops_check)

        self._inner_layout.addWidget(self._box_det)

    def _build_input_section(self) -> None:
        self._box_inp = SectionGroup("Input Files", self._scroll_widget)
        lay = self._box_inp.inner_layout()

        self.btn_add_files = QPushButton("+ Files", self._box_inp)
        self.btn_add_folder = QPushButton("+ Folder", self._box_inp)
        self.btn_clear = QPushButton("Clear", self._box_inp)
        self.btn_clear.setObjectName("danger")

        self.btn_add_files.clicked.connect(self.addFilesClicked)
        self.btn_add_folder.clicked.connect(self.addFolderClicked)
        self.btn_clear.clicked.connect(self.clearFilesClicked)

        self._btn_row = QHBoxLayout()
        self._btn_row.setSpacing(4)
        self._btn_row.addWidget(self.btn_add_files)
        self._btn_row.addWidget(self.btn_add_folder)
        self._btn_row.addWidget(self.btn_clear)
        lay.addLayout(self._btn_row)

        self._file_count_lbl = QLabel("0 files queued", self._box_inp)
        self._file_count_lbl.setStyleSheet(
            f"color:{COLORS['text_muted']};font-size:11px;"
            f"background:transparent;border:none;"
        )
        lay.addWidget(self._file_count_lbl)

        self._inner_layout.addWidget(self._box_inp)

    def _build_bottom(self, root: QVBoxLayout) -> None:
        """Pinned bottom strip — always visible regardless of scroll position."""
        self._bottom = QWidget(self)
        self._bottom.setStyleSheet(
            f"background:{COLORS['surface']};border-top:1px solid {COLORS['border']};"
        )
        self._bottom_lay = QVBoxLayout(self._bottom)
        self._bottom_lay.setContentsMargins(10, 8, 10, 10)
        self._bottom_lay.setSpacing(5)

        # ── hint label — shows what's missing before Run is enabled ──────
        self._hint_lbl = QLabel("", self._bottom)
        self._hint_lbl.setWordWrap(True)
        self._hint_lbl.setStyleSheet(
            f"color:{COLORS['warning']};"
            f"font-size:10px;"
            f"background:transparent;"
            f"border:none;"
            f"padding:2px 0;"
        )
        self._hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint_lbl.hide()  # hidden until needed
        self._bottom_lay.addWidget(self._hint_lbl)

        self._bottom_lay.addWidget(Divider(self._bottom))
        self._bottom_lay.addSpacing(2)

        self.btn_run = QPushButton("▶  Run Detection", self._bottom)
        self.btn_run.setObjectName("primary")
        self.btn_run.setFixedHeight(40)
        self.btn_run.setEnabled(False)
        self.btn_run.setToolTip(
            "Load a YOLO model, load the OCR engine, and add files first."
        )
        self.btn_run.clicked.connect(self.runClicked)
        self._bottom_lay.addWidget(self.btn_run)

        self.btn_export = QPushButton("↓  Export Results (ZIP)", self._bottom)
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self.exportClicked)
        self._bottom_lay.addWidget(self.btn_export)

        root.addWidget(self._bottom)

    # =========================================================================
    #  SLOTS / HELPERS
    # =========================================================================

    def _browse_model(self) -> None:
        """Open a native file-picker for .pt / .pth files."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select YOLO model",
            "",
            "PyTorch Model (*.pt *.pth)",
        )
        if path:
            self.model_path_edit.setText(path)

    # =========================================================================
    #  PUBLIC API  (called by MainWindow)
    # =========================================================================

    @property
    def model_path(self) -> str:
        """Stripped text of the model-path input field."""
        return self.model_path_edit.text().strip()

    @property
    def conf(self) -> float:
        """Confidence threshold as a float in [0.0, 1.0]."""
        return self.conf_slider.value() / 100.0

    @property
    def save_crops(self) -> bool:
        """Whether 'Save cropped detections' is checked."""
        return self.save_crops_check.isChecked()

    @property
    def use_gpu(self) -> bool:
        """Whether 'Use GPU' is checked."""
        return self.gpu_check.isChecked()

    @property
    def languages(self) -> list[str]:
        """EasyOCR language codes for the currently selected combo item."""
        return self._LANG_MAP.get(self.lang_combo.currentText(), ["id", "en"])

    def setFileCount(self, n: int) -> None:
        """Update the queued-file counter label."""
        word = "file" if n == 1 else "files"
        self._file_count_lbl.setText(f"{n} {word} queued")

    def setRunnable(self, enabled: bool) -> None:
        """Enable / disable the Run Detection button and clear the hint."""
        self.btn_run.setEnabled(enabled)
        if enabled:
            self._hint_lbl.hide()

    def setExportable(self, enabled: bool) -> None:
        """Enable / disable the Export Results button."""
        self.btn_export.setEnabled(enabled)

    def setRunHint(self, msg: str) -> None:
        """
        Show a short hint above the Run button explaining what's still needed.

        Pass an empty string to hide the hint.

        Called by MainWindow._update_run_state() to keep the user informed.
        """
        if msg:
            self._hint_lbl.setText(msg)
            self._hint_lbl.show()
        else:
            self._hint_lbl.hide()
