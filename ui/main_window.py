import os
import sys
import zipfile
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from core.file_utils import collect_files_from_folder, collect_files_from_paths
from core.inference import InferenceWorker
from core.model_loader import ModelLoader
from ui.panel_center import CenterPanel
from ui.panel_left import LeftPanel
from ui.panel_log import LogPanel
from ui.panel_right import RightPanel
from ui.theme import COLORS, STYLESHEET
from ui.widgets import Badge


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLO · OCR  —  Detection Suite")
        self.resize(1280, 820)
        self.setMinimumSize(900, 600)

        self._model: object = None
        self._reader: object = None
        self._files: list[dict] = []
        self._results: list[dict] = []
        self._output_dir: str | None = None

        self._model_loader: ModelLoader | None = None
        self._ocr_loader: ModelLoader | None = None
        self._worker: InferenceWorker | None = None

        self._build_ui()
        self._connect_signals()
        self._update_run_state()

        # ── auto-load model if models/best.pt is pre-filled ───────────────
        # Use a short delay so the window has time to show before the
        # (potentially slow) model-loading thread starts.
        if self.left.model_path and os.path.isfile(self.left.model_path):
            QTimer.singleShot(300, self._load_model)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_topbar())

        vsplit = QSplitter(Qt.Orientation.Vertical)
        vsplit.setHandleWidth(1)
        vsplit.addWidget(self._build_body())
        vsplit.addWidget(self._build_log_wrap())
        vsplit.setSizes([620, 130])
        vsplit.setCollapsible(0, False)
        vsplit.setCollapsible(1, False)
        root.addWidget(vsplit)

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(44)
        bar.setStyleSheet(
            f"background:{COLORS['surface']};"
            f"border-bottom:1px solid {COLORS['border']};"
        )

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(10)

        title = QLabel("YOLO · OCR")
        title.setStyleSheet(
            f"color:{COLORS['text_primary']};"
            f"font-size:13px;font-weight:700;"
            f"letter-spacing:1px;font-family:'Consolas',monospace;"
        )
        lay.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color:{COLORS['border']};")
        sep.setFixedWidth(1)
        lay.addWidget(sep)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedWidth(200)
        self._progress_bar.setFixedHeight(4)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setValue(0)
        lay.addWidget(self._progress_bar)

        self._progress_lbl = QLabel("")
        self._progress_lbl.setStyleSheet(
            f"color:{COLORS['text_muted']};"
            f"font-size:11px;font-family:'Consolas',monospace;"
            f"min-width:260px;"
        )
        lay.addWidget(self._progress_lbl)

        lay.addStretch()

        self._model_badge = Badge("idle", "Model")
        self._ocr_badge = Badge("idle", "OCR")
        lay.addWidget(self._model_badge)
        lay.addSpacing(8)
        lay.addWidget(self._ocr_badge)

        return bar

    def _build_body(self) -> QSplitter:
        self.left = LeftPanel()
        self.center = CenterPanel()
        self.right = RightPanel()

        body = QSplitter(Qt.Orientation.Horizontal)
        body.setHandleWidth(1)
        body.addWidget(self.left)
        body.addWidget(self.center)
        body.addWidget(self.right)
        body.setSizes([280, 580, 380])
        body.setCollapsible(0, False)
        body.setCollapsible(1, False)
        body.setCollapsible(2, False)

        return body

    def _build_log_wrap(self) -> QWidget:
        wrap = QWidget()
        wrap.setStyleSheet(
            f"background:{COLORS['surface']};border-top:1px solid {COLORS['border']};"
        )
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.log_panel = LogPanel()
        lay.addWidget(self.log_panel)

        return wrap

    def _connect_signals(self) -> None:
        L = self.left

        L.loadModelClicked.connect(self._load_model)
        L.loadOCRClicked.connect(self._load_ocr)
        L.addFilesClicked.connect(self._add_files)
        L.addFolderClicked.connect(self._add_folder)
        L.clearFilesClicked.connect(self._clear_files)
        L.runClicked.connect(self._run)
        L.exportClicked.connect(self._export)

        self.center.fileSelected.connect(self._on_file_selected)

    def _update_run_state(self) -> None:
        ready = bool(self._model and self._reader and self._files)
        self.left.setRunnable(ready)

        if ready:
            self.left.setRunHint("")
            return

        missing = []
        if not self._model:
            missing.append("① Load Model")
        if not self._reader:
            missing.append("② Load OCR")
        if not self._files:
            missing.append("③ Add files")
        self.left.setRunHint("  ·  ".join(missing))

    def _post_status(self, msg: str) -> None:
        self._status_bar.showMessage(msg)
        self.log_panel.append(msg)

    def _refresh_file_list(self) -> None:
        self.left.setFileCount(len(self._files))
        self.center.setFiles(self._files)
        self._update_run_state()

    def _load_model(self) -> None:
        path = self.left.model_path
        if not path or not os.path.isfile(path):
            QMessageBox.warning(
                self,
                "Model not found",
                f"File not found:\n{path or '(empty)'}",
            )
            return

        self.left.model_badge.setState("busy", "Loading…")
        self._model_badge.setState("busy", "Model")
        self.left.btn_load_model.setEnabled(False)
        self._post_status(f"Loading YOLO model — {os.path.basename(path)} …")

        self._model_loader = ModelLoader("yolo", model_path=path)
        self._model_loader.done.connect(self._on_loader_done)
        self._model_loader.error.connect(self._on_load_error)
        self._model_loader.start()

    def _load_ocr(self) -> None:
        self.left.ocr_badge.setState("busy", "Loading…")
        self._ocr_badge.setState("busy", "OCR")
        self.left.btn_load_ocr.setEnabled(False)
        self._post_status("Loading EasyOCR reader …")

        self._ocr_loader = ModelLoader(
            "ocr",
            languages=self.left.languages,
            use_gpu=self.left.use_gpu,
        )
        self._ocr_loader.done.connect(self._on_loader_done)
        self._ocr_loader.error.connect(self._on_load_error)
        self._ocr_loader.start()

    def _on_loader_done(self, obj: object, kind: str) -> None:
        if kind == "yolo":
            self._model = obj
            self.left.model_badge.setState("ok", "Ready")
            self._model_badge.setState("ok", "Model")
            self.left.btn_load_model.setEnabled(True)
            self._post_status("YOLO model loaded successfully.")

        elif kind == "ocr":
            self._reader = obj
            self.left.ocr_badge.setState("ok", "Ready")
            self._ocr_badge.setState("ok", "OCR")
            self.left.btn_load_ocr.setEnabled(True)
            self._post_status("EasyOCR reader loaded successfully.")

        self._update_run_state()

    def _on_load_error(self, msg: str) -> None:
        self.left.model_badge.setState("error", "Error")
        self.left.ocr_badge.setState("error", "Error")
        self._model_badge.setState("error", "Model")
        self._ocr_badge.setState("error", "OCR")
        self.left.btn_load_model.setEnabled(True)
        self.left.btn_load_ocr.setEnabled(True)
        self._post_status(f"Error: {msg}")
        QMessageBox.critical(self, "Load Error", msg)

    def _add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select images",
            "",
            "Images (*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.dcm)",
        )
        if not paths:
            return

        new_entries = collect_files_from_paths(paths)

        existing = {f["path"] for f in self._files if f.get("type") == "path"}
        added = [e for e in new_entries if e["path"] not in existing]

        self._files.extend(added)
        self._refresh_file_list()
        if added:
            self._post_status(f"Added {len(added)} file(s) to queue.")

    def _add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select folder")
        if not folder:
            return

        new_entries = collect_files_from_folder(folder)

        existing = {f["path"] for f in self._files if f.get("type") == "path"}
        added = [e for e in new_entries if e["path"] not in existing]

        self._files.extend(added)
        self._refresh_file_list()
        self._post_status(
            f"Added {len(added)} file(s) from {os.path.basename(folder)}/"
        )

    def _clear_files(self) -> None:
        self._files.clear()
        self._results.clear()
        self.center.clearResults()
        self._refresh_file_list()
        self.right.clear()
        self.left.setExportable(False)
        self._post_status("File queue cleared.")

    def _on_file_selected(self, file_dict: dict) -> None:
        name = file_dict.get("name", "")
        for r in self._results:
            if r.get("filename") == name:
                self.right.showResult(r)
                return
        self.right.clear()

    def _run(self) -> None:
        if self._worker and self._worker.isRunning():
            return

        self.left.btn_run.setEnabled(False)
        self.left.setExportable(False)
        self._progress_bar.setValue(0)
        self._progress_lbl.setText("")
        self._results = []
        self.right.clear()
        self._post_status("Starting detection …")

        self._worker = InferenceWorker(
            model=self._model,
            reader=self._reader,
            files=self._files,
            conf=self.left.conf,
            save_crops=self.left.save_crops,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.result.connect(self._on_result)
        self._worker.error.connect(self._on_inference_error)
        self._worker.log.connect(self.log_panel.append)
        self._worker.start()

    def _on_progress(self, pct: int, label: str) -> None:
        self._progress_bar.setValue(pct)
        self._progress_lbl.setText(label)

    def _on_result(self, results: list, output_dir: str) -> None:
        self._results = results
        self._output_dir = output_dir

        self._progress_bar.setValue(100)
        self._progress_lbl.setText("Done")

        self.left.btn_run.setEnabled(True)
        self.left.setExportable(True)

        for r in results:
            self.center.markProcessed(r["filename"], r)

        if results:
            self.right.showResult(results[0])

        self._post_status(f"Detection complete — {len(results)} image(s) processed.")
        self._update_run_state()

    def _on_inference_error(self, msg: str) -> None:
        self.left.btn_run.setEnabled(True)
        self._post_status(f"Error: {msg}")
        QMessageBox.critical(self, "Inference Error", msg)
        self._update_run_state()

    def _export(self) -> None:
        if not self._output_dir or not os.path.isdir(self._output_dir):
            QMessageBox.warning(self, "Nothing to export", "No output directory found.")
            return

        default_name = f"detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export results",
            default_name,
            "ZIP archive (*.zip)",
        )
        if not save_path:
            return

        try:
            with zipfile.ZipFile(save_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for dirpath, _dirs, filenames in os.walk(self._output_dir):
                    for fname in filenames:
                        abs_path = os.path.join(dirpath, fname)
                        arc_name = os.path.relpath(abs_path, self._output_dir)
                        zf.write(abs_path, arc_name)
            self._post_status(f"Exported → {save_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", str(exc))


def _apply_palette(app: QApplication) -> None:
    """Apply a dark Fusion palette so native widgets match the stylesheet."""
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(COLORS["bg"]))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(COLORS["text_primary"]))
    pal.setColor(QPalette.ColorRole.Base, QColor(COLORS["surface"]))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(COLORS["surface2"]))
    pal.setColor(QPalette.ColorRole.Text, QColor(COLORS["text_primary"]))
    pal.setColor(QPalette.ColorRole.Button, QColor(COLORS["surface2"]))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(COLORS["text_primary"]))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(COLORS["accent"]))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLORS["surface2"]))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor(COLORS["text_primary"]))
    app.setPalette(pal)


def _setup_dpi() -> None:
    """
    Configure High-DPI scaling before QApplication is created.

    On Windows with display scaling > 100 % (e.g. 125 %, 150 %), Qt can
    mis-map logical ↔ physical pixel coordinates, causing clicks to land
    on the wrong widget or the layout to collapse.  Setting these env vars
    before QApplication() ensures Qt uses the correct scale factor and
    keeps rounding consistent across the whole session.
    """
    # Let the OS report the true fractional scale factor instead of
    # rounding it to the nearest integer — critical for 125 % / 150 % DPI.
    os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
    # Honour per-monitor DPI changes when the window is moved between
    # screens with different scale factors.
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")


def launch() -> None:
    """Create the QApplication, apply theme, show the window, and run."""
    _setup_dpi()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    _apply_palette(app)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())
